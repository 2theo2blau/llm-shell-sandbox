import os
import subprocess
from typing import Dict, Any, List, Optional


class CommandService:
    """Service to manage command execution and security."""
    
    def __init__(self, allowed_commands=None, timeout=120):
        """Initialize with optional allowed commands list and timeout."""
        self.timeout = timeout
        
        # Default allowed commands if none provided
        self.allowed_commands = allowed_commands or [
            "ls", "echo", "pwd", "cat", "mkdir", "touch", "rm", "cp", "mv",
            "grep", "find", "python", "python3", "pip", "cd", "wc"
        ]
    
    def sanitize_command(self, command: str) -> Dict[str, Any]:
        """
        Validate a command against security rules.
        Returns a dict with validation status and message.
        """
        if not command or not command.strip():
            return {"valid": False, "message": "Empty command."}
        
        # Split the command to get the base command
        base_command = command.split()[0]
        
        # Check if the base command is in the allowed list
        if base_command not in self.allowed_commands:
            return {"valid": False, "message": f"Command '{base_command}' is not allowed."}
        
        # Additional security checks could be implemented here
        # For example, checking for dangerous flags or patterns
        
        return {"valid": True, "message": "Command is valid."}
    
    def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a shell command and capture the output.
        Returns a dict with execution result.
        """
        # First, sanitize the command
        validation = self.sanitize_command(command)
        if not validation["valid"]:
            return {
                "success": False,
                "output": validation["message"],
                "command": command
            }
        
        try:
            # Execute the command and capture the output
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                cwd=cwd
            )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                if output:
                    output += "\n" + result.stderr
                else:
                    output = result.stderr
            
            return {
                "success": result.returncode == 0,
                "output": output,
                "command": command,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": f"Command timed out after {self.timeout} seconds.",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Error executing command: {str(e)}",
                "command": command
            }
    
    def execute_command_sequence(self, commands: List[str], cwd: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute a sequence of commands and return the results for each.
        """
        results = []
        
        for command in commands:
            result = self.execute_command(command, cwd)
            results.append(result)
            
            # Stop execution if a command fails
            if not result["success"]:
                break
        
        return results 