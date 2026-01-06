from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Booking, Seat

@receiver(post_delete, sender=Booking)
def reset_seats_on_booking_delete(sender, instance, **kwargs):
    print(f"Signal fired: resetting seats for booking {instance.id}")
    for seat in instance.seats.all():
        seat.is_reserved = False
        seat.is_booked = False
        seat.reserved_until = None
        seat.save()
