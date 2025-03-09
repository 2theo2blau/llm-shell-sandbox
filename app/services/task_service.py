import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.task import Task
from app.services.filesystem_service import FilesystemService
from app.models.filesystem_state import FilesystemState


class TaskService:
    """Service to manage task execution and history."""
    
    def __init__(self, filesystem_service: FilesystemService = None):
        """Initialize with optional filesystem service."""
        self.filesystem_service = filesystem_service or FilesystemService()
    
    def create_task(self, db: Session, task_description: str):
        """
        Create a new task and record the initial filesystem state.
        Returns the created task.
        """
        # Create the task
        task = Task(
            task_description=task_description,
            commands=[],
            final_status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Capture initial filesystem state if filesystem service is available
        if self.filesystem_service:
            state_id = self.filesystem_service.capture_filesystem_state(
                db=db,
                task_id=task.id,
                state_type="initial"
            )
        
        return task
    
    def update_task_with_command(self, db: Session, task_id: int, command: str, 
                               command_output: str, success: bool):
        """
        Update a task with a new command execution result.
        Returns the updated task.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Get command index (position in the commands list)
        command_index = len(task.commands)
        
        # Capture filesystem state before command if filesystem service is available
        before_state_id = None
        if self.filesystem_service:
            before_state_id = self.filesystem_service.capture_filesystem_state(
                db=db,
                task_id=task.id,
                state_type="before_command",
                command_index=command_index,
                command_text=command
            )
        
        # Add command to task history
        command_data = {
            "command": command,
            "output": command_output,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update task commands
        updated_commands = task.commands.copy() if task.commands else []
        updated_commands.append(command_data)
        task.commands = updated_commands
        
        db.commit()
        db.refresh(task)
        
        # Capture filesystem state after command if filesystem service is available
        if self.filesystem_service and before_state_id:
            after_state_id, changes = self.filesystem_service.compare_and_capture_changes(
                db=db,
                previous_state_id=before_state_id,
                task_id=task.id,
                state_type="after_command",
                command_index=command_index,
                command_text=command
            )
            
            # Enhance command data with filesystem changes
            updated_commands[-1]["filesystem_changes"] = changes
            task.commands = updated_commands
            db.commit()
        
        return task
    
    def complete_task(self, db: Session, task_id: int, final_status: str = "completed", 
                     final_output: str = None, error_message: str = None):
        """
        Mark a task as completed and capture the final state.
        """
        start_time = time.time()
        
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Update task
        task.is_completed = True
        task.completed_at = datetime.utcnow()
        task.final_status = final_status
        task.final_output = final_output
        task.error_message = error_message
        
        # Calculate execution time
        if task.created_at:
            task.execution_time_seconds = int(time.time() - time.mktime(task.created_at.timetuple()))
        
        # Capture final filesystem state
        if self.filesystem_service:
            final_state_id = self.filesystem_service.capture_filesystem_state(
                db=db,
                task_id=task.id,
                state_type="final"
            )
        
        db.commit()
        db.refresh(task)
        
        return task
    
    def get_task(self, db: Session, task_id: int):
        """Get a task by ID."""
        return db.query(Task).filter(Task.id == task_id).first()
    
    def get_recent_tasks(self, db: Session, limit: int = 10):
        """Get the most recent tasks."""
        return db.query(Task).order_by(Task.created_at.desc()).limit(limit).all()
    
    def get_task_history(self, db: Session, task_id: int):
        """
        Get detailed task history, including commands and filesystem changes.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Get all filesystem states for this task
        filesystem_states = db.query(FilesystemState).filter(
            FilesystemState.task_id == task_id
        ).order_by(FilesystemState.timestamp).all()
        
        return {
            "task": task.to_dict(),
            "filesystem_states": [state.to_dict() for state in filesystem_states]
        } 