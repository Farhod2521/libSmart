from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book, Customer, Notification

@receiver(post_save, sender=Book)
def notify_customers_on_new_book(sender, instance, created, **kwargs):
    if created:
        customers = Customer.objects.all()
        for customer in customers:
            Notification.objects.create(
                customer=customer,
                message=f"Yangi kitob qo‘shildi: {instance.title}"
            )