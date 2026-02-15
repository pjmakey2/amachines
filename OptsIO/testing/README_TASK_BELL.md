# Task Bell Notification Testing

## Prerequisites

Before testing, make sure these services are running:

```bash
# 1. Redis
redis-cli ping  # Should return PONG

# 2. Celery worker
celery -A Toca3d worker -l info

# 3. Daphne (ASGI server for WebSocket)
daphne -b 0.0.0.0 -p 8000 Toca3d.asgi:application
# OR
python manage.py runserver  # Uses Channels automatically
```

## Quick Test

### Step 1: Open Browser
Open the application in your browser and make sure you're logged in.

### Step 2: Start Demo Task

```bash
python manage.py shell
```

```python
>>> from OptsIO.testing.test_task_bell import *
>>> result = run_demo_task()
```

You'll see output like:
```
============================================================
DEMO TASK STARTED
============================================================
Task ID: abc123-def456-...
Steps: 10, Delay: 1s, Name: Demo Task

To see in browser, run in browser console:
  taskBell.addTask('abc123-def456-...', 'Demo Task', 'Starting...');
============================================================
```

### Step 3: Subscribe in Browser

Copy the JavaScript command and paste it in your browser console (F12 → Console):

```javascript
taskBell.addTask('abc123-def456-...', 'Demo Task', 'Starting...');
```

### Step 4: Watch the Bell

You should see:
- Bell icon shows red badge with "1"
- Click bell to see dropdown with task
- Progress bar animates from 0% to 100%
- Messages update as task progresses
- Task turns green when complete
- Auto-removes after 30 seconds

## Available Test Functions

### `run_demo_task(steps=10, delay=1, name="Demo Task")`
Run a configurable demo task.

```python
>>> run_demo_task()           # 10-step task
>>> run_demo_task(20, 2)      # 20 steps, 2s each
>>> run_demo_task(5, 1, "Sync")  # Custom name
```

### `run_quick_task()`
Quick 3-second task for fast testing.

```python
>>> run_quick_task()
```

### `run_error_task(fail_at=5, steps=10, delay=1)`
Task that fails at a specific step (tests error display).

```python
>>> run_error_task()      # Fails at step 5
>>> run_error_task(3)     # Fails at step 3
```

### `run_multiple_tasks(count=3)`
Run multiple concurrent tasks.

```python
>>> results = run_multiple_tasks(3)
```

### `run_long_task(minutes=1)`
Run a longer task for realistic testing.

```python
>>> run_long_task(2)  # 2-minute task
```

### `task_info(result)`
Get information about a task.

```python
>>> result = run_demo_task()
>>> task_info(result)  # Check state/result
```

## Testing Scenarios

### Test 1: Basic Progress
```python
>>> run_demo_task()
```
- Should show task with animated progress bar
- Progress updates every second
- Completes with green checkmark

### Test 2: Error Handling
```python
>>> run_error_task(3)
```
- Progresses to step 3
- Fails with red alert icon
- Error message displayed

### Test 3: Multiple Tasks
```python
>>> run_multiple_tasks(3)
```
- Badge shows "3"
- All tasks in dropdown
- Each has own progress

### Test 4: Auto-cleanup
```python
>>> run_quick_task()
```
- Task completes
- Auto-removes after 30 seconds
- Or click X to remove manually

## Frontend API

The `taskBell` object is globally available:

```javascript
// Add a task
taskBell.addTask('task-id', 'Task Name', 'Message', 0);

// Remove a task
taskBell.removeTask('task-id');

// Clear completed tasks
taskBell.clearCompleted();

// Set task name
taskBell.setTaskName('task-id', 'New Name');
```

## Troubleshooting

### Task not appearing in bell

1. **Check WebSocket connection**: Browser console should show "WebSocket connected"
2. **Check Celery is running**: `celery -A Toca3d worker -l info`
3. **Check Redis**: `redis-cli ping`
4. **Make sure you subscribed**: `taskBell.addTask('task-id', ...)`

### Progress not updating

1. Check Daphne/runserver is running
2. Check browser console for errors
3. Verify Redis channel layer is configured

### Task stuck as "processing"

1. Check Celery worker logs for errors
2. Task may have crashed - check Celery output
3. Try running `task_info(result)` to see state

## Integration Example

Here's how to integrate with your real tasks:

```python
# In your view or API
from OptsIO.tasks import demo_task_with_progress

def start_sync_task(request):
    # Start the task
    result = my_celery_task.delay(...)

    # Return task ID for frontend to track
    return JsonResponse({
        'task_id': result.id,
        'status': 'started'
    })
```

```javascript
// In your frontend
async function startSync() {
    const response = await axios.post('/api/start-sync/');
    const taskId = response.data.task_id;

    // Add to bell notification
    taskBell.addTask(taskId, 'Data Sync', 'Starting...');
}
```

## Notes

- Tasks auto-remove after 30 seconds when completed
- Failed tasks stay until manually cleared
- Badge only shows count of running tasks
- Maximum ~100 tasks recommended for performance
