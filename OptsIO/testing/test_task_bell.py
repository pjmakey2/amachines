#!/usr/bin/env python
"""
Task Bell Notification Test Suite

Test the bell notification in the header with demo Celery tasks.

Usage from Django shell:
    >>> from OptsIO.testing.test_task_bell import *
    >>> run_demo_task()  # Runs a 10-step task

Make sure:
1. Redis is running
2. Celery worker is running: celery -A Toca3d worker -l info
3. Daphne is running: daphne -b 0.0.0.0 -p 8000 Toca3d.asgi:application
4. Browser is open with the app loaded
5. In browser console, subscribe to task: taskBell.addTask('task-id', 'Demo', 'Starting...')
"""

from OptsIO.tasks import (
    demo_task_with_progress,
    demo_task_with_error,
    demo_quick_task
)


def run_demo_task(steps=10, delay=1, name="Demo Task"):
    """
    Run the demo task with progress updates.

    Args:
        steps: Number of steps (default: 10)
        delay: Delay between steps in seconds (default: 1)
        name: Task name to display (default: "Demo Task")

    Returns:
        AsyncResult with task_id

    Example:
        >>> result = run_demo_task()
        >>> print(f"Task ID: {result.id}")
        >>> # In browser: taskBell.addTask('{result.id}', 'Demo Task', 'Starting...')
    """
    result = demo_task_with_progress.delay(steps, delay, name)
    print(f"\n{'='*60}")
    print("DEMO TASK STARTED")
    print(f"{'='*60}")
    print(f"Task ID: {result.id}")
    print(f"Steps: {steps}, Delay: {delay}s, Name: {name}")
    print(f"\nTo see in browser, run in browser console:")
    print(f"  taskBell.addTask('{result.id}', '{name}', 'Starting...');")
    print(f"{'='*60}\n")
    return result


def run_quick_task():
    """
    Run a quick 3-second demo task.

    Example:
        >>> result = run_quick_task()
    """
    result = demo_task_with_progress.delay(3, 1, "Quick Demo")
    print(f"\n{'='*60}")
    print("QUICK DEMO TASK STARTED")
    print(f"{'='*60}")
    print(f"Task ID: {result.id}")
    print(f"\nTo see in browser, run in browser console:")
    print(f"  taskBell.addTask('{result.id}', 'Quick Demo', 'Starting...');")
    print(f"{'='*60}\n")
    return result


def run_error_task(fail_at=5, steps=10, delay=1):
    """
    Run a demo task that will fail at a specific step.

    Args:
        fail_at: Step number at which to fail (default: 5)
        steps: Total steps (default: 10)
        delay: Delay between steps (default: 1)

    Example:
        >>> result = run_error_task(3)  # Fails at step 3
    """
    result = demo_task_with_error.delay(fail_at, steps, delay)
    print(f"\n{'='*60}")
    print("ERROR DEMO TASK STARTED")
    print(f"{'='*60}")
    print(f"Task ID: {result.id}")
    print(f"Will fail at step {fail_at} of {steps}")
    print(f"\nTo see in browser, run in browser console:")
    print(f"  taskBell.addTask('{result.id}', 'Error Demo', 'Starting...');")
    print(f"{'='*60}\n")
    return result


def run_multiple_tasks(count=3):
    """
    Run multiple demo tasks simultaneously to test concurrent display.

    Args:
        count: Number of tasks to run (default: 3)

    Example:
        >>> results = run_multiple_tasks(5)
    """
    results = []
    print(f"\n{'='*60}")
    print(f"STARTING {count} CONCURRENT TASKS")
    print(f"{'='*60}")

    for i in range(1, count + 1):
        result = demo_task_with_progress.delay(
            10,  # steps
            1,   # delay
            f"Task {i}"
        )
        results.append(result)
        print(f"Task {i} ID: {result.id}")

    print(f"\nTo see all in browser, run in browser console:")
    for i, result in enumerate(results, 1):
        print(f"  taskBell.addTask('{result.id}', 'Task {i}', 'Starting...');")

    print(f"{'='*60}\n")
    return results


def run_long_task(minutes=1):
    """
    Run a longer demo task (useful for realistic testing).

    Args:
        minutes: Duration in minutes (default: 1)

    Example:
        >>> result = run_long_task(2)  # 2-minute task
    """
    steps = minutes * 12  # 12 steps per minute (5 seconds each)
    result = demo_task_with_progress.delay(steps, 5, f"Long Task ({minutes}min)")
    print(f"\n{'='*60}")
    print(f"LONG DEMO TASK STARTED ({minutes} minutes)")
    print(f"{'='*60}")
    print(f"Task ID: {result.id}")
    print(f"Steps: {steps} (5 seconds each)")
    print(f"\nTo see in browser, run in browser console:")
    print(f"  taskBell.addTask('{result.id}', 'Long Task', 'Starting...');")
    print(f"{'='*60}\n")
    return result


# Helper to print task info
def task_info(result):
    """
    Print information about a task result.

    Args:
        result: AsyncResult from a task

    Example:
        >>> result = run_demo_task()
        >>> task_info(result)
    """
    print(f"\n{'='*40}")
    print(f"Task ID: {result.id}")
    print(f"State: {result.state}")
    print(f"Ready: {result.ready()}")
    if result.ready():
        try:
            print(f"Result: {result.result}")
        except Exception as e:
            print(f"Error: {e}")
    print(f"{'='*40}\n")


if __name__ == '__main__':
    print(__doc__)
    print("\nAvailable functions:")
    print("  run_demo_task()     - Run a 10-step demo task")
    print("  run_quick_task()    - Run a quick 3-second task")
    print("  run_error_task()    - Run a task that fails")
    print("  run_multiple_tasks()- Run multiple concurrent tasks")
    print("  run_long_task()     - Run a 1-minute task")
    print("  task_info(result)   - Get info about a task")
