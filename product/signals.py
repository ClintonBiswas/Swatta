from product.tasks import send_sms_task
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from django.core.exceptions import ValidationError

@receiver(post_save, sender=Order)
def send_order_status_sms(sender, instance, created, **kwargs):
    if not created and instance.status in ['confirmed', 'delivered', 'shipped', 'canceled']:
        send_sms_task.delay(instance.id)

@receiver(pre_save, sender=Order)
def validate_status_change(sender, instance, **kwargs):
    if instance.id:  # Only for existing instances
        old = Order.objects.get(id=instance.id)
        if old.status != instance.status:
            # Add any validation logic here
            if instance.status == 'confirmed' and not instance.is_verified:
                raise ValidationError("Cannot confirm unverified order")