from rest_framework import serializers
from .models import Order, SagaLog


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class SagaLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SagaLog
        fields = '__all__'
