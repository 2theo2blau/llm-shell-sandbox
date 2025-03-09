from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class FilesystemState(Base):
    """Model to store filesystem state snapshots."""
    __tablename__ = 'filesystem_states'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    state_type = Column(String(50), default="snapshot")  # Options: snapshot, before_command, after_command
    
    # Store the filesystem structure as a nested JSON object
    # Format: { path: { type: 'file|dir', size: bytes, last_modified: timestamp, hash: 'md5' } }
    filesystem_data = Column(JSON, nullable=False)
    
    # Reference to the command if this state is related to a specific command
    command_index = Column(Integer, nullable=True)
    command_text = Column(Text, nullable=True)
    
    # Changed files during this state transition
    # Format: [{ path: string, change_type: 'created|modified|deleted', before_hash: 'md5', after_hash: 'md5' }]
    changes = Column(JSON, default=list)
    
    # Relationship with Task
    task = relationship("Task", back_populates="filesystem_states")
    
    def to_dict(self):
        """Convert the filesystem state model to a dictionary."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'state_type': self.state_type,
            'filesystem_data': self.filesystem_data,
            'command_index': self.command_index,
            'command_text': self.command_text,
            'changes': self.changes
        } 