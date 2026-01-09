from django.core.mail import EmailMultiAlternatives

def send_ticket_confirmation(user, booking):
    subject = f"Booking Confirmation – {booking.event.name}"
    text_body = (
        f"Hello {user.first_name},\n\n"
        f"Your booking has been confirmed!\n\n"
        f"Booking ID: {booking.id}\n"
        f"Event: {booking.event.name}\n"
        f"Date: {booking.event.date}\n"
        f"Seat Number: {booking.seat_number}\n\n"
        f"Thank you for choosing BookMySeat.\n"
        f"Enjoy the show!\n"
    )

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color:#2c3e50;">Booking Confirmation</h2>
        <p>Hello {user.first_name},</p>
        <p>Your booking has been confirmed!</p>
        <ul>
          <li><strong>Booking ID:</strong> {booking.id}</li>
          <li><strong>Event:</strong> {booking.event.name}</li>
          <li><strong>Date:</strong> {booking.event.date}</li>
          <li><strong>Seat Number:</strong> {booking.seat_number}</li>
        </ul>
        <p>Thank you for choosing <strong>BookMySeat</strong>. We look forward to seeing you!</p>
        <hr>
        <p style="font-size:12px; color:#7f8c8d;">
          This is an automated message from BookMySeat. Please do not reply.
        </p>
      </body>
    </html>
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email="noreply@bookmyseat.com",
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
