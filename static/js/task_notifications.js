/**
 * Task Notification WebSocket Manager
 * Handles real-time task updates via WebSocket
 */

class TaskNotificationManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.subscribedTasks = new Set();
        this.subscribedGroups = new Set();
        this.callbacks = {};
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/tasks/`;

        console.log('Connecting to WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;

            // Resubscribe to tasks after reconnection
            this.subscribedTasks.forEach(taskId => {
                this.subscribe(taskId);
            });

            // Resubscribe to groups after reconnection
            this.subscribedGroups.forEach(groupName => {
                this.subscribeToGroup(groupName);
            });
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);

            this.handleMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    subscribe(taskId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.subscribedTasks.add(taskId);
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                task_id: taskId
            }));
            console.log(`Subscribed to task: ${taskId}`);
        }
    }

    unsubscribe(taskId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.subscribedTasks.delete(taskId);
            this.ws.send(JSON.stringify({
                action: 'unsubscribe',
                task_id: taskId
            }));
            console.log(`Unsubscribed from task: ${taskId}`);
        }
    }

    subscribeToGroup(groupName) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.subscribedGroups.add(groupName);
            this.ws.send(JSON.stringify({
                action: 'subscribe_group',
                group_name: groupName
            }));
            console.log(`Subscribed to group: ${groupName}`);
        }
    }

    unsubscribeFromGroup(groupName) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.subscribedGroups.delete(groupName);
            this.ws.send(JSON.stringify({
                action: 'unsubscribe_group',
                group_name: groupName
            }));
            console.log(`Unsubscribed from group: ${groupName}`);
        }
    }

    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    handleMessage(data) {
        const { type, task_id } = data;

        // Trigger event-specific callbacks
        if (this.callbacks[type]) {
            this.callbacks[type].forEach(callback => callback(data));
        }

        // Trigger all callbacks
        if (this.callbacks['*']) {
            this.callbacks['*'].forEach(callback => callback(data));
        }

        // Handle specific message types
        switch (type) {
            case 'subscription_confirmed':
                console.log(`Subscription confirmed for task: ${task_id}`);
                break;

            case 'task_update':
                this.handleTaskUpdate(data);
                break;

            case 'task_complete':
                this.handleTaskComplete(data);
                break;

            case 'task_error':
                this.handleTaskError(data);
                break;

            case 'user_message':
                this.handleUserMessage(data);
                break;

            case 'user_notification':
                this.handleUserNotification(data);
                break;

            case 'user_file':
                this.handleUserFile(data);
                break;

            case 'group_subscription_confirmed':
                console.log(`Group subscription confirmed: ${data.group_name}`);
                break;

            case 'group_message':
                this.handleGroupMessage(data);
                break;

            case 'group_notification':
                this.handleGroupNotification(data);
                break;

            case 'group_file':
                this.handleGroupFile(data);
                break;

            case 'active_tasks':
                this.handleActiveTasks(data);
                break;
        }
    }

    handleActiveTasks(data) {
        const { tasks } = data;
        console.log(`Received ${tasks.length} active tasks from server`);

        // Trigger callbacks for active_tasks event
        if (this.callbacks['active_tasks']) {
            this.callbacks['active_tasks'].forEach(callback => callback(data));
        }

        // Auto-subscribe to processing tasks
        tasks.forEach(task => {
            if (task.status === 'processing') {
                this.subscribedTasks.add(task.task_id);
            }
        });
    }

    handleTaskUpdate(data) {
        const { task_id, message, progress } = data;
        console.log(`Task ${task_id} update: ${message} (${progress}%)`);

        // Update UI
        this.updateTaskUI(task_id, 'processing', message, progress);
    }

    handleTaskComplete(data) {
        const { task_id, message, result } = data;
        console.log(`Task ${task_id} completed: ${message}`, result);

        // Update UI
        this.updateTaskUI(task_id, 'completed', message, 100);

        // Auto-unsubscribe after completion
        this.unsubscribe(task_id);
    }

    handleTaskError(data) {
        const { task_id, error, message } = data;
        console.error(`Task ${task_id} error: ${message}`, error);

        // Update UI
        this.updateTaskUI(task_id, 'error', message, 0);
    }

    updateTaskUI(taskId, status, message, progress) {
        // Find task container in DOM
        const taskElement = document.getElementById(`task-${taskId}`);
        if (!taskElement) return;

        // Update status
        const statusElement = taskElement.querySelector('.task-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `task-status status-${status}`;
        }

        // Update message
        const messageElement = taskElement.querySelector('.task-message');
        if (messageElement) {
            messageElement.textContent = message;
        }

        // Update progress bar
        const progressBar = taskElement.querySelector('.task-progress-bar');
        if (progressBar && progress !== undefined) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
    }

    handleUserMessage(data) {
        const { username, message, timestamp } = data;
        console.log(`User message from ${username}: ${message}`);

        // Show message using UiB if available, otherwise console
        if (typeof UiB !== 'undefined' && UiB.MsgInfo) {
            UiB.MsgInfo(message);
        } else {
            console.log('User Message:', message);
            // Fallback: show browser notification if permitted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('Message', { body: message });
            }
        }
    }

    handleUserNotification(data) {
        const { username, notification_type, title, message, timestamp } = data;
        console.log(`User notification [${notification_type}]: ${title} - ${message}`);

        // Map notification types to UiB methods
        if (typeof UiB !== 'undefined') {
            const titleText = title ? `${title}: ${message}` : message;

            switch (notification_type) {
                case 'success':
                    if (UiB.MsgSuccess) UiB.MsgSuccess(titleText);
                    break;
                case 'error':
                    if (UiB.MsgError) UiB.MsgError(titleText);
                    break;
                case 'warning':
                    if (UiB.MsgWarning) UiB.MsgWarning(titleText);
                    break;
                case 'info':
                default:
                    if (UiB.MsgInfo) UiB.MsgInfo(titleText);
                    break;
            }
        } else {
            console.log(`[${notification_type.toUpperCase()}] ${title}: ${message}`);
        }
    }

    handleUserFile(data) {
        const { username, message, file_url, file_name, file_size, timestamp } = data;
        console.log(`File available for ${username}: ${file_name} at ${file_url}`);

        // Format file size if provided
        let sizeText = '';
        if (file_size) {
            const sizeMB = (file_size / (1024 * 1024)).toFixed(2);
            sizeText = ` (${sizeMB} MB)`;
        }

        const fullMessage = `${message}${sizeText}`;

        // Show notification with download option
        if (typeof UiB !== 'undefined' && UiB.MsgSwall) {
            UiB.MsgSwall({
                msg: `<p>${fullMessage}</p><p><strong>${file_name}</strong></p>`,
                ttype: 'info',
                showCancelButton: true,
                confirmButtonText: 'Download',
                cancelButtonText: 'Close'
            }).then((result) => {
                if (result.isConfirmed || result.value === true) {
                    // Open file in new tab or trigger download
                    window.open(file_url, '_blank');
                }
            });
        } else {
            // Fallback: just log and auto-download
            console.log('File download:', file_url);
            if (confirm(`${fullMessage}\n\nDownload ${file_name}?`)) {
                window.open(file_url, '_blank');
            }
        }
    }

    handleGroupMessage(data) {
        const { group_name, message, timestamp } = data;
        console.log(`Group message from ${group_name}: ${message}`);

        // Show message using UiB if available
        if (typeof UiB !== 'undefined' && UiB.MsgInfo) {
            UiB.MsgInfo(`[${group_name}] ${message}`);
        } else {
            console.log('Group Message:', message);
            // Fallback: show browser notification if permitted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(`Group: ${group_name}`, { body: message });
            }
        }
    }

    handleGroupNotification(data) {
        const { group_name, notification_type, title, message, timestamp } = data;
        console.log(`Group notification [${notification_type}] from ${group_name}: ${title} - ${message}`);

        // Map notification types to UiB methods
        if (typeof UiB !== 'undefined') {
            const prefix = `[${group_name}]`;
            const titleText = title ? `${prefix} ${title}: ${message}` : `${prefix} ${message}`;

            switch (notification_type) {
                case 'success':
                    if (UiB.MsgSuccess) UiB.MsgSuccess(titleText);
                    break;
                case 'error':
                    if (UiB.MsgError) UiB.MsgError(titleText);
                    break;
                case 'warning':
                    if (UiB.MsgWarning) UiB.MsgWarning(titleText);
                    break;
                case 'info':
                default:
                    if (UiB.MsgInfo) UiB.MsgInfo(titleText);
                    break;
            }
        } else {
            console.log(`[${group_name}] [${notification_type.toUpperCase()}] ${title}: ${message}`);
        }
    }

    handleGroupFile(data) {
        const { group_name, message, file_url, file_name, file_size, timestamp } = data;
        console.log(`File available for group ${group_name}: ${file_name} at ${file_url}`);

        // Format file size if provided
        let sizeText = '';
        if (file_size) {
            const sizeMB = (file_size / (1024 * 1024)).toFixed(2);
            sizeText = ` (${sizeMB} MB)`;
        }

        const fullMessage = `[${group_name}] ${message}${sizeText}`;

        // Show notification with download option
        if (typeof UiB !== 'undefined' && UiB.MsgSwall) {
            UiB.MsgSwall({
                msg: `<p>${fullMessage}</p><p><strong>${file_name}</strong></p>`,
                ttype: 'info',
                showCancelButton: true,
                confirmButtonText: 'Download',
                cancelButtonText: 'Close'
            }).then((result) => {
                if (result.isConfirmed || result.value === true) {
                    // Open file in new tab or trigger download
                    window.open(file_url, '_blank');
                }
            });
        } else {
            // Fallback: just log and auto-download
            console.log('File download:', file_url);
            if (confirm(`${fullMessage}\n\nDownload ${file_name}?`)) {
                window.open(file_url, '_blank');
            }
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Global instance
var taskNotifications = new TaskNotificationManager();

// Auto-connect when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    taskNotifications.connect();
});
