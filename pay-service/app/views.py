import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Fault injection state (in-memory)
_fault_config = {
    'enabled': False,
    'remaining_failures': 0,
}


class PaymentProcess(APIView):
    """Original payment processing endpoint (kept for backwards compatibility)."""
    def post(self, request):
        order_id = request.data.get("order_id")
        amount = request.data.get("amount")
        method = request.data.get("method", "credit_card")
        
        if not order_id or amount is None:
            return Response({"error": "order_id and amount are required"}, status=400)
            
        method_labels = {
            "credit_card": "Credit Card",
            "paypal": "PayPal",
            "cod": "Cash on Delivery"
        }
        label = method_labels.get(method, method)
        
        return Response({
            "message": f"Payment of ${amount} via {label} successful for order {order_id}",
            "status": "SUCCESS",
            "method": method
        }, status=200)


class PaymentReserve(APIView):
    """
    Reserve payment for an order (Saga step).
    Simulates holding funds for the order amount.
    """
    def post(self, request):
        order_id = request.data.get("order_id")
        amount = request.data.get("amount")
        method = request.data.get("method", "credit_card")

        if not order_id or amount is None:
            return Response({"error": "order_id and amount are required"}, status=400)

        # Check fault injection
        if _fault_config['enabled'] and _fault_config['remaining_failures'] > 0:
            _fault_config['remaining_failures'] -= 1
            if _fault_config['remaining_failures'] == 0:
                _fault_config['enabled'] = False
            logger.warning(f"FAULT INJECTION: Payment reservation failed for order {order_id}")
            return Response({
                "error": "Payment reservation failed (fault injected)",
                "status": "FAILED",
                "order_id": order_id,
            }, status=500)

        method_labels = {
            "credit_card": "Credit Card",
            "paypal": "PayPal",
            "cod": "Cash on Delivery"
        }
        label = method_labels.get(method, method)

        logger.info(f"Payment reserved: ${amount} via {label} for order {order_id}")
        return Response({
            "message": f"Payment of ${amount} via {label} reserved for order {order_id}",
            "status": "RESERVED",
            "order_id": order_id,
            "method": method,
        }, status=200)


class PaymentCancel(APIView):
    """
    Cancel a payment reservation (Saga compensation step).
    """
    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({"error": "order_id is required"}, status=400)

        logger.info(f"Payment reservation cancelled for order {order_id}")
        return Response({
            "message": f"Payment reservation cancelled for order {order_id}",
            "status": "CANCELLED",
            "order_id": order_id,
        }, status=200)


class FaultEnable(APIView):
    """Enable fault injection for testing saga compensation."""
    def post(self, request):
        count = request.data.get("count", 1)
        _fault_config['enabled'] = True
        _fault_config['remaining_failures'] = int(count)
        logger.warning(f"Fault injection enabled for {count} request(s)")
        return Response({
            "message": f"Fault injection enabled for next {count} request(s)",
            "enabled": True,
        })


class FaultDisable(APIView):
    """Disable fault injection."""
    def post(self, request):
        _fault_config['enabled'] = False
        _fault_config['remaining_failures'] = 0
        logger.info("Fault injection disabled")
        return Response({
            "message": "Fault injection disabled",
            "enabled": False,
        })


class HealthView(APIView):
    """Health check endpoint."""
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "pay-service",
            "timestamp": datetime.utcnow().isoformat(),
        })
