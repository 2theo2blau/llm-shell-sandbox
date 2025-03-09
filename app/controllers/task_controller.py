import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.task_service import TaskService
from app.services.llm_service import LLMService
from app.services.command_service import CommandService
from app.services.python_service import PythonService
from app.services.filesystem_service import FilesystemService


class TaskController:
    """Controller to coordinate task execution flow."""
    
    def __init__(self, 
                 task_service: TaskService,
                 llm_service: LLMService,
                 command_service: CommandService,
                 python_service: PythonService = None,
                 max_commands: int = 10):
        """Initialize with required services."""
        self.task_service = task_service
        self.llm_service = llm_service
        self.command_service = command_service
        self.python_service = python_service
        self.max_commands = max_commands
    
    def execute_task(self, db: Session, task_description: str) -> Dict[str, Any]:
        """
        Execute a complete task, generating and running commands as needed.
        Returns a dict with task execution results.
        """
        # Create a new task in the database
        task = self.task_service.create_task(db, task_description)
        
        # Initialize conversation history with system prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that helps execute shell commands based on the user's task. "
                    "Provide only the necessary shell commands to accomplish the task. Output only one command at a time. "
                    "After each command, evaluate if the task is complete based on the command output. "
                    "If the task is complete, respond with exactly 'TASK_COMPLETE'. "
                    "Consider all previously executed commands and their outputs when determining if additional commands are needed. "
                    "Avoid repeating commands unless absolutely necessary."
                )
            },
            {
                "role": "user",
                "content": f"Task: {task_description}\nPreviously executed commands: []"
            }
        ]
        
        command_count = 0
        task_complete = False
        final_output = ""
        executed_commands = []
        
        # Execute commands until task is complete or max commands reached
        while command_count < self.max_commands and not task_complete:
            # Generate command
            try:
                command = self.llm_service.generate_shell_command(messages)
            except Exception as e:
                error_msg = f"Failed to get command from LLM: {str(e)}"
                self.task_service.complete_task(db, task.id, "failed", error_message=error_msg)
                return {
                    "task_id": task.id,
                    "success": False,
                    "error": error_msg
                }
            
            # Check if task is complete
            if command.strip() == "TASK_COMPLETE":
                task_complete = True
                break
            
            # Check if command is a special directive for generating Python code
            if command.startswith("PYTHON_FILE:") or command.startswith("PYTHON_CODE:"):
                self._handle_python_command(db, task, command, executed_commands, messages)
                command_count += 1
                continue
            
            # Execute the command
            execution_result = self.command_service.execute_command(command)
            executed_commands.append({
                "command": command,
                "output": execution_result.get("output", ""),
                "success": execution_result.get("success", False)
            })
            
            # Update task with command result
            self.task_service.update_task_with_command(
                db, 
                task.id, 
                command, 
                execution_result.get("output", ""), 
                execution_result.get("success", False)
            )
            
            # Append to final output
            final_output += f"Command: {command}\nOutput:\n{execution_result.get('output', '')}\n\n"
            
            # Analyze command result to determine if task is complete
            analysis = self.llm_service.analyze_command_result(
                task_description,
                command,
                execution_result.get("output", ""),
                executed_commands
            )
            
            if analysis.get("task_complete", False):
                task_complete = True
                break
            
            # Add the executed command and its output to conversation history
            messages.append({
                "role": "assistant",
                "content": command
            })
            messages.append({
                "role": "user",
                "content": (
                    f"Command output: {execution_result.get('output', '')}\n"
                    f"Current task status: {task_description}\n"
                    f"Previously executed commands: {[cmd.get('command') for cmd in executed_commands]}\n"
                    "If the task is complete, respond with exactly 'TASK_COMPLETE'. "
                    "Otherwise, provide the next command needed."
                )
            })
            
            command_count += 1
        
        # Update task status
        final_status = "completed" if task_complete else "incomplete"
        self.task_service.complete_task(db, task.id, final_status, final_output=final_output)
        
        return {
            "task_id": task.id,
            "success": task_complete,
            "commands_executed": command_count,
            "output": final_output
        }
    
    def _handle_python_command(self, db: Session, task, command, executed_commands, messages):
        """Helper method to handle Python code generation and execution."""
        if not self.python_service:
            result = {
                "success": False,
                "output": "Python service is not available."
            }
        else:
            # Parse the Python command
            if command.startswith("PYTHON_FILE:"):
                # Format: PYTHON_FILE:filename.py:description
                parts = command.split(":", 2)
                filename = parts[1] if len(parts) > 1 else "script.py"
                description = parts[2] if len(parts) > 2 else "Generate a Python script"
                
                # Generate code
                code_result = self.llm_service.generate_python_code(description, filename)
                
                if code_result.get("success", False):
                    # Create the file
                    file_result = self.python_service.create_python_file(filename, code_result.get("code", ""))
                    
                    if file_result.get("success", False):
                        result = {
                            "success": True,
                            "output": f"Created Python file: {filename}\n{file_result.get('message', '')}"
                        }
                    else:
                        result = file_result
                else:
                    result = code_result
            
            elif command.startswith("PYTHON_CODE:"):
                # Format: PYTHON_CODE:description
                description = command[len("PYTHON_CODE:"):]
                
                # Generate code
                code_result = self.llm_service.generate_python_code(description)
                
                if code_result.get("success", False):
                    # Execute the code
                    exec_result = self.python_service.execute_python_code(
                        code_result.get("code", ""),
                        use_file=True
                    )
                    
                    result = {
                        "success": exec_result.get("success", False),
                        "output": f"Python code execution:\n{exec_result.get('output', '')}"
                    }
                else:
                    result = code_result
            else:
                result = {
                    "success": False,
                    "output": "Invalid Python command format."
                }
        
        # Update records
        executed_commands.append({
            "command": command,
            "output": result.get("output", ""),
            "success": result.get("success", False)
        })
        
        # Update task with command result
        self.task_service.update_task_with_command(
            db, 
            task.id, 
            command, 
            result.get("output", ""), 
            result.get("success", False)
        )
        
        # Add to conversation history
        messages.append({
            "role": "assistant",
            "content": command
        })
        messages.append({
            "role": "user",
            "content": (
                f"Command output: {result.get('output', '')}\n"
                f"Previously executed commands: {[cmd.get('command') for cmd in executed_commands]}\n"
                "If the task is complete, respond with exactly 'TASK_COMPLETE'. "
                "Otherwise, provide the next command needed."
            )
        }) 