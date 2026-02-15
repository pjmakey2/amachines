"""
WebSocket Utility Functions
Send real-time messages to users via WebSocket from Django shell or anywhere in the codebase
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def ws_send_message(username: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send a general message to a specific user via WebSocket

    Args:
        username: Username to send the message to
        message: Message text to send
        data: Optional additional data to include

    Returns:
        True if message was sent successfully, False otherwise

    Example:
        >>> from OptsIO.ws_utils import ws_send_message
        >>> ws_send_message('amadmin', 'Hello from the shell!')
        >>> ws_send_message('amadmin', 'Processing complete', data={'count': 100})
    """
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        group_name = f"user_{username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "user.message",
                "username": username,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Message sent to user {username}: {message}")
        return True

    except Exception as e:
        logger.error(f"Error sending WebSocket message to {username}: {str(e)}")
        return False


def ws_send_notification(
    username: str,
    message: str,
    notification_type: str = 'info',
    title: str = '',
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a notification to a specific user via WebSocket

    Args:
        username: Username to send the notification to
        message: Notification message
        notification_type: Type of notification ('success', 'error', 'info', 'warning')
        title: Optional notification title
        data: Optional additional data to include

    Returns:
        True if notification was sent successfully, False otherwise

    Example:
        >>> from OptsIO.ws_utils import ws_send_notification
        >>> ws_send_notification('amadmin', 'Report generated successfully', 'success', 'Report Ready')
        >>> ws_send_notification('amadmin', 'Failed to process file', 'error', 'Error')
    """
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        valid_types = ['success', 'error', 'info', 'warning']
        if notification_type not in valid_types:
            logger.warning(f"Invalid notification type: {notification_type}, defaulting to 'info'")
            notification_type = 'info'

        group_name = f"user_{username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "user.notification",
                "username": username,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Notification sent to user {username}: [{notification_type}] {message}")
        return True

    except Exception as e:
        logger.error(f"Error sending WebSocket notification to {username}: {str(e)}")
        return False


def ws_send_file(
    username: str,
    file_url: str,
    file_name: str = '',
    message: str = 'File ready for download',
    file_size: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a file download notification to a specific user via WebSocket

    Args:
        username: Username to send the file notification to
        file_url: URL or path to the file (e.g., '/media/reports/report.xlsx')
        file_name: Optional filename to display
        message: Optional message to accompany the file
        file_size: Optional file size in bytes
        data: Optional additional data to include

    Returns:
        True if file notification was sent successfully, False otherwise

    Example:
        >>> from OptsIO.ws_utils import ws_send_file
        >>> ws_send_file('amadmin', '/media/reports/sales_2025.xlsx', 'sales_2025.xlsx')
        >>> ws_send_file('amadmin', '/media/exports/data.csv', 'data.csv', 'Your export is ready', 156789)
    """
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        group_name = f"user_{username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "user.file",
                "username": username,
                "message": message,
                "file_url": file_url,
                "file_name": file_name or file_url.split('/')[-1],
                "file_size": file_size,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"File notification sent to user {username}: {file_name or file_url}")
        return True

    except Exception as e:
        logger.error(f"Error sending WebSocket file notification to {username}: {str(e)}")
        return False


# Convenience alias for your preferred function name
ws_connect = ws_send_message


def ws_send_task_update(
    username: str,
    task_id: str,
    task_name: str,
    message: str,
    progress: int = 0,
    status: str = 'processing',
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a task update to the user's task notification bell

    Args:
        username: Username to send the update to
        task_id: Unique task identifier
        task_name: Human-readable task name
        message: Progress message
        progress: Progress percentage (0-100)
        status: Task status ('processing', 'completed', 'error')
        data: Optional additional data

    Returns:
        True if update was sent successfully, False otherwise
    """
    try:
        # Persist task to database for page refresh support
        from OptsIO.models import UserTask
        UserTask.objects.update_or_create(
            task_id=task_id,
            defaults={
                'username': username,
                'name': task_name,
                'message': message,
                'progress': progress,
                'status': status
            }
        )

        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        group_name = f"user_{username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "task.update",
                "task_id": task_id,
                "task_name": task_name,
                "status": status,
                "message": message,
                "progress": progress,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Task update sent to user {username}: {task_name} - {message}")
        return True

    except Exception as e:
        logger.error(f"Error sending task update to {username}: {str(e)}")
        return False


def ws_send_task_complete(
    username: str,
    task_id: str,
    task_name: str,
    message: str,
    result: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a task completion notification to the user's task notification bell

    Args:
        username: Username to send the completion to
        task_id: Unique task identifier
        task_name: Human-readable task name
        message: Completion message
        result: Optional task result data

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        # Update task in database
        from OptsIO.models import UserTask
        UserTask.objects.update_or_create(
            task_id=task_id,
            defaults={
                'username': username,
                'name': task_name,
                'message': message,
                'progress': 100,
                'status': 'completed',
                'result': result
            }
        )

        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        group_name = f"user_{username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "task.complete",
                "task_id": task_id,
                "task_name": task_name,
                "status": "completed",
                "message": message,
                "result": result or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Task complete sent to user {username}: {task_name}")
        return True

    except Exception as e:
        logger.error(f"Error sending task complete to {username}: {str(e)}")
        return False


def ws_send_task_error(
    username: str,
    task_id: str,
    task_name: str,
    error: str,
    message: str = ''
) -> bool:
    """
    Send a task error notification to the user's task notification bell

    Args:
        username: Username to send the error to
        task_id: Unique task identifier
        task_name: Human-readable task name
        error: Error message
        message: Optional additional message

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        # Update task in database
        from OptsIO.models import UserTask
        UserTask.objects.update_or_create(
            task_id=task_id,
            defaults={
                'username': username,
                'name': task_name,
                'message': message or error,
                'status': 'error',
                'error': error
            }
        )

        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        group_name = f"user_{username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "task.error",
                "task_id": task_id,
                "task_name": task_name,
                "status": "error",
                "error": error,
                "message": message or error,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Task error sent to user {username}: {task_name} - {error}")
        return True

    except Exception as e:
        logger.error(f"Error sending task error to {username}: {str(e)}")
        return False


def ws_broadcast_message(message: str, usernames: Optional[list] = None, data: Optional[Dict[str, Any]] = None) -> int:
    """
    Broadcast a message to multiple users

    Args:
        message: Message text to send
        usernames: List of usernames to send to (if None, would need to query all active users)
        data: Optional additional data to include

    Returns:
        Number of successful sends

    Example:
        >>> from OptsIO.ws_utils import ws_broadcast_message
        >>> ws_broadcast_message('System maintenance in 10 minutes', ['amadmin', 'user1', 'user2'])
    """
    if not usernames:
        logger.warning("No usernames provided for broadcast")
        return 0

    success_count = 0
    for username in usernames:
        if ws_send_message(username, message, data):
            success_count += 1

    logger.info(f"Broadcast sent to {success_count}/{len(usernames)} users")
    return success_count


def test_websocket_connection(username: str) -> bool:
    """
    Test if WebSocket connection is working by sending a test message

    Args:
        username: Username to test with

    Returns:
        True if test message was sent, False otherwise

    Example:
        >>> from OptsIO.ws_utils import test_websocket_connection
        >>> test_websocket_connection('amadmin')
    """
    return ws_send_message(
        username,
        'WebSocket test message - if you see this, WebSocket is working!',
        data={'test': True}
    )


# ==================== GROUP MESSAGING FUNCTIONS ====================


def ws_send_group_message(group_name: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send a message to all users in a custom group

    Args:
        group_name: Name of the group (e.g., 'sales_team', 'admins', 'project_alpha')
        message: Message text to send
        data: Optional additional data to include

    Returns:
        True if message was sent successfully, False otherwise

    Example:
        >>> from OptsIO.ws_utils import ws_send_group_message
        >>> ws_send_group_message('sales_team', 'New leads available!')
        >>> ws_send_group_message('admins', 'System backup complete', data={'size': '50GB'})
    """
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        full_group_name = f"group_{group_name}"

        async_to_sync(channel_layer.group_send)(
            full_group_name,
            {
                "type": "group.message",
                "group_name": group_name,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Message sent to group {group_name}: {message}")
        return True

    except Exception as e:
        logger.error(f"Error sending WebSocket message to group {group_name}: {str(e)}")
        return False


def ws_send_group_notification(
    group_name: str,
    message: str,
    notification_type: str = 'info',
    title: str = '',
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a notification to all users in a custom group

    Args:
        group_name: Name of the group
        message: Notification message
        notification_type: Type of notification ('success', 'error', 'info', 'warning')
        title: Optional notification title
        data: Optional additional data to include

    Returns:
        True if notification was sent successfully, False otherwise

    Example:
        >>> from OptsIO.ws_utils import ws_send_group_notification
        >>> ws_send_group_notification('sales_team', 'Monthly target achieved!', 'success', 'Great Job!')
        >>> ws_send_group_notification('developers', 'Deployment failed', 'error', 'Alert')
    """
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        valid_types = ['success', 'error', 'info', 'warning']
        if notification_type not in valid_types:
            logger.warning(f"Invalid notification type: {notification_type}, defaulting to 'info'")
            notification_type = 'info'

        full_group_name = f"group_{group_name}"

        async_to_sync(channel_layer.group_send)(
            full_group_name,
            {
                "type": "group.notification",
                "group_name": group_name,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Notification sent to group {group_name}: [{notification_type}] {message}")
        return True

    except Exception as e:
        logger.error(f"Error sending WebSocket notification to group {group_name}: {str(e)}")
        return False


def ws_send_group_file(
    group_name: str,
    file_url: str,
    file_name: str = '',
    message: str = 'File ready for download',
    file_size: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a file download notification to all users in a custom group

    Args:
        group_name: Name of the group
        file_url: URL or path to the file
        file_name: Optional filename to display
        message: Optional message to accompany the file
        file_size: Optional file size in bytes
        data: Optional additional data to include

    Returns:
        True if file notification was sent successfully, False otherwise

    Example:
        >>> from OptsIO.ws_utils import ws_send_group_file
        >>> ws_send_group_file('sales_team', '/media/reports/monthly_sales.xlsx', 'monthly_sales.xlsx')
        >>> ws_send_group_file('managers', '/media/reports/summary.pdf', 'summary.pdf', 'Q4 Summary Report')
    """
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return False

        full_group_name = f"group_{group_name}"

        async_to_sync(channel_layer.group_send)(
            full_group_name,
            {
                "type": "group.file",
                "group_name": group_name,
                "message": message,
                "file_url": file_url,
                "file_name": file_name or file_url.split('/')[-1],
                "file_size": file_size,
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"File notification sent to group {group_name}: {file_name or file_url}")
        return True

    except Exception as e:
        logger.error(f"Error sending WebSocket file notification to group {group_name}: {str(e)}")
        return False
