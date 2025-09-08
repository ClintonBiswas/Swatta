from django.db.models.signals import post_save
from user.models import CustomUser
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from email.utils import formataddr

@receiver(post_save, sender=CustomUser)

def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        subject = "Welcome to Our Website!"
        message = f"Hi {instance.name},\n\nThank you for registering on our website!"
        from_email = formataddr(("Rongdhanu", settings.EMAIL_HOST_USER)) 
        recipient_list = [instance.email]

        send_mail(subject, message, from_email, recipient_list)

        print(f"Welcome email sent to {instance.email}")  # Debugging