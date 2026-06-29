from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from hospitalapp.models import (
    User, Patient, Doctor, Nurse, Admission, Bed, EmergencyAlert,
    NursingStationRequest, NursingTaskAssignment, NurseAvailability,
    NursingMessage, NursingAuditLog
)

class NursingStationTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.admin_user = User.objects.create_user(username='admin_user', password='password123', role='admin')
        self.doctor_user = User.objects.create_user(username='doctor_user', password='password123', role='doctor')
        self.nurse_user = User.objects.create_user(username='nurse_user', password='password123', role='nurse')
        self.ns_user = User.objects.create_user(username='ns_user', password='password123', role='nursing_station')
        self.patient_user = User.objects.create_user(username='patient_user', password='password123', role='patient')

        # Create Profiles
        self.patient = Patient.objects.create(
            user=self.patient_user,
            name="Alice Smith",
            age=28,
            gender="Female",
            address="456 Avenue",
            phone="1122334455",
            email="alice@example.com"
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            name="Dr. John Carter",
            specialization="General Physician",
            phone="9988776655",
            email="carter@example.com",
            availability="Mon-Sat (9 AM - 5 PM)"
        )
        self.nurse = Nurse.objects.create(
            user=self.nurse_user,
            name="Nurse Hathaway",
            phone="8877665544",
            email="hathaway@example.com",
            qualification="BSN",
            assigned_ward="General Ward"
        )

        # Ensure availability entry exists
        self.nurse_availability, _ = NurseAvailability.objects.get_or_create(nurse=self.nurse)

        # Clients for testing requests
        self.client_doctor = Client()
        self.client_doctor.login(username='doctor_user', password='password123')

        self.client_ns = Client()
        self.client_ns.login(username='ns_user', password='password123')

        self.client_nurse = Client()
        self.client_nurse.login(username='nurse_user', password='password123')

    def test_role_based_access(self):
        # Nursing Station Dashboard: Allowed for nursing_station
        response = self.client_ns.get(reverse('nursing_station_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Forbidden for Doctor
        response = self.client_doctor.get(reverse('nursing_station_dashboard'))
        self.assertEqual(response.status_code, 403)  # Should return 403 Forbidden because of @role_required

    def test_nursing_station_workflow(self):
        # 1. Doctor creates a request
        response = self.client_doctor.post(reverse('doctor_nursing_requests'), {
            'request_type': 'Vitals Check',
            'patient_type': 'OP',
            'notes': 'Check temperature and BP immediately.'
        })
        self.assertEqual(response.status_code, 302) # Redirect back on success
        
        # Verify request creation
        n_req = NursingStationRequest.objects.filter(doctor=self.doctor, request_type='Vitals Check').first()
        self.assertIsNotNone(n_req)
        self.assertEqual(n_req.status, 'Pending')

        # 2. Nursing station assigns a nurse to the request
        response = self.client_ns.post(reverse('nursing_station_dashboard'), {
            'action': 'assign_nurse',
            'request_id': n_req.id,
            'nurse_id': self.nurse.nurse_id,
            'notes': 'Please check patient vitals.'
        })
        self.assertEqual(response.status_code, 302)

        # Check request status updated
        n_req.refresh_from_db()
        self.assertEqual(n_req.status, 'Assigned')

        # Check assignment created
        assignment = NursingTaskAssignment.objects.filter(request=n_req, nurse=self.nurse).first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.status, 'Assigned')

        # Check nurse availability is Busy
        self.nurse_availability.refresh_from_db()
        self.assertEqual(self.nurse_availability.status, 'Busy')

        # 3. Nurse accepts the task
        response = self.client_nurse.post(reverse('nurse_tasks'), {
            'action': 'accept',
            'assignment_id': assignment.id
        })
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Accepted')

        # 4. Nurse starts the task
        response = self.client_nurse.post(reverse('nurse_tasks'), {
            'action': 'start',
            'assignment_id': assignment.id
        })
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'In Progress')

        # 5. Nurse completes the task
        response = self.client_nurse.post(reverse('nurse_tasks'), {
            'action': 'complete',
            'assignment_id': assignment.id,
            'completion_notes': 'Vitals normal: BP 120/80, Temp 98.6.'
        })
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Completed')
        self.assertGreater(assignment.duration, 0)

        # Check nurse availability is back to Available
        self.nurse_availability.refresh_from_db()
        self.assertEqual(self.nurse_availability.status, 'Available')

    def test_emergency_escalation_and_resolution(self):
        # 1. Broadcast an emergency alert
        response = self.client_ns.post(reverse('nursing_station_dashboard'), {
            'action': 'escalate_emergency',
            'alert_type': 'Code Blue',
            'alert_message': 'Code Blue in General Ward Room 101'
        })
        self.assertEqual(response.status_code, 302)

        # Verify alert created
        alert = EmergencyAlert.objects.filter(alert_type='Code Blue', is_resolved=False).first()
        self.assertIsNotNone(alert)

        # 2. Allocate Nurse to Emergency Alert
        response = self.client_ns.post(reverse('nursing_station_dashboard'), {
            'action': 'allocate_emergency_nurse',
            'alert_id': alert.id,
            'nurse_id': self.nurse.nurse_id
        })
        self.assertEqual(response.status_code, 302)

        # Verify nurse availability is Emergency Duty
        self.nurse_availability.refresh_from_db()
        self.assertEqual(self.nurse_availability.status, 'Emergency Duty')
        self.assertEqual(self.nurse_availability.current_assignment, f"EMERGENCY: Code Blue (#{alert.id})")

        # 3. Resolve Emergency Alert
        response = self.client_ns.post(reverse('nursing_station_dashboard'), {
            'action': 'resolve_emergency',
            'alert_id': alert.id,
            'emergency_log': 'Patient resuscitated and stabilized.'
        })
        self.assertEqual(response.status_code, 302)

        alert.refresh_from_db()
        self.assertTrue(alert.is_resolved)
        self.assertIsNotNone(alert.response_time)

        # Verify nurse availability returned to Available
        self.nurse_availability.refresh_from_db()
        self.assertEqual(self.nurse_availability.status, 'Available')
        self.assertIsNone(self.nurse_availability.current_assignment)
