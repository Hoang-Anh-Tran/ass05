import requests
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app.middleware import get_metrics
import json
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiParameter

# Service URLs
SERVICE_URLS = {
    'customer-service': 'http://customer-service:4000',
    'book-service': 'http://book-service:4000',
    'cart-service': 'http://cart-service:4000',
    'staff-service': 'http://staff-service:4000',
    'manager-service': 'http://manager-service:4000',
    'catalog-service': 'http://catalog-service:4000',
    'order-service': 'http://order-service:4000',
    'ship-service': 'http://ship-service:4000',
    'pay-service': 'http://pay-service:4000',
    'comment-rate-service': 'http://comment-rate-service:4000',
    'recommender-ai-service': 'http://recommender-ai-service:4000',
    'auth-service': 'http://auth-service:4000',
}


# ---------------- HOME ----------------
def home(request):
    return JsonResponse({
        "message": "API Gateway is running",
        "version": "2.0 - Industry Level",
        "features": [
            "JWT Authentication",
            "Rate Limiting",
            "Request Logging",
            "Saga Pattern (Order Service)",
            "RabbitMQ Event Bus",
            "Health Checks",
            "Metrics",
        ],
        "routes": [
            "/auth/", "/customers/", "/books/", "/cart/", "/staff/",
            "/manager/", "/catalog/", "/orders/", "/shipping/", "/payment/",
            "/comments/", "/recommendations/", "/health/", "/metrics/"
        ]
    })


# ---------------- PROXY LOGIC ----------------
def proxy_request(request, base_url, path_suffix):
    try:
        url = f"{base_url}/{path_suffix}"
        
        # Clean double slashes except in http://
        url = url.replace("://", "___").replace("//", "/").replace("___", "://")
        
        # Forward authentication headers to downstream services
        headers = {}
        for header_name in ['HTTP_X_USER_ID', 'HTTP_X_USER_EMAIL', 'HTTP_X_USER_ROLE']:
            value = request.META.get(header_name, '')
            if value:
                # Convert HTTP_X_USER_ID to X-User-Id format
                formatted = header_name.replace('HTTP_', '').replace('_', '-').title()
                headers[formatted] = value

        # Parse body safely
        body_data = None
        if request.body:
            try:
                body_data = json.loads(request.body)
            except json.JSONDecodeError:
                pass

        if request.method == "GET":
            response = requests.get(url, params=request.GET, headers=headers, timeout=30)
        elif request.method == "POST":
            response = requests.post(url, json=body_data, headers=headers, timeout=30)
        elif request.method == "PUT":
            response = requests.put(url, json=body_data, headers=headers, timeout=30)
        elif request.method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return JsonResponse({"error": "Method not supported"}, status=405)

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
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Auth Service Proxy",
    description="Proxies requests to the Authentication Service (register, login, token refresh).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def auth(request, path=""):
    return proxy_request(request, "http://auth-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Customer Service Proxy",
    description="Proxies requests to the Customer Service (profiles, data).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def customers(request, path=""):
    return proxy_request(request, "http://customer-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Book Service Proxy",
    description="Proxies requests to the Book Service (listing, details).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def books(request, path=""):
    return proxy_request(request, "http://book-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Cart Service Proxy",
    description="Proxies requests to the Cart Service (item management).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def cart(request, path=""):
    return proxy_request(request, "http://cart-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Staff Service Proxy",
    description="Proxies requests to the Staff Service (administrative tasks).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def staff(request, path=""):
    return proxy_request(request, "http://staff-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Manager Service Proxy",
    description="Proxies requests to the Manager Service (business logic).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def manager(request, path=""):
    return proxy_request(request, "http://manager-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Catalog Service Proxy",
    description="Proxies requests to the Catalog Service (vouchers, categories).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def catalog(request, path=""):
    return proxy_request(request, "http://catalog-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Order Service Proxy",
    description="Proxies requests to the Order Service (Saga creation, status).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def orders(request, path=""):
    return proxy_request(request, "http://order-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Shipping Service Proxy",
    description="Proxies requests to the Shipping Service (tracking, methods).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def shipping(request, path=""):
    return proxy_request(request, "http://ship-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Payment Service Proxy",
    description="Proxies requests to the Payment Service (processing, status).",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def payment(request, path=""):
    return proxy_request(request, "http://pay-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Comment Service Proxy",
    description="Proxies requests to the Comment & Rating Service.",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def comments(request, path=""):
    return proxy_request(request, "http://comment-rate-service:4000", path)

@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@extend_schema(
    summary="Recommendation AI Service Proxy",
    description="Proxies requests to the Recommender AI Service.",
    parameters=[OpenApiParameter("path", str, OpenApiParameter.PATH)]
)
def recommendations(request, path=""):
    return proxy_request(request, "http://recommender-ai-service:4000", path)


# ---------------- OBSERVABILITY ----------------

def health(request):
    """Aggregated health check - checks all downstream services."""
    results = {}
    overall_healthy = True

    for service_name, url in SERVICE_URLS.items():
        try:
            resp = requests.get(f"{url}/health/", timeout=5)
            if resp.status_code == 200:
                results[service_name] = {"status": "healthy"}
            else:
                results[service_name] = {"status": "unhealthy", "code": resp.status_code}
                overall_healthy = False
        except Exception as e:
            results[service_name] = {"status": "unreachable", "error": str(e)}
            overall_healthy = False

    return JsonResponse({
        "status": "healthy" if overall_healthy else "degraded",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "downstream_services": results,
    })


def metrics(request):
    """Return gateway metrics (request counts, error rates, response times)."""
    metrics_data = get_metrics()
    metrics_data['service'] = 'api-gateway'
    metrics_data['timestamp'] = datetime.utcnow().isoformat()
    return JsonResponse(metrics_data)