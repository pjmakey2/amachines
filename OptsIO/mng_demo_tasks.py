"""
Demo Task Management Module

Provides methods to start demo Celery tasks via the iom endpoint.
Used for testing the bell notification system.
"""

import logging
from OptsIO.tasks import demo_task_with_progress, demo_task_with_error
from OptsIO.models import UserTask

logger = logging.getLogger(__name__)


class DemoTasks:
    """
    Class to manage demo tasks via iom endpoint.

    Usage from frontend:
        formData.append('module', 'OptsIO');
        formData.append('package', 'mng_demo_tasks');
        formData.append('attr', 'DemoTasks');
        formData.append('mname', 'start_demo_task');
    """

    def start_demo_task(self, *args, **kwargs) -> dict:
        """
        Start a demo task with progress updates.

        Parameters (from qdict):
            steps: Number of steps (default: 10)
            delay: Delay between steps in seconds (default: 1)
            name: Task name (default: "Demo Task")

        Returns:
            dict with task_id
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        username = userobj.username if userobj else 'anonymous'

        steps = int(q.get('steps', 10))
        delay = int(q.get('delay', 1))
        name = q.get('name', 'Demo Task')

        # Start Celery task
        result = demo_task_with_progress.delay(steps, delay, name)

        # Save task to database for persistence
        UserTask.create_task(
            task_id=result.id,
            username=username,
            name=name
        )

        logger.info(f"Started demo task {result.id}: {name}, {steps} steps, {delay}s delay for user {username}")

        return {
            'task_id': result.id,
            'name': name,
            'steps': steps,
            'delay': delay,
            'status': 'started'
        }

    def start_error_task(self, *args, **kwargs) -> dict:
        """
        Start a demo task that will fail at a specific step.

        Parameters (from qdict):
            fail_at: Step at which to fail (default: 5)
            steps: Total steps (default: 10)
            delay: Delay between steps (default: 1)

        Returns:
            dict with task_id
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        username = userobj.username if userobj else 'anonymous'

        fail_at = int(q.get('fail_at', 5))
        steps = int(q.get('steps', 10))
        delay = int(q.get('delay', 1))

        # Start Celery task
        result = demo_task_with_error.delay(fail_at, steps, delay)

        # Save task to database for persistence
        UserTask.create_task(
            task_id=result.id,
            username=username,
            name='Error Test'
        )

        logger.info(f"Started error demo task {result.id}: fails at step {fail_at} for user {username}")

        return {
            'task_id': result.id,
            'fail_at': fail_at,
            'steps': steps,
            'delay': delay,
            'status': 'started'
        }

    def start_quick_task(self, *args, **kwargs) -> dict:
        """
        Start a quick 3-second demo task.

        Returns:
            dict with task_id
        """
        userobj = kwargs.get('userobj')
        username = userobj.username if userobj else 'anonymous'

        result = demo_task_with_progress.delay(3, 1, "Quick Demo")

        # Save task to database for persistence
        UserTask.create_task(
            task_id=result.id,
            username=username,
            name='Quick Demo'
        )

        logger.info(f"Started quick demo task {result.id} for user {username}")

        return {
            'task_id': result.id,
            'name': 'Quick Demo',
            'steps': 3,
            'delay': 1,
            'status': 'started'
        }

    def start_multiple_tasks(self, *args, **kwargs) -> dict:
        """
        Start multiple demo tasks simultaneously.

        Parameters (from qdict):
            count: Number of tasks to start (default: 3)

        Returns:
            dict with task_ids list
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        username = userobj.username if userobj else 'anonymous'
        count = int(q.get('count', 3))

        task_ids = []
        for i in range(1, count + 1):
            name = f"Task {i}"
            result = demo_task_with_progress.delay(8, 1, name)
            task_ids.append(result.id)

            # Save task to database for persistence
            UserTask.create_task(
                task_id=result.id,
                username=username,
                name=name
            )

            logger.info(f"Started task {i} of {count}: {result.id} for user {username}")

        return {
            'task_ids': task_ids,
            'count': count,
            'status': 'started'
        }

    def get_user_tasks(self, *args, **kwargs) -> dict:
        """
        Get all active tasks for the current user.

        Returns:
            dict with tasks list
        """
        userobj = kwargs.get('userobj')
        username = userobj.username if userobj else 'anonymous'

        tasks = UserTask.get_user_tasks(username, include_completed=True)

        task_list = []
        for task in tasks:
            task_list.append({
                'task_id': task.task_id,
                'name': task.name,
                'message': task.message,
                'progress': task.progress,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            })

        return {
            'tasks': task_list,
            'count': len(task_list)
        }

    def remove_task(self, *args, **kwargs) -> dict:
        """
        Remove a task from the user's task list.

        Parameters (from qdict):
            task_id: Task ID to remove

        Returns:
            dict with status
        """
        q = kwargs.get('qdict', {})
        task_id = q.get('task_id')

        if task_id:
            UserTask.objects.filter(task_id=task_id).delete()
            return {'status': 'removed', 'task_id': task_id}

        return {'status': 'error', 'message': 'No task_id provided'}
