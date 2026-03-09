from rest_framework.views import APIView
from rest_framework.response import Response

class PaymentProcess(APIView):
    def post(self, request):
        order_id = request.data.get("order_id")
        amount = request.data.get("amount")
        method = request.data.get("method", "credit_card")
        
        if not order_id or not amount:
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
