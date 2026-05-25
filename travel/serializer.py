from rest_framework import serializers
from travel.models import *

class ProductSerializers(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'