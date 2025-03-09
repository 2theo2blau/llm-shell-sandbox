document.addEventListener('DOMContentLoaded', function() {
    // Initialize
    updateDirectoryTree();
    loadTaskHistory();
    
    // Setup loading modal
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    
    // Form submission handler for tasks
    document.getElementById('taskForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const taskInput = document.getElementById('taskInput');
        const task = taskInput.value.trim();
        
        if (!task) return;
        
        try {
            // Show loading modal
            document.getElementById('loadingMessage').textContent = 'Executing task...';
            loadingModal.show();
            
            // Disable input while processing
            taskInput.disabled = true;
            
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task: task })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Add to command history
            addToCommandHistory(task, data);
            
            // Update directory tree after command execution
            updateDirectoryTree();
            
            // Refresh task history
            loadTaskHistory();
            
        } catch (error) {
            console.error('Error:', error);
            addToCommandHistory(task, { error: error.message || 'Failed to execute task' });
        } finally {
            // Re-enable input
            taskInput.disabled = false;
            taskInput.value = '';
            
            // Hide loading modal
            loadingModal.hide();
        }
    });
    
    // Python file form submission
    document.getElementById('pythonFileForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const filename = document.getElementById('pythonFilename').value.trim();
        const code = document.getElementById('pythonCode').value.trim();
        
        if (!filename || !code) {
            alert('Both filename and code are required');
            return;
        }
        
        try {
            // Show loading modal
            document.getElementById('loadingMessage').textContent = 'Creating Python file...';
            loadingModal.show();
            
            const response = await fetch('/api/python/file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    file_path: filename,
                    code: code
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to create Python file');
            }
            
            // Show success message in Python output
            const pythonOutput = document.getElementById('pythonOutput');
            pythonOutput.innerHTML = `<div class="alert alert-success">
                File created successfully: ${filename}
            </div>`;
            
            // Update directory tree
            updateDirectoryTree();
            
        } catch (error) {
            console.error('Error:', error);
            const pythonOutput = document.getElementById('pythonOutput');
            pythonOutput.innerHTML = `<div class="alert alert-danger">
                ${error.message || 'An error occurred'}
            </div>`;
        } finally {
            loadingModal.hide();
        }
    });
    
    // Execute Python code button
    document.getElementById('executeCodeBtn').addEventListener('click', async function() {
        const code = document.getElementById('pythonCode').value.trim();
        
        if (!code) {
            alert('Please enter Python code to execute');
            return;
        }
        
        try {
            // Show loading modal
            document.getElementById('loadingMessage').textContent = 'Executing Python code...';
            loadingModal.show();
            
            const response = await fetch('/api/python/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    code: code,
                    use_file: true
                })
            });
            
            const data = await response.json();
            
            // Display execution result
            const pythonOutput = document.getElementById('pythonOutput');
            
            if (data.success) {
                pythonOutput.innerHTML = `<pre class="bg-light p-3 border rounded">${data.output || 'No output'}</pre>`;
            } else {
                pythonOutput.innerHTML = `<div class="alert alert-danger">
                    <strong>Error:</strong>
                    <pre>${data.output || 'Unknown error'}</pre>
                </div>`;
            }
            
        } catch (error) {
            console.error('Error:', error);
            const pythonOutput = document.getElementById('pythonOutput');
            pythonOutput.innerHTML = `<div class="alert alert-danger">
                ${error.message || 'An error occurred'}
            </div>`;
        } finally {
            loadingModal.hide();
        }
    });
    
    // Create filesystem snapshot button
    document.getElementById('createSnapshotBtn').addEventListener('click', async function() {
        try {
            // Show loading modal
            document.getElementById('loadingMessage').textContent = 'Creating filesystem snapshot...';
            loadingModal.show();
            
            const response = await fetch('/api/filesystem/snapshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display snapshot ID
            const filesystemChanges = document.getElementById('filesystemChanges');
            filesystemChanges.innerHTML = `<div class="alert alert-success">
                Snapshot created with ID: ${data.state_id}
            </div>`;
            
        } catch (error) {
            console.error('Error:', error);
            const filesystemChanges = document.getElementById('filesystemChanges');
            filesystemChanges.innerHTML = `<div class="alert alert-danger">
                ${error.message || 'Failed to create snapshot'}
            </div>`;
        } finally {
            loadingModal.hide();
        }
    });
    
    // Compare filesystem states button
    document.getElementById('compareSnapshotsBtn').addEventListener('click', async function() {
        const previousStateId = prompt('Enter the previous state ID to compare with current state:');
        
        if (!previousStateId) return;
        
        try {
            // Show loading modal
            document.getElementById('loadingMessage').textContent = 'Comparing filesystem states...';
            loadingModal.show();
            
            const response = await fetch('/api/filesystem/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ previous_state_id: previousStateId })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display filesystem changes
            displayFilesystemChanges(data.changes);
            
        } catch (error) {
            console.error('Error:', error);
            const filesystemChanges = document.getElementById('filesystemChanges');
            filesystemChanges.innerHTML = `<div class="alert alert-danger">
                ${error.message || 'Failed to compare filesystem states'}
            </div>`;
        } finally {
            loadingModal.hide();
        }
    });
});

async function updateDirectoryTree() {
    try {
        const response = await fetch('/ls');
        const data = await response.json();
        const directoryTree = document.getElementById('directoryTree');
        
        if (data.success) {
            directoryTree.innerHTML = `<pre>${data.output}</pre>`;
        } else {
            directoryTree.innerHTML = `<div class="alert alert-danger">${data.error || 'Error loading directory'}</div>`;
        }
    } catch (error) {
        console.error('Error fetching directory structure:', error);
        const directoryTree = document.getElementById('directoryTree');
        directoryTree.innerHTML = `<div class="alert alert-danger">Failed to load directory structure</div>`;
    }
}

function addToCommandHistory(task, result) {
    const history = document.getElementById('commandHistory');
    const entry = document.createElement('div');
    entry.className = 'command-entry';
    
    // Add task
    const taskElement = document.createElement('div');
    taskElement.className = 'command-text';
    taskElement.textContent = `Task: ${task}`;
    entry.appendChild(taskElement);
    
    // Add output or error
    const outputElement = document.createElement('div');
    outputElement.className = 'command-output';
    
    if (result.error) {
        outputElement.classList.add('error-output');
        outputElement.textContent = result.error;
    } else {
        if (result.success === false) {
            outputElement.classList.add('error-output');
        } else if (result.success === true) {
            outputElement.classList.add('success-output');
        }
        outputElement.textContent = result.output;
    }
    
    entry.appendChild(outputElement);
    
    // Add to history
    history.insertBefore(entry, history.firstChild);
}

async function loadTaskHistory() {
    try {
        const response = await fetch('/api/tasks');
        const tasks = await response.json();
        
        const taskList = document.getElementById('taskList');
        
        if (tasks.error) {
            taskList.innerHTML = `<div class="alert alert-danger">${tasks.error}</div>`;
            return;
        }
        
        if (tasks.length === 0) {
            taskList.innerHTML = '<div class="text-muted">No tasks found</div>';
            return;
        }
        
        // Create tasks list
        taskList.innerHTML = '<ul class="list-group">' + 
            tasks.map(task => `
                <li class="list-group-item" data-task-id="${task.id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="task-description">${truncateText(task.task_description, 40)}</span>
                        <span class="badge ${getStatusBadgeClass(task.final_status)}">${task.final_status}</span>
                    </div>
                    <small class="text-muted">
                        ${new Date(task.created_at).toLocaleString()}
                    </small>
                </li>
            `).join('') + 
            '</ul>';
        
        // Add click event to task list items
        taskList.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', () => loadTaskDetails(item.dataset.taskId));
        });
        
    } catch (error) {
        console.error('Error loading task history:', error);
        const taskList = document.getElementById('taskList');
        taskList.innerHTML = '<div class="alert alert-danger">Failed to load task history</div>';
    }
}

async function loadTaskDetails(taskId) {
    try {
        const taskList = document.getElementById('taskList');
        taskList.querySelectorAll('.list-group-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.taskId === taskId) {
                item.classList.add('active');
            }
        });
        
        const response = await fetch(`/api/tasks/${taskId}`);
        const taskHistory = await response.json();
        
        if (taskHistory.error) {
            throw new Error(taskHistory.error);
        }
        
        const task = taskHistory.task;
        const filesystemStates = taskHistory.filesystem_states || [];
        
        // Display task details
        const taskDetails = document.getElementById('taskDetails');
        
        let commandsList = '';
        if (task.commands && task.commands.length > 0) {
            commandsList = `
                <h6 class="mt-3">Commands:</h6>
                <div class="commands-list">
                    ${task.commands.map((cmd, index) => `
                        <div class="command-entry">
                            <div class="command-text">
                                <span class="badge bg-secondary">${index + 1}</span> 
                                ${cmd.command}
                            </div>
                            <div class="command-output ${cmd.success ? 'success-output' : 'error-output'}">
                                <pre>${cmd.output || 'No output'}</pre>
                            </div>
                            ${cmd.filesystem_changes && cmd.filesystem_changes.length > 0 ? 
                                `<div class="filesystem-changes small">
                                    <span class="badge bg-info">${cmd.filesystem_changes.length} filesystem changes</span>
                                </div>` : 
                                ''}
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            commandsList = '<div class="text-muted">No commands executed</div>';
        }
        
        taskDetails.innerHTML = `
            <div class="task-header">
                <h5>${task.task_description}</h5>
                <div class="d-flex gap-2 align-items-center">
                    <span class="badge ${getStatusBadgeClass(task.final_status)}">${task.final_status}</span>
                    ${task.execution_time_seconds ? 
                        `<span class="badge bg-secondary">
                            <i class="bi bi-clock"></i> ${formatTime(task.execution_time_seconds)}
                        </span>` : 
                        ''}
                </div>
                <div class="text-muted small">
                    Created: ${new Date(task.created_at).toLocaleString()}
                    ${task.completed_at ? 
                        ` • Completed: ${new Date(task.completed_at).toLocaleString()}` : 
                        ''}
                </div>
            </div>
            ${commandsList}
        `;
        
    } catch (error) {
        console.error('Error loading task details:', error);
        const taskDetails = document.getElementById('taskDetails');
        taskDetails.innerHTML = `<div class="alert alert-danger">${error.message || 'Failed to load task details'}</div>`;
    }
}

function displayFilesystemChanges(changes) {
    const filesystemChanges = document.getElementById('filesystemChanges');
    
    if (!changes || changes.length === 0) {
        filesystemChanges.innerHTML = '<div class="text-muted">No changes detected</div>';
        return;
    }
    
    const changesList = document.createElement('div');
    changesList.className = 'changes-list';
    
    changes.forEach(change => {
        const changeItem = document.createElement('div');
        changeItem.className = `change-item change-${change.change_type}`;
        
        const iconClass = {
            created: 'bi-plus-circle-fill text-success',
            modified: 'bi-pencil-fill text-warning',
            deleted: 'bi-trash-fill text-danger'
        };
        
        changeItem.innerHTML = `
            <div class="change-header">
                <i class="bi ${iconClass[change.change_type]}"></i>
                <span class="change-path">${change.path}</span>
                <span class="badge bg-secondary">${change.file_type}</span>
            </div>
            ${change.change_type === 'modified' ? 
                `<div class="change-details">
                    <small class="text-muted">Before hash: ${change.before_hash || 'N/A'}</small>
                    <small class="text-muted">After hash: ${change.after_hash || 'N/A'}</small>
                </div>` : 
                ''}
        `;
        
        changesList.appendChild(changeItem);
    });
    
    filesystemChanges.innerHTML = '';
    filesystemChanges.appendChild(changesList);
}

// Helper functions
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substr(0, maxLength) + '...' : text;
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'completed':
            return 'bg-success';
        case 'failed':
            return 'bg-danger';
        case 'pending':
            return 'bg-warning';
        case 'incomplete':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

function formatTime(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
} 