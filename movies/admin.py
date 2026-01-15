from django.contrib import admin
from .models import Movie, Theater, Seat,Booking
from django.utils.html import format_html


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'genre', 'language', 'trailer_preview','poster_preview'] 
    fields = ['name', 'rating', 'cast', 'description', 'genre', 'language', 'trailer_url','poster_url']
    def trailer_preview(self, obj): 
        if obj.embed_url(): 
            return format_html(
                '<iframe width="200" height="120" src="{}" frameborder="0" allowfullscreen></iframe>', 
                obj.embed_url() 
            )
        return "No trailer"
    def poster_preview(self, obj):
        if obj.poster_url: 
            return format_html('<img src="{}" width="100" />', obj.poster_url)
        return "No poster"
    
    trailer_preview.short_description = "Trailer"
@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'movie', 'time']

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater', 'seat_number', 'is_booked']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie','theater','booked_at','status']
    def display_seats(self, obj):
        return ", ".join([seat.seat_number for seat in obj.seats.all()])
    display_seats.short_description = "Seats"