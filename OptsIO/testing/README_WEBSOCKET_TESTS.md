# WebSocket User Messaging Tests

## Quick Start

### 1. Open Django Shell

```bash
python manage.py shell
```

### 2. Import and Run Tests

```python
from OptsIO.testing.test_websocket_user import *

# Run all tests for user 'amadmin'
test_all('amadmin')
```

**Important:** Make sure the user has the application open in a browser before running tests!

## Individual Tests

### Test Simple Message
```python
test_simple_message('amadmin')
```

### Test ws_connect Alias
```python
test_ws_connect_alias('amadmin')
```

### Test All Notification Types
```python
test_notifications('amadmin')
```

### Test File Notification
```python
test_file_notification('amadmin')
```

### Test Message with Data
```python
test_message_with_data('amadmin')
```

### Test Broadcast
```python
test_broadcast(['amadmin', 'user1', 'user2'])
```

### Test Connection
```python
test_connection('amadmin')
```

## Quick Test Functions

For quick manual testing:

```python
# Quick message
quick_test('amadmin')

# Quick notification
quick_notify('amadmin', 'Hello!', 'success')

# Quick file notification
quick_file('amadmin', '/media/reports/myfile.xlsx')
```

## Using ws_utils Directly

You can also use the utility functions directly:

```python
from OptsIO.ws_utils import ws_send_message, ws_send_notification, ws_send_file

# Simple message
ws_send_message('amadmin', 'Hello!')

# Notification
ws_send_notification('amadmin', 'Success!', 'success', 'Done')

# File
ws_send_file('amadmin', '/media/file.xlsx', 'file.xlsx')
```

## Expected Results

When tests run successfully, you should see:
- Toast notifications in the browser
- File download dialogs (for file tests)
- Console messages in browser DevTools
- `True` return values in shell

## Troubleshooting

If tests return `False`:
1. Check Redis is running: `redis-cli ping`
2. Check Daphne is running: `ps aux | grep daphne`
3. Check user is logged in and has browser open
4. Check browser console for WebSocket connection status
5. Check Django logs for errors

## More Information

See the main documentation:
- [WEBSOCKET_USER_MESSAGING.md](../../WEBSOCKET_USER_MESSAGING.md)
- [WEBSOCKET_SETUP.md](../../WEBSOCKET_SETUP.md)
