from django.db.models.signals import post_save
from django.dispatch import receiver
from fyle_slack_app.models import User, NotificationPreference
from fyle_slack_app.models.notification_preferences import NotificationType


# This signal acts as a trigger when a user is created
# This will automatically add the notification preferences for that user
@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    if created:
        # Creating notification preferences list for bulk create
        notification_preferences = []
        for notification_type in NotificationType:
            notification_preference = NotificationPreference(
                slack_user=instance,
                notification_type=notification_type.value
            )
            notification_preferences.append(notification_preference)

        # Creating notification preferences in bulk for a user
        NotificationPreference.objects.bulk_create(notification_preferences)
