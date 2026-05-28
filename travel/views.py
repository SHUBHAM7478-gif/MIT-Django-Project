from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from datetime import datetime
import os
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
import razorpay
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt


def landing(request):
    result = Package.objects.filter(populer_tour=True)[:3]
    h = Hotel.objects.filter(populer_hotel=True)[:3]

    return render(request, "travels.html", {
        "packages": result,
        "hotels": h,
        "query": None,
        'user_name': request.session.get('user_name')
    })


def succes(request, booking_id=None):
    """Success page after booking confirmation"""
    booking = None
    if booking_id:
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            pass
    
    return render(request, 'bookingsuccsfull.html', {
        'booking': booking,
        'user_name': request.session.get('user_name')
    })


def user_registration(request):
    if request.method == 'POST':
        user_name = request.POST.get('user_name')   
        user_email = request.POST.get('user_email')
        user_password = make_password(request.POST.get('user_password'))

        # Check if user already exists
        if User.objects.filter(user_email=user_email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'signup.html')
        
        if User.objects.filter(user_name=user_name).exists():
            messages.error(request, 'Username already taken!')
            return render(request, 'signup.html')

        User.objects.create(
            user_name=user_name,
            user_email=user_email,
            user_password=user_password
        )
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')

    return render(request, 'signup.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('user_name')
        password = request.POST.get('user_password')

        user = User.objects.filter(user_name=username).first()

        if user and check_password(password, user.user_password):
            
            request.session['user_id'] = user.id
            request.session['user_name'] = user.user_name
            request.session['user_email'] = user.user_email

            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)

            messages.success(request, f'Welcome back, {user.user_name}!')
            return redirect('travels')
        else:
            messages.error(request, 'Invalid username or password!')
            return render(request, 'login.html')

    return render(request, 'login.html')


def travels_page(request):
    user_name = request.session.get('user_name')
    result = Package.objects.filter(populer_tour=True)[:3]
    h = Hotel.objects.filter(populer_hotel=True)[:3]
    return render(request, 'travels.html', {
        'user_name': user_name,
        "packages": result,
        "hotels": h,
        "query": None
    })


def logout_user(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('/')


def search_method(request):
    user_name = request.session.get('user_name')
    query = request.GET.get('search')
    packages = []
    hotels = []

    if query:
        packages = Package.objects.filter(destination__name__icontains=query)
        hotels = Hotel.objects.filter(destination__name__icontains=query)

    return render(request, 'travels.html', {
        'packages': packages,
        'hotels': hotels,
        'query': query,
        'user_name': user_name
    })


# def package_booking(request, id):
#     """Package booking - handles both cash and online payment"""
#     if not request.session.get('user_id'):
#         return redirect(f'/login/?next=/package-book/{id}/')
    
#     package = get_object_or_404(Package, id=id)
#     user_id = request.session.get('user_id')
#     user = get_object_or_404(User, id=user_id)

#     if request.method == "POST":
#         print("="*50)
#         print("PACKAGE BOOKING POST REQUEST RECEIVED")
#         print("POST Data:", request.POST)
#         print("="*50)
        
#         payment_method = request.POST.get("payment_method")
#         name = request.POST.get('name')
#         email = request.POST.get('email')
#         address = request.POST.get('address')
#         check_in = request.POST.get('check_in')
#         check_out = request.POST.get('check_out')
#         guests = int(request.POST.get('guests') or 1)

#         # Validate dates
#         check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
#         check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
#         today = timezone.now().date()
        
#         if check_in_date < today:
#             messages.error(request, "Check-in date cannot be in the past!")
#             return render(request, 'package.html', {
#                 'package': package, 
#                 'user_name': request.session.get('user_name'),
#                 'initial_name': user.user_name,
#                 'initial_email': user.user_email,
#                 'initial_address': user.user_address or ''
#             })
        
#         if check_out_date <= check_in_date:
#             messages.error(request, "Check-out date must be after check-in date!")
#             return render(request, 'package.html', {
#                 'package': package, 
#                 'user_name': request.session.get('user_name'),
#                 'initial_name': user.user_name,
#                 'initial_email': user.user_email,
#                 'initial_address': user.user_address or ''
#             })
        
#         # Calculate duration and check against package limits
#         duration_days = (check_out_date - check_in_date).days
#         if duration_days > package.duration_days:
#             messages.error(request, f"This package allows maximum {package.duration_days} days only! You selected {duration_days} days.")
#             return render(request, 'package.html', {
#                 'package': package, 
#                 'user_name': request.session.get('user_name'),
#                 'initial_name': user.user_name,
#                 'initial_email': user.user_email,
#                 'initial_address': user.user_address or ''
#             })

#         total_price = guests * package.package_price

#         if payment_method == "cash":
#             # Cash on arrival - create booking directly
#             booking = Booking.objects.create(
#                 user_id=user_id,
#                 package=package,
#                 name=name,
#                 email=email,
#                 address=address,
#                 check_in=check_in,
#                 check_out=check_out,
#                 guests=guests,
#                 total_price=total_price,
#                 payment_method='cash',
#                 payment_status='confirmed'
#             )
#             messages.success(request, f'✅ Package booking confirmed! Booking ID: #{booking.id}. Total: ₹{total_price} (Pay on arrival)')
#             return redirect('success_page', booking_id=booking.id)
#         else:
#             # Online payment - store in session
#             booking_data = {
#                 'type': 'package',
#                 'package_id': package.id,
#                 'user_id': user_id,
#                 'name': name,
#                 'email': email,
#                 'address': address,
#                 'check_in': check_in,
#                 'check_out': check_out,
#                 'guests': guests,
#                 'total_price': str(total_price),
#                 'payment_method': 'online',
#             }
#             request.session['temp_booking'] = booking_data
#             return redirect('payment_page')

#     # GET request - show form with pre-filled data
#     return render(request, 'package.html', {
#         'package': package, 
#         'user_name': request.session.get('user_name'),
#         'initial_name': user.user_name,
#         'initial_email': user.user_email,
#         'initial_address': user.user_address or ''
#     })


def hotel_booking(request, id):
    """Hotel booking - handles both cash and online payment"""
    if not request.session.get('user_id'):
        return redirect(f'/login/?next=/hotel-book/{id}/')
    
    hotel = get_object_or_404(Hotel, id=id)
    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        print("="*50)
        print("HOTEL BOOKING POST REQUEST RECEIVED")
        print("POST Data:", request.POST)
        print("="*50)
        
        payment_method = request.POST.get("payment_method")
        name = request.POST.get('h_name')
        email = request.POST.get('h_email')
        address = request.POST.get('Address')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests') or 1)
        
        # Validate dates
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        today = timezone.now().date()
        
        if check_in_date < today:
            messages.error(request, "Check-in date cannot be in the past!")
            return render(request, 'hotel.html', {
                'hotel': hotel, 
                'user_name': request.session.get('user_name'),
                'initial_name': user.user_name,
                'initial_email': user.user_email,
                'initial_address': user.user_address or ''
            })
        
        if check_out_date <= check_in_date:
            messages.error(request, "Check-out date must be after check-in date!")
            return render(request, 'hotel.html', {
                'hotel': hotel, 
                'user_name': request.session.get('user_name'),
                'initial_name': user.user_name,
                'initial_email': user.user_email,
                'initial_address': user.user_address or ''
            })

        # Check room availability
        days = (check_out_date - check_in_date).days
        if hotel.room_availability < 1:
            messages.error(request, "Sorry, no rooms available for selected dates!")
            return render(request, 'hotel.html', {
                'hotel': hotel, 
                'user_name': request.session.get('user_name'),
                'initial_name': user.user_name,
                'initial_email': user.user_email,
                'initial_address': user.user_address or ''
            })

        total_price = (days * float(hotel.price_per_night)) * guests

        if payment_method == "cash":
            # Cash on arrival - create booking directly and reduce room availability
            hotel.room_availability -= 1
            hotel.save()
            
            booking = Booking.objects.create(
                user_id=user_id,
                hotel=hotel,
                name=name,
                email=email,
                address=address,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                total_price=total_price,
                payment_method='cash',
                payment_status='confirmed'
            )
            messages.success(request, f'✅ Hotel booked! Booking ID: #{booking.id}. Total: ₹{total_price} (Pay on arrival)')
            return redirect('success_page', booking_id=booking.id)
        else:
            # Online payment - store in session
            booking_data = {
                'type': 'hotel',
                'hotel_id': hotel.id,
                'user_id': user_id,
                'name': name,
                'email': email,
                'address': address,
                'check_in': check_in,
                'check_out': check_out,
                'guests': guests,
                'total_price': str(total_price),
                'payment_method': 'online',
            }
            request.session['temp_booking'] = booking_data
            return redirect('payment_page')

    # GET request - show form with pre-filled data
    return render(request, 'hotel.html', {
        'hotel': hotel, 
        'user_name': request.session.get('user_name'),
        'initial_name': user.user_name,
        'initial_email': user.user_email,
        'initial_address': user.user_address or ''
    })


def payment_page(request):
    """Payment page with Razorpay"""
    temp_booking = request.session.get('temp_booking')
    
    if not temp_booking:
        messages.error(request, "No booking found! Please start over.")
        return redirect('travels')
    
    amount_rupees = float(temp_booking['total_price'])
    amount_paisa = int(amount_rupees * 100)
    
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    
    # Create Razorpay order
    payment = client.order.create({
        "amount": amount_paisa,
        "currency": "INR",
        "payment_capture": 1,
        "receipt": f"booking_{temp_booking.get('user_id')}_{int(timezone.now().timestamp())}"
    })
    
    # Store payment order ID in session
    request.session['razorpay_order_id'] = payment['id']
    
    # Get booking name for display
    booking_name = temp_booking.get('name', 'Guest')
    
    # Get package or hotel name for display
    if temp_booking.get('type') == 'package':
        try:
            package = Package.objects.get(id=temp_booking['package_id'])
            booking_item_name = package.package_name
        except:
            booking_item_name = "Package Booking"
    else:
        try:
            hotel = Hotel.objects.get(id=temp_booking['hotel_id'])
            booking_item_name = hotel.hotel_name
        except:
            booking_item_name = "Hotel Booking"
    
    context = {
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount_rupees,
        "booking_name": booking_name,
        "booking_email": temp_booking.get('email', ''),
        "name": booking_name,
        "pac": booking_item_name,
        "user_name": request.session.get('user_name')
    }
    
    return render(request, "payment.html", context)


def booking_history(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    
    bookings = Booking.objects.filter(user_id=user_id).order_by('-booking_at')

    packages_count = bookings.filter(package__isnull=False).count()
    hotels_count = bookings.filter(hotel__isnull=False).count()
    total_guests = sum(booking.guests for booking in bookings)
    total_spent = sum(float(booking.total_price) for booking in bookings if booking.payment_status == 'confirmed')
    
    context = {
        'bookings': bookings,
        'packages_count': packages_count,
        'hotels_count': hotels_count,
        'total_guests': total_guests,
        'total_spent': total_spent,
        'user_name': request.session.get('user_name'),
        'today': timezone.now().date(),
    }

    return render(request, 'booking_history.html', context)


# def cancel_booking(request, id):
#     """Professional cancel booking - with refund logic and status tracking"""
#     booking = get_object_or_404(Booking, id=id)
    
#     # Check if user owns this booking
#     if booking.user.id != request.session.get('user_id'):
#         messages.error(request, "You don't have permission to cancel this booking!")
#         return redirect('my_bookings')
    
#     # Check if already cancelled
#     if booking.payment_status == 'cancelled':
#         messages.warning(request, f"Booking #{booking.id} is already cancelled.")
#         return redirect('my_bookings')
    
#     # Check if already completed
#     if booking.payment_status == 'completed':
#         messages.error(request, "Cannot cancel completed booking.")
#         return redirect('my_bookings')
    
#     # Check if check-in date has passed
#     today = timezone.now().date()
#     if booking.check_in and booking.check_in < today:
#         messages.error(request, "Cannot cancel booking after check-in date has passed.")
#         return redirect('my_bookings')
    
#     # Calculate cancellation fee based on days before check-in
#     cancellation_fee_percentage = 0
#     refund_amount = float(booking.total_price)
    
#     if booking.check_in:
#         days_before = (booking.check_in - today).days
        
#         if days_before < 0:
#             messages.error(request, "Cannot cancel booking after check-in date.")
#             return redirect('my_bookings')
#         elif days_before == 0:
#             cancellation_fee_percentage = 100  # No refund on same day
#             messages.warning(request, "Same-day cancellation: No refund will be issued.")
#         elif days_before <= 2:
#             cancellation_fee_percentage = 75  # 25% refund
#             refund_amount = refund_amount * 0.25
#             messages.warning(request, f"Cancellation fee: 75%. Refund amount: ₹{refund_amount:.2f}")
#         elif days_before <= 7:
#             cancellation_fee_percentage = 50  # 50% refund
#             refund_amount = refund_amount * 0.50
#             messages.warning(request, f"Cancellation fee: 50%. Refund amount: ₹{refund_amount:.2f}")
#         elif days_before <= 14:
#             cancellation_fee_percentage = 25  # 75% refund
#             refund_amount = refund_amount * 0.75
#             messages.warning(request, f"Cancellation fee: 25%. Refund amount: ₹{refund_amount:.2f}")
#         else:
#             messages.info(request, f"Full refund of ₹{refund_amount:.2f} will be processed.")
    
#     # Update booking status
#     booking.payment_status = 'cancelled'
#     booking.save()
    
#     # Restore hotel room availability if applicable
#     if booking.hotel:
#         booking.hotel.room_availability += 1
#         booking.hotel.save()
#         messages.info(request, f"Room availability restored for {booking.hotel.hotel_name}.")
    
#     # For online payments, initiate refund (in production, integrate with payment gateway)
#     if booking.payment_method == 'online' and cancellation_fee_percentage < 100:
#         messages.info(request, f"Refund of ₹{refund_amount:.2f} will be processed to your original payment method within 5-7 business days.")
#     elif booking.payment_method == 'online' and cancellation_fee_percentage == 100:
#         messages.warning(request, "No refund applicable for this cancellation.")
    
#     messages.success(request, f'✅ Booking #{booking.id} has been cancelled successfully.')
#     return redirect('my_bookings')


def package_details(request, id):
    package = get_object_or_404(Package, id=id)

    return render(request, 'viewdetails.html', {
        'package': package,
        'd': package.package_description,
        'user_name': request.session.get('user_name')
    })


def hotel_details(request, id):
    hotel = get_object_or_404(Hotel, id=id)

    return render(request, 'viewdetails.html', {
        'hotel': hotel,
        'user_name': request.session.get('user_name')
    })


def show_package(request):
    package = Package.objects.all()
    return render(request, 'Show_Package.html', {
        'packages': package, 
        'user_name': request.session.get('user_name')
    })


def show_hotel(request):
    hotels = Hotel.objects.all()
    return render(request, 'Show_Hotel.html', {
        'hotels': hotels, 
        'user_name': request.session.get('user_name')
    })


def add_to_cart(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    
    cart = request.session.get('cart', [])

    if id not in cart:
        cart.append(id)
        messages.success(request, 'Package added to wishlist!')

    request.session['cart'] = cart

    return redirect(request.META.get('HTTP_REFERER', '/travels/'))


def add_hotel_cart(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    
    hotel_cart = request.session.get('hotel_cart', [])

    if id not in hotel_cart:
        hotel_cart.append(id)
        messages.success(request, 'Hotel added to wishlist!')

    request.session['hotel_cart'] = hotel_cart
    return redirect(request.META.get('HTTP_REFERER', '/travels/'))


def remove_package_cart(request, id):
    cart = request.session.get('cart', [])
    if id in cart:
        cart.remove(id)
        messages.success(request, 'Package removed from wishlist!')
    request.session['cart'] = cart
    return redirect('cart_details')


def remove_hotel_cart(request, id):
    hotel_cart = request.session.get('hotel_cart', [])
    if id in hotel_cart:
        hotel_cart.remove(id)
        messages.success(request, 'Hotel removed from wishlist!')
    request.session['hotel_cart'] = hotel_cart
    return redirect('cart_details')


def cart_details(request):
    cart = request.session.get('cart', [])
    hotel_cart = request.session.get('hotel_cart', [])

    packages = Package.objects.filter(id__in=cart)
    hotels = Hotel.objects.filter(id__in=hotel_cart)

    total = Decimal('0')

    for p in packages:
        total += Decimal(str(p.package_price))

    for h in hotels:
        total += Decimal(str(h.price_per_night))

    context = {
        'packages': packages,
        'hotels': hotels,
        'total': total,
        'user_name': request.session.get('user_name')
    }

    return render(request, 'addcart.html', context)


def foot(request):
    page_type = request.GET.get('type')

    context = {
        'enquiry': page_type == 'enquiry',
        'booking': page_type == 'booking',
        'privacy': page_type == 'privacy',
        'refund': page_type == 'refund',
        'adventure': page_type == 'adventure',
        'hotels': page_type == 'hotels',
        'beach': page_type == 'beach',
        'user_name': request.session.get('user_name')
    }

    return render(request, 'footerdetails.html', context)


def contact(request):
    return render(request, 'contract.html', {'user_name': request.session.get('user_name')})


def my_Profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')
    
    bookings = Booking.objects.filter(user=user).order_by('-booking_at')
    
    today = timezone.now().date()
    completed_bookings = 0
    active_bookings = 0
    upcoming_bookings = 0
    
    for booking in bookings:
        if booking.payment_status == 'cancelled':
            continue
        if booking.check_out and booking.check_out < today:
            completed_bookings += 1
        elif booking.check_in and booking.check_in <= today and booking.check_out and booking.check_out >= today:
            active_bookings += 1
        elif booking.check_in and booking.check_in > today:
            upcoming_bookings += 1
    
    context = {
        'user_name': request.session.get('user_name'),
        'user': user,
        'bookings': bookings,
        'recent_bookings': bookings.filter(payment_status='confirmed')[:5],
        'total_bookings': bookings.filter(payment_status='confirmed').count(),
        'completed_bookings': completed_bookings,
        'active_bookings': active_bookings,
        'upcoming_bookings': upcoming_bookings,
        'member_since': user.member_since.year if user.member_since else 2024,
        'today': today,
    }
    
    return render(request, 'my_profile.html', context)


def update_profile(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        try:
            user = User.objects.get(id=user_id)
            user.user_name = request.POST.get('user_name')
            user.user_email = request.POST.get('user_email')
            user.user_phone = request.POST.get('user_phone')
            user.user_dob = request.POST.get('user_dob') or None
            user.user_address = request.POST.get('user_address')
            user.user_city = request.POST.get('user_city')
            user.user_country = request.POST.get('user_country')
            user.save()
            
            # Update session name if changed
            request.session['user_name'] = user.user_name
            request.session['user_email'] = user.user_email
            
            messages.success(request, 'Profile updated successfully!')
        except User.DoesNotExist:
            messages.error(request, 'User not found!')

    return redirect('profile')


def change_password(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        try:
            user = User.objects.get(id=user_id)
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not check_password(current_password, user.user_password):
                messages.error(request, 'Current password is incorrect!')
            elif len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters!')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match!')
            else:
                user.user_password = make_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully! Please login again.')
                request.session.flush()
                return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User not found!')
    
    return redirect('profile')


def change_avatar(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Please login first!")
            return redirect('login')

        user = User.objects.get(id=user_id)
        image = request.FILES.get('user_avatar')

        if image:
            # Delete old avatar if exists
            if user.user_avatar:
                user.user_avatar.delete()
            user.user_avatar = image
            user.save()
            messages.success(request, "Profile picture updated successfully!")
        else:
            messages.error(request, "Please select an image!")

    return redirect('profile')


def update_preferences(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        
        try:
            user = User.objects.get(id=user_id)
            user.preferred_currency = request.POST.get('preferred_currency', 'INR')
            user.preferred_language = request.POST.get('preferred_language', 'en')
            user.auto_confirm_bookings = request.POST.get('auto_confirm_bookings') == 'on'
            user.save_payment_methods = request.POST.get('save_payment_methods') == 'on'
            user.save()
            messages.success(request, 'Preferences updated successfully!')
        except User.DoesNotExist:
            messages.error(request, 'User not found!')
    
    return redirect('profile')


def update_notifications(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        
        try:
            user = User.objects.get(id=user_id)
            user.email_notifications = request.POST.get('email_notifications') == 'on'
            user.sms_notifications = request.POST.get('sms_notifications') == 'on'
            user.promo_emails = request.POST.get('promo_emails') == 'on'
            user.booking_reminders = request.POST.get('booking_reminders') == 'on'
            user.save()
            messages.success(request, 'Notification settings updated successfully!')
        except User.DoesNotExist:
            messages.error(request, 'User not found!')
    
    return redirect('profile')


def download_booking_bill(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user owns this booking
    if booking.user.id != request.session.get('user_id'):
        messages.error(request, "You don't have permission to download this bill!")
        return redirect('my_bookings')

    response = HttpResponse(content_type='application/pdf')
    filename = f"booking_bill_{booking_id}_{datetime.now().timestamp()}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'title_style',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=24,
        textColor=colors.HexColor('#1a5d7f'),
        spaceAfter=20
    )

    normal_style = styles['BodyText']

    elements = []

    elements.append(Paragraph("TripTravels", title_style))
    elements.append(Paragraph("Premium Travel Booking Invoice", styles['Heading3']))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%"))
    elements.append(Spacer(1, 20))

    booking_type = "Tour Package" if booking.package else "Hotel Booking"
    booking_name = ""
    if booking.package:
        booking_name = booking.package.package_name
    if booking.hotel:
        booking_name = booking.hotel.hotel_name

    # Calculate duration nights
    duration_nights = "N/A"
    if booking.check_in and booking.check_out:
        duration_nights = (booking.check_out - booking.check_in).days

    data = [
        ['Booking ID', f'#{booking.id}'],
        ['Booking Type', booking_type],
        ['Booking Name', booking_name],
        ['Customer Name', booking.name],
        ['Email', booking.email or 'N/A'],
        ['Guests', str(booking.guests)],
        ['Check In', str(booking.check_in)],
        ['Check Out', str(booking.check_out)],
        ['Duration', f'{duration_nights} nights' if duration_nights != "N/A" else "N/A"],
        ['Payment Method', booking.payment_method.title()],
        ['Payment Status', booking.payment_status.title()],
        ['Total Amount', f'₹ {booking.total_price}'],
    ]

    table = Table(data, colWidths=[180, 280])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5d7f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#e0e0e0")),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))
    
    status_color = colors.HexColor('#27ae60') if booking.payment_status == 'confirmed' else colors.HexColor('#e67e22')
    status_style = ParagraphStyle(
        'status_style',
        parent=normal_style,
        textColor=status_color,
        fontSize=12
    )
    
    elements.append(Paragraph(f"<b>Payment Status:</b> {booking.payment_status.title()}", status_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Thank you for booking with TripTravels. We wish you a wonderful journey.", normal_style))
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%"))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Generated Automatically by TripTravels", styles['Italic']))

    doc.build(elements)
    return response


# @csrf_exempt
# def payment_verification(request):
#     """Verify payment and create booking"""
#     if request.method == "POST":
#         try:
#             payment_id = request.POST.get('razorpay_payment_id', '')
#             order_id = request.POST.get('razorpay_order_id', '')
#             signature = request.POST.get('razorpay_signature', '')
            
#             client = razorpay.Client(
#                 auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
#             )
            
#             params_dict = {
#                 'razorpay_order_id': order_id,
#                 'razorpay_payment_id': payment_id,
#                 'razorpay_signature': signature
#             }
            
#             client.utility.verify_payment_signature(params_dict)
            
#             temp_booking = request.session.get('temp_booking')
            
#             if not temp_booking:
#                 messages.error(request, "Session expired! Please book again.")
#                 return redirect('travels')
            
#             user = User.objects.get(id=temp_booking['user_id'])
#             booking = None
            
#             if temp_booking['type'] == 'package':
#                 package = Package.objects.get(id=temp_booking['package_id'])
                
#                 booking = Booking.objects.create(
#                     user=user,
#                     package=package,
#                     name=temp_booking['name'],
#                     email=temp_booking['email'],
#                     address=temp_booking['address'],
#                     check_in=temp_booking['check_in'],
#                     check_out=temp_booking['check_out'],
#                     guests=temp_booking['guests'],
#                     total_price=temp_booking['total_price'],
#                     payment_method='online',
#                     payment_status='confirmed',
#                     razorpay_order_id=order_id,
#                     razorpay_payment_id=payment_id,
#                     razorpay_signature=signature
#                 )
                
#             elif temp_booking['type'] == 'hotel':
#                 hotel = Hotel.objects.get(id=temp_booking['hotel_id'])
                
#                 # Reduce room availability
#                 hotel.room_availability -= 1
#                 hotel.save()
                
#                 booking = Booking.objects.create(
#                     user=user,
#                     hotel=hotel,
#                     name=temp_booking['name'],
#                     email=temp_booking['email'],
#                     address=temp_booking['address'],
#                     check_in=temp_booking['check_in'],
#                     check_out=temp_booking['check_out'],
#                     guests=temp_booking['guests'],
#                     total_price=temp_booking['total_price'],
#                     payment_method='online',
#                     payment_status='confirmed',
#                     razorpay_order_id=order_id,
#                     razorpay_payment_id=payment_id,
#                     razorpay_signature=signature
#                 )
            
#             # Clear session
#             if 'temp_booking' in request.session:
#                 del request.session['temp_booking']
#             if 'razorpay_order_id' in request.session:
#                 del request.session['razorpay_order_id']
            
#             messages.success(request, f'✅ Payment successful! Booking confirmed. ID: #{booking.id}')
#             return redirect('success_page', booking_id=booking.id)
            
#         except razorpay.errors.SignatureVerificationError:
#             messages.error(request, '❌ Payment verification failed!')
#             if 'temp_booking' in request.session:
#                 del request.session['temp_booking']
#             return redirect('travels')
#         except Exception as e:
#             messages.error(request, f'Error: {str(e)}')
#             return redirect('travels')
    
#     return redirect('travels')


def payment_cancel(request):
    """Handle payment cancellation"""
    if 'temp_booking' in request.session:
        del request.session['temp_booking']
    if 'razorpay_order_id' in request.session:
        del request.session['razorpay_order_id']
    
    messages.warning(request, 'Payment cancelled. No booking created.')
    return redirect('travels')




# PACKAGE BOOKING


def package_booking(request, id):

    if not request.session.get("user_id"):

        return redirect(
            f"/login/?next=/package-book/{id}/"
        )

    package = get_object_or_404(
        Package,
        id=id
    )

    user = get_object_or_404(
        User,
        id=request.session.get("user_id")
    )

    if request.method == "POST":

        try:

            payment_method = request.POST.get(
                "payment_method"
            )

            name = request.POST.get("name")
            email = request.POST.get("email")
            address = request.POST.get("address")

            check_in = request.POST.get("check_in")
            check_out = request.POST.get("check_out")

            guests = int(
                request.POST.get("guests") or 1
            )

            
            # DATE VALIDATION
            

            check_in_date = datetime.strptime(
                check_in,
                "%Y-%m-%d"
            ).date()

            check_out_date = datetime.strptime(
                check_out,
                "%Y-%m-%d"
            ).date()

            today = timezone.now().date()

            if check_in_date < today:

                messages.error(
                    request,
                    "Check-in cannot be in past!"
                )

                return redirect(
                    "package_booking",
                    id=id
                )

            if check_out_date <= check_in_date:

                messages.error(
                    request,
                    "Check-out must be after check-in!"
                )

                return redirect(
                    "package_booking",
                    id=id
                )

            
            # PRICE CALCULATION
           

            total_price = (
                float(package.package_price)
                * guests
            )

            
            # CASH PAYMENT
            

            if payment_method == "cash":

                booking = Booking.objects.create(

                    user=user,

                    package=package,

                    name=name,

                    email=email,

                    address=address,

                    check_in=check_in_date,

                    check_out=check_out_date,

                    guests=guests,

                    total_price=total_price,

                    payment_method="cash",

                    payment_status="confirmed"
                )

                messages.success(
                    request,
                    "Package booked successfully!"
                )

                return redirect(
                    "success_page",
                    booking_id=booking.id
                )

            
            # ONLINE PAYMENT
            

            booking_data = {

                "type": "package",

                "package_id": package.id,

                "user_id": user.id,

                "name": name,

                "email": email,

                "address": address,

                "check_in": str(check_in_date),

                "check_out": str(check_out_date),

                "guests": guests,

                "total_price": total_price
            }

            request.session[
                "temp_booking"
            ] = booking_data

            return redirect("payment_page")

        except Exception as e:

            print("PACKAGE ERROR:", e)

            messages.error(
                request,
                str(e)
            )

            return redirect(
                "package_book",
                id=id
            )

    return render(
        request,
        "package.html",
        {

            "package": package,

            "user_name": request.session.get(
                "user_name"
            ),

            "initial_name": user.user_name,

            "initial_email": user.user_email
        }
    )


# =========================================
# PAYMENT PAGE
# =========================================

def payment_page(request):

    temp_booking = request.session.get(
        "temp_booking"
    )

    if not temp_booking:

        messages.error(
            request,
            "No booking data found!"
        )

        return redirect("travels")

    amount_rupees = float(
        temp_booking["total_price"]
    )

    # RAZORPAY USES PAISA

    amount_paisa = int(
        amount_rupees * 100
    )

    # MINIMUM ₹1

    if amount_paisa < 100:

        amount_paisa = 100

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    payment = client.order.create({

        "amount": amount_paisa,

        "currency": "INR",

        "payment_capture": 1
    })

    request.session[
        "razorpay_order_id"
    ] = payment["id"]

    return render(
        request,
        "payment.html",
        {
            'user_name': request.session.get('user_name'),

            "payment": payment,

            "amount": amount_rupees,

            "razorpay_key": settings.RAZORPAY_KEY_ID
        }
    )


# =========================================
# PAYMENT VERIFICATION
# =========================================

@csrf_exempt
def payment_verification(request):

    if request.method == "POST":

        try:

            payment_id = request.POST.get(
                "razorpay_payment_id"
            )

            order_id = request.POST.get(
                "razorpay_order_id"
            )

            signature = request.POST.get(
                "razorpay_signature"
            )

            client = razorpay.Client(
                auth=(
                    settings.RAZORPAY_KEY_ID,
                    settings.RAZORPAY_KEY_SECRET
                )
            )

            params_dict = {

                "razorpay_order_id": order_id,

                "razorpay_payment_id": payment_id,

                "razorpay_signature": signature
            }

            client.utility.verify_payment_signature(
                params_dict
            )

            temp_booking = request.session.get(
                "temp_booking"
            )

            if not temp_booking:

                messages.error(
                    request,
                    "Session expired!"
                )

                return redirect("travels")

            user = User.objects.get(
                id=temp_booking["user_id"]
            )

            package = Package.objects.get(
                id=temp_booking["package_id"]
            )

            booking = Booking.objects.create(

                user=user,

                package=package,

                name=temp_booking["name"],

                email=temp_booking["email"],

                address=temp_booking["address"],

                check_in=temp_booking["check_in"],

                check_out=temp_booking["check_out"],

                guests=temp_booking["guests"],

                total_price=temp_booking["total_price"],

                payment_method="online",

                payment_status="confirmed",

                razorpay_order_id=order_id,

                razorpay_payment_id=payment_id,

                razorpay_signature=signature
            )

            # CLEAR SESSION

            if "temp_booking" in request.session:

                del request.session[
                    "temp_booking"
                ]

            messages.success(
                request,
                "Payment successful!"
            )

            return redirect(
                "success_page",
                booking_id=booking.id
            )

        except Exception as e:

            messages.error(
                request,
                str(e)
            )

            return redirect("travels")

    return redirect("travels")


# =========================================
# CANCEL BOOKING
# =========================================

def cancel_booking(request, id):

    booking = get_object_or_404(
        Booking,
        id=id
    )

    # SECURITY CHECK

    if booking.user.id != request.session.get(
        "user_id"
    ):

        messages.error(
            request,
            "Permission denied!"
        )

        return redirect("my_bookings")

    # ALREADY CANCELLED

    if booking.payment_status == "cancelled":

        messages.warning(
            request,
            "Booking already cancelled!"
        )

        return redirect("my_bookings")

    # CANCEL BOOKING

    booking.payment_status = "cancelled"

    booking.save()

    # RETURN HOTEL ROOM

    if booking.hotel:

        booking.hotel.room_availability += 1

        booking.hotel.save()

    messages.success(
        request,
        "Booking cancelled successfully!"
    )

    return redirect("my_bookings")

