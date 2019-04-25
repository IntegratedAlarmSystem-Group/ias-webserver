from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """ Create token for user """
    if created:
        Token.objects.create(user=instance)


def reset_auth_token(instance):
    """ Method to assign a new token to a user """
    token = Token.objects.filter(user=instance)
    token.delete()
    Token.objects.get_or_create(user=instance)
