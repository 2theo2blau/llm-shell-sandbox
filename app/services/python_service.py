import os
import tempfile
import subprocess
from pathlib import Path


class PythonService:
    """Service to manage Python code execution and file operations."""
    
    def __init__(self, base_path="/app"):
        """Initialize with the base path for operations."""
        self.base_path = base_path
    
    def create_python_file(self, file_path, code_content):
        """
        Create a Python file with the given content.
        Returns a dict with success status and message.
        """
        try:
            # Ensure the file path is relative to the base path
            if os.path.isabs(file_path):
                # If absolute path is provided, ensure it's inside the base path
                if not file_path.startswith(self.base_path):
                    return {
                        "success": False,
                        "message": f"For security reasons, cannot create files outside of {self.base_path}"
                    }
                full_path = file_path
            else:
                # Handle relative paths
                full_path = os.path.join(self.base_path, file_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file
            with open(full_path, 'w') as f:
                f.write(code_content)
            
            return {
                "success": True,
                "message": f"Created Python file at {file_path}",
                "path": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create Python file: {str(e)}"
            }
    
    def execute_python_code(self, code, use_file=False):
        """
        Execute Python code either directly or from a temporary file.
        Returns dict with execution result.
        """
        try:
            if use_file:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(suffix='.py', dir=self.base_path, delete=False) as tmp_file:
                    tmp_file.write(code.encode('utf-8'))
                    tmp_path = tmp_file.name
                
                # Execute the file
                try:
                    output = subprocess.check_output(
                        ['python', tmp_path], 
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=30
                    )
                    success = True
                except subprocess.CalledProcessError as e:
                    output = e.output
                    success = False
                except subprocess.TimeoutExpired:
                    output = "Execution timed out after 30 seconds."
                    success = False
                
                # Clean up the temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            else:
                # Execute code directly through python -c
                try:
                    output = subprocess.check_output(
                        ['python', '-c', code],
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=30
                    )
                    success = True
                except subprocess.CalledProcessError as e:
                    output = e.output
                    success = False
                except subprocess.TimeoutExpired:
                    output = "Execution timed out after 30 seconds."
                    success = False
            
            return {
                "success": success,
                "output": output
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Error executing Python code: {str(e)}"
            }
    
    def execute_python_file(self, file_path, args=None):
        """
        Execute a Python file with optional arguments.
        Returns dict with execution result.
        """
        try:
            # Ensure the file path is relative to the base path
            if os.path.isabs(file_path):
                # If absolute path is provided, ensure it's inside the base path
                if not file_path.startswith(self.base_path):
                    return {
                        "success": False,
                        "output": f"For security reasons, cannot execute files outside of {self.base_path}"
                    }
                full_path = file_path
            else:
                # Handle relative paths
                full_path = os.path.join(self.base_path, file_path)
            
            # Validate the file exists
            if not os.path.isfile(full_path):
                return {
                    "success": False,
                    "output": f"Python file not found: {file_path}"
                }
            
            # Prepare command
            command = ['python', full_path]
            if args:
                if isinstance(args, list):
                    command.extend(args)
                else:
                    command.append(args)
            
            # Execute the file
            try:
                output = subprocess.check_output(
                    command,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30
                )
                success = True
            except subprocess.CalledProcessError as e:
                output = e.output
                success = False
            except subprocess.TimeoutExpired:
                output = "Execution timed out after 30 seconds."
                success = False
            
            return {
                "success": success,
                "output": output
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Error executing Python file: {str(e)}"
            } 