from django.urls import path
from . import views
from .views import confirm_booking,create_checkout_session,stripe_success,stripe_cancel
urlpatterns=[
    path('',views.movie_list,name='movie_list'),
    path('<int:movie_id>/theaters',views.theater_list,name='theater_list'),
    path('theater/<int:theater_id>/seats/book/',views.book_seats,name='book_seats'),
    path('booking/<int:booking_id>/confirm/', confirm_booking, name='confirm_booking'),
    # #razorpay
    # path('booking/<int:booking_id>/pay/', initiate_payment, name='initiate_payment'),
    # path('payment/callback/', payment_callback, name='payment_callback'),
    
    #stripe
    path('booking/<int:booking_id>/stripe/', create_checkout_session, name='create_checkout_session'),
    path("payment/stripe/success/", views.stripe_success, name="stripe_success"),
    path("payment/stripe/cancel/", views.stripe_cancel, name="stripe_cancel"),
    path("create-checkout-session/<int:booking_id>/", views.create_checkout_session, name="create_checkout_session"),
    path("checkout/<int:booking_id>/", views.checkout_page, name="checkout_page"),
]
