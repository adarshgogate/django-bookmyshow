from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from users.utils.email_utils import send_ticket_confirmation
from movies.models import Booking
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, F
from django.contrib.admin.views.decorators import staff_member_required
from movies.utils.email import send_ticket_confirmation
from django.core.mail import EmailMultiAlternatives
import logging
from django.db import transaction
import sendgrid



logger = logging.getLogger(__name__)
from django.core.mail import EmailMultiAlternatives
from decouple import config

def send_ticket_confirmation(user, booking):
    try:
        subject = f"Your Booking Confirmation – {booking.event.name}"
        from_email = config("DEFAULT_FROM_EMAIL", default="gogateadarsh@gmail.com")  # verified sender
        to_email = user.email

        text_body = (
            f"Hi {user.first_name},\n\n"
            f"Thank you for booking with BookMySeat!\n\n"
            f"Your booking is confirmed:\n"
            f"Event: {booking.event.name}\n"
            f"Date: {booking.event.date.strftime('%B %d, %Y')}\n"
            f"Seat Number: {booking.seat_number}\n\n"
            f"We look forward to seeing you!\n\n"
            f"Best regards,\n"
            f"The BookMySeat Team"
        )

        html_body = f"""
        <html>
          <body>
            <p>Hi {user.first_name},</p>
            <p>Thank you for booking with <strong>BookMySeat</strong>!</p>
            <p>Your booking is confirmed:</p>
            <ul>
              <li><strong>Event:</strong> {booking.event.name}</li>
              <li><strong>Date:</strong> {booking.event.date.strftime('%B %d, %Y')}</li>
              <li><strong>Seat Number:</strong> {booking.seat_number}</li>
            </ul>
            <p>We look forward to seeing you!</p>
            <p>Best regards,<br>The BookMySeat Team</p>
          </body>
        </html>
        """

        msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()

        logger.info(f"✅ Email sent to {user.email} for booking #{booking.id}")
    except Exception as e:
        logger.error(f"❌ Email failed for booking #{booking.id}: {e}")

# stripe integration
stripe.api_key = settings.STRIPE_SECRET_KEY

def movie_list(request):
    search_query = request.GET.get('search')

    genre = request.GET.get('genre')
    language = request.GET.get('language')

    if search_query:
        movies = Movie.objects.filter(name__icontains=search_query)
    else:
        movies = Movie.objects.all()

    if genre:
        movies = movies.filter(genre__iexact=genre)

    if language:
        movies = movies.filter(language__iexact=language)

    return render(request, 'movies/movie_list.html', {'movies': movies})


def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theater = Theater.objects.filter(movie=movie)
    return render(request, 'movies/theater_list.html', {'movie': movie, 'theaters': theater})

# @login_required(login_url='/login/')
# def book_seats(request, theater_id):
#     theaters = get_object_or_404(Theater, id=theater_id)
#     seats = Seat.objects.filter(theater=theaters)

#     if request.method == 'POST':
#         selected_seats = request.POST.getlist('seats')
#         if not selected_seats:
#             return render(request, "movies/seat_selection.html", {
#                 'theaters': theaters,
#                 'seats': seats,
#                 'error': "No seat selected"
#             })

#         # Check if any selected seat is already booked
#         already_booked = Seat.objects.filter(id__in=selected_seats, is_booked=True)
#         if already_booked.exists():
#             error_message = f"The following seats are already booked: {', '.join([s.seat_number for s in already_booked])}"
#             return render(request, "movies/seat_selection.html", {
#                 'theaters': theaters,
#                 'seats': seats,
#                 'error': error_message
#             })

#         # For simplicity, one seat per booking
#         seat = Seat.objects.get(id=selected_seats[0])
#         booking = Booking.objects.create(
#             user=request.user,
#             seat=seat,
#             movie=theaters.movie,
#             theater=theaters,
#             status="pending"   # ✅ mark as pending until payment succeeds
#         )

#         # Redirect to Stripe Checkout
#         return redirect('create_checkout_session', booking_id=booking.id)

#     return render(request, 'movies/seat_selection.html', {'theaters': theaters, 'seats': seats})

def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = "confirmed"
    booking.save()
    print(f"📌 Confirming booking {booking.id} for user {booking.user.email}")
    try:
        send_ticket_confirmation(booking.user, booking)
        print(f"✅ Email sent to {booking.user.email} for booking #{booking.id}")
    except Exception as e:
        print(f"❌ Email failed for booking #{booking.id}: {e}")

    return redirect('profile')



@login_required(login_url='/login/')
def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "inr",
                "product_data": {
                    "name": f"{booking.movie.name} - {booking.theater.name} Seat {booking.seat.seat_number}"
                },
                "unit_amount": 50000,  # ₹500 in paise
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.build_absolute_uri(f"/payment/stripe/success/?booking_id={booking.id}"),
        cancel_url=request.build_absolute_uri("/payment/stripe/cancel/"),
    )

    return redirect(session.url, code=303)

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

@transaction.atomic
def stripe_success(request):
    booking_id = request.GET.get("booking_id")
    booking = get_object_or_404(Booking.objects.select_for_update(), id=booking_id)

    # Release expired reservations
    expired_reservations = Seat.objects.filter(
        is_reserved=True,
        reserved_until__lt=timezone.now(),
        id__in=booking.seats.values_list("id", flat=True)
    )
    for seat in expired_reservations:
        seat.is_reserved = False
        seat.reserved_until = None
        seat.save()

    # Safety check
    if booking.seats.filter(is_booked=True).exists():
        return redirect("checkout_error")

    # Mark seats as booked
    reserved_seats = booking.seats.filter(is_reserved=True, reserved_until__gte=timezone.now())
    for seat in reserved_seats:
        seat.is_reserved = False
        seat.is_booked = True
        seat.reserved_until = None
        seat.save()

    # Update booking
    booking.status = "confirmed"
    booking.payment_status = "paid"
    booking.save()

    # Collect seat numbers
    seat_numbers = ", ".join([seat.seat_number for seat in booking.seats.all()])

    # ✅ Send confirmation email via SendGrid
    try:
        sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = booking.user.email
        subject = "Booking Confirmed"

        html_content = f"""
            <h2>🎬 Booking Confirmation</h2>
            <p>Hi {booking.user.first_name},</p>
            <p>Your booking for <b>{booking.movie.name}</b> at <b>{booking.theater.name}</b> is confirmed.</p>
            <p><b>Seats:</b> {seat_numbers}</p>
            <p>Thank you for choosing <b>BookMySeat</b>.</p>
            <p><i>📩 If you don’t see this email in your inbox, please check your Spam or Promotions folder and mark it as “Not Spam” to ensure future delivery.</i></p>
        """

        mail = Mail(
            from_email = settings.DEFAULT_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        response = sg.send(mail)
        logger.info(f"✅ Email sent to {booking.user.email}, status {response.status_code}")

    except Exception as e:
        logger.error(f"❌ Email failed: {e}")

    return render(request, "movies/payment_success.html", {"booking": booking, "seat_numbers": seat_numbers})

def stripe_cancel(request):
    return render(request, "movies/payment_failed.html")

def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    print("Stripe backend key:", stripe.api_key)

    if request.method == "POST":
        seat_ids = request.POST.getlist("seats")
        if not seat_ids:
            messages.error(request, "Please select at least one seat.")
            return render(request, "movies/seat_selection.html", {
                "theaters": theater,
                "seats": theater.seats.all()
            })

        # Check for already booked seats
        already_booked = Seat.objects.filter(id__in=seat_ids, is_booked=True)
        if already_booked.exists():
            messages.error(request, "One or more selected seats are already booked.")
            return render(request, "movies/seat_selection.html", {
                "theaters": theater,
                "seats": theater.seats.all()
            })


        # Reserve seats for 5 minutes
        Seat.objects.filter(id__in=seat_ids).update(
            is_reserved=True,
            reserved_until=timezone.now() + timedelta(minutes=5)
        )
        booking = Booking.objects.create(
            user=request.user,
            movie=theater.movie,
            theater=theater,
            status="reserved",
            payment_status="unpaid"
        )
        booking.seats.add(*map(int, seat_ids))
        booking.save()


        print("Booking seats after add:", booking.seats.all())  # Debug

        # ✅ Build seat_numbers string for Stripe
        seat_numbers = ", ".join(
            Seat.objects.filter(id__in=seat_ids).values_list("seat_number", flat=True)
        )

        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "inr",
                    "product_data": {
                        "name": f"{booking.movie.name} - {booking.theater.name} Seats {seat_numbers}"
                    },
                    "unit_amount": 50000,  # ₹500 in paise
                },
                "quantity": len(seat_ids),
            }],
            mode="payment",
            success_url=request.build_absolute_uri(
                reverse("stripe_success") + f"?booking_id={booking.id}"
            ),
            cancel_url=request.build_absolute_uri(reverse("stripe_cancel")),
        )

        return redirect(session.url, code=303)

    return render(request, "movies/seat_selection.html", {
        "theaters": theater,
        "seats": theater.seats.all()
    })

    

def checkout_page(request, booking_id):
    print("Frontend Stripe key:", settings.STRIPE_PUBLISHABLE_KEY)
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "checkout.html", {
        "booking": booking,
        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY
    })
   
def reserve_seat(request, seat_id): 
    seat = get_object_or_404(Seat, id=seat_id) 
    if not seat.is_reserved and not seat.is_booked: 
        seat.is_reserved = True 
        seat.reserved_until = timezone.now() + timedelta(minutes=5)
        seat.save()
        # Redirect to checkout or seat selection page
        return redirect("checkout_page")
    else:
        # Seat already reserved or booked 
        return redirect("seat_selection_page")
    

@staff_member_required
def analytics_dashboard(request):
    # Total revenue (assuming ₹500 per seat)
    total_revenue = (
        Booking.objects.filter(status="confirmed")
        .aggregate(revenue=Count("seats") * 500)["revenue"]
    )

    # Most popular movies
    popular_movies = (
        Booking.objects.filter(status="confirmed")
        .values("movie__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    # Busiest theaters
    busiest_theaters = (
        Booking.objects.filter(status="confirmed")
        .values("theater__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    context = {
        "total_revenue": total_revenue or 0,
        "popular_movies": popular_movies,
        "busiest_theaters": busiest_theaters,
    }
    return render(request, "admin/analytics_dashboard.html", context)


#razorpay
# def initiate_payment(request, booking_id):
#     booking = get_object_or_404(Booking, id=booking_id)

#     client = razorpay.Client(
#         auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
#     )

#     razorpay_order = client.order.create({
#         "amount": 500 * 100,   # paise
#         "currency": "INR",
#         "payment_capture": 1
#     })

#     # Save Razorpay order id
#     booking.payment_id = razorpay_order["id"]
#     booking.save()

#     return render(request, "movies/payment.html", {
#         "razorpay_order_id": razorpay_order["id"],   # ✅ explicit
#         "amount": razorpay_order["amount"],          # ✅ explicit
#         "booking": booking,
#         "razorpay_key": settings.RAZORPAY_KEY_ID
#     })
    
# @csrf_exempt
# def payment_callback(request):
#     print(">>> Callback POST:", request.POST)

#     if request.method == "POST":
#         data = {
#             "razorpay_order_id": request.POST.get("razorpay_order_id"),
#             "razorpay_payment_id": request.POST.get("razorpay_payment_id"),
#             "razorpay_signature": request.POST.get("razorpay_signature"),
#         }
#     else:
#         return HttpResponseBadRequest("Invalid request method")

#     client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#     try:
#         client.utility.verify_payment_signature(data)

#         booking = Booking.objects.get(payment_id=data["razorpay_order_id"])
#         booking.status = "confirmed"
#         booking.save()

#         send_ticket_confirmation(booking.user, booking)

#         return render(request, "movies/payment_success.html", {"booking": booking})

#     except Exception as e:
#         print(">>> Payment failed:", e)
#         return render(request, "movies/payment_failed.html")
