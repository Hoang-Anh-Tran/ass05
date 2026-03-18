import sys
import os
import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, SagaLog
from .serializers import OrderSerializer, SagaLogSerializer
import requests

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
try:
    from event_bus import publish_event
except ImportError:
    def publish_event(event_type, data):
        logger.warning(f"Event bus not available, skipping event: {event_type}")
        return False

logger = logging.getLogger(__name__)

PAY_SERVICE_URL = "http://pay-service:4000"
SHIP_SERVICE_URL = "http://ship-service:4000"
CART_SERVICE_URL = "http://cart-service:4000"
BOOK_SERVICE_URL = "http://book-service:4000"


class OrderCreate(APIView):
    """
    Saga Orchestrator for Order Creation.
    
    Steps:
    1. Create Order (PENDING)
    2. Reserve Payment
    3. Reserve Shipping
    4. Confirm Order
    On failure: Compensate (cancel previous steps)
    """

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Step 1: Create order in PENDING state
        order = serializer.save(status='PENDING')
        self._log_step(order, 'ORDER_CREATED', 'SUCCESS', 'Order created with PENDING status')
        
        logger.info(f"Saga started for Order #{order.id}")
        publish_event('order.created', {
            'order_id': order.id,
            'customer_id': order.customer_id,
            'total_amount': str(order.total_amount),
            'pay_method': order.pay_method,
            'ship_method': order.ship_method,
        })

        # Step 2: Reserve Payment
        payment_reserved = self._reserve_payment(order)
        if not payment_reserved:
            self._compensate(order, payment_reserved=False, shipping_reserved=False)
            return Response({
                "error": "Payment reservation failed",
                "order": OrderSerializer(order).data,
                "saga_log": SagaLogSerializer(order.saga_logs.all(), many=True).data,
            }, status=400)

        # Step 3: Reserve Shipping
        shipping_reserved = self._reserve_shipping(order)
        if not shipping_reserved:
            self._compensate(order, payment_reserved=True, shipping_reserved=False)
            return Response({
                "error": "Shipping reservation failed, payment compensated",
                "order": OrderSerializer(order).data,
                "saga_log": SagaLogSerializer(order.saga_logs.all(), many=True).data,
            }, status=400)

        # Step 4: Confirm order
        order.status = 'CONFIRMED'
        order.save()
        self._log_step(order, 'ORDER_CONFIRMED', 'SUCCESS', 'Order confirmed successfully')
        self._log_step(order, 'SAGA_COMPLETED', 'SUCCESS', 'Saga completed successfully')

        # Decrease stock for cart items
        self._decrease_stock(order.customer_id)

        logger.info(f"Saga completed for Order #{order.id}")
        publish_event('order.confirmed', {
            'order_id': order.id,
            'customer_id': order.customer_id,
            'status': 'CONFIRMED',
        })

        return Response({
            "order": OrderSerializer(order).data,
            "saga_log": SagaLogSerializer(order.saga_logs.all(), many=True).data,
        }, status=201)

    def _reserve_payment(self, order):
        """Step 2: Reserve payment via pay-service."""
        try:
            resp = requests.post(f"{PAY_SERVICE_URL}/reserve/", json={
                "order_id": order.id,
                "amount": str(order.total_amount),
                "method": order.pay_method,
            }, timeout=10)
            
            if resp.status_code in [200, 201]:
                order.status = 'PAYMENT_RESERVED'
                order.save()
                self._log_step(order, 'PAYMENT_RESERVE', 'SUCCESS', 'Payment reserved')
                publish_event('payment.reserved', {
                    'order_id': order.id,
                    'amount': str(order.total_amount),
                })
                return True
            else:
                self._log_step(order, 'PAYMENT_RESERVE_FAILED', 'FAILED',
                               f"Payment service returned {resp.status_code}: {resp.text}")
                publish_event('payment.failed', {'order_id': order.id})
                return False
        except Exception as e:
            self._log_step(order, 'PAYMENT_RESERVE_FAILED', 'FAILED', f"Exception: {str(e)}")
            publish_event('payment.failed', {'order_id': order.id, 'error': str(e)})
            return False

    def _reserve_shipping(self, order):
        """Step 3: Reserve shipping via ship-service."""
        try:
            resp = requests.post(f"{SHIP_SERVICE_URL}/reserve/", json={
                "order_id": order.id,
                "customer_id": order.customer_id,
                "method": order.ship_method,
            }, timeout=10)
            
            if resp.status_code in [200, 201]:
                order.status = 'SHIPPING_RESERVED'
                order.save()
                self._log_step(order, 'SHIPPING_RESERVE', 'SUCCESS', 'Shipping reserved')
                publish_event('shipping.reserved', {
                    'order_id': order.id,
                    'customer_id': order.customer_id,
                })
                return True
            else:
                self._log_step(order, 'SHIPPING_RESERVE_FAILED', 'FAILED',
                               f"Ship service returned {resp.status_code}: {resp.text}")
                publish_event('shipping.failed', {'order_id': order.id})
                return False
        except Exception as e:
            self._log_step(order, 'SHIPPING_RESERVE_FAILED', 'FAILED', f"Exception: {str(e)}")
            publish_event('shipping.failed', {'order_id': order.id, 'error': str(e)})
            return False

    def _compensate(self, order, payment_reserved, shipping_reserved):
        """Execute compensating transactions to rollback saga."""
        logger.warning(f"Compensating saga for Order #{order.id}")
        order.status = 'COMPENSATING'
        order.save()

        # Cancel shipping if it was reserved
        if shipping_reserved:
            try:
                requests.post(f"{SHIP_SERVICE_URL}/cancel/", json={
                    "order_id": order.id,
                }, timeout=10)
                self._log_step(order, 'COMPENSATION_SHIPPING_CANCEL', 'SUCCESS',
                               'Shipping reservation cancelled')
            except Exception as e:
                self._log_step(order, 'COMPENSATION_SHIPPING_CANCEL', 'FAILED', str(e))

        # Cancel payment if it was reserved
        if payment_reserved:
            try:
                requests.post(f"{PAY_SERVICE_URL}/cancel/", json={
                    "order_id": order.id,
                }, timeout=10)
                self._log_step(order, 'COMPENSATION_PAYMENT_CANCEL', 'SUCCESS',
                               'Payment reservation cancelled')
            except Exception as e:
                self._log_step(order, 'COMPENSATION_PAYMENT_CANCEL', 'FAILED', str(e))

        order.status = 'FAILED'
        order.save()
        self._log_step(order, 'SAGA_FAILED', 'FAILED', 'Saga failed with compensation')
        
        publish_event('order.failed', {
            'order_id': order.id,
            'customer_id': order.customer_id,
        })

    def _decrease_stock(self, customer_id):
        """Decrease book stock for cart items after successful order."""
        try:
            cart_resp = requests.get(f"{CART_SERVICE_URL}/{customer_id}/", timeout=5)
            if cart_resp.status_code != 200:
                return
            cart_items = cart_resp.json().get("items", [])

            books_resp = requests.get(f"{BOOK_SERVICE_URL}/", timeout=5)
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
                        json={"stock": new_stock},
                        timeout=5,
                    )
        except Exception as e:
            logger.warning(f"Stock update failed: {e}")

    def _log_step(self, order, step, status, details=''):
        """Log a saga step."""
        SagaLog.objects.create(order=order, step=step, status=status, details=details)


class OrderList(APIView):
    def get(self, request):
        customer_id = request.query_params.get("customer_id")
        if customer_id:
            orders = Order.objects.filter(customer_id=customer_id)
        else:
            orders = Order.objects.all()
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetail(APIView):
    """Get order details with saga log."""
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        return Response({
            "order": OrderSerializer(order).data,
            "saga_log": SagaLogSerializer(order.saga_logs.all(), many=True).data,
        })


class HealthView(APIView):
    """Health check endpoint."""
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "order-service",
            "timestamp": datetime.utcnow().isoformat(),
        })
