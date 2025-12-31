from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Booking

@receiver(post_delete, sender=Booking)
def reset_seat_on_booking_delete(sender, instance, **kwargs):
    print(f"Signal fired: resetting seat {instance.seat.seat_number}")
    if instance.seat:
        instance.seat.is_booked = False
        instance.seat.save()

