from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime

def landing(request):
    if request.session.get('user_id'):
        return redirect('travels')   
    return render(request,"travels.html")



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

    return render(request, 'travels.html', {
        'user_name': user_name
    })



def logout_user(request):
    request.session.flush()
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





# hotel booking function


def book_hotel(request, id):
    if not request.session.get('user_id'):
        return redirect(f'/login/?next=/hotel-book/{id}/')

    hotel = Hotel.objects.get(id=id)

    if request.method == "POST":
        h_name= request.POST.get('h_name')
        h_email= request.POST.get('h_email')
        Address= request.POST.get('Address')

        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests') or 1)

        # Convert to date
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")

        days = (check_out_date - check_in_date).days

        
        total_price = days * hotel.price_per_night

        
        if hotel.room_availability <= 0:
            return HttpResponse("No rooms available")

       
        Booking.objects.create(
            user_id=request.session.get('user_id'),
            name=h_name,
            email=h_email,
            address=Address,
            hotel=hotel,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            total_price=total_price,
             package=None,
        )

        
        hotel.room_availability -= 1
        hotel.save()

        return redirect('travels')

    return render(request, 'hotel.html', {'hotel': hotel})





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

        return redirect('travels')

    return render(request, 'package.html', {'package': package})




# booking history
def booking_history(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')
    

    bookings = Booking.objects.filter(user_id=user_id).order_by('-booking_at')

    return render(request, 'booking_history.html', {
        'bookings': bookings,
        'user_name': request.session.get('user_name')
    })