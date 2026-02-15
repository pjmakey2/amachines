import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class TaskNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for task notifications and user messages
    - Clients can subscribe to task updates by task_id
    - Users are automatically subscribed to their username channel
    - Supports direct messaging to users from backend/shell
    """

    async def connect(self):
        self.user = self.scope["user"]
        self.task_groups = set()

        # Accept connection
        await self.accept()

        # Auto-subscribe user to their own channel for direct messages
        if self.user.is_authenticated:
            username = self.user.username
            user_group = f"user_{username}"
            self.task_groups.add(user_group)
            await self.channel_layer.group_add(user_group, self.channel_name)
            logger.info(f"WebSocket connected: {self.channel_name}, user: {username}, auto-subscribed to {user_group}")

            # Send active tasks to user and auto-subscribe to them
            await self.send_active_tasks(username)
        else:
            logger.info(f"WebSocket connected: {self.channel_name} (anonymous)")

    async def send_active_tasks(self, username):
        """Send all active tasks for the user and auto-subscribe to them."""
        tasks = await self.get_user_tasks(username)

        if tasks:
            # Send the task list to the client
            await self.send(text_data=json.dumps({
                'type': 'active_tasks',
                'tasks': tasks
            }))

            # Auto-subscribe to each active task
            for task in tasks:
                if task['status'] == 'processing':
                    task_group = f"task_{task['task_id']}"
                    self.task_groups.add(task_group)
                    await self.channel_layer.group_add(task_group, self.channel_name)

            logger.info(f"Sent {len(tasks)} active tasks to user {username}")

    @database_sync_to_async
    def get_user_tasks(self, username):
        """Get active tasks from database."""
        from OptsIO.models import UserTask

        tasks = UserTask.objects.filter(
            username=username,
            dismissed=False
        ).exclude(
            status='completed'
        ).order_by('-created_at')[:20]  # Limit to 20 most recent

        return [{
            'task_id': task.task_id,
            'name': task.name,
            'message': task.message,
            'progress': task.progress,
            'status': task.status,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        } for task in tasks]

    async def disconnect(self, close_code):
        # Leave all task groups
        if hasattr(self, 'task_groups'):
            for group_name in self.task_groups:
                await self.channel_layer.group_discard(group_name, self.channel_name)

        logger.info(f"WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        """
        Receive message from WebSocket
        Expected formats:
        - {"action": "subscribe", "task_id": "xxx"}
        - {"action": "subscribe_group", "group_name": "sales_team"}
        - {"action": "unsubscribe_group", "group_name": "sales_team"}
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'subscribe':
                task_id = data.get('task_id')
                if task_id:
                    await self.subscribe_to_task(task_id)

            elif action == 'unsubscribe':
                task_id = data.get('task_id')
                if task_id:
                    await self.unsubscribe_from_task(task_id)

            elif action == 'subscribe_group':
                group_name = data.get('group_name')
                if group_name:
                    await self.subscribe_to_group(group_name)

            elif action == 'unsubscribe_group':
                group_name = data.get('group_name')
                if group_name:
                    await self.unsubscribe_from_group(group_name)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")

    async def subscribe_to_task(self, task_id):
        """Subscribe to a specific task's updates"""
        group_name = f"task_{task_id}"

        self.task_groups.add(group_name)
        await self.channel_layer.group_add(group_name, self.channel_name)

        logger.info(f"Subscribed to {group_name}")

        # Send confirmation
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'task_id': task_id
        }))

    async def unsubscribe_from_task(self, task_id):
        """Unsubscribe from a specific task's updates"""
        group_name = f"task_{task_id}"

        if hasattr(self, 'task_groups') and group_name in self.task_groups:
            self.task_groups.remove(group_name)
            await self.channel_layer.group_discard(group_name, self.channel_name)
            logger.info(f"Unsubscribed from {group_name}")

    async def subscribe_to_group(self, group_name):
        """
        Subscribe to a custom group
        Group names can be anything: 'sales_team', 'admins', 'project_alpha', etc.
        """
        # Prefix with 'group_' to avoid conflicts
        full_group_name = f"group_{group_name}"

        self.task_groups.add(full_group_name)
        await self.channel_layer.group_add(full_group_name, self.channel_name)

        logger.info(f"User {self.user.username if self.user.is_authenticated else 'anonymous'} subscribed to {full_group_name}")

        # Send confirmation
        await self.send(text_data=json.dumps({
            'type': 'group_subscription_confirmed',
            'group_name': group_name
        }))

    async def unsubscribe_from_group(self, group_name):
        """Unsubscribe from a custom group"""
        full_group_name = f"group_{group_name}"

        if hasattr(self, 'task_groups') and full_group_name in self.task_groups:
            self.task_groups.remove(full_group_name)
            await self.channel_layer.group_discard(full_group_name, self.channel_name)
            logger.info(f"User {self.user.username if self.user.is_authenticated else 'anonymous'} unsubscribed from {full_group_name}")

    # Handler for task.update messages
    async def task_update(self, event):
        """
        Send task update to WebSocket
        Called when a message is sent to the group
        """
        await self.send(text_data=json.dumps({
            'type': 'task_update',
            'task_id': event['task_id'],
            'status': event['status'],
            'message': event['message'],
            'progress': event.get('progress'),
            'data': event.get('data', {})
        }))

    # Handler for task.complete messages
    async def task_complete(self, event):
        """Send task completion notification"""
        await self.send(text_data=json.dumps({
            'type': 'task_complete',
            'task_id': event['task_id'],
            'status': event['status'],
            'message': event['message'],
            'result': event.get('result', {})
        }))

    # Handler for task.error messages
    async def task_error(self, event):
        """Send task error notification"""
        await self.send(text_data=json.dumps({
            'type': 'task_error',
            'task_id': event['task_id'],
            'error': event['error'],
            'message': event['message']
        }))

    # Handler for user.message - General message to user
    async def user_message(self, event):
        """
        Send user message to WebSocket
        Called when a direct message is sent to the user
        """
        await self.send(text_data=json.dumps({
            'type': 'user_message',
            'username': event.get('username'),
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))

    # Handler for user.notification - Notification with type
    async def user_notification(self, event):
        """Send user notification (success, error, info, warning)"""
        await self.send(text_data=json.dumps({
            'type': 'user_notification',
            'username': event.get('username'),
            'notification_type': event.get('notification_type', 'info'),  # success, error, info, warning
            'title': event.get('title', ''),
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))

    # Handler for user.file - File download notification
    async def user_file(self, event):
        """Send file download notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'user_file',
            'username': event.get('username'),
            'message': event.get('message', 'File ready for download'),
            'file_url': event['file_url'],
            'file_name': event.get('file_name', ''),
            'file_size': event.get('file_size'),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))

    # Handler for group.message - Group message
    async def group_message(self, event):
        """
        Send group message to WebSocket
        Called when a message is sent to a group
        """
        await self.send(text_data=json.dumps({
            'type': 'group_message',
            'group_name': event.get('group_name'),
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))

    # Handler for group.notification - Group notification
    async def group_notification(self, event):
        """Send group notification"""
        await self.send(text_data=json.dumps({
            'type': 'group_notification',
            'group_name': event.get('group_name'),
            'notification_type': event.get('notification_type', 'info'),
            'title': event.get('title', ''),
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))

    # Handler for group.file - Group file notification
    async def group_file(self, event):
        """Send file notification to group"""
        await self.send(text_data=json.dumps({
            'type': 'group_file',
            'group_name': event.get('group_name'),
            'message': event.get('message', 'File ready for download'),
            'file_url': event['file_url'],
            'file_name': event.get('file_name', ''),
            'file_size': event.get('file_size'),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))
