from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

# User model
class User(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(unique=True)
    user_password = models.CharField(max_length=255)

    # Add Additional fields for profile
    user_phone = models.CharField(max_length=15, blank=True, null=True)
    user_dob = models.DateField(blank=True, null=True)
    user_address = models.TextField(max_length=255, blank=True, null=True)
    user_city = models.CharField(max_length=100, blank=True, null=True)
    user_country = models.CharField(max_length=100, default="India", blank=True, null=True)
    user_avatar = models.ImageField(upload_to='profile_avatars/', blank=True, null=True)

    # preferences
    preferred_currency = models.CharField(max_length=3, default='INR')
    preferred_language = models.CharField(max_length=10, default='en')
    auto_confirm_bookings = models.BooleanField(default=False)
    save_payment_methods = models.BooleanField(default=True)

    # notification settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    promo_emails = models.BooleanField(default=True)
    booking_reminders = models.BooleanField(default=True)

    # Account status
    loyalty_points = models.IntegerField(default=0)
    member_since = models.DateTimeField(auto_now_add=True)

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
    populer_hotel = models.BooleanField(default=False)

    def __str__(self):
        return self.hotel_name


# package model
class Package(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    hotel_name = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    package_name = models.CharField(max_length=100)
    package_description = models.TextField()  # Changed from CharField to TextField
    package_price = models.FloatField()
    duration_days = models.IntegerField()
    image = models.ImageField(upload_to='package_image/')
    populer_tour = models.BooleanField(default=False)

    def __str__(self):
        return self.package_name


# Booking Model - Working with your existing system
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

    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online Payment'),
            ('cash', 'Cash on Arrival')
        ],
        default='cash'
    )

    booking_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)

    # Payment status choices - keep as is (no 'completed' status needed)
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),      # Keep as 'success' for your existing data
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.user_name} booking - {self.payment_status}"


class BookingSession(models.Model):
    """Temporary storage for booking details before payment"""
    session_key = models.CharField(max_length=100, unique=True)
    booking_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


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