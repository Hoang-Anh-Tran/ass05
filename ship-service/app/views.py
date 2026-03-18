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


class ShippingProcess(APIView):
    """Original shipping processing endpoint (kept for backwards compatibility)."""
    def post(self, request):
        order_id = request.data.get("order_id")
        customer_id = request.data.get("customer_id")
        method = request.data.get("method", "standard")
        
        if not order_id or not customer_id:
            return Response({"error": "order_id and customer_id are required"}, status=400)

        method_labels = {
            "standard": "Standard Shipping (5-7 days)",
            "express": "Express Shipping (1-2 days)",
            "overnight": "Overnight Shipping"
        }
        label = method_labels.get(method, method)
            
        return Response({
            "message": f"Shipping scheduled for order {order_id} via {label}",
            "status": "SCHEDULED",
            "method": method,
            "tracking_number": f"TRK-{order_id}-{method[:3].upper()}"
        }, status=200)


class ShippingReserve(APIView):
    """
    Reserve shipping slot for an order (Saga step).
    Simulates reserving a shipping slot.
    """
    def post(self, request):
        order_id = request.data.get("order_id")
        customer_id = request.data.get("customer_id")
        method = request.data.get("method", "standard")

        if not order_id:
            return Response({"error": "order_id is required"}, status=400)

        # Check fault injection
        if _fault_config['enabled'] and _fault_config['remaining_failures'] > 0:
            _fault_config['remaining_failures'] -= 1
            if _fault_config['remaining_failures'] == 0:
                _fault_config['enabled'] = False
            logger.warning(f"FAULT INJECTION: Shipping reservation failed for order {order_id}")
            return Response({
                "error": "Shipping reservation failed (fault injected)",
                "status": "FAILED",
                "order_id": order_id,
            }, status=500)

        method_labels = {
            "standard": "Standard Shipping (5-7 days)",
            "express": "Express Shipping (1-2 days)",
            "overnight": "Overnight Shipping"
        }
        label = method_labels.get(method, method)

        logger.info(f"Shipping reserved for order {order_id} via {label}")
        return Response({
            "message": f"Shipping reserved for order {order_id} via {label}",
            "status": "RESERVED",
            "order_id": order_id,
            "method": method,
            "tracking_number": f"TRK-{order_id}-{method[:3].upper()}",
        }, status=200)


class ShippingCancel(APIView):
    """
    Cancel a shipping reservation (Saga compensation step).
    """
    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({"error": "order_id is required"}, status=400)

        logger.info(f"Shipping reservation cancelled for order {order_id}")
        return Response({
            "message": f"Shipping reservation cancelled for order {order_id}",
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
            "service": "ship-service",
            "timestamp": datetime.utcnow().isoformat(),
        })
