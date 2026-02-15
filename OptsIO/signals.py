"""OptsIO Signals"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from OptsIO.models import UserProfile, UserBusiness
from datetime import datetime
import logging

log = logging.getLogger(__name__)


@receiver(user_logged_in)
def create_user_profile_on_login(sender, request, user, **kwargs):
    """
    Create UserProfile for user if it doesn't exist when they log in
    Also update last_login timestamp
    Check if user has Business configured and set flag in session
    """
    try:
        profile, created = UserProfile.objects.get_or_create(
            username=user.username,
            defaults={'preferences': {}}
        )

        if created:
            log.info(f'UserProfile created for user: {user.username}')
        else:
            # Update last_login
            profile.last_login = datetime.now()
            profile.save()
            log.info(f'UserProfile last_login updated for user: {user.username}')

        # Check if user has at least one business
        user_businesses_count = UserBusiness.objects.filter(userprofileobj=profile).count()

        if user_businesses_count == 0:
            request.session['needs_business_setup'] = True
            log.info(f'User {user.username} needs business setup')
        else:
            request.session['needs_business_setup'] = False

    except Exception as e:
        log.error(f'Error creating/updating UserProfile for {user.username}: {str(e)}')
