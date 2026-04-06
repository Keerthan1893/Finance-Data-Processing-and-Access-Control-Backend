from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.records.models import FinancialRecord
from apps.records.serializers import (
    FinancialRecordSerializer,
    FinancialRecordCreateSerializer,
    FinancialRecordUpdateSerializer,
)
from apps.records.filters import FinancialRecordFilter
from apps.users.permissions import IsActiveUser, CanViewRecords, CanManageRecords
from apps.core.responses import success_response, error_response


CACHE_INVALIDATE_KEYS = [
    "dashboard:summary",
    "dashboard:category_breakdown",
    "dashboard:monthly_trends",
    "dashboard:weekly_trends",
]


def invalidate_dashboard_cache():
    for key in CACHE_INVALIDATE_KEYS:
        cache.delete(key)


@extend_schema(tags=["Financial Records"])
class FinancialRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD for Financial Records.
    Viewable by: Admin, Analyst
    Manageable by: Admin
    """
    queryset = FinancialRecord.objects.all().select_related("created_by")
    permission_classes = [IsAuthenticated, IsActiveUser, CanViewRecords]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = FinancialRecordFilter
    search_fields = ["category", "notes"]
    ordering_fields = ["date", "amount", "created_at"]
    ordering = ["-date"]

    def get_permissions(self):
        """Allow Analysts/Admins to view, but only Admins to manage."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsActiveUser(), CanManageRecords()]
        return super().get_permissions()

    def get_queryset(self):
        """Only exclude deleted records by default if no filter is applied (handled by filterset)."""
        qs = super().get_queryset()
        
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return FinancialRecordCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return FinancialRecordUpdateSerializer
        return FinancialRecordSerializer

    # 🔹 LIST
    @extend_schema(
        parameters=[
            OpenApiParameter("type", str),
            OpenApiParameter("category", str),
            OpenApiParameter("date_from", str),
            OpenApiParameter("date_to", str),
            OpenApiParameter("month", int),
            OpenApiParameter("year", int),
            OpenApiParameter("amount_min", float),
            OpenApiParameter("amount_max", float),
            OpenApiParameter("search", str),
            OpenApiParameter("ordering", str),
            OpenApiParameter("include_deleted", bool),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        return success_response(
            data=serializer.data,
            message="Records retrieved successfully.",
            pagination={
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
            },
        )

    # 🔹 CREATE
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()

        invalidate_dashboard_cache()

        return success_response(
            data=FinancialRecordSerializer(record).data,
            message="Financial record created successfully.",
            status=status.HTTP_201_CREATED,
        )

    # 🔹 RETRIEVE
    def retrieve(self, request, pk=None):
        record = get_object_or_404(self.get_queryset(), pk=pk)
        return success_response(data=FinancialRecordSerializer(record).data)

    # 🔹 UPDATE
    def partial_update(self, request, pk=None):
        record = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        invalidate_dashboard_cache()

        return success_response(
            data=FinancialRecordSerializer(record).data,
            message="Record updated successfully.",
        )

    # 🔹 DELETE (SOFT DELETE)
    def destroy(self, request, pk=None):
        record = get_object_or_404(self.get_queryset(), pk=pk)
        record.soft_delete(user=request.user)

        invalidate_dashboard_cache()

        return success_response(message="Record deleted successfully.")