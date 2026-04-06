from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.users.models import User
from apps.users.serializers import (
    UserSerializer,
    UserUpdateSerializer,
    UserRegisterSerializer,
)
from apps.users.permissions import IsAdmin, IsActiveUser
from apps.core.responses import success_response, error_response


@extend_schema(tags=["Users"])
class UserViewSet(viewsets.ModelViewSet):
    """
    User Management API.
    Accessible by: Admin only.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    # 🔹 LIST USERS
    @extend_schema(
        parameters=[
            OpenApiParameter("role", str, description="Filter by role"),
            OpenApiParameter("is_active", bool, description="Filter by active status"),
            OpenApiParameter("search", str, description="Search by name or email"),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        role = request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                name__icontains=search
            ) | queryset.filter(email__icontains=search)

        page = self.paginate_queryset(queryset)
        serializer = UserSerializer(page, many=True)

        return success_response(
            data=serializer.data,
            message="Users retrieved successfully.",
            pagination={
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
            },
        )

    # 🔹 CREATE USER
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return success_response(
            data=UserSerializer(user).data,
            message="User created successfully.",
            status=status.HTTP_201_CREATED,
        )

    # 🔹 RETRIEVE USER
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        return success_response(data=UserSerializer(user).data)

    # 🔹 UPDATE USER
    def partial_update(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        # Logic: Admins cannot change their own role to something else via this API 
        # to prevent accidental lockout of the last admin.
        if user == request.user and request.data.get("role"):
            return error_response(
                message="You cannot change your own role.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            data=UserSerializer(user).data,
            message="User updated successfully.",
        )

    # 🔹 DELETE USER
    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            return error_response(
                message="You cannot delete your own account.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return success_response(message="User deleted successfully.")

    # 🔥 CUSTOM ACTION → TOGGLE STATUS
    @action(detail=True, methods=["post"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            return error_response(
                message="You cannot deactivate your own account.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        action_text = "activated" if user.is_active else "deactivated"

        return success_response(
            data=UserSerializer(user).data,
            message=f"User {action_text} successfully.",
        )
