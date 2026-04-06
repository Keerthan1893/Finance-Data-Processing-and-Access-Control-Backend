import django_filters
from apps.records.models import FinancialRecord, TransactionType


class FinancialRecordFilter(django_filters.FilterSet):
    # Date range
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    # Exact type
    type = django_filters.ChoiceFilter(choices=TransactionType.choices)

    # Case-insensitive category contains
    category = django_filters.CharFilter(field_name="category", lookup_expr="icontains")

    # Amount range
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")

    # Month / Year shortcuts
    month = django_filters.NumberFilter(field_name="date", lookup_expr="month")
    year = django_filters.NumberFilter(field_name="date", lookup_expr="year")

    # Soft delete visibility
    include_deleted = django_filters.BooleanFilter(method="filter_include_deleted", label="Include soft-deleted records")

    class Meta:
        model = FinancialRecord
        fields = ["type", "category", "date_from", "date_to", "amount_min", "amount_max", "month", "year", "include_deleted"]

    def filter_include_deleted(self, queryset, name, value):
        if value:
            return queryset
        return queryset.filter(is_deleted=False)
