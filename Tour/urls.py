"""
URL configuration for Tour project.
"""
from django.contrib import admin
from django.urls import path
from travel import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing),
    path('register/', views.user_registration, name='register'),
    path('login/', views.user_login, name='login'),
    path('travels/', views.travels_page, name='travels'),
    path('search/', views.search_method, name='search'),
    path('logout/', views.logout_user, name='logout'),
    path('success/<int:booking_id>/', views.succes, name='success_page'),

    path('package-book/<int:id>/', views.package_booking, name='package_book'),
    path('hotel-book/<int:id>/', views.hotel_booking, name='hotel_book'),
    path('my-bookings/', views.booking_history, name='my_bookings'),
    path('my-bookings/delete/<int:id>/', views.cancel_booking, name='delete'),
    path(
    'my-bookings/remove/<int:id>/',views.delete_booking,name='delete_booking'),
    path('package/<int:id>/', views.package_details, name='package_details'),
    path('hotel/<int:id>/', views.hotel_details, name='hotel_details'),

    path('show_package/', views.show_package, name="package"),
    path('show_hotel/', views.show_hotel, name="hotel"),

    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('add-hotel-cart/<int:id>/', views.add_hotel_cart, name='add_hotel_cart'),
    path('remove-package/<int:id>/', views.remove_package_cart, name='remove_package_cart'),
    path('remove-hotel/<int:id>/', views.remove_hotel_cart, name='remove_hotel_cart'),
    path('cart/', views.cart_details, name='cart_details'),
    path('foot/', views.foot, name='foot'),
    path('con/', views.contact, name='contact'),

    path('show_profile/', views.my_Profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/change-avatar/', views.change_avatar, name='change_avatar'),
    path('profile/update-preferences/', views.update_preferences, name='update_preferences'),
    path('profile/update-notifications/', views.update_notifications, name='update_notifications'),
    path('download-booking-bill/<int:booking_id>/', views.download_booking_bill, name='download_booking_bill'),

    # Payment URLs
    path('payment/', views.payment_page, name='payment_page'),
    path('payment-verification/', views.payment_verification, name='payment_verification'),
    path('payment-cancelled/', views.payment_cancel, name='payment_cancelled'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)