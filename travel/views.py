from django.shortcuts import render, redirect,get_object_or_404
from .models import *
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from decimal import Decimal


def landing(request):
    result = Package.objects.filter(populer_tour=True)[:3]
    h = Hotel.objects.filter(populer_hotel=True)[:3]

    return render(request, "travels.html", {
        "packages": result,
        "hotels": h,
        "query": None,
        'user_name': request.session.get('user_name')
    })




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

        Booking.objects.create(
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

        return redirect('/my-bookings')

    return render(request, 'hotel.html', {'hotel': hotel,'user_name': request.session.get('user_name')})


# package booking system
def package_booking(request, id):

    if not request.session.get('user_id'):
        return redirect(f'/login/?next=/package-book/{id}/')

    package = Package.objects.get(id=id)
    user_id = request.session.get('user_id')

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests') or 1)

        total_price = guests * package.package_price

        Booking.objects.create(
            user_id=user_id,              
            package=package,
            hotel=package.hotel_name,     
            name=name,
            email=email,
            address=address,
            check_in=check_in if check_in else None,
            check_out=check_out if check_out else None,
            guests=guests,
            total_price=total_price
        )

        return redirect('/my-bookings')

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



def remove_package_cart(request, id):

    cart = request.session.get('cart', [])

    if id in cart:
        cart.remove(id)

    request.session['cart'] = cart

    return redirect('cart_details')


def remove_hotel_cart(request, id):

    hotel_cart = request.session.get('hotel_cart', [])

    if id in hotel_cart:
        hotel_cart.remove(id)

    request.session['hotel_cart'] = hotel_cart

    return redirect('cart_details')

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