from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
import requests

PAY_SERVICE_URL = "http://pay-service:4000/"
SHIP_SERVICE_URL = "http://ship-service:4000/"
CART_SERVICE_URL = "http://cart-service:4000"
BOOK_SERVICE_URL = "http://book-service:4000"

class OrderCreate(APIView):
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save(status='PROCESSING')
            customer_id = order.customer_id

            # Fetch cart items to know what was ordered
            cart_items = []
            try:
                cart_resp = requests.get(f"{CART_SERVICE_URL}/{customer_id}/")
                if cart_resp.status_code == 200:
                    cart_data = cart_resp.json()
                    cart_items = cart_data.get("items", [])
            except Exception:
                pass

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

                    # Decrease stock for each book in the cart
                    self.decrease_stock(cart_items)

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

    def decrease_stock(self, cart_items):
        """Decrease book stock for each item in the cart."""
        try:
            # Fetch all books
            books_resp = requests.get(f"{BOOK_SERVICE_URL}/")
            if books_resp.status_code != 200:
                return
            books = {b["id"]: b for b in books_resp.json()}

            for item in cart_items:
                book_id = item.get("book_id")
                qty = item.get("quantity", 0)
                if book_id in books:
                    current_stock = books[book_id].get("stock", 0)
                    new_stock = max(0, current_stock - qty)
                    requests.put(
                        f"{BOOK_SERVICE_URL}/{book_id}/",
                        json={"stock": new_stock}
                    )
        except Exception:
            pass  # Stock update failure shouldn't block the order

class OrderList(APIView):
    def get(self, request):
        customer_id = request.query_params.get("customer_id")
        if customer_id:
            orders = Order.objects.filter(customer_id=customer_id)
        else:
            orders = Order.objects.all()
        return Response(OrderSerializer(orders, many=True).data)
