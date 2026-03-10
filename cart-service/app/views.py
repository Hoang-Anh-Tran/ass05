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
        customer_id = request.data.get("customer_id")
        book_id = request.data.get("book_id")
        quantity = request.data.get("quantity", 1)

        if not customer_id or not book_id:
            return Response({"error": "customer_id and book_id are required"}, status=400)

        # Verify book exists
        try:
            r = requests.get(f"{BOOK_SERVICE_URL}/")
            books = r.json()
            if not any(b["id"] == book_id for b in books):
                return Response({"error": "Book not found"}, status=404)
        except Exception:
            return Response({"error": "Failed to verify book"}, status=500)

        # Find or create cart for this customer
        cart, created = Cart.objects.get_or_create(customer_id=customer_id)

        # Check if item already in cart, if so increment quantity
        existing = CartItem.objects.filter(cart=cart, book_id=book_id).first()
        if existing:
            existing.quantity += quantity
            existing.save()
            return Response(CartItemSerializer(existing).data, status=200)

        # Create new cart item
        item = CartItem.objects.create(cart=cart, book_id=book_id, quantity=quantity)
        return Response(CartItemSerializer(item).data, status=201)

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
        # Auto-create cart if it doesn't exist
        cart, created = Cart.objects.get_or_create(customer_id=customer_id)
            
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response({
            "cart_id": cart.id,
            "customer_id": cart.customer_id,
            "items": serializer.data
        })

class ClearCart(APIView):
    def delete(self, request, customer_id):
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=404)
        
        CartItem.objects.filter(cart=cart).delete()
        return Response({"message": "Cart cleared"}, status=204)