from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User, Role

class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.test_user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }

    def test_registration_success(self):
        """Standard registration should succeed and default to VIEWER."""
        response = self.client.post(self.register_url, self.test_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['role'], Role.VIEWER)
        self.assertTrue(User.objects.filter(email=self.test_user_data['email']).exists())

    def test_registration_passwords_mismatch(self):
        """Registration should fail if passwords do not match."""
        data = self.test_user_data.copy()
        data['confirm_password'] = "Mismatched1!"
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """User should get JWT tokens on successful login."""
        User.objects.create_user(
            email="login@example.com",
            name="Login User",
            password="LoginPass123!"
        )
        data = {
            "email": "login@example.com",
            "password": "LoginPass123!"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], "login@example.com")

    def test_login_inactive_user(self):
        """Inactive users should not be allowed to login."""
        User.objects.create_user(
            email="inactive@example.com",
            name="Inactive",
            password="Password123!",
            is_active=False
        )
        data = {"email": "inactive@example.com", "password": "Password123!"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
