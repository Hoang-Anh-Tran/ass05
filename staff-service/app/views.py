import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# book-service root is now at / (not /books/)
BOOK_SERVICE_URL = "http://book-service:4000"

@csrf_exempt
def manage_books(request, book_id=None):
    try:
        if request.method == "GET":
            url = f"{BOOK_SERVICE_URL}/{book_id}/" if book_id else f"{BOOK_SERVICE_URL}/"
            response = requests.get(url)
            return JsonResponse(response.json(), safe=False)
            
        elif request.method == "POST":
            # Add new book
            data = json.loads(request.body) if request.body else {}
            response = requests.post(f"{BOOK_SERVICE_URL}/", json=data)
            return JsonResponse(response.json(), safe=False)
            
        elif request.method == "PUT":
            if not book_id:
                return JsonResponse({"error": "book_id required for PUT"}, status=400)
            data = json.loads(request.body) if request.body else {}
            response = requests.put(f"{BOOK_SERVICE_URL}/{book_id}/", json=data)
            return JsonResponse(response.json(), safe=False)
            
        elif request.method == "DELETE":
            if not book_id:
                return JsonResponse({"error": "book_id required for DELETE"}, status=400)
            response = requests.delete(f"{BOOK_SERVICE_URL}/{book_id}/")
            return JsonResponse({"message": "Deleted successfully"} if response.status_code == 204 else response.json(), safe=False)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
