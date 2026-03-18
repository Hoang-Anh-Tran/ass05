import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AuthUser, RefreshToken
from .serializers import RegisterSerializer, AuthUserSerializer
from .jwt_utils import generate_access_token, generate_refresh_token, decode_token

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Register a new user with hashed password."""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered: {user.email} with role {user.role}")
            return Response({
                "message": "User registered successfully",
                "user": AuthUserSerializer(user).data,
            }, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    """Authenticate user and return JWT tokens."""

    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")

        try:
            user = AuthUser.objects.get(email=email)
        except AuthUser.DoesNotExist:
            logger.warning(f"Login attempt with unknown email: {email}")
            return Response({"error": "Invalid email or password"}, status=401)

        if not user.check_password(password):
            logger.warning(f"Failed login attempt for: {email}")
            return Response({"error": "Invalid email or password"}, status=401)

        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        # Store refresh token in database
        RefreshToken.objects.create(user=user, token=refresh_token)

        logger.info(f"User logged in: {email}")
        return Response({
            "access": access_token,
            "refresh": refresh_token,
            "user": AuthUserSerializer(user).data,
        })


class TokenRefreshView(APIView):
    """Refresh an access token using a valid refresh token."""

    def post(self, request):
        refresh_token = request.data.get("refresh", "")

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=400)

        # Check if token exists and is not revoked
        try:
            stored_token = RefreshToken.objects.get(token=refresh_token, is_revoked=False)
        except RefreshToken.DoesNotExist:
            return Response({"error": "Invalid or revoked refresh token"}, status=401)

        try:
            payload = decode_token(refresh_token)
            if payload.get('type') != 'refresh':
                return Response({"error": "Invalid token type"}, status=401)
        except ValueError as e:
            return Response({"error": str(e)}, status=401)

        user = stored_token.user
        new_access_token = generate_access_token(user)

        logger.info(f"Token refreshed for: {user.email}")
        return Response({
            "access": new_access_token,
        })


class TokenVerifyView(APIView):
    """Verify if a given token is valid."""

    def post(self, request):
        token = request.data.get("token", "")

        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            payload = decode_token(token)
            return Response({
                "valid": True,
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "exp": payload.get("exp"),
            })
        except ValueError as e:
            return Response({"valid": False, "error": str(e)}, status=401)


class HealthView(APIView):
    """Health check endpoint."""

    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "auth-service",
            "timestamp": datetime.utcnow().isoformat(),
        })
