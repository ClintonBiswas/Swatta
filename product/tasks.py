from celery import shared_task
import requests
from django.conf import settings
from .models import Order, ScheduledMessage
from django.urls import reverse
from django.core.mail import send_mail
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def send_sms_task(order_id):
    try:
        order = Order.objects.get(id=order_id)
        phone = order.shipping_info.phone
        invoice_url = f"{settings.SITE_DOMAIN}{reverse('product:order_confirmation', args=[order.order_id])}"
        facebook_url = "https://www.facebook.com/swattaa"

        if order.status == 'confirmed':
            message = (
            f"📢 Dear Customer,\n"
            f"✅ Your order has been confirmed!\n"
            f"📄 View your invoice: {invoice_url}\n\n"
            f"🙏 Thank you for shopping with us.\n"
            f"🛍️ Swatta - সত্তা "
        )
        elif order.status == 'delivered':
            message = (
            f"📦 Dear Customer,\n"
            f"🎉 Your order has been delivered successfully!\n"
            f"❤️ We hope you’re happy with your purchase.\n\n"
            f"👍 Stay connected with us on Facebook: {facebook_url}\n\n"
            f"🙏 Thank you for shopping with us.\n"
            f"🛍️ Swatta - সত্তা "
        )
        elif order.status == 'shipped':
            message = (
            f"🚚 Dear Customer,\n"
            f"📦 Your order has been shipped and is on its way!\n\n"
            f"📞 We’ll notify you once it’s delivered.\n"
            f"👍 Stay updated on our Facebook page: {facebook_url}\n\n"
            f"🙏 Thank you for shopping with us.\n"
            f"🛍️ Swatta - সত্তা "
        )
        elif order.status == 'canceled':
            message = (
            f"⚠️ Dear Customer,\n"
            f"❌ Your order has been canceled.\n"
            f"If this was a mistake or you have any questions, please contact us.\n\n"
            f"👍 Stay connected: {facebook_url}\n"
            f"📞 We’re here to help!\n\n"
            f"🛍️ Swatta - সত্তা "
        )

        payload = {
            "api_key": settings.BULKSMS_API_KEY,
            "senderid": settings.BULKSMS_SENDER_ID,
            "number": phone,
            "message": message
        }
        requests.post(settings.BULKSMS_API_URL, data=payload)

    except Exception as e:
        print(f"SMS Task failed: {e}")



@shared_task(bind=True, max_retries=3)
def send_verification_code_task(self, phone, email, verification_code):
    try:
        # Validate phone number
        if len(phone) != 11 or not phone.startswith(('013', '014', '015', '016', '017', '018', '019')):
            raise ValueError(f"Invalid Bangladeshi phone number: {phone}")

        # Prepare messages
        sms_message = f"Swatta - সত্তা: আপনার কোড {verification_code}। নিরাপত্তার জন্য এটি কারও সাথে শেয়ার করবেন না।"
        email_message = f"Your Let's Shop verification code is: {verification_code}\n\nDo not share this code with anyone."

        # Try SMS first
        try:
            sms_params = {
                "api_key": settings.BULKSMS_API_KEY,
                "type": "text",
                "number": phone,
                "senderid": settings.BULKSMS_SENDER_ID,
                "message": sms_message
            }

            response = requests.get(
                settings.BULKSMS_API_URL, 
                params=sms_params, 
                timeout=10
            )
            
            if response.status_code == 200 and "SMS SUBMITTED" in response.text.upper():
                logger.info(f"SMS sent to {phone}")
                return {'status': 'success', 'method': 'sms'}
            
            raise ValueError(f"SMS API error: {response.text}")
            
        except Exception as sms_error:
            logger.warning(f"SMS failed ({phone}): {str(sms_error)}")
            # Fallback to email
            try:
                send_mail(
                    subject='Your Verification Code',
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False
                )
                logger.info(f"Email sent to {email}")
                return {'status': 'success', 'method': 'email'}
            except Exception as email_error:
                logger.error(f"Email failed ({email}): {str(email_error)}")
                raise

    except Exception as e:
        logger.error(f"Verification code sending failed: {str(e)}")
        raise self.retry(exc=e, countdown=60)

# scheduling message

@shared_task
def process_scheduled_messages():
    due_messages = ScheduledMessage.objects.filter(
        status='pending',
        scheduled_time__lte=timezone.now()
    )

    for scheduled in due_messages:
        scheduled.status = 'processing'
        scheduled.save()

        try:
            # Decide recipients
            if scheduled.send_to_all:
                recipients = Order.objects.values_list('shipping_info__phone', flat=True).distinct()
            else:
                recipients = scheduled.phone_numbers.split(',')

            for phone in recipients:
                if not phone:
                    continue
                payload = {
                    "api_key": settings.BULKSMS_API_KEY,
                    "senderid": settings.BULKSMS_SENDER_ID,
                    "number": phone.strip(),
                    "message": scheduled.message
                }
                requests.post(settings.BULKSMS_API_URL, data=payload)

            scheduled.status = 'sent'
            scheduled.save()

        except Exception as e:
            scheduled.status = 'failed'
            scheduled.save()
            logger = logging.getLogger(__name__)
            logger.error(f"Scheduled message {scheduled.id} failed: {e}")