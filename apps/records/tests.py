from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User, Role
from apps.records.models import FinancialRecord, TransactionType

class RecordCRUDTests(APITestCase):
    def setUp(self):
        
        self.admin = User.objects.create_user(
            email="admin@example.com", name="Admin", password="Password123!", role=Role.ADMIN
        )
        self.analyst = User.objects.create_user(
            email="analyst@example.com", name="Analyst", password="Password123!", role=Role.ANALYST
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com", name="Viewer", password="Password123!", role=Role.VIEWER
        )

        self.list_url = reverse('records-list')
        self.record_data = {
            "amount": "1500.00",
            "type": TransactionType.EXPENSE,
            "category": "Office Supplies",
            "date": "2024-03-25"
        }

    def test_admin_can_create_record(self):
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, self.record_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FinancialRecord.objects.count(), 1)

    def test_analyst_cannot_create_record(self):
        
        self.client.force_authenticate(user=self.analyst)
        response = self.client.post(self.list_url, self.record_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_view_record_list(self):
        
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_can_view_record_list(self):
       
        # Pre-create a record
        FinancialRecord.objects.create(
            amount=500, type=TransactionType.INCOME, category="Gift", 
            date=date.today(), created_by=self.admin
        )
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_admin_can_soft_delete_record(self):
        """Deleting a record should mark it as is_deleted instead of removing it."""
        record = FinancialRecord.objects.create(
            amount=100, type=TransactionType.EXPENSE, category="Food", 
            date=date.today(), created_by=self.admin
        )
        url = reverse('records-detail', kwargs={'pk': record.pk})
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record.refresh_from_db()
        self.assertTrue(record.is_deleted)
        self.assertEqual(FinancialRecord.objects.filter(is_deleted=False).count(), 0)
