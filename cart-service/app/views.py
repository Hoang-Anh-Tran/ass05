from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
import requests

BOOK_SERVICE_URL = "http://book-service:4000"

class CartCreate(APIView):
    def post(self, request):
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class AddCartItem(APIView):
    def post(self, request):
        book_id = request.data.get("book_id")
        
        try:
            r = requests.get(f"{BOOK_SERVICE_URL}/")
            books = r.json()
            if not any(b["id"] == book_id for b in books):
                return Response({"error": "Book not found"}, status=404)
        except Exception:
            # Fallback or error handling if book service is unreachable
            return Response({"error": "Failed to verify book"}, status=500)

        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ModifyCartItem(APIView):
    def put(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)
            
        quantity = request.data.get("quantity")
        if quantity is not None:
            item.quantity = quantity
            item.save()
            return Response(CartItemSerializer(item).data)
        return Response({"error": "quantity required"}, status=400)
        
    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id)
            item.delete()
            return Response({"message": "Item removed"}, status=204)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

class ViewCart(APIView):
    def get(self, request, customer_id):
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=404)
            
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response({
            "cart_id": cart.id,
            "customer_id": cart.customer_id,
            "items": serializer.data
        })