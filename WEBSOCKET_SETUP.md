# WebSocket Integration Guide for Toca3d

## Overview

WebSocket integration provides real-time communication between backend and frontend:
- **Task Notifications**: Real-time updates from Celery tasks to the browser
- **User Messaging**: Send messages, notifications, and file alerts directly to users from Django shell or code

## Documentation

- **This Guide**: WebSocket setup and task notifications
- **[User Messaging Guide](WEBSOCKET_USER_MESSAGING.md)**: Send messages to users from shell/code

## Architecture

```
Browser → WebSocket → Django Channels Consumer → Redis Channel Layer ← Celery Task
```

## Installation

### 1. Install packages

```bash
pip install -r requirements-websockets.txt
```

### 2. Verify Redis is running

```bash
redis-cli ping
# Should return: PONG
```

## Running the Application

### Development

```bash
# Start Django with Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8002 Toca3d.asgi:application

# Or use runserver (Channels will use Daphne automatically)
python manage.py runserver
```

### Production with Systemd

Create `/etc/systemd/system/daphne-toca3d.service`:

```ini
[Unit]
Description=Daphne ASGI Server for Toca3d
After=network.target redis.target

[Service]
Type=simple
User=peter
Group=peter
WorkingDirectory=/home/peter/projects/Toca3d
ExecStart=/home/peter/.virtualenv/toca3d/bin/daphne -b 0.0.0.0 -p 8000 Toca3d.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start daphne-toca3d
sudo systemctl enable daphne-toca3d
```

## Usage Examples

### From Frontend (JavaScript)

```javascript
// Connect to WebSocket
taskNotifications.connect();

// Subscribe to a task
const taskId = 'some-task-id';
taskNotifications.subscribe(taskId);

// Listen for updates
taskNotifications.on('task_update', (data) => {
    console.log('Progress:', data.message, data.progress);
});

taskNotifications.on('task_complete', (data) => {
    console.log('Completed!', data.result);
});
```

### From Celery Task

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task(bind=True)
def my_long_task(self):
    channel_layer = get_channel_layer()
    task_id = self.request.id

    # Send progress update
    async_to_sync(channel_layer.group_send)(
        f"task_{task_id}",
        {
            "type": "task.update",
            "task_id": task_id,
            "status": "processing",
            "message": "Processing step 1...",
            "progress": 25
        }
    )

    # Do work...

    # Send completion
    async_to_sync(channel_layer.group_send)(
        f"task_{task_id}",
        {
            "type": "task.complete",
            "task_id": task_id,
            "status": "completed",
            "message": "All done!",
            "result": {"some": "data"}
        }
    )
```

### From CLI

When running tasks from CLI, they will still send WebSocket notifications if users are subscribed:

```bash
# Start RUC sync
python manage.py mng_sifen_mainline --sync_rucs

# Users with browser open and subscribed to task IDs will receive updates
```

## Testing

### 1. Test WebSocket Connection

```bash
# Install wscat for testing
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/tasks/

# Subscribe to a task
> {"action": "subscribe", "task_id": "test-123"}
```

### 2. Test Django Channels

```bash
python manage.py shell

# Test channel layer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

# Send test message
async_to_sync(channel_layer.group_send)(
    "task_test-123",
    {
        "type": "task.update",
        "task_id": "test-123",
        "status": "processing",
        "message": "Test message",
        "progress": 50
    }
)
```

## Message Types

### task.update
```json
{
    "type": "task_update",
    "task_id": "abc-123",
    "status": "processing",
    "message": "Processing 1500 records...",
    "progress": 45,
    "data": {}
}
```

### task.complete
```json
{
    "type": "task_complete",
    "task_id": "abc-123",
    "status": "completed",
    "message": "Completed: 1500 created, 0 updated",
    "result": {
        "created": 1500,
        "updated": 0,
        "errors": 0
    }
}
```

### task.error
```json
{
    "type": "task_error",
    "task_id": "abc-123",
    "error": "Database connection failed",
    "message": "An error occurred"
}
```

## Monitoring

### Check Channels Connection

```bash
python manage.py shell

from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# This should not raise an error
import asyncio
asyncio.run(channel_layer.send("test", {"type": "test"}))
```

### Monitor Redis Channels

```bash
redis-cli
> PUBSUB CHANNELS
> MONITOR
```

## Troubleshooting

### WebSocket won't connect

1. Check Daphne is running
2. Check ALLOWED_HOSTS in settings.py
3. Check browser console for errors

### No messages received

1. Verify Redis is running
2. Check channel layer configuration
3. Ensure you're subscribed to the correct task_id

### Task doesn't send updates

1. Check task has `bind=True` in decorator
2. Verify `channel_layer` is not None
3. Check Celery logs for errors

## Security Considerations

1. **Authentication**: The consumer uses Django's `AuthMiddlewareStack` - only authenticated users can connect
2. **Origin Validation**: `AllowedHostsOriginValidator` checks request origin
3. **SSL**: In production, use WSS (WebSocket Secure) with HTTPS

## Performance

- Each WebSocket connection uses minimal resources
- Redis Pub/Sub handles message distribution efficiently
- Consider connection limits in production (default: 1024)
- Use NGINX or HAProxy for WebSocket load balancing

## Next Steps

1. Add progress tracking to `sync_to_database` method for granular updates
2. Create dashboard UI for monitoring all active tasks
3. Add task history and logs
4. Implement task cancellation via WebSocket
