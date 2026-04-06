from django.core.cache import cache
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncWeek
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.records.models import FinancialRecord, TransactionType
from apps.users.permissions import CanViewDashboard, IsActiveUser
from apps.core.responses import success_response

CACHE_TTL = 300  # 5 minutes


def _base_qs(filters: dict = None):
    """Return active (non-deleted) records, optionally filtered."""
    qs = FinancialRecord.objects.filter(is_deleted=False)
    if filters:
        qs = qs.filter(**filters)
    return qs


@extend_schema(tags=["Dashboard"])
class SummaryView(APIView):
    
    permission_classes = [IsAuthenticated, IsActiveUser, CanViewDashboard]

    @extend_schema(
        parameters=[
            OpenApiParameter("year", int, description="Filter by year (e.g. 2024)"),
            OpenApiParameter("month", int, description="Filter by month number (1-12)"),
        ]
    )
    def get(self, request):
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        cache_key = f"dashboard:summary:y{year}:m{month}"
        cached = cache.get(cache_key)
        if cached:
            return success_response(data=cached, message="Dashboard summary (cached).")

        filters = {}
        if year:
            filters["date__year"] = year
        if month:
            filters["date__month"] = month

        qs = _base_qs(filters)

        totals = qs.aggregate(
            total_income=Sum("amount", filter=Q(type=TransactionType.INCOME)),
            total_expenses=Sum("amount", filter=Q(type=TransactionType.EXPENSE)),
            total_records=Count("id"),
            income_count=Count("id", filter=Q(type=TransactionType.INCOME)),
            expense_count=Count("id", filter=Q(type=TransactionType.EXPENSE)),
        )

        total_income = float(totals["total_income"] or 0)
        total_expenses = float(totals["total_expenses"] or 0)

        data = {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": round(total_income - total_expenses, 2),
            "total_records": totals["total_records"],
            "income_count": totals["income_count"],
            "expense_count": totals["expense_count"],
            "filters_applied": {"year": year, "month": month},
        }

        cache.set(cache_key, data, CACHE_TTL)
        return success_response(data=data, message="Dashboard summary retrieved.")


@extend_schema(tags=["Dashboard"])
class CategoryBreakdownView(APIView):
    
    permission_classes = [IsAuthenticated, IsActiveUser, CanViewDashboard]

    @extend_schema(
        parameters=[
            OpenApiParameter("type", str, description="Filter by type: income or expense"),
            OpenApiParameter("year", int, description="Filter by year"),
            OpenApiParameter("month", int, description="Filter by month"),
        ]
    )
    def get(self, request):
        record_type = request.query_params.get("type")
        year = request.query_params.get("year")
        month = request.query_params.get("month")

        cache_key = f"dashboard:category_breakdown:t{record_type}:y{year}:m{month}"
        cached = cache.get(cache_key)
        if cached:
            return success_response(data=cached, message="Category breakdown (cached).")

        filters = {}
        if record_type in (TransactionType.INCOME, TransactionType.EXPENSE):
            filters["type"] = record_type
        if year:
            filters["date__year"] = year
        if month:
            filters["date__month"] = month

        qs = _base_qs(filters)

        breakdown = (
            qs.values("category", "type")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        # Structure as { category: { income: x, expense: y, net: z } }
        result = {}
        for row in breakdown:
            cat = row["category"]
            if cat not in result:
                result[cat] = {"category": cat, "income": 0.0, "expense": 0.0, "net": 0.0, "count": 0}
            result[cat][row["type"]] = float(row["total"])
            result[cat]["count"] += row["count"]

        for cat in result:
            result[cat]["net"] = round(result[cat]["income"] - result[cat]["expense"], 2)

        data = {
            "categories": sorted(result.values(), key=lambda x: x["count"], reverse=True),
            "filters_applied": {"type": record_type, "year": year, "month": month},
        }

        cache.set(cache_key, data, CACHE_TTL)
        return success_response(data=data, message="Category breakdown retrieved.")


@extend_schema(tags=["Dashboard"])
class MonthlyTrendsView(APIView):
   
    permission_classes = [IsAuthenticated, IsActiveUser, CanViewDashboard]

    @extend_schema(
        parameters=[
            OpenApiParameter("year", int, description="Year to fetch trends for (defaults to current year)"),
        ]
    )
    def get(self, request):
        from django.utils import timezone
        year = request.query_params.get("year", timezone.now().year)

        cache_key = f"dashboard:monthly_trends:y{year}"
        cached = cache.get(cache_key)
        if cached:
            return success_response(data=cached, message="Monthly trends (cached).")

        qs = _base_qs({"date__year": year})

        monthly = (
            qs.annotate(month=TruncMonth("date"))
            .values("month", "type")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("month")
        )

        # Build month-keyed dict
        months = {}
        for row in monthly:
            key = row["month"].strftime("%Y-%m")
            label = row["month"].strftime("%b %Y")
            if key not in months:
                months[key] = {
                    "period": key,
                    "label": label,
                    "income": 0.0,
                    "expense": 0.0,
                    "net": 0.0,
                }
            months[key][row["type"]] = float(row["total"])

        for key in months:
            months[key]["net"] = round(months[key]["income"] - months[key]["expense"], 2)

        data = {
            "year": year,
            "trends": sorted(months.values(), key=lambda x: x["period"]),
        }

        cache.set(cache_key, data, CACHE_TTL)
        return success_response(data=data, message="Monthly trends retrieved.")


@extend_schema(tags=["Dashboard"])
class WeeklyTrendsView(APIView):
    
    permission_classes = [IsAuthenticated, IsActiveUser, CanViewDashboard]

    def get(self, request):
        from django.utils import timezone
        import datetime

        cache_key = "dashboard:weekly_trends"
        cached = cache.get(cache_key)
        if cached:
            return success_response(data=cached, message="Weekly trends (cached).")

        cutoff = timezone.now().date() - datetime.timedelta(weeks=12)
        qs = _base_qs({"date__gte": cutoff})

        weekly = (
            qs.annotate(week=TruncWeek("date"))
            .values("week", "type")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("week")
        )

        weeks = {}
        for row in weekly:
            key = row["week"].strftime("%Y-%m-%d")
            if key not in weeks:
                weeks[key] = {
                    "week_start": key,
                    "income": 0.0,
                    "expense": 0.0,
                    "net": 0.0,
                }
            weeks[key][row["type"]] = float(row["total"])

        for key in weeks:
            weeks[key]["net"] = round(weeks[key]["income"] - weeks[key]["expense"], 2)

        data = {"weeks": sorted(weeks.values(), key=lambda x: x["week_start"])}

        cache.set(cache_key, data, CACHE_TTL)
        return success_response(data=data, message="Weekly trends retrieved.")


@extend_schema(tags=["Dashboard"])
class RecentActivityView(APIView):
    
    permission_classes = [IsAuthenticated, IsActiveUser, CanViewDashboard]

    @extend_schema(
        parameters=[
            OpenApiParameter("limit", int, description="Number of recent records to return (default 10, max 50)"),
        ]
    )
    def get(self, request):
        from apps.records.serializers import FinancialRecordSerializer

        try:
            limit = min(int(request.query_params.get("limit", 10)), 50)
        except (ValueError, TypeError):
            limit = 10

        records = _base_qs().select_related("created_by")[:limit]
        data = FinancialRecordSerializer(records, many=True).data
        return success_response(data=data, message="Recent activity retrieved.")
