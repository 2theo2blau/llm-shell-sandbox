document.addEventListener('DOMContentLoaded', function() {
    // Initialize
    updateDirectoryTree();
    
    // Form submission handler
    document.getElementById('taskForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const taskInput = document.getElementById('taskInput');
        const task = taskInput.value.trim();
        
        if (!task) return;
        
        try {
            // Disable input while processing
            taskInput.disabled = true;
            
            const response = await fetch('/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task: task })
            });
            
            const data = await response.json();
            
            // Add to command history
            addToCommandHistory(task, data);
            
            // Update directory tree after command execution
            updateDirectoryTree();
            
        } catch (error) {
            console.error('Error:', error);
            addToCommandHistory(task, { error: 'Failed to execute task' });
        } finally {
            // Re-enable input
            taskInput.disabled = false;
            taskInput.value = '';
        }
    });
});

async function updateDirectoryTree() {
    try {
        const response = await fetch('/ls');
        const data = await response.json();
        const directoryTree = document.getElementById('directoryTree');
        directoryTree.textContent = data.output;
    } catch (error) {
        console.error('Error fetching directory structure:', error);
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
        outputElement.textContent = result.output;
    }
    
    entry.appendChild(outputElement);
    
    // Add to history
    history.insertBefore(entry, history.firstChild);
} 