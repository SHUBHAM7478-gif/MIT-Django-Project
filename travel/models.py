from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.


# User model
class User(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(unique=True)
    user_password = models.CharField(max_length=255)

    def __str__(self):
        return self.user_name
    


# Destination Model
class Destination(models.Model):

    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    description = models.TextField()
    

    def __str__(self):
        return self.name
    
    


# Hotel model
class Hotel(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    hotel_name = models.TextField(max_length=100)
    hotel_address = models.TextField()
    ratings = models.FloatField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    room_availability = models.IntegerField()
    image = models.ImageField(upload_to='hotel_image/')

    populer_hotel=models.BooleanField(default=False)



    def __str__(self):
        return self.hotel_name
    


# package model
class Package(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)

    hotel_name = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    package_name = models.CharField(max_length=100)
    package_description = models.CharField()

    package_price = models.FloatField()
    duration_days = models.IntegerField()

    image = models.ImageField(upload_to='package_image/')
    populer_tour=models.BooleanField(default=False)


    def __str__(self):
        return self.package_name
    


# Booking Model
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100, default="Unknown")
    email = models.EmailField(null=True, blank=True)   
    address = models.CharField(max_length=255, null=True, blank=True)

    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)

    guests = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    booking_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user_name} booking"

class PackageImage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='package_images/')

    def __str__(self):
        return self.package.package_name
    
class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotel_images/')

    def __str__(self):
        return self.hotel.hotel_name