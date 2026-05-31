from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Confirmation, WasteReport


class ReportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            password='password123',
        )
        self.admin = get_user_model().objects.create_user(
            username='admin1',
            email='admin@example.com',
            password='password123',
            is_staff=True,
            role='admin',
        )
        self.client.force_authenticate(self.user)

    def test_anonymous_user_cannot_list_reports(self):
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/reports/')

        self.assertEqual(response.status_code, 401)

    def test_user_can_create_report(self):
        image = SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg')

        response = self.client.post(
            '/api/reports/',
            {
                'description': 'Waste beside the road',
                'photo': image,
                'latitude': 4.156,
                'longitude': 9.265,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(WasteReport.objects.count(), 1)

    def test_citizen_cannot_update_report_status(self):
        report = WasteReport.objects.create(
            user=self.user,
            description='Waste beside the road',
            photo=SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg'),
            latitude=4.156,
            longitude=9.265,
        )

        response = self.client.patch(
            f'/api/reports/{report.id}/',
            {'status': WasteReport.Status.RESOLVED},
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_update_report_status(self):
        report = WasteReport.objects.create(
            user=self.user,
            description='Waste beside the road',
            photo=SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg'),
            latitude=4.156,
            longitude=9.265,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f'/api/reports/{report.id}/',
            {'status': WasteReport.Status.RESOLVED},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], WasteReport.Status.RESOLVED)
        self.assertEqual(response.data['progress_percent'], 100)

    def test_user_can_confirm_own_report(self):
        report = WasteReport.objects.create(
            user=self.user,
            description='Waste beside the road',
            photo=SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg'),
            latitude=4.156,
            longitude=9.265,
        )

        response = self.client.post(
            '/api/confirm/',
            {'report': report.id, 'is_cleared': True},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Confirmation.objects.count(), 1)

    def test_user_can_delete_own_report(self):
        report = WasteReport.objects.create(
            user=self.user,
            description='Waste beside the road',
            photo=SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg'),
            latitude=4.156,
            longitude=9.265,
        )

        response = self.client.delete(f'/api/reports/{report.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(WasteReport.objects.filter(id=report.id).exists())

    def test_user_cannot_delete_another_users_report(self):
        other_user = get_user_model().objects.create_user(
            username='citizen2',
            email='citizen2@example.com',
            password='password123',
        )
        report = WasteReport.objects.create(
            user=other_user,
            description='Waste beside the road',
            photo=SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg'),
            latitude=4.156,
            longitude=9.265,
        )

        response = self.client.delete(f'/api/reports/{report.id}/')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(WasteReport.objects.filter(id=report.id).exists())


class ReportDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='citizen1',
            email='citizen@example.com',
            password='password123',
        )
        self.admin = get_user_model().objects.create_user(
            username='admin1',
            email='admin@example.com',
            password='password123',
            is_staff=True,
            role='admin',
        )
        self.report = WasteReport.objects.create(
            user=self.user,
            description='Overflowing bin near the main road',
            photo=SimpleUploadedFile('waste.jpg', b'filecontent', content_type='image/jpeg'),
            latitude=4.156,
            longitude=9.265,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('reports-dashboard-home'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('reports-dashboard-login'), response.url)

    def test_non_admin_cannot_access_dashboard(self):
        self.client.force_authenticate(user=None)
        self.client.login(username='citizen1', password='password123')

        response = self.client.get(reverse('reports-dashboard-home'))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_dashboard(self):
        self.client.force_authenticate(user=None)
        self.client.login(username='admin1', password='password123')

        response = self.client.get(reverse('reports-dashboard-home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Waste report operations')
        self.assertContains(response, 'Overflowing bin near the main road')

    def test_admin_can_update_status_from_dashboard(self):
        self.client.force_authenticate(user=None)
        self.client.login(username='admin1', password='password123')

        response = self.client.post(
            reverse('reports-dashboard-status', args=[self.report.id]),
            {'status': WasteReport.Status.IN_PROGRESS},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, WasteReport.Status.IN_PROGRESS)
        self.assertContains(response, 'updated to In Progress')
