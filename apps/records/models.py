from django.db import models
from django.conf import settings


class TransactionType(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class FinancialRecord(models.Model):
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    category = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="records",
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_records",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_records"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["type", "date"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_deleted"]),
        ]

    def __str__(self):
        return f"[{self.type.upper()}] {self.category} — ₹{self.amount} on {self.date}"

    def soft_delete(self, user):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
