/**
 * Task Bell Manager
 * Manages the task notification bell in the header
 * Requires: task_notifications.js (taskNotifications must be available)
 */

class TaskBellManager {
    constructor() {
        this.tasks = new Map();
        this.badge = document.getElementById('taskBadge');
        this.countHeader = document.getElementById('taskCountHeader');
        this.container = document.getElementById('taskListContainer');
        this.noTasksMessage = document.getElementById('noTasksMessage');
        this.taskFooter = document.getElementById('taskFooter');
        this.clearBtn = document.getElementById('clearCompletedTasks');

        this.init();
    }

    init() {
        // Clear completed tasks button
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearCompleted();
            });
        }

        // Listen for WebSocket task events
        if (typeof taskNotifications !== 'undefined') {
            taskNotifications.on('task_update', (data) => this.handleTaskUpdate(data));
            taskNotifications.on('task_complete', (data) => this.handleTaskComplete(data));
            taskNotifications.on('task_error', (data) => this.handleTaskError(data));
            taskNotifications.on('active_tasks', (data) => this.handleActiveTasks(data));
        } else {
            console.warn('TaskBellManager: taskNotifications not available, retrying in 1s...');
            setTimeout(() => this.init(), 1000);
        }
    }

    // Handle active tasks received on WebSocket connect (for persistence across page refreshes)
    handleActiveTasks(data) {
        const { tasks } = data;
        console.log(`TaskBell: Loading ${tasks.length} active tasks`);

        tasks.forEach(task => {
            const taskData = {
                id: task.task_id,
                name: task.name,
                message: task.message,
                progress: task.progress || 0,
                status: task.status,
                startTime: new Date(task.created_at),
                updateTime: new Date(task.updated_at)
            };

            this.tasks.set(task.task_id, taskData);
        });

        this.renderTasks();
        this.updateBadge();
    }

    // Add or update a task
    addTask(taskId, taskName, message = 'Starting...', progress = 0) {
        const task = {
            id: taskId,
            name: taskName,
            message: message,
            progress: progress,
            status: 'processing',
            startTime: new Date(),
            updateTime: new Date()
        };

        this.tasks.set(taskId, task);

        // Auto-subscribe to task updates via WebSocket
        if (typeof taskNotifications !== 'undefined') {
            taskNotifications.subscribe(taskId);
        }

        this.renderTasks();
        this.updateBadge();

        return taskId;
    }

    // Handle task update from WebSocket
    handleTaskUpdate(data) {
        const { task_id, message, progress, status } = data;

        let task = this.tasks.get(task_id);

        if (!task) {
            task = {
                id: task_id,
                name: `Task ${task_id.substring(0, 8)}...`,
                message: message,
                progress: progress || 0,
                status: status || 'processing',
                startTime: new Date(),
                updateTime: new Date()
            };
            this.tasks.set(task_id, task);
        } else {
            task.message = message;
            task.progress = progress || task.progress;
            task.status = status || task.status;
            task.updateTime = new Date();
        }

        this.renderTasks();
        this.updateBadge();
    }

    // Handle task completion
    handleTaskComplete(data) {
        const { task_id, message, result } = data;

        let task = this.tasks.get(task_id);

        if (task) {
            task.status = 'completed';
            task.message = message;
            task.progress = 100;
            task.updateTime = new Date();
            task.result = result;
        } else {
            task = {
                id: task_id,
                name: `Task ${task_id.substring(0, 8)}...`,
                message: message,
                progress: 100,
                status: 'completed',
                startTime: new Date(),
                updateTime: new Date(),
                result: result
            };
            this.tasks.set(task_id, task);
        }

        this.renderTasks();
        this.updateBadge();

        // Auto-remove completed tasks after 30 seconds
        setTimeout(() => {
            if (this.tasks.get(task_id)?.status === 'completed') {
                this.removeTask(task_id);
            }
        }, 30000);
    }

    // Handle task error
    handleTaskError(data) {
        const { task_id, error, message } = data;

        let task = this.tasks.get(task_id);

        if (task) {
            task.status = 'error';
            task.message = message || error;
            task.updateTime = new Date();
            task.error = error;
        } else {
            task = {
                id: task_id,
                name: `Task ${task_id.substring(0, 8)}...`,
                message: message || error,
                progress: 0,
                status: 'error',
                startTime: new Date(),
                updateTime: new Date(),
                error: error
            };
            this.tasks.set(task_id, task);
        }

        this.renderTasks();
        this.updateBadge();
    }

    // Remove a task
    removeTask(taskId, dismissOnServer = true) {
        this.tasks.delete(taskId);
        this.renderTasks();
        this.updateBadge();

        if (dismissOnServer) {
            this.dismissTaskOnServer(taskId);
        }
    }

    // Dismiss task on server
    async dismissTaskOnServer(taskId) {
        try {
            const formData = new FormData();
            formData.append('module', 'OptsIO');
            formData.append('package', 'io_tasks');
            formData.append('attr', 'IOTasks');
            formData.append('mname', 'dismiss_task');
            formData.append('task_id', taskId);

            await axios.post('/io/iom/', formData);
            console.log(`Task ${taskId} dismissed on server`);
        } catch (error) {
            console.error(`Error dismissing task ${taskId}:`, error);
        }
    }

    // Clear all completed tasks
    clearCompleted() {
        const taskIdsToRemove = [];

        for (const [taskId, task] of this.tasks) {
            if (task.status === 'completed' || task.status === 'error') {
                taskIdsToRemove.push(taskId);
                this.tasks.delete(taskId);
            }
        }

        this.renderTasks();
        this.updateBadge();

        if (taskIdsToRemove.length > 0) {
            this.dismissMultipleTasksOnServer(taskIdsToRemove);
        }
    }

    // Dismiss multiple tasks on server
    async dismissMultipleTasksOnServer(taskIds) {
        try {
            const formData = new FormData();
            formData.append('module', 'OptsIO');
            formData.append('package', 'io_tasks');
            formData.append('attr', 'IOTasks');
            formData.append('mname', 'dismiss_multiple_tasks');
            formData.append('task_ids', JSON.stringify(taskIds));

            await axios.post('/io/iom/', formData);
            console.log(`${taskIds.length} tasks dismissed on server`);
        } catch (error) {
            console.error('Error dismissing tasks:', error);
        }
    }

    // Update badge count
    updateBadge() {
        if (!this.badge) return;

        const runningCount = Array.from(this.tasks.values()).filter(
            t => t.status === 'processing'
        ).length;

        const totalCount = this.tasks.size;

        if (runningCount > 0) {
            this.badge.textContent = runningCount;
            this.badge.classList.remove('d-none');
            this.badge.classList.add('animate');
            setTimeout(() => this.badge.classList.remove('animate'), 300);
        } else {
            this.badge.classList.add('d-none');
        }

        if (this.countHeader) {
            this.countHeader.textContent = totalCount;
        }

        // Show/hide footer
        if (this.taskFooter) {
            const hasCompletedOrError = Array.from(this.tasks.values()).some(
                t => t.status === 'completed' || t.status === 'error'
            );

            if (hasCompletedOrError) {
                this.taskFooter.classList.remove('d-none');
            } else {
                this.taskFooter.classList.add('d-none');
            }
        }
    }

    // Render all tasks
    renderTasks() {
        if (!this.container) return;

        if (this.tasks.size === 0) {
            if (this.noTasksMessage) this.noTasksMessage.classList.remove('d-none');
            const taskItems = this.container.querySelectorAll('.task-item');
            taskItems.forEach(item => item.remove());
            return;
        }

        if (this.noTasksMessage) this.noTasksMessage.classList.add('d-none');

        // Sort tasks: processing first, then by update time
        const sortedTasks = Array.from(this.tasks.values()).sort((a, b) => {
            if (a.status === 'processing' && b.status !== 'processing') return -1;
            if (b.status === 'processing' && a.status !== 'processing') return 1;
            return b.updateTime - a.updateTime;
        });

        // Clear existing task items
        const existingItems = this.container.querySelectorAll('.task-item');
        existingItems.forEach(item => item.remove());

        // Render each task
        sortedTasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            this.container.appendChild(taskElement);
        });
    }

    // Create task HTML element
    createTaskElement(task) {
        const div = document.createElement('div');
        div.className = `task-item ${task.status}`;
        div.id = `task-bell-${task.id}`;

        const iconClass = this.getStatusIcon(task.status);
        const progressClass = this.getProgressClass(task.status);
        const timeAgo = this.getTimeAgo(task.updateTime);

        div.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="task-status-icon ${task.status} me-2">
                    <i class="mdi ${iconClass}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="task-name">${task.name}</div>
                    <div class="task-message">${task.message}</div>
                    ${task.status === 'processing' ? `
                        <div class="progress">
                            <div class="progress-bar ${progressClass}" role="progressbar"
                                 style="width: ${task.progress}%"
                                 aria-valuenow="${task.progress}"
                                 aria-valuemin="0"
                                 aria-valuemax="100"></div>
                        </div>
                    ` : ''}
                    <div class="task-time mt-1">${timeAgo}</div>
                </div>
                ${task.status !== 'processing' ? `
                    <button class="btn btn-sm btn-link text-muted p-0 ms-2" onclick="taskBell.removeTask('${task.id}')">
                        <i class="mdi mdi-close"></i>
                    </button>
                ` : ''}
            </div>
        `;

        return div;
    }

    // Get icon for task status
    getStatusIcon(status) {
        switch (status) {
            case 'processing':
                return 'mdi-loading mdi-spin';
            case 'completed':
                return 'mdi-check-circle';
            case 'error':
                return 'mdi-alert-circle';
            default:
                return 'mdi-circle-outline';
        }
    }

    // Get progress bar class
    getProgressClass(status) {
        switch (status) {
            case 'processing':
                return 'bg-primary progress-bar-striped progress-bar-animated';
            case 'completed':
                return 'bg-success';
            case 'error':
                return 'bg-danger';
            default:
                return 'bg-secondary';
        }
    }

    // Get human-readable time ago
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }

    // Set task name (for when task is added before we know the name)
    setTaskName(taskId, name) {
        const task = this.tasks.get(taskId);
        if (task) {
            task.name = name;
            this.renderTasks();
        }
    }
}

// Global variable (will be initialized by templates after DOM is ready)
var taskBell = null;
