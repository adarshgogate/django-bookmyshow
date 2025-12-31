from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def send_ticket_confirmation(user, booking):
    subject = f"Your Ticket Confirmation - Booking #{booking.id}"

    message = render_to_string('emails/ticket_confirmation.html', {
        'user_name': user.first_name or user.username,
        'booking_id': booking.id,
        'movie_name': booking.movie.name,
        'theater_name': booking.theater.name,
        'seat_number': booking.seat.seat_number,
        'show_time': getattr(booking.theater, 'time', None),  # if theater has time
    })

    email = EmailMessage(
        subject=subject,
        body=message,
        to=[user.email]
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)
