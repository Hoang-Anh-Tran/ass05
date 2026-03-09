import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# ---------------- HOME ----------------
def home(request):
    return JsonResponse({
        "message": "API Gateway is running",
        "routes": [
            "/customers/", "/books/", "/cart/", "/staff/", "/manager/",
            "/catalog/", "/orders/", "/shipping/", "/payment/", "/comments/", "/recommendations/"
        ]
    })

# ---------------- PROXY LOGIC ----------------
def proxy_request(request, base_url, path_suffix):
    try:
        url = f"{base_url}/{path_suffix}"
        
        # Clean double slashes except in http://
        url = url.replace("://", "___").replace("//", "/").replace("___", "://")
        
        # Parse body safely
        body_data = None
        if request.body:
            try:
                body_data = json.loads(request.body)
            except json.JSONDecodeError:
                pass # Body exists but not JSON

        if request.method == "GET":
            response = requests.get(url, params=request.GET)
        elif request.method == "POST":
            response = requests.post(url, json=body_data)
        elif request.method == "PUT":
            response = requests.put(url, json=body_data)
        elif request.method == "DELETE":
            response = requests.delete(url)
        else:
            return JsonResponse({"error": "Method not supported"}, status=405)

        # Handle empty responses seamlessly
        if response.status_code == 204 or not response.content:
            return JsonResponse({"message": "Success"}, status=204)

        return JsonResponse(response.json(), safe=False, status=response.status_code)
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Service unavailable: {str(e)}"}, status=503)
    except ValueError as e:
        return JsonResponse({"error": "Invalid JSON response from downstream service"}, status=502)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ---------------- FORWARDING VIEWS ----------------

@csrf_exempt
def customers(request, path=""):
    return proxy_request(request, "http://customer-service:4000", path)

@csrf_exempt
def books(request, path=""):
    return proxy_request(request, "http://book-service:4000", path)

@csrf_exempt
def cart(request, path=""):
    return proxy_request(request, "http://cart-service:4000", path)

@csrf_exempt
def staff(request, path=""):
    return proxy_request(request, "http://staff-service:4000", path)

@csrf_exempt
def manager(request, path=""):
    return proxy_request(request, "http://manager-service:4000", path)

@csrf_exempt
def catalog(request, path=""):
    return proxy_request(request, "http://catalog-service:4000", path)

@csrf_exempt
def orders(request, path=""):
    return proxy_request(request, "http://order-service:4000", path)

@csrf_exempt
def shipping(request, path=""):
    return proxy_request(request, "http://ship-service:4000", path)

@csrf_exempt
def payment(request, path=""):
    return proxy_request(request, "http://pay-service:4000", path)

@csrf_exempt
def comments(request, path=""):
    return proxy_request(request, "http://comment-rate-service:4000", path)

@csrf_exempt
def recommendations(request, path=""):
    return proxy_request(request, "http://recommender-ai-service:4000", path)