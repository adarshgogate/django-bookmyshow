from django.db import models
from django.contrib.auth.models import User 
import re
from django.utils import timezone 

YOUTUBE_ID_RE = re.compile( 
            r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{11})" 
        )
class Movie(models.Model):
    name= models.CharField(max_length=255)
    image= models.ImageField(upload_to="movies/")
    rating = models.DecimalField(max_digits=3,decimal_places=1)
    cast= models.TextField()
    description= models.TextField(blank=True,null=True) # optional
    genre = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    trailer_url = models.URLField(blank=True, null=True)
    demo_poster = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.name

    def trailer_id(self):
        """Extract YouTube video ID from the stored URL.""" 
        if not self.trailer_url: 
            return None 
        match = YOUTUBE_ID_RE.search(self.trailer_url) 
        return match.group(1) if match else None
    
    def embed_url(self): 
        """Return the proper embed URL for iframe."""
        vid = self.trailer_id() 
        if vid: 
            return f"https://www.youtube-nocookie.com/embed/{vid}" 
        return None
    
class Theater(models.Model):
    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie,on_delete=models.CASCADE,related_name='theaters')
    time= models.DateTimeField()

    def __str__(self):
        return f'{self.name} - {self.movie.name} at {self.time}'

class Seat(models.Model):
    theater = models.ForeignKey(Theater,on_delete=models.CASCADE,related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked=models.BooleanField(default=False)
    is_reserved = models.BooleanField(default=False)
    reserved_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'
    def release_if_expired(self):
        if self.is_reserved and self.reserved_until and timezone.now() > self.reserved_until: 
            self.is_reserved = False 
            self.reserved_until = None 
            self.save()

class Booking(models.Model):
    STATUS_CHOICES = [ ("reserved", "Reserved"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ]
    PAYMENT_CHOICES = [ ("unpaid", "Unpaid"), ("paid", "Paid"), ]
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)
    movie=models.ForeignKey(Movie,on_delete=models.CASCADE)
    theater=models.ForeignKey(Theater,on_delete=models.CASCADE)
    booked_at=models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="reserved")
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="unpaid")
    
    def __str__(self):
        seat_numbers = ", ".join([seat.seat_number for seat in self.seats.all()])
        return f"Booking by {self.user.username} for {seat_numbers} at {self.theater.name}"
    
   
