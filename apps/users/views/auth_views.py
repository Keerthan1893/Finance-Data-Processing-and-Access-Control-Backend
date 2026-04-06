from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.users.serializers import (
    UserRegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
)
from apps.users.permissions import IsActiveUser
from apps.core.responses import success_response, error_response
from apps.users.models import Role


@extend_schema(tags=["Auth"])
class RegisterView(generics.CreateAPIView):
    """
    Public registration endpoint. 
    Defaults to VIEWER role unless an Admin is creating the user.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        request = self.request
        role = Role.VIEWER
        
        # Only authenticated Admins can specify a role during registration
        if request.user.is_authenticated and request.user.role == Role.ADMIN:
            role = request.data.get("role", Role.VIEWER)

        serializer.save(role=role)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return success_response(
            data=UserSerializer(serializer.instance).data,
            message="User registered successfully.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"])
class LoginView(TokenObtainPairView):
    """Obtain JWT access and refresh tokens."""
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=["Auth"])
class TokenRefreshAPIView(TokenRefreshView):
    """Refresh the access token."""
    pass


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    """Blacklist the refresh token to logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response(
                message="No refresh token provided.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass

        return success_response(message="Logged out successfully.")


@extend_schema(tags=["Auth"])
class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Prevent role and active status changes by the user themselves
        serializer.validated_data.pop("role", None)
        serializer.validated_data.pop("is_active", None)

        self.perform_update(serializer)

        return success_response(
            data=serializer.data,
            message="Profile updated.",
        )

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_object()).data)


@extend_schema(tags=["Auth"])
class ChangePasswordView(APIView):
    """Update the password for the authenticated user."""
    permission_classes = [IsAuthenticated, IsActiveUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return error_response(
                message="Old password is incorrect.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return success_response(message="Password changed successfully.")