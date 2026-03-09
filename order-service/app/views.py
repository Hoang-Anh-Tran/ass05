from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
import requests

PAY_SERVICE_URL = "http://pay-service:4000/"
SHIP_SERVICE_URL = "http://ship-service:4000/"

class OrderCreate(APIView):
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save(status='PROCESSING')
            
            # Trigger payment with selected method
            pay_resp = requests.post(PAY_SERVICE_URL, json={
                "order_id": order.id,
                "amount": float(order.total_amount),
                "method": order.pay_method
            })
            
            if pay_resp.status_code in [200, 201]:
                order.status = 'PAID'
                order.save()
                
                # Trigger shipping with selected method
                ship_resp = requests.post(SHIP_SERVICE_URL, json={
                    "order_id": order.id,
                    "customer_id": order.customer_id,
                    "method": order.ship_method
                })
                
                if ship_resp.status_code in [200, 201]:
                    order.status = 'SHIPPED'
                    order.save()
                    return Response(OrderSerializer(order).data)
                else:
                    order.status = 'SHIPPING_FAILED'
                    order.save()
                    return Response({"error": "Shipping failed", "order": OrderSerializer(order).data}, status=500)
            else:
                order.status = 'PAYMENT_FAILED'
                order.save()
                return Response({"error": "Payment failed", "order": OrderSerializer(order).data}, status=400)
                
        return Response(serializer.errors, status=400)

class OrderList(APIView):
    def get(self, request):
        customer_id = request.query_params.get("customer_id")
        if customer_id:
            orders = Order.objects.filter(customer_id=customer_id)
        else:
            orders = Order.objects.all()
        return Response(OrderSerializer(orders, many=True).data)
