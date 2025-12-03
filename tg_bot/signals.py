from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from tg_bot.models import Event


@receiver(pre_save, sender=Event)
def update_event_status(sender, instance, **kwargs):
    now = timezone.now()
    
    if instance.date <= now:
        instance.is_active = True
    
    elif instance.date >= now + timezone.timedelta(hours=3):
        instance.is_active = False