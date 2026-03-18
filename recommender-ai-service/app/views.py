from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime


class HealthView(APIView):
    """Health check endpoint."""
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "recommender-ai-service",
            "timestamp": datetime.utcnow().isoformat(),
        })
