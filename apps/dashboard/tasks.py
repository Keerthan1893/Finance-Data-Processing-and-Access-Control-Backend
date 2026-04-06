"""
Celery tasks for the dashboard.

The `warm_dashboard_cache` task pre-computes and stores all summary
analytics in Redis so the first API request after cache expiry
is never slow. It runs every 5 minutes via django-celery-beat.

Setup: After running migrations, add a periodic task in the admin panel:
  Task name   : apps.dashboard.tasks.warm_dashboard_cache
  Schedule    : Every 5 minutes (interval)
  Description : Pre-warm dashboard summary cache
"""

from celery import shared_task
from django.core.cache import cache
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.records.models import FinancialRecord, TransactionType

CACHE_TTL = 300  # 5 minutes


def _base_qs():
    return FinancialRecord.objects.filter(is_deleted=False)


@shared_task(name="apps.dashboard.tasks.warm_dashboard_cache", bind=True, max_retries=3)
def warm_dashboard_cache(self):
    """Pre-compute and cache all dashboard analytics."""
    try:
        _cache_global_summary()
        _cache_category_breakdown()
        _cache_monthly_trends()
        return "Dashboard cache warmed successfully."
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


def _cache_global_summary():
    qs = _base_qs()
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
        "filters_applied": {"year": None, "month": None},
    }
    cache.set("dashboard:summary:yNone:mNone", data, CACHE_TTL)


def _cache_category_breakdown():
    qs = _base_qs()
    breakdown = (
        qs.values("category", "type")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
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
        "filters_applied": {"type": None, "year": None, "month": None},
    }
    cache.set("dashboard:category_breakdown:tNone:yNone:mNone", data, CACHE_TTL)


def _cache_monthly_trends():
    year = timezone.now().year
    qs = _base_qs().filter(date__year=year)
    monthly = (
        qs.annotate(month=TruncMonth("date"))
        .values("month", "type")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("month")
    )
    months = {}
    for row in monthly:
        key = row["month"].strftime("%Y-%m")
        if key not in months:
            months[key] = {
                "period": key,
                "label": row["month"].strftime("%b %Y"),
                "income": 0.0,
                "expense": 0.0,
                "net": 0.0,
            }
        months[key][row["type"]] = float(row["total"])
    for key in months:
        months[key]["net"] = round(months[key]["income"] - months[key]["expense"], 2)

    data = {"year": year, "trends": sorted(months.values(), key=lambda x: x["period"])}
    cache.set(f"dashboard:monthly_trends:y{year}", data, CACHE_TTL)
