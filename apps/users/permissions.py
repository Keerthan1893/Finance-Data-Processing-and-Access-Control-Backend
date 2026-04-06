from rest_framework.permissions import BasePermission
from apps.users.models import Role


class IsAdmin(BasePermission):
    """Only admin users can access."""
    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsAnalyst(BasePermission):
    """Only analyst users can access."""
    message = "You must be an analyst to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ANALYST
        )


class IsViewer(BasePermission):
    """Only viewer users can access."""
    message = "You must be a viewer to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.VIEWER
        )


class CanViewDashboard(BasePermission):
    """Admins, Analysts, and Viewers can see dashboard summaries."""
    message = "You do not have permission to view the dashboard."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.ANALYST, Role.VIEWER)
        )


class CanViewRecords(BasePermission):
    """Only Admins and Analysts can see detailed transaction records."""
    message = "You must be an analyst or admin to view financial records."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.ANALYST)
        )


class CanManageRecords(BasePermission):
    """Only Admins can create, update, or delete records."""
    message = "Only administrators can manage financial records."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsActiveUser(BasePermission):
    """Only active users can use the API."""
    message = "Your account has been deactivated. Please contact an admin."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )
