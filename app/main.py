import os
import subprocess
import json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuration
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://host.docker.internal:11434/api/chat")
MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "mistral-nemo:12b-instruct-2407-fp16")
TIMEOUT = 60  # seconds
MAX_COMMANDS = int(os.getenv("MAX_COMMANDS", 5))  # Maximum number of commands per task

# Allowed commands whitelist (for security)
ALLOWED_COMMANDS = [
    "ls",
    "echo",
    "pwd",
    "cat",
    "mkdir",
    "touch",
    "rm",
    "cp",
    "mv",
    "grep",
    "find",
    # Add more allowed commands as needed
]

def sanitize_command(command):
    """
    Validates the command against the allowed commands whitelist.
    """
    if not command:
        return False, "Empty command."
    # Split the command to get the base command
    base_command = command.split()[0]
    if base_command not in ALLOWED_COMMANDS:
        return False, f"Command '{base_command}' is not allowed."
    return True, ""

def get_shell_command(messages):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False  # Disable streaming for simplicity
    }

    print("\n=== LLM Request ===")
    print("Messages:", json.dumps(messages, indent=2))
    
    response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()

    print("\n=== LLM Response ===")
    print(json.dumps(data, indent=2))

    assistant_message = data.get("message", {}).get("content", "").strip()
    return assistant_message

def execute_command(command):
    try:
        # Execute the command and capture the output
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=TIMEOUT, text=True)
        return {"success": True, "output": result}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.output}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Command timed out."}

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    task = data.get('task')

    if not task:
        return jsonify({"error": "No task provided."}), 400

    # Initialize conversation history
    messages = [
        {
            "role": "system",
            "content": "You are an AI assistant that helps execute shell commands based on the user's task. "
                       "Provide only the necessary shell commands to accomplish the task. "
                       "Do not output commands inside of ``` characters. Output only the content of the command."
                       "After each command, wait for the output before suggesting the next command."
                       "If the task is complete, output 'No further commands are needed.'"
        },
        {
            "role": "user",
            "content": f"Task: {task}"
        }
    ]

    command_count = 0
    final_output = ""

    while command_count < MAX_COMMANDS:
        try:
            command = get_shell_command(messages)
        except Exception as e:
            return jsonify({"error": f"Failed to get command from LLM: {str(e)}"}), 500

        # Sanitize and validate the command
        is_valid, error_msg = sanitize_command(command)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        execution_result = execute_command(command)

        # Append the executed command and its output to the conversation history
        messages.append({
            "role": "assistant",
            "content": command
        })
        messages.append({
            "role": "user",
            "content": execution_result.get("output", "")
        })

        final_output += f"Command: {command}\nOutput:\n{execution_result.get('output', '')}\n\n"

        if not execution_result.get("success", False):
            # If command execution failed, stop the loop
            break

        command_count += 1

        # Check if the assistant wants to stop
        if "No further commands are needed." in execution_result.get("output", ""):
            break

    return jsonify({
        "task": task,
        "commands_executed": command_count,
        "output": final_output
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5220)