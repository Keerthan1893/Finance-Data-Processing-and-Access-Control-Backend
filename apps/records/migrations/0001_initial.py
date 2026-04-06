from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinancialRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                (
                    "type",
                    models.CharField(
                        choices=[("income", "Income"), ("expense", "Expense")],
                        max_length=10,
                    ),
                ),
                ("category", models.CharField(max_length=100)),
                ("date", models.DateField()),
                ("notes", models.TextField(blank=True, default="")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="deleted_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "financial_records", "ordering": ["-date", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="financialrecord",
            index=models.Index(fields=["type", "date"], name="financial_r_type_date_idx"),
        ),
        migrations.AddIndex(
            model_name="financialrecord",
            index=models.Index(fields=["category"], name="financial_r_category_idx"),
        ),
        migrations.AddIndex(
            model_name="financialrecord",
            index=models.Index(fields=["is_deleted"], name="financial_r_is_deleted_idx"),
        ),
    ]
