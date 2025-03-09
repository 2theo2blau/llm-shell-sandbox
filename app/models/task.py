from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Task(Base):
    """Model to store task history and related information."""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    task_description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Store the commands executed for this task
    commands = Column(JSON, default=list)
    
    # Store the final status and output
    final_status = Column(String(50), default="pending")
    final_output = Column(Text, nullable=True)
    
    # Additional metadata
    execution_time_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationship with FilesystemState
    filesystem_states = relationship("FilesystemState", back_populates="task", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert the task model to a dictionary."""
        return {
            'id': self.id,
            'task_description': self.task_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_completed': self.is_completed,
            'commands': self.commands,
            'final_status': self.final_status,
            'final_output': self.final_output,
            'execution_time_seconds': self.execution_time_seconds,
            'error_message': self.error_message
        } 