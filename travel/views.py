from django.shortcuts import render, redirect,get_object_or_404
from .models import *
from datetime import datetime
import os
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.http import HttpResponse
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
from .serializer import ProductSerializers 
import razorpay
from django.conf import settings


def landing(request):
    result = Package.objects.filter(populer_tour=True)[:3]
    h = Hotel.objects.filter(populer_hotel=True)[:3]

    return render(request, "travels.html", {
        "packages": result,
        "hotels": h,
        "query": None,
        'user_name': request.session.get('user_name')
    })


def succes(request):
    user_id = request.session.get('user_id')
    return render(request,'bookingsuccsfull.html',{'user_name': request.session.get('user_name')})

# for user registration

def user_registration(request):
    if request.method == 'POST':
        user_name = request.POST.get('user_name')   
        user_email = request.POST.get('user_email')
        user_password = make_password(request.POST.get('user_password'))

        User.objects.create(
            user_name=user_name,
            user_email=user_email,
            user_password=user_password
        )

        return redirect('login')   # go to login page after signup

    return render(request, 'signup.html')



# for user login

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('user_name')
        password = request.POST.get('user_password')

        user = User.objects.filter(user_name=username).first()

        if user and check_password(password, user.user_password):
            
            request.session['user_id'] = user.id
            request.session['user_name'] = user.user_name

            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)

            return redirect('travels')
        else:
            return render(request, 'login.html', {'error': 'invalid credentials'})

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


# Logout function
def logout_user(request):
    request.session.flush()
    return redirect('/')


# searching method
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





# hotel booking system

def book_hotel(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect(f'/login/?next=/hotel-book/{id}/')

    hotel = get_object_or_404(Hotel, id=id)

    if request.method == "POST":
        h_name = request.POST.get('h_name')
        h_email = request.POST.get('h_email')
        address = request.POST.get('Address')

        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests') or 1)

        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")

        days = (check_out_date - check_in_date).days

        total_price = (days * hotel.price_per_night)*guests

        booking =Booking.objects.create(
            user_id=user_id,
            name=h_name,
            email=h_email,
            address=address,
            hotel=hotel,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            total_price=total_price,
            package=None,
        )

        hotel.room_availability -= 1
        hotel.save()

        return redirect('payment', id=booking.id)

    return render(request, 'hotel.html', {'hotel': hotel,'user_name': request.session.get('user_name')})


# package booking system
def package_booking(request, id):

    if not request.session.get('user_id'):
        return redirect(f'/login/?next=/package-book/{id}/')
    package = Package.objects.get(id=id)
    user_id = request.session.get('user_id')

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        if not payment_method:
            messages.error(request, "Please select payment method")
            return redirect(request.path)
        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests') or 1)

        total_price = guests * package.package_price

        booking=Booking.objects.create(
            user_id=user_id,              
            package=package,
            hotel=package.hotel_name,     
            name=name,
            email=email,
            address=address,
            check_in=check_in if check_in else None,
            check_out=check_out if check_out else None,
            guests=guests,
              payment_method=payment_method,
            total_price=total_price
        )

         # CASH PAYMENT
        if payment_method == "cash":

            return redirect('s')

        # ONLINE PAYMENT
        elif payment_method == "online":

            return redirect('payment', booking.id)


    return render(request, 'package.html', {'package': package, 'user_name': request.session.get('user_name')})




# booking history
def booking_history(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    

    bookings = Booking.objects.filter(user_id=user_id).order_by('-booking_at')

    # Calculate counts
    packages_count = bookings.filter(package__isnull=False).count()
    hotels_count = bookings.filter(hotel__isnull=False).count()
    total_guests = sum(booking.guests for booking in bookings)
    total_spent = sum(booking.total_price for booking in bookings)
    
    context = {
        'bookings': bookings,
        'packages_count': packages_count,
        'hotels_count': hotels_count,
        'total_guests': total_guests,
        'total_spent': total_spent,
        'user_name' : request.session.get('user_name')
    }

    return render(request, 'booking_history.html', context)


# cancelling system
def cancel_booking(request,id):
    booking = get_object_or_404(Booking, id=id)

    if booking.hotel:
        booking.hotel.room_availability += 1
        booking.hotel.save()

    booking.delete()
    return redirect('/my-bookings/')


# showing details of package to user
def package_details(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect(f'/login/?next=/package/{id}/')

    package = get_object_or_404(Package, id=id)
    # desciption = get_object_or_404(Destination, id=id)

    return render(request, 'viewdetails.html', {
        'package': package,
         'd':package.destination.description,
        'user_name': request.session.get('user_name')
    })


# showing details of hotel to user
def hotel_details(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect(f'/login/?next=/hotel/{id}/')

    hotel = get_object_or_404(Hotel, id=id)

    return render(request, 'viewdetails.html', {
        'hotel': hotel,
        'user_name': request.session.get('user_name')
    })


# showing packages clicking package
def show_package(request):
    package = Package.objects.all()
    return render(request, 'Show_Package.html', {
        'packages' : package, 
        'user_name': request.session.get('user_name')
    })



# showing hotel clicking hotel
def show_hotel(request):
    hotels = Hotel.objects.all()
    return render(request, 'Show_Hotel.html', {
        'hotels' : hotels, 
        'user_name': request.session.get('user_name')
    })


# add to cart features upload for package
def add_to_cart(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    package = get_object_or_404(Package, id=id)
   

    cart = request.session.get('cart', [])

    if id not in cart:
        cart.append(id)

    request.session['cart'] = cart

    return redirect(request.META.get('HTTP_REFERER', '/travels/'))
from .models import Hotel


# add to cart for hotels
def add_hotel_cart(request, id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    hotel = get_object_or_404(Hotel, id=id)

    hotel_cart = request.session.get('hotel_cart', [])

    if id not in hotel_cart:
        hotel_cart.append(id)

    request.session['hotel_cart'] = hotel_cart
    return redirect(request.META.get('HTTP_REFERER', '/travels/'))


# remove from cart for package
def remove_package_cart(request, id):

    cart = request.session.get('cart', [])

    if id in cart:
        cart.remove(id)

    request.session['cart'] = cart

    return redirect('cart_details')

# for hotel
def remove_hotel_cart(request, id):

    hotel_cart = request.session.get('hotel_cart', [])

    if id in hotel_cart:
        hotel_cart.remove(id)

    request.session['hotel_cart'] = hotel_cart

    return redirect('cart_details')


# details of cart
def cart_details(request):
    
    cart = request.session.get('cart', [])
    hotel_cart = request.session.get('hotel_cart', [])

    packages = Package.objects.filter(id__in=cart)
    hotels = Hotel.objects.filter(id__in=hotel_cart)

    total = 0

    for p in packages:
        total +=Decimal(p.package_price)

    for h in hotels:
        total +=Decimal(h.price_per_night)

    context = {
        'packages': packages,
        'hotels': hotels,
        'total': total,
        'user_name': request.session.get('user_name')
    }

    return render(request, 'addcart.html', context)

# for footer option
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
    return render(request,'contract.html',{'user_name': request.session.get('user_name')})

def my_Profile(request):
     # Get the logged-in user (you need to store user_id in session)
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')
    
    # Get user's bookings
    bookings = Booking.objects.filter(user=user).order_by('-booking_at')
    
    # Calculate booking statistics
    today = timezone.now().date()
    completed_bookings = 0
    active_bookings = 0
    upcoming_bookings = 0
    
    for booking in bookings:
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
        'recent_bookings': bookings[:5],  # Last 5 bookings
        'total_bookings': bookings.count(),
        'completed_bookings': completed_bookings,
        'active_bookings': active_bookings,
        'upcoming_bookings': upcoming_bookings,
        'member_since': user.member_since.year if user.member_since else 2024,
        'today': today,
    }
    
    return render(request, 'my_profile.html', context)




def update_profile(request):

    # update user profile info

    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        try:
            user = User.objects.get(id = user_id)

            # update user fields
            user.user_name = request.POST.get('user_name')
            user.user_email = request.POST.get('user_email')
            user.user_phone = request.POST.get('user_phone')
            user.user_dob = request.POST.get('user_dob') or None
            user.user_address = request.POST.get('user_address')
            user.user_city = request.POST.get('user_city')
            user.user_country = request.POST.get('user_country')

            user.save()
            messages.success(request, 'Profile updated sucessfully!')

        except User.DoesNotExist:
            messages.success(request, 'User does not found!')

    return redirect('profile')



    

def change_password(request):

    # update user profile info

    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        try:
            user = User.objects.get(id = user_id)

            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')


            # check current password
            if not check_password(current_password, user.user_password):
                messages.error(request, 'Current password is incorrect!')

            elif new_password != confirm_password:
                messages.error(request, 'New password do not match!')

            
            else:
                user.user_password = make_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully!')

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
            user.user_avatar = image
            user.save()

            messages.success(request, "Profile picture updated successfully!")

        else:
            messages.error(request, "Please select an image!")

    return redirect('profile')


def update_preferences(request):
    """Update user preferences"""
    
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
    """Update notification settings"""
    
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

    booking = Booking.objects.get(id=booking_id)

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

    # COMPANY TITLE
    elements.append(
        Paragraph("TripTravels", title_style)
    )

    elements.append(
        Paragraph(
            "Premium Travel Booking Invoice",
            styles['Heading3']
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(HRFlowable(width="100%"))

    elements.append(Spacer(1, 20))

    # BOOKING TYPE
    booking_type = "Tour Package"

    if booking.hotel:
        booking_type = "Hotel Booking"

    # BOOKING NAME
    booking_name = ""

    if booking.package:
        booking_name = booking.package.package_name

    if booking.hotel:
        booking_name = booking.hotel.hotel_name

    # TABLE DATA
    data = [
        ['Booking ID', f'#{booking.id}'],
        ['Booking Type', booking_type],
        ['Booking Name', booking_name],
        ['Customer Name', booking.name],
        ['Email', booking.email],
        ['Guests', str(booking.guests)],
        ['Check In', str(booking.check_in)],
        ['Check Out', str(booking.check_out)],
        # ['Payment Method', str(booking.payment_method).upper()],
        ['Total Amount', f'₹ {booking.total_price}'],
    ]

    table = Table(data, colWidths=[180, 280])

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5d7f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#649fc3")),

        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),

        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),

        ('FONTSIZE', (0, 0), (-1, -1), 11),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),

        ('TOPPADDING', (0, 0), (-1, -1), 10),

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))

    # PAYMENT STATUS
    elements.append(
        Paragraph(
            "<b>Payment Status:</b> Confirmed",
            normal_style
        )
    )

    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            "Thank you for booking with TripTravels. We wish you a wonderful journey.",
            normal_style
        )
    )

    elements.append(Spacer(1, 25))

    elements.append(HRFlowable(width="100%"))

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Generated Automatically by TripTravels",
            styles['Italic']
        )
    )

    doc.build(elements)

    return response

def payment_page(request, id):

    booking = get_object_or_404(Booking, id=id)

    amount_rupees = booking.total_price
    amount_paisa = int(amount_rupees * 100)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment = client.order.create({
        "amount": amount_paisa,
        "currency": "INR",
        "payment_capture": 1
    })

    context = {
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount_rupees,
        "booking": booking,
        "name": booking.name,
        "pac":booking.package
    }

    return render(request, "payment.html", context)
