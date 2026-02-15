#!/usr/bin/env python
"""
WebSocket User Messaging Test Script

Run this from Django shell to test WebSocket user messaging:
    python manage.py shell
    >>> from OptsIO.testing.test_websocket_user import *
    >>> test_all('amadmin')
"""

from OptsIO.ws_utils import (
    ws_send_message,
    ws_send_notification,
    ws_send_file,
    ws_broadcast_message,
    test_websocket_connection,
    ws_connect,
    # Group functions
    ws_send_group_message,
    ws_send_group_notification,
    ws_send_group_file
)


def test_simple_message(username):
    """Test simple message sending"""
    print(f"\n=== Testing Simple Message to {username} ===")
    result = ws_send_message(username, 'Hello from test script!')
    print(f"Result: {result}")
    return result


def test_ws_connect_alias(username):
    """Test ws_connect alias"""
    print(f"\n=== Testing ws_connect alias to {username} ===")
    result = ws_connect(username=username, message='Testing ws_connect alias!')
    print(f"Result: {result}")
    return result


def test_notifications(username):
    """Test all notification types"""
    print(f"\n=== Testing Notifications to {username} ===")

    results = []

    # Success notification
    print("Sending success notification...")
    result = ws_send_notification(username, 'Operation completed successfully!', 'success', 'Success')
    results.append(('success', result))
    print(f"Success result: {result}")

    # Error notification
    print("Sending error notification...")
    result = ws_send_notification(username, 'An error occurred', 'error', 'Error')
    results.append(('error', result))
    print(f"Error result: {result}")

    # Warning notification
    print("Sending warning notification...")
    result = ws_send_notification(username, 'This is a warning', 'warning', 'Warning')
    results.append(('warning', result))
    print(f"Warning result: {result}")

    # Info notification
    print("Sending info notification...")
    result = ws_send_notification(username, 'This is an info message', 'info', 'Info')
    results.append(('info', result))
    print(f"Info result: {result}")

    return results


def test_file_notification(username):
    """Test file download notification"""
    print(f"\n=== Testing File Notification to {username} ===")

    # Test with a sample file URL
    result = ws_send_file(
        username=username,
        file_url='/media/reports/test_report.xlsx',
        file_name='test_report.xlsx',
        message='Your test report is ready!',
        file_size=123456
    )
    print(f"Result: {result}")
    return result


def test_message_with_data(username):
    """Test message with additional data"""
    print(f"\n=== Testing Message with Data to {username} ===")

    data = {
        'count': 100,
        'status': 'completed',
        'timestamp': '2025-11-17 10:30:00'
    }

    result = ws_send_message(
        username,
        'Process completed',
        data=data
    )
    print(f"Result: {result}")
    print(f"Data sent: {data}")
    return result


def test_broadcast(usernames):
    """Test broadcasting to multiple users"""
    print(f"\n=== Testing Broadcast to {len(usernames)} users ===")

    result = ws_broadcast_message(
        'System maintenance scheduled for tonight',
        usernames=usernames
    )
    print(f"Sent to {result}/{len(usernames)} users")
    return result


def test_connection(username):
    """Test WebSocket connection"""
    print(f"\n=== Testing WebSocket Connection for {username} ===")
    result = test_websocket_connection(username)
    print(f"Result: {result}")
    return result


def test_all(username='amadmin'):
    """Run all tests for a specific user"""
    print(f"\n{'='*60}")
    print(f"WEBSOCKET USER MESSAGING TEST SUITE")
    print(f"Testing with username: {username}")
    print(f"{'='*60}")

    results = {}

    # Test connection first
    results['connection'] = test_connection(username)

    # Test simple message
    results['simple_message'] = test_simple_message(username)

    # Test ws_connect alias
    results['ws_connect_alias'] = test_ws_connect_alias(username)

    # Test message with data
    results['message_with_data'] = test_message_with_data(username)

    # Test notifications
    results['notifications'] = test_notifications(username)

    # Test file notification
    results['file_notification'] = test_file_notification(username)

    # Test broadcast
    results['broadcast'] = test_broadcast([username])

    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    for test_name, result in results.items():
        if test_name == 'notifications':
            print(f"{test_name}: {len([r for _, r in result if r])}/{len(result)} passed")
        else:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name}: {status}")

    print(f"{'='*60}")
    print("\nCheck your browser to see if notifications appeared!")
    print(f"{'='*60}\n")

    return results


# Quick test functions for shell usage
def quick_test(username='amadmin'):
    """Quick single message test"""
    return ws_send_message(username, '🚀 Quick test from OptsIO!')


def quick_notify(username='amadmin', msg='Test notification', ntype='info'):
    """Quick notification test"""
    return ws_send_notification(username, msg, ntype, 'Test')


def quick_file(username='amadmin', url='/media/test.xlsx'):
    """Quick file notification test"""
    return ws_send_file(username, url, url.split('/')[-1])


# ==================== GROUP MESSAGING TESTS ====================

def test_group_message(group_name='test_group'):
    """Test sending message to a group"""
    print(f"\n=== Testing Group Message to {group_name} ===")
    result = ws_send_group_message(group_name, 'Hello to the group!')
    print(f"Result: {result}")
    return result


def test_group_notifications(group_name='test_group'):
    """Test all notification types for groups"""
    print(f"\n=== Testing Group Notifications to {group_name} ===")

    results = []

    # Success notification
    print("Sending success group notification...")
    result = ws_send_group_notification(group_name, 'Group task completed!', 'success', 'Success')
    results.append(('success', result))
    print(f"Success result: {result}")

    # Error notification
    print("Sending error group notification...")
    result = ws_send_group_notification(group_name, 'Group error occurred', 'error', 'Error')
    results.append(('error', result))
    print(f"Error result: {result}")

    # Info notification
    print("Sending info group notification...")
    result = ws_send_group_notification(group_name, 'Group information', 'info', 'Info')
    results.append(('info', result))
    print(f"Info result: {result}")

    return results


def test_group_file(group_name='test_group'):
    """Test group file notification"""
    print(f"\n=== Testing Group File Notification to {group_name} ===")

    result = ws_send_group_file(
        group_name,
        '/media/reports/group_report.xlsx',
        'group_report.xlsx',
        message='Report ready for the team',
        file_size=987654
    )
    print(f"Result: {result}")
    return result


def test_all_groups(group_name='test_group'):
    """Run all group messaging tests"""
    print(f"\n{'='*60}")
    print(f"WEBSOCKET GROUP MESSAGING TEST SUITE")
    print(f"Testing with group: {group_name}")
    print(f"{'='*60}")
    print("\nNOTE: Make sure users have subscribed to this group first!")
    print(f"Frontend: taskNotifications.subscribeToGroup('{group_name}');")
    print(f"{'='*60}\n")

    results = {}

    # Test group message
    results['group_message'] = test_group_message(group_name)

    # Test group notifications
    results['group_notifications'] = test_group_notifications(group_name)

    # Test group file
    results['group_file'] = test_group_file(group_name)

    print(f"\n{'='*60}")
    print("GROUP TEST SUMMARY")
    print(f"{'='*60}")

    for test_name, result in results.items():
        if test_name == 'group_notifications':
            print(f"{test_name}: {len([r for _, r in result if r])}/{len(result)} passed")
        else:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{test_name}: {status}")

    print(f"{'='*60}")
    print("\nCheck subscribed users' browsers to see if notifications appeared!")
    print(f"{'='*60}\n")

    return results


# Quick group test functions
def quick_group_msg(group_name='test_group', msg='Quick group test!'):
    """Quick group message test"""
    return ws_send_group_message(group_name, msg)


def quick_group_notify(group_name='test_group', msg='Group notification', ntype='info'):
    """Quick group notification test"""
    return ws_send_group_notification(group_name, msg, ntype, 'Test')


if __name__ == '__main__':
    print("Import this module in Django shell and run test_all('your_username')")
    print("For group tests, run: test_all_groups('your_group_name')")
