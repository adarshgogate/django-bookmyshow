from celery import shared_task
from django.utils import timezone
from .models import Seat

@shared_task
def release_expired_seats():
    now = timezone.now()
    expired = Seat.objects.filter(is_reserved=True, reserved_until__lt=now)
    count = expired.count()
    if count > 0:
        expired.update(is_reserved=False, reserved_until=None)
        return f"Released {count} expired seat reservations."
    return "No expired reservations found."
