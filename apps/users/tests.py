from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient
import tempfile

from .models import DeviceToken

def _valid_png_bytes():
    buffer = BytesIO()
    Image.new('RGB', (1, 1), color='green').save(buffer, format='PNG')
    return buffer.getvalue()


VALID_PNG_BYTES = _valid_png_bytes()
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='wastemanagement-users-tests-')


class RegisterApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_can_register(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': ' citizen1 ',
                'email': 'CITIZEN@example.com',
                'first_name': 'Citizen',
                'last_name': 'User',
                'phone_number': '+234 801 234 5678',
                'password': 'SecurePass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['role'], 'citizen')
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.first()
        self.assertEqual(user.username, 'citizen1')
        self.assertEqual(user.email, 'citizen@example.com')

    def test_duplicate_email_is_rejected(self):
        get_user_model().objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            password='SecurePass123!',
        )

        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'citizen2',
                'email': 'citizen@example.com',
                'first_name': 'Citizen',
                'last_name': 'Two',
                'phone_number': '123456789',
                'password': 'SecurePass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'citizen3',
                'email': 'citizen3@example.com',
                'first_name': 'Citizen',
                'last_name': 'Three',
                'phone_number': '123456789',
                'password': 'password',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)

    def test_user_can_obtain_token(self):
        get_user_model().objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            password='SecurePass123!',
        )

        response = self.client.post(
            '/api/auth/token/',
            {
                'username': 'citizen1',
                'password': 'SecurePass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_can_store_device_token(self):
        user = get_user_model().objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user)

        response = self.client.post(
            '/api/auth/device-token/',
            {
                'token': 'fcm-token-123',
                'platform': 'android',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(DeviceToken.objects.count(), 1)
        self.assertEqual(DeviceToken.objects.first().user, user)

    def test_existing_device_token_is_updated_for_current_user(self):
        first_user = get_user_model().objects.create_user(
            username='citizen2',
            email='citizen2@example.com',
            password='SecurePass123!',
        )
        second_user = get_user_model().objects.create_user(
            username='citizen3',
            email='citizen3@example.com',
            password='SecurePass123!',
        )
        DeviceToken.objects.create(
            user=first_user,
            token='fcm-token-reused',
            platform='android',
        )
        self.client.force_authenticate(second_user)

        response = self.client.post(
            '/api/auth/device-token/',
            {'token': 'fcm-token-reused', 'platform': 'android'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(DeviceToken.objects.get(token='fcm-token-reused').user, second_user)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            first_name='Citizen',
            last_name='One',
            phone_number='+2348012345678',
            password='SecurePass123!',
        )

    def test_authenticated_user_can_fetch_profile_photo_field(self):
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_photo', response.data)

    def test_authenticated_user_can_update_profile_fields(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            '/api/auth/me/',
            {
                'username': 'citizen-renamed',
                'email': 'updated@example.com',
                'first_name': 'Updated',
                'last_name': 'User',
                'phone_number': '+234 800 000 0000',
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'citizen-renamed')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.phone_number, '+234 800 000 0000')

    def test_duplicate_username_is_rejected_on_update(self):
        get_user_model().objects.create_user(
            username='citizen2',
            email='citizen2@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            '/api/auth/me/',
            {'username': 'citizen2'},
            format='multipart',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.data)

    def test_duplicate_email_is_rejected_on_update(self):
        get_user_model().objects.create_user(
            username='citizen2',
            email='citizen2@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            '/api/auth/me/',
            {'email': 'citizen2@example.com'},
            format='multipart',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_user_can_upload_profile_photo(self):
        self.client.force_authenticate(self.user)
        image = SimpleUploadedFile('profile.png', VALID_PNG_BYTES, content_type='image/png')

        response = self.client.patch(
            '/api/auth/me/',
            {'profile_photo': image},
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.profile_photo))
        self.assertIn('profile_photo', response.data)

    def test_user_can_remove_existing_profile_photo(self):
        self.user.profile_photo = SimpleUploadedFile('profile.png', VALID_PNG_BYTES, content_type='image/png')
        self.user.save()
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            '/api/auth/me/',
            {'remove_profile_photo': 'true'},
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.profile_photo))

    def test_anonymous_user_cannot_update_profile(self):
        response = self.client.patch(
            '/api/auth/me/',
            {'first_name': 'Updated'},
            format='multipart',
        )

        self.assertEqual(response.status_code, 401)
