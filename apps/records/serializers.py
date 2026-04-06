from rest_framework import serializers
from apps.records.models import FinancialRecord, TransactionType
from apps.users.serializers import UserSerializer


class FinancialRecordSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            "id", "amount", "type", "category", "date", "notes",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class FinancialRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialRecord
        fields = ["amount", "type", "category", "date", "notes"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value

    def validate_type(self, value):
        valid = [t.value for t in TransactionType]
        if value not in valid:
            raise serializers.ValidationError(f"Type must be one of: {', '.join(valid)}.")
        return value

    def validate_category(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Category must be at least 2 characters.")
        return value.strip().title()

    def create(self, validated_data):
        request = self.context.get("request")
        return FinancialRecord.objects.create(
            created_by=request.user,
            **validated_data,
        )


class FinancialRecordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialRecord
        fields = ["amount", "type", "category", "date", "notes"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value
