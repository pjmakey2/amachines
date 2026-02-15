# WebSocket Group Messaging Guide

## Overview

Send real-time messages, notifications, and files to **groups** of users simultaneously. Perfect for team communications, department-wide announcements, project updates, and role-based messaging.

## What are Groups?

Groups are custom channels that users can subscribe to. You can create groups for:
- **Teams**: `sales_team`, `support_team`, `developers`
- **Departments**: `finance`, `hr`, `operations`
- **Projects**: `project_alpha`, `migration_2025`
- **Roles**: `admins`, `managers`, `supervisors`
- **Custom**: Any grouping that makes sense for your application

## Quick Start

### 1. Subscribe Users to a Group (Frontend)

Users must subscribe to a group to receive messages:

```javascript
// Subscribe to a group
taskNotifications.subscribeToGroup('sales_team');

// Unsubscribe from a group
taskNotifications.unsubscribeFromGroup('sales_team');
```

### 2. Send Message to Group (Backend/Shell)

```python
python manage.py shell

>>> from OptsIO.ws_utils import ws_send_group_message
>>> ws_send_group_message('sales_team', 'New leads available in the system!')
True
```

All users subscribed to `sales_team` will instantly receive the message!

## Backend Functions

### 1. `ws_send_group_message()` - Send Message to Group

Send a simple message to all users in a group.

```python
from OptsIO.ws_utils import ws_send_group_message

# Basic group message
ws_send_group_message('sales_team', 'Team meeting in 15 minutes!')

# With additional data
ws_send_group_message(
    'developers',
    'Deployment successful',
    data={'version': '2.0.1', 'server': 'production'}
)
```

**Parameters:**
- `group_name` (str): Name of the group
- `message` (str): Message text
- `data` (dict, optional): Additional data

### 2. `ws_send_group_notification()` - Send Typed Notification to Group

Send a notification with a specific type (success, error, info, warning).

```python
from OptsIO.ws_utils import ws_send_group_notification

# Success notification
ws_send_group_notification(
    'sales_team',
    'Monthly target achieved!',
    'success',
    'Great Job!'
)

# Error notification
ws_send_group_notification(
    'admins',
    'Database backup failed',
    'error',
    'Critical Alert'
)

# Warning notification
ws_send_group_notification(
    'all_users',
    'System maintenance in 30 minutes',
    'warning',
    'Scheduled Maintenance'
)

# Info notification
ws_send_group_notification(
    'developers',
    'New API documentation available',
    'info',
    'Documentation Update'
)
```

**Parameters:**
- `group_name` (str): Name of the group
- `message` (str): Notification message
- `notification_type` (str): 'success', 'error', 'info', 'warning'
- `title` (str, optional): Notification title
- `data` (dict, optional): Additional data

### 3. `ws_send_group_file()` - Send File to Group

Notify all users in a group that a file is ready.

```python
from OptsIO.ws_utils import ws_send_group_file

# Basic file notification
ws_send_group_file(
    'sales_team',
    '/media/reports/weekly_sales.xlsx',
    'weekly_sales.xlsx'
)

# With custom message and file size
ws_send_group_file(
    'managers',
    '/media/reports/quarterly_summary.pdf',
    'quarterly_summary.pdf',
    message='Q4 Summary Report is ready',
    file_size=2457600  # bytes
)
```

**Parameters:**
- `group_name` (str): Name of the group
- `file_url` (str): URL or path to the file
- `file_name` (str, optional): Filename to display
- `message` (str, optional): Custom message
- `file_size` (int, optional): File size in bytes
- `data` (dict, optional): Additional data

## Frontend (JavaScript) Usage

### Subscribe to Groups

```javascript
// Subscribe when user joins a team/project
taskNotifications.subscribeToGroup('sales_team');
taskNotifications.subscribeToGroup('project_alpha');
taskNotifications.subscribeToGroup('admins');

// Unsubscribe when user leaves
taskNotifications.unsubscribeFromGroup('sales_team');
```

### Listen for Group Events

```javascript
// Listen for all group messages
taskNotifications.on('group_message', function(data) {
    console.log(`Message from ${data.group_name}: ${data.message}`);
    // Custom handling here
});

// Listen for group notifications
taskNotifications.on('group_notification', function(data) {
    console.log(`Notification from ${data.group_name}: ${data.message}`);
    // Custom handling here
});

// Listen for group files
taskNotifications.on('group_file', function(data) {
    console.log(`File from ${data.group_name}: ${data.file_name}`);
    // Custom download logic here
});
```

### Auto-subscribe Based on User Attributes

You can auto-subscribe users to groups based on their role, department, etc.:

```javascript
// Example: Auto-subscribe based on user data
document.addEventListener('DOMContentLoaded', () => {
    // Get user data from backend (example)
    const userDepartment = '{{ user.department }}';  // From Django template
    const userRole = '{{ user.role }}';

    // Auto-subscribe to relevant groups
    if (userDepartment === 'sales') {
        taskNotifications.subscribeToGroup('sales_team');
    }

    if (userRole === 'admin') {
        taskNotifications.subscribeToGroup('admins');
    }

    // Subscribe all users to general announcements
    taskNotifications.subscribeToGroup('all_users');
});
```

## Usage Examples

### Example 1: Team Announcements

```python
# From Django shell or view
from OptsIO.ws_utils import ws_send_group_notification

def announce_to_team(team_name, announcement):
    ws_send_group_notification(
        team_name,
        announcement,
        'info',
        'Team Announcement'
    )

# Usage
announce_to_team('sales_team', 'New product launch next week!')
announce_to_team('developers', 'Code freeze begins Friday')
```

### Example 2: Department-wide File Distribution

```python
from OptsIO.ws_utils import ws_send_group_file
import os

def distribute_report(department, file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    ws_send_group_file(
        f"{department}_dept",
        f"/media/reports/{file_name}",
        file_name,
        message=f"Monthly report for {department.upper()}",
        file_size=file_size
    )

# Usage
distribute_report('sales', '/path/to/sales_report.xlsx')
distribute_report('finance', '/path/to/finance_report.pdf')
```

### Example 3: Project Status Updates

```python
from OptsIO.ws_utils import ws_send_group_notification

class Project:
    def __init__(self, name):
        self.group_name = f"project_{name}"

    def notify_progress(self, message, status='info'):
        ws_send_group_notification(
            self.group_name,
            message,
            status,
            f'Project Update'
        )

# Usage
alpha = Project('alpha')
alpha.notify_progress('Phase 1 complete!', 'success')
alpha.notify_progress('Deployment in progress...', 'info')
```

### Example 4: Role-based Alerts

```python
from OptsIO.ws_utils import ws_send_group_notification

def alert_admins(message, level='warning'):
    ws_send_group_notification(
        'admins',
        message,
        level,
        'Admin Alert'
    )

def alert_managers(message):
    ws_send_group_notification(
        'managers',
        message,
        'info',
        'Management Notice'
    )

# Usage
alert_admins('Disk space at 90%', 'error')
alert_managers('Weekly reports are due tomorrow')
```

### Example 5: Dynamic Group Management in Views

```python
from django.shortcuts import render
from OptsIO.ws_utils import ws_send_group_message

def add_user_to_project(request, project_id):
    project = Project.objects.get(id=project_id)
    user = request.user

    # Add user to project (your logic)
    project.members.add(user)

    # Notify the project group
    ws_send_group_message(
        f'project_{project.slug}',
        f'{user.username} has joined the project!'
    )

    # Frontend will auto-subscribe the user to the group
    return render(request, 'project_detail.html', {
        'project': project,
        'subscribe_to_group': f'project_{project.slug}'
    })
```

Then in your template:
```html
<script>
    {% if subscribe_to_group %}
    document.addEventListener('DOMContentLoaded', () => {
        taskNotifications.subscribeToGroup('{{ subscribe_to_group }}');
    });
    {% endif %}
</script>
```

## Common Group Patterns

### 1. All Users Broadcast
```python
# Subscribe all users to 'all_users' group on login
# JavaScript in base template:
taskNotifications.subscribeToGroup('all_users');

# Send system-wide announcements
ws_send_group_notification('all_users', 'System update complete', 'success')
```

### 2. Department-based Groups
```python
# Auto-subscribe based on user department
# JavaScript:
taskNotifications.subscribeToGroup('dept_{{ user.department }}');

# Send department-specific messages
ws_send_group_message('dept_sales', 'Sales meeting at 2 PM')
ws_send_group_message('dept_hr', 'New benefits package available')
```

### 3. Role-based Groups
```python
# Auto-subscribe based on user role
# JavaScript:
{% for role in user.roles.all %}
    taskNotifications.subscribeToGroup('role_{{ role.name }}');
{% endfor %}

# Send role-specific notifications
ws_send_group_notification('role_admin', 'Admin panel updated', 'info')
ws_send_group_notification('role_manager', 'Approval queue has 5 items', 'warning')
```

### 4. Project/Task Groups
```python
# Subscribe users to their active projects
# JavaScript:
{% for project in user.active_projects.all %}
    taskNotifications.subscribeToGroup('project_{{ project.id }}');
{% endfor %}

# Send project updates
ws_send_group_notification('project_123', 'Milestone reached!', 'success')
```

## Group Naming Conventions

### Recommended Patterns

1. **Prefix by type:**
   - `team_sales`, `team_support`, `team_dev`
   - `dept_finance`, `dept_hr`, `dept_ops`
   - `project_123`, `project_alpha`
   - `role_admin`, `role_manager`

2. **Use lowercase and underscores:**
   - ✅ `sales_team`, `project_alpha`
   - ❌ `SalesTeam`, `Project-Alpha`

3. **Be descriptive but concise:**
   - ✅ `sales_north_region`
   - ❌ `sales_team_for_northern_sales_region_2025`

4. **Avoid special characters:**
   - ✅ `project_alpha_beta`
   - ❌ `project@alpha!beta`

## Combining User and Group Messaging

You can use both user-specific and group messages in the same application:

```python
from OptsIO.ws_utils import ws_send_message, ws_send_group_message

# Send to specific user
ws_send_message('john', 'You have been assigned a new task')

# Send to entire team
ws_send_group_message('sales_team', 'Team meeting in 10 minutes')

# Send to user AND their team
username = 'john'
team = 'sales_team'

ws_send_message(username, 'You are now team leader!')
ws_send_group_message(team, f'{username} is now the team leader!')
```

## Frontend Display

Group messages are displayed with a `[group_name]` prefix:

- **Messages**: `[sales_team] New leads available`
- **Notifications**: `[admins] Critical Alert: System backup failed`
- **Files**: `[managers] Q4 Summary Report is ready`

This helps users identify which group the message came from.

## Security Considerations

1. **Subscription Control**: Users can only subscribe from the frontend. Consider adding server-side validation if needed.

2. **Access Control**: Implement backend checks before sending group messages:
   ```python
   def send_to_admin_group(user, message):
       if not user.is_staff:
           return False
       return ws_send_group_message('admins', message)
   ```

3. **Group Validation**: Validate group names to prevent abuse:
   ```python
   VALID_GROUPS = ['sales_team', 'developers', 'admins', 'managers']

   def send_validated_group_message(group_name, message):
       if group_name not in VALID_GROUPS:
           logger.error(f"Invalid group: {group_name}")
           return False
       return ws_send_group_message(group_name, message)
   ```

4. **Rate Limiting**: Consider rate limiting for group broadcasts to prevent spam.

## Performance Considerations

- Group messages are sent to **all subscribed users** simultaneously
- Redis handles message distribution efficiently
- No performance impact on users not subscribed to the group
- Messages are only sent to **connected** users (users with browser open)

## Troubleshooting

### Users Not Receiving Group Messages

**Check if users are subscribed:**
```javascript
// In browser console
console.log(taskNotifications.subscribedGroups);
// Should show Set with group names
```

**Verify backend sending:**
```python
result = ws_send_group_message('test_group', 'Test message')
print(f"Sent: {result}")  # Should print True
```

**Check browser console:**
- Look for "Subscribed to group: ..." messages
- Check for "Group subscription confirmed: ..." messages

### Group Subscription Not Persisting

Group subscriptions are **per-session**. Users must re-subscribe after:
- Page refresh (unless you auto-subscribe in JavaScript)
- WebSocket reconnection (handled automatically if user was subscribed)
- Browser restart

**Solution**: Auto-subscribe in your page template:
```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Auto-subscribe to user's groups
    taskNotifications.subscribeToGroup('sales_team');
    taskNotifications.subscribeToGroup('all_users');
});
```

## Advanced: Server-side Group Management

You can create a Django model to manage group memberships:

```python
from django.db import models

class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField('auth.User', related_name='ws_groups')

    def send_message(self, message, data=None):
        from OptsIO.ws_utils import ws_send_group_message
        return ws_send_group_message(self.name, message, data)

    def send_notification(self, message, ntype='info', title=''):
        from OptsIO.ws_utils import ws_send_group_notification
        return ws_send_group_notification(self.name, message, ntype, title)

# Usage
sales_group = UserGroup.objects.get(name='sales_team')
sales_group.send_message('Team meeting in 15 minutes!')
```

Then in your template:
```html
<script>
    // Auto-subscribe to user's groups from database
    {% for group in user.ws_groups.all %}
        taskNotifications.subscribeToGroup('{{ group.name }}');
    {% endfor %}
</script>
```

---

**Created:** 2025-11-17
**Version:** 1.0

**See Also:**
- [WebSocket User Messaging](WEBSOCKET_USER_MESSAGING.md) - Send messages to specific users
- [WebSocket Setup](WEBSOCKET_SETUP.md) - Initial setup and configuration
