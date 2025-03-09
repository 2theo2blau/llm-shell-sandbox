from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.task_service import TaskService
from app.services.filesystem_service import FilesystemService
from app.services.llm_service import LLMService
from app.services.command_service import CommandService
from app.services.python_service import PythonService
from app.controllers.task_controller import TaskController


# Create Blueprint
api = Blueprint('api', __name__)

# Initialize services
filesystem_service = FilesystemService()
task_service = TaskService(filesystem_service=filesystem_service)
llm_service = LLMService()
command_service = CommandService()
python_service = PythonService()

# Initialize controller
task_controller = TaskController(
    task_service=task_service,
    llm_service=llm_service,
    command_service=command_service,
    python_service=python_service
)


@api.route('/execute', methods=['POST'])
def execute_task():
    """
    Execute a task based on the natural language description.
    """
    data = request.get_json()
    task_description = data.get('task')

    if not task_description:
        return jsonify({"error": "No task provided."}), 400
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Execute the task
        result = task_controller.execute_task(db, task_description)
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        db.close()


@api.route('/tasks', methods=['GET'])
def get_recent_tasks():
    """
    Get recent tasks from the database.
    """
    limit = request.args.get('limit', default=10, type=int)
    
    # Get database session
    db = SessionLocal()
    
    try:
        tasks = task_service.get_recent_tasks(db, limit=limit)
        return jsonify([task.to_dict() for task in tasks]), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        db.close()


@api.route('/tasks/<int:task_id>', methods=['GET'])
def get_task_details(task_id):
    """
    Get details for a specific task.
    """
    # Get database session
    db = SessionLocal()
    
    try:
        task_history = task_service.get_task_history(db, task_id)
        return jsonify(task_history), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        db.close()


@api.route('/filesystem/snapshot', methods=['POST'])
def create_filesystem_snapshot():
    """
    Create a snapshot of the current filesystem state.
    """
    # Get database session
    db = SessionLocal()
    
    try:
        state_id = filesystem_service.capture_filesystem_state(db)
        return jsonify({"state_id": state_id}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        db.close()


@api.route('/filesystem/compare', methods=['POST'])
def compare_filesystem_states():
    """
    Compare two filesystem states.
    """
    data = request.get_json()
    previous_state_id = data.get('previous_state_id')
    
    if not previous_state_id:
        return jsonify({"error": "No previous state ID provided."}), 400
    
    # Get database session
    db = SessionLocal()
    
    try:
        state_id, changes = filesystem_service.compare_and_capture_changes(
            db, 
            previous_state_id=previous_state_id
        )
        
        return jsonify({
            "state_id": state_id,
            "changes": changes
        }), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        db.close()


@api.route('/command', methods=['POST'])
def execute_single_command():
    """
    Execute a single command directly.
    """
    data = request.get_json()
    command = data.get('command')
    
    if not command:
        return jsonify({"error": "No command provided."}), 400
    
    # Execute the command
    result = command_service.execute_command(command)
    return jsonify(result), 200


@api.route('/python/execute', methods=['POST'])
def execute_python():
    """
    Execute Python code directly.
    """
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({"error": "No Python code provided."}), 400
    
    use_file = data.get('use_file', True)
    
    # Execute the code
    result = python_service.execute_python_code(code, use_file=use_file)
    return jsonify(result), 200


@api.route('/python/file', methods=['POST'])
def create_python_file():
    """
    Create a Python file with the provided content.
    """
    data = request.get_json()
    file_path = data.get('file_path')
    code_content = data.get('code')
    
    if not file_path or not code_content:
        return jsonify({"error": "File path and code content are required."}), 400
    
    # Create the file
    result = python_service.create_python_file(file_path, code_content)
    return jsonify(result), 200 if result.get('success', False) else 400 