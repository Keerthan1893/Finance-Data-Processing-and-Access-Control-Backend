from django.urls import path
from apps.dashboard.views import (
    SummaryView,
    CategoryBreakdownView,
    MonthlyTrendsView,
    WeeklyTrendsView,
    RecentActivityView,
)

urlpatterns = [
    path("summary/", SummaryView.as_view(), name="dashboard-summary"),
    path("category-breakdown/", CategoryBreakdownView.as_view(), name="dashboard-category-breakdown"),
    path("trends/monthly/", MonthlyTrendsView.as_view(), name="dashboard-monthly-trends"),
    path("trends/weekly/", WeeklyTrendsView.as_view(), name="dashboard-weekly-trends"),
    path("recent-activity/", RecentActivityView.as_view(), name="dashboard-recent-activity"),
]
