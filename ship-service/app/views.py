from rest_framework.views import APIView
from rest_framework.response import Response

class ShippingProcess(APIView):
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
