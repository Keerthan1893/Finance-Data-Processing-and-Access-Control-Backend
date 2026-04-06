from django.contrib import admin
from apps.records.models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "type", "category", "amount", "date", "created_by", "is_deleted"]
    list_filter = ["type", "category", "is_deleted", "date"]
    search_fields = ["category", "notes"]
    ordering = ["-date"]
    readonly_fields = ["created_at", "updated_at", "deleted_at", "deleted_by"]

    def get_queryset(self, request):
        # Show all records including soft-deleted in admin
        return FinancialRecord.objects.all()
