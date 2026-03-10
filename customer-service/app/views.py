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

            # Call cart-service root (cart-service now maps "" to CartCreate)
            try:
                requests.post(
                    f"{CART_SERVICE_URL}/",
                    json={"customer_id": customer.id},
                    timeout=5
                )
            except Exception:
                pass  # Cart creation failure shouldn't block customer creation

            return Response(serializer.data)

        return Response(serializer.errors)


class CustomerLogin(APIView):
    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")

        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            return Response({"error": "Email not found"}, status=404)

        if customer.password != password:
            return Response({"error": "Wrong password"}, status=401)

        return Response(CustomerSerializer(customer).data)