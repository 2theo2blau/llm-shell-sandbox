import os
import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.filesystem_state import FilesystemState


class FilesystemService:
    """Service to track and manage filesystem state."""
    
    def __init__(self, base_path="/app"):
        """Initialize with the base path to track."""
        self.base_path = base_path
    
    def capture_filesystem_state(self, db: Session, task_id=None, state_type="snapshot", 
                                command_index=None, command_text=None):
        """
        Capture the current state of the filesystem.
        Returns the ID of the created FilesystemState.
        """
        # Get the current filesystem structure
        fs_data = self._scan_filesystem(self.base_path)
        
        # Create a new filesystem state record
        fs_state = FilesystemState(
            task_id=task_id,
            state_type=state_type,
            filesystem_data=fs_data,
            command_index=command_index,
            command_text=command_text,
            changes=[]  # No changes for a snapshot
        )
        
        db.add(fs_state)
        db.commit()
        db.refresh(fs_state)
        
        return fs_state.id
    
    def compare_and_capture_changes(self, db: Session, previous_state_id, task_id=None, 
                                  state_type="after_command", command_index=None, command_text=None):
        """
        Compare the current filesystem state with a previous state,
        record the changes, and create a new state record.
        """
        # Get the previous state
        previous_state = db.query(FilesystemState).filter(FilesystemState.id == previous_state_id).first()
        if not previous_state:
            raise ValueError(f"Previous state with ID {previous_state_id} not found")
        
        # Get the current filesystem structure
        current_fs_data = self._scan_filesystem(self.base_path)
        
        # Compare and identify changes
        changes = self._compare_filesystem_states(previous_state.filesystem_data, current_fs_data)
        
        # Create a new filesystem state record with the changes
        fs_state = FilesystemState(
            task_id=task_id,
            state_type=state_type,
            filesystem_data=current_fs_data,
            command_index=command_index,
            command_text=command_text,
            changes=changes
        )
        
        db.add(fs_state)
        db.commit()
        db.refresh(fs_state)
        
        return fs_state.id, changes
    
    def _scan_filesystem(self, path):
        """
        Recursively scan the filesystem and return a structured representation.
        """
        result = {}
        
        for root, dirs, files in os.walk(path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Process regular files
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.base_path)
                
                try:
                    stat_info = os.stat(file_path)
                    file_hash = self._calculate_file_hash(file_path) if os.path.isfile(file_path) else None
                    
                    result[rel_path] = {
                        'type': 'file',
                        'size': stat_info.st_size,
                        'last_modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        'hash': file_hash
                    }
                except Exception as e:
                    # Skip files we can't access
                    continue
            
            # Add directories
            for directory in dirs:
                dir_path = os.path.join(root, directory)
                rel_path = os.path.relpath(dir_path, self.base_path)
                
                try:
                    stat_info = os.stat(dir_path)
                    
                    result[rel_path] = {
                        'type': 'dir',
                        'last_modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    }
                except Exception as e:
                    # Skip directories we can't access
                    continue
        
        return result
    
    def _calculate_file_hash(self, file_path, block_size=65536):
        """Calculate MD5 hash of a file."""
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(block_size), b''):
                    md5.update(block)
            return md5.hexdigest()
        except Exception as e:
            return None
    
    def _compare_filesystem_states(self, old_state, new_state):
        """
        Compare two filesystem states and return a list of changes.
        """
        changes = []
        
        # Check for created and modified files
        for path, info in new_state.items():
            if path not in old_state:
                changes.append({
                    'path': path,
                    'change_type': 'created',
                    'file_type': info.get('type', 'file'),
                    'after_hash': info.get('hash')
                })
            elif info.get('type') == 'file' and old_state[path].get('hash') != info.get('hash'):
                changes.append({
                    'path': path,
                    'change_type': 'modified',
                    'file_type': 'file',
                    'before_hash': old_state[path].get('hash'),
                    'after_hash': info.get('hash')
                })
        
        # Check for deleted files and directories
        for path, info in old_state.items():
            if path not in new_state:
                changes.append({
                    'path': path,
                    'change_type': 'deleted',
                    'file_type': info.get('type', 'file'),
                    'before_hash': info.get('hash')
                })
        
        return changes 