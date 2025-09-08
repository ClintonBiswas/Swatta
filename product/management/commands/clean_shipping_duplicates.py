# product/management/commands/clean_shipping_duplicates.py

from django.core.management.base import BaseCommand
from django.db.models import Count
from product.models import ShippingInformation

class Command(BaseCommand):
    help = 'Clean duplicate (user, phone) shipping info entries'

    def handle(self, *args, **kwargs):
        duplicates = ShippingInformation.objects \
            .values('user', 'phone') \
            .annotate(count=Count('id')) \
            .filter(count__gt=1)

        for dup in duplicates:
            user = dup['user']
            phone = dup['phone']
            records = ShippingInformation.objects.filter(user=user, phone=phone).order_by('-created_at')
            keep = records.first()
            to_delete = records.exclude(pk=keep.pk)
            self.stdout.write(self.style.WARNING(f"Deleting {to_delete.count()} duplicates for user {user} - phone {phone}"))
            to_delete.delete()

        self.stdout.write(self.style.SUCCESS("Duplicate shipping entries deleted."))
