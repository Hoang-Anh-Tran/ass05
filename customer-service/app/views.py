from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomerSerializer
import requests

CART_SERVICE_URL = "http://cart-service:4000"

class CustomerListCreate(APIView):

    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)

        if serializer.is_valid():
            customer = serializer.save()

            # Call cart-service
            requests.post(
                f"{CART_SERVICE_URL}/carts/",
                json={"customer_id": customer.id}
            )

            return Response(serializer.data)

        return Response(serializer.errors)