from django.test import TestCase
from django.urls import reverse
from hospitalapp.models import User, Nurse, NurseAvailability, NursingMessage, Bed

class NursingSuperintendentTestCase(TestCase):
    def setUp(self):
        # Create different user roles
        self.superintendent_user = User.objects.create_user(
            username='superintendent1', password='pass', role='nursing_superintendent'
        )
        self.nurse_user = User.objects.create_user(
            username='regular_nurse', password='pass', role='nurse'
        )
        self.patient_user = User.objects.create_user(
            username='patient1', password='pass', role='patient'
        )
        self.station_user = User.objects.create_user(
            username='station_icu', password='pass', role='nursing_station'
        )

        # Create initial Nurse profile for regular_nurse
        self.nurse = Nurse.objects.create(
            user=self.nurse_user,
            name='Regular Nurse Jane',
            phone='1234567890',
            email='jane@hosp.com',
            qualification='B.Sc',
            assigned_ward='General Ward',
            is_head_nurse=False
        )
        NurseAvailability.objects.create(nurse=self.nurse, status='Available')

    def test_dashboard_access_control(self):
        dashboard_url = reverse('nursing_superintendent_dashboard')

        # 1. Anonymous user redirected to login
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

        # 2. Unauthorized roles (e.g. regular nurse, patient) get 403 Forbidden
        self.client.login(username='regular_nurse', password='pass')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username='patient1', password='pass')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # 3. Authorized Nursing Superintendent can access dashboard (200 OK)
        self.client.login(username='superintendent1', password='pass')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hospitalapp/nursing_superintendent/dashboard.html')

    def test_add_nurse_profile(self):
        self.client.login(username='superintendent1', password='pass')
        dashboard_url = reverse('nursing_superintendent_dashboard')

        post_data = {
            'action': 'add_nurse',
            'username': 'new_nurse',
            'password': 'Password123',
            'name': 'New Nurse Alice',
            'email': 'alice@hosp.com',
            'phone': '9876543210',
            'qualification': 'GNH',
            'assigned_ward': 'ICU',
            'is_head_nurse': 'on'
        }

        # Submit add nurse action
        response = self.client.post(dashboard_url, post_data)
        self.assertEqual(response.status_code, 302) # Redirects back to dashboard

        # Verify User and Nurse profile are created
        self.assertTrue(User.objects.filter(username='new_nurse', role='nurse').exists())
        new_nurse = Nurse.objects.filter(name='New Nurse Alice').first()
        self.assertIsNotNone(new_nurse)
        self.assertEqual(new_nurse.assigned_ward, 'ICU')
        self.assertTrue(new_nurse.is_head_nurse)
        self.assertEqual(new_nurse.qualification, 'GNH')

    def test_toggle_head_nurse_status(self):
        self.client.login(username='superintendent1', password='pass')
        dashboard_url = reverse('nursing_superintendent_dashboard')

        self.assertFalse(self.nurse.is_head_nurse)

        # Toggle to head nurse
        response = self.client.post(dashboard_url, {
            'action': 'toggle_head_nurse',
            'nurse_id': self.nurse.nurse_id
        })
        self.assertEqual(response.status_code, 302)
        self.nurse.refresh_from_db()
        self.assertTrue(self.nurse.is_head_nurse)

        # Toggle back to regular nurse
        response = self.client.post(dashboard_url, {
            'action': 'toggle_head_nurse',
            'nurse_id': self.nurse.nurse_id
        })
        self.assertEqual(response.status_code, 302)
        self.nurse.refresh_from_db()
        self.assertFalse(self.nurse.is_head_nurse)

    def test_assign_ward(self):
        self.client.login(username='superintendent1', password='pass')
        dashboard_url = reverse('nursing_superintendent_dashboard')

        self.assertEqual(self.nurse.assigned_ward, 'General Ward')

        # Change ward to ICU
        response = self.client.post(dashboard_url, {
            'action': 'assign_ward',
            'nurse_id': self.nurse.nurse_id,
            'assigned_ward': 'ICU'
        })
        self.assertEqual(response.status_code, 302)
        self.nurse.refresh_from_db()
        self.assertEqual(self.nurse.assigned_ward, 'ICU')

    def test_send_broadcast_message(self):
        self.client.login(username='superintendent1', password='pass')
        dashboard_url = reverse('nursing_superintendent_dashboard')

        post_data = {
            'action': 'send_message',
            'receiver_id': self.station_user.user_id,
            'message': 'Superintendent notice: Mandatory staff meeting at 4 PM.',
            'category': 'Urgent'
        }

        # Submit broadcast action
        response = self.client.post(dashboard_url, post_data)
        self.assertEqual(response.status_code, 302)

        # Verify message is created
        msg = NursingMessage.objects.filter(receiver=self.station_user).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender, self.superintendent_user)
        self.assertEqual(msg.category, 'Urgent')
        self.assertEqual(msg.message, 'Superintendent notice: Mandatory staff meeting at 4 PM.')
