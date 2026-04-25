from django.shortcuts import render, redirect
from .models import *
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime


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

            return render(request, 'travels.html')
        else:
            return render(request, 'login.html', {'error': 'invalid credentials'})

    return render(request, 'login.html')





def travels_page(request):
    if not request.session.get('user_id'):
        return redirect('login/')   
    user_name = request.session.get('user_name')

    return render(request, 'travels.html',{'user_name':user_name})



def logout_user(request):
    request.session.flush()
    return redirect('/')



def search_method(request):
    user_name = request.session.get('user_name')
    if not request.session.get('user_id'):
        return redirect('login/')
        
    query = request.GET.get('search')
    results = []

    if query:
        results = Package.objects.filter(
            destination__name__icontains=query
        )

    return render(request, 'travels.html', {
    'results': results,
    'query': query,
    'user_name':user_name})






# hotel booking function


def book_hotel(request, id):
    if not request.session.get('user_id'):
        return redirect('login')

    hotel = Hotel.objects.get(id=id)

    if request.method == "POST":
        h_name= request.POST.get('h_name')
        h_email= request.POST.get('h_email')
        Address= request.POST.get('Address')

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

        # 💾 Save booking
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