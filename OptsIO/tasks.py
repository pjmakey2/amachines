from datetime import date, datetime
import time
import random
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from OptsIO.models import UserTask

actions = {
    'recepcion_paquete': 'Recepcion Paquetes: Inserta-Reg. Paquete codigo {paquetecodigo} Tracking {paquetetracking}'
}


# ==================== DEMO TASK FOR TESTING BELL NOTIFICATIONS ====================

@shared_task(bind=True)
def demo_task_with_progress(self, total_steps=10, step_delay=1, task_name="Demo Task"):
    """
    Demo task that simulates a long-running process with progress updates.

    Args:
        total_steps: Number of steps to simulate (default: 10)
        step_delay: Delay in seconds between steps (default: 1)
        task_name: Name to display in notifications (default: "Demo Task")

    Usage from shell:
        >>> from OptsIO.tasks import demo_task_with_progress
        >>> result = demo_task_with_progress.delay(10, 1, "My Test Task")
        >>> print(f"Task ID: {result.id}")  # Use this ID to subscribe in browser

    Usage from frontend (subscribe first):
        taskBell.addTask('task-id', 'Demo Task', 'Starting...');
    """
    channel_layer = get_channel_layer()
    task_id = self.request.id

    # Send start notification
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task.update",
                "task_id": task_id,
                "status": "processing",
                "message": f"Starting {task_name}...",
                "progress": 0
            }
        )

    results = {
        "processed": 0,
        "errors": 0,
        "steps": []
    }

    # Process each step
    for step in range(1, total_steps + 1):
        # Simulate work
        time.sleep(step_delay)

        # Calculate progress
        progress = int((step / total_steps) * 100)

        # Simulate occasional "processing"
        action = random.choice([
            f"Processing item {step}...",
            f"Validating data batch {step}...",
            f"Syncing records {step * 100}-{(step + 1) * 100}...",
            f"Analyzing chunk {step} of {total_steps}...",
            f"Computing results for step {step}..."
        ])

        results["processed"] += 1
        results["steps"].append(f"Step {step} completed")

        # Send progress update
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"task_{task_id}",
                {
                    "type": "task.update",
                    "task_id": task_id,
                    "status": "processing",
                    "message": action,
                    "progress": progress
                }
            )

        # Update database
        UserTask.update_task_progress(task_id, action, progress)

    # Send completion notification
    completion_message = f"Completed: {results['processed']} items processed successfully"

    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task.complete",
                "task_id": task_id,
                "status": "completed",
                "message": completion_message,
                "result": results
            }
        )

    # Update database
    UserTask.complete_task(task_id, completion_message, results)

    return results


@shared_task(bind=True)
def demo_task_with_error(self, fail_at_step=5, total_steps=10, step_delay=1):
    """
    Demo task that fails at a specific step to test error handling.

    Args:
        fail_at_step: Step number at which to fail (default: 5)
        total_steps: Total number of steps (default: 10)
        step_delay: Delay in seconds between steps (default: 1)

    Usage:
        >>> from OptsIO.tasks import demo_task_with_error
        >>> result = demo_task_with_error.delay(5, 10, 1)
        >>> print(f"Task ID: {result.id}")
    """
    channel_layer = get_channel_layer()
    task_id = self.request.id

    # Send start notification
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task.update",
                "task_id": task_id,
                "status": "processing",
                "message": "Starting task (will fail)...",
                "progress": 0
            }
        )

    # Process steps until failure
    for step in range(1, total_steps + 1):
        time.sleep(step_delay)

        progress = int((step / total_steps) * 100)

        # Check if we should fail
        if step == fail_at_step:
            error_message = f"Error at step {step}: Simulated failure for testing"

            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"task_{task_id}",
                    {
                        "type": "task.error",
                        "task_id": task_id,
                        "error": error_message,
                        "message": f"Task failed at step {step}"
                    }
                )

            # Update database
            UserTask.fail_task(task_id, f"Task failed at step {step}", error_message)

            raise Exception(error_message)

        # Send progress update
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"task_{task_id}",
                {
                    "type": "task.update",
                    "task_id": task_id,
                    "status": "processing",
                    "message": f"Processing step {step}...",
                    "progress": progress
                }
            )

        # Update database
        UserTask.update_task_progress(task_id, f"Processing step {step}...", progress)

    return {"status": "completed"}


@shared_task(bind=True)
def demo_quick_task(self):
    """
    Quick demo task that completes in 3 seconds.
    Good for quick testing.

    Usage:
        >>> from OptsIO.tasks import demo_quick_task
        >>> result = demo_quick_task.delay()
        >>> print(f"Task ID: {result.id}")
    """
    return demo_task_with_progress(self, total_steps=3, step_delay=1, task_name="Quick Demo")

