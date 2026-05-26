from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Destination)
admin.site.register(User)
admin.site.register(Hotel)
admin.site.register(Package)
admin.site.register(Booking)
admin.site.register(PackageImage)
admin.site.register(HotelImage)