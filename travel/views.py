from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime

def landing(request):
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
    user_name = request.session.get('user_name')  # can be None

    return render(request, 'travels.html', {
        'user_name': user_name
    })



def logout_user(request):
    request.session.flush()
    return redirect('login')



def search_method(request):
    user_name = request.session.get('user_name')  # optional
    query = request.GET.get('search')
    results = []

    if query:
        results = Package.objects.filter(
            destination__name__icontains=query
        )

    return render(request, 'travels.html', {
        'results': results,
        'query': query,
        'user_name': user_name
    })






# hotel booking function


def book_hotel(request, id):
    if not request.session.get('user_id'):
        return redirect(f'/login/?next=/hotel-book/{id}/')

    hotel = Hotel.objects.get(id=id)

    if request.method == "POST":
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests'))

        # Convert to date
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")

        days = (check_out_date - check_in_date).days

        
        total_price = days * hotel.price_per_night

        
        if hotel.room_availability <= 0:
            return HttpResponse("No rooms available")

       
        Booking.objects.create(
            user_id=request.session.get('user_id'),
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







from django.shortcuts import get_object_or_404
from django.urls import reverse

def book_package(request, id):
    if not request.session.get('user_id'):
        return redirect(f"{reverse('login')}?next={reverse('package_book', args=[id])}")

    package = get_object_or_404(Package, id=id)

    if request.method == "POST":
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = int(request.POST.get('guests'))


        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        
        total_price = package.package_price * guests

       
        hotel = package.hotel_name

        Booking.objects.create(
            user_id=request.session.get('user_id'),
            check_in=check_in,
            check_out=check_out,
            package=package,
            hotel=hotel,
            guests=guests,
            total_price=total_price,
        )

        return redirect('travels')

    return render(request, 'package.html', {'package': package})