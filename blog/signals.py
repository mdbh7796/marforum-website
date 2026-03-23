# Signals for blog app
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Post


@receiver(post_save, sender=Post)
def publish_post_if_ready(sender, instance, created, **kwargs):
    if instance.status == 'pending_review':
        pass
