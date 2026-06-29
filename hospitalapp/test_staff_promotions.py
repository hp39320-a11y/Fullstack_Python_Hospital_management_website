from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from hospitalapp.models import Nurse, Bed

User = get_user_model()

class StaffPromotionsTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_user', password='password', role='admin'
        )
        self.nurse_user = User.objects.create_user(
            username='nurse_test', password='password', role='nurse'
        )
        self.nurse = Nurse.objects.create(
            user=self.nurse_user,
            name='Test Nurse',
            phone='1234567890',
            email='testnurse@example.com',
            qualification='B.Sc',
            assigned_ward='General Ward',
            is_head_nurse=False
        )

    def test_add_inventory_manager(self):
        self.client.login(username='admin_user', password='password')
        url = reverse('add_inventory_manager')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'username': 'inv_manager_new',
            'email': 'inv@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)  # Redirects to manage_staff

        user = User.objects.get(username='inv_manager_new')
        self.assertEqual(user.role, 'inventory_manager')

    def test_promote_and_demote_flows(self):
        self.client.login(username='admin_user', password='password')
        url = reverse('manage_nurses')

        # 1. Start as Staff Nurse
        self.assertFalse(self.nurse.is_head_nurse)

        # 2. Promote Staff Nurse to Head Nurse
        response = self.client.post(url, {
            'action': 'promote_head_nurse',
            'nurse_id': self.nurse.nurse_id,
        })
        self.assertEqual(response.status_code, 302)
        self.nurse.refresh_from_db()
        self.assertTrue(self.nurse.is_head_nurse)

        # 3. Demote Head Nurse back to Staff Nurse
        response = self.client.post(url, {
            'action': 'demote_staff_nurse',
            'nurse_id': self.nurse.nurse_id,
        })
        self.assertEqual(response.status_code, 302)
        self.nurse.refresh_from_db()
        self.assertFalse(self.nurse.is_head_nurse)

        # 4. Promote again to Head Nurse to test Superintendent promotion
        self.nurse.is_head_nurse = True
        self.nurse.save()

        # 5. Promote Head Nurse to Nursing Superintendent
        response = self.client.post(url, {
            'action': 'promote_superintendent',
            'nurse_id': self.nurse.nurse_id,
        })
        self.assertEqual(response.status_code, 302)
        self.nurse_user.refresh_from_db()
        self.assertEqual(self.nurse_user.role, 'nursing_superintendent')

        # 6. Demote Nursing Superintendent back to Head Nurse
        response = self.client.post(url, {
            'action': 'demote_superintendent',
            'user_id': self.nurse_user.user_id,
        })
        self.assertEqual(response.status_code, 302)
        self.nurse_user.refresh_from_db()
        self.assertEqual(self.nurse_user.role, 'nurse')
        self.nurse.refresh_from_db()
        self.assertTrue(self.nurse.is_head_nurse)

