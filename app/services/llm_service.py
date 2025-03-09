import os
import json
import requests
from typing import List, Dict, Any, Optional


class LLMService:
    """Service to handle interactions with the LLM for command and code generation."""
    
    def __init__(self, 
                 api_url=None, 
                 model_name=None, 
                 temperature=0.3, 
                 context_length=8192, 
                 timeout=120):
        """Initialize with LLM configuration."""
        self.api_url = api_url or os.getenv("OLLAMA_API_URL", "http://host.docker.internal:11434/api/chat")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME", "mistral-nemo:12b-instruct-2409-fp16")
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", str(temperature)))
        self.context_length = int(os.getenv("OLLAMA_CONTEXT_LENGTH", str(context_length)))
        self.timeout = int(os.getenv("TIMEOUT_SECONDS", str(timeout)))
    
    def generate_shell_command(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a shell command based on the provided messages.
        Returns the generated command as a string.
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_length
            }
        }
        
        try:
            print("\n=== LLM Request (Shell Command) ===")
            print("Messages:", json.dumps(messages, indent=2))
            print("Configuration:", json.dumps(payload["options"], indent=2))
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            print("\n=== LLM Response ===")
            print(json.dumps(data, indent=2))
            
            return data.get("message", {}).get("content", "").strip()
        
        except Exception as e:
            print(f"Error generating shell command: {str(e)}")
            return f"ERROR: {str(e)}"
    
    def generate_python_code(self, prompt: str, file_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate Python code based on the provided prompt.
        Returns a dict with the generated code and metadata.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant specialized in writing Python code. "
                    "Generate clean, well-documented, and efficient Python code based on the user's requirements. "
                    "Only respond with the Python code itself, without any markdown formatting, explanations, or comments outside the code. "
                    "Include appropriate docstrings and comments inside the code. "
                    "Make sure the code is complete, correct, and ready to execute."
                )
            },
            {
                "role": "user",
                "content": f"Write Python code for the following task: {prompt}"
                           + (f"\n\nThis code will be saved to a file with the following description: {file_description}" 
                              if file_description else "")
            }
        ]
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_length
            }
        }
        
        try:
            print("\n=== LLM Request (Python Code) ===")
            print("Prompt:", prompt)
            print("Configuration:", json.dumps(payload["options"], indent=2))
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            code = data.get("message", {}).get("content", "").strip()
            
            # Clean up code if it has markdown code blocks
            if code.startswith("```python"):
                code = code[len("```python"):].strip()
            if code.startswith("```"):
                code = code[len("```"):].strip()
            if code.endswith("```"):
                code = code[:-len("```")].strip()
            
            return {
                "success": True,
                "code": code,
                "prompt": prompt,
                "file_description": file_description
            }
        
        except Exception as e:
            print(f"Error generating Python code: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
    
    def analyze_command_result(self, 
                              task: str, 
                              command: str, 
                              output: str, 
                              previous_commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the result of a command execution and determine next steps.
        Returns a dict with analysis and recommendation.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that helps analyze shell command outputs and determine next steps. "
                    "Based on the task, command executed, and its output, determine if the task is complete or what command should be executed next. "
                    "Provide your assessment and, if the task is not complete, suggest the next command to run."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\n"
                    f"Command executed: {command}\n\n"
                    f"Command output: {output}\n\n"
                    f"Previous commands: {json.dumps(previous_commands, indent=2)}\n\n"
                    "Is the task complete? If not, what should be the next command to execute? "
                    "Respond with a JSON object with the following structure:\n"
                    "{\n"
                    '  "task_complete": true/false,\n'
                    '  "next_command": "command to execute if task is not complete",\n'
                    '  "explanation": "brief explanation of your assessment"\n'
                    "}"
                )
            }
        ]
        
        try:
            response_text = self.generate_shell_command(messages)
            
            # Extract JSON from response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    # Default response if JSON not found
                    result = {
                        "task_complete": False,
                        "next_command": "",
                        "explanation": "Failed to parse LLM response as JSON."
                    }
            except json.JSONDecodeError:
                # Default response if JSON parsing fails
                result = {
                    "task_complete": False,
                    "next_command": "",
                    "explanation": "Failed to parse LLM response as JSON."
                }
            
            return result
            
        except Exception as e:
            return {
                "task_complete": False,
                "next_command": "",
                "explanation": f"Error analyzing command result: {str(e)}"
            } 