from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from hospitalapp.models import (
    User, Patient, Doctor, Nurse, Casuality, EmergencyZone,
    EmergencyBed, EmergencyTriage, EmergencyTreatmentRecord,
    LabOrder, LabOrderItem, LabTest, RadiologyOrder, RadiologyOrderItem, RadiologyTest, Bill
)

class EmergencyZoneTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.admin_user = User.objects.create_user(username='admin_user', password='password123', role='admin')
        self.doctor_user = User.objects.create_user(username='doctor_user', password='password123', role='doctor')
        self.nurse_user = User.objects.create_user(username='nurse_user', password='password123', role='nurse')
        
        # Create Profiles
        self.patient = Patient.objects.create(
            name="Bob Brown",
            age=45,
            gender="Male",
            address="123 Emergency St",
            phone="9999999999",
            email="bob@example.com"
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            name="Dr. Gregory House",
            specialization="Emergency Medicine",
            phone="8888888888",
            email="house@example.com",
            availability="Emergency (24/7)"
        )
        self.nurse = Nurse.objects.create(
            user=self.nurse_user,
            name="Nurse Abby",
            phone="7777777777",
            email="abby@example.com",
            qualification="BSN",
            assigned_ward="General Ward"
        )
        
        # Seed Zones (Red, Orange, Yellow, Green)
        self.red_zone = EmergencyZone.objects.create(zone_name='RED', color_code='danger', priority_level=1, target_response_time=0)
        self.orange_zone = EmergencyZone.objects.create(zone_name='ORANGE', color_code='orange', priority_level=2, target_response_time=15)
        self.yellow_zone = EmergencyZone.objects.create(zone_name='YELLOW', color_code='warning', priority_level=3, target_response_time=60)
        self.green_zone = EmergencyZone.objects.create(zone_name='GREEN', color_code='success', priority_level=4, target_response_time=120)

        # Seed Beds
        self.red_bed = EmergencyBed.objects.create(bed_number='R-Test-1', zone=self.red_zone, status='Available')
        self.orange_bed = EmergencyBed.objects.create(bed_number='O-Test-1', zone=self.orange_zone, status='Available')
        
        # Create casualty case (registered patient)
        self.casualty_case = Casuality.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            priority='Medium',
            emergency_reason='Severe chest pain and shortness of breath.',
            status='Pending'
        )
        
        # Clients
        self.client_nurse = Client()
        self.client_nurse.login(username='nurse_user', password='password123')
        
        self.client_doctor = Client()
        self.client_doctor.login(username='doctor_user', password='password123')

        self.client_admin = Client()
        self.client_admin.login(username='admin_user', password='password123')

    def test_suggested_zone_logic_red(self):
        # Triggering RED (GCS <= 8)
        response = self.client_nurse.post(reverse('triage_patient', args=[self.casualty_case.id]), {
            'chief_complaint': 'Unresponsive after fall',
            'pain_score': 10,
            'bp_systolic': 110,
            'bp_diastolic': 70,
            'temperature': 98.6,
            'oxygen_level': 97,
            'heart_rate': 80,
            'respiratory_rate': 16,
            'sugar_level': 100,
            'gcs_score': 6, # RED trigger
            'notes': 'Immediate resuscitation needed'
        })
        self.assertEqual(response.status_code, 302)
        
        self.casualty_case.refresh_from_db()
        self.assertEqual(self.casualty_case.zone, self.red_zone)
        self.assertEqual(self.casualty_case.assigned_bed, self.red_bed)
        self.red_bed.refresh_from_db()
        self.assertEqual(self.red_bed.status, 'Occupied')
        self.assertEqual(self.casualty_case.status, 'Under Emergency Care')

    def test_suggested_zone_logic_orange(self):
        # Triggering ORANGE (SpO2 90-94%)
        response = self.client_nurse.post(reverse('triage_patient', args=[self.casualty_case.id]), {
            'chief_complaint': 'Shortness of breath',
            'pain_score': 8,
            'bp_systolic': 130,
            'bp_diastolic': 85,
            'temperature': 99.1,
            'oxygen_level': 92, # ORANGE trigger
            'heart_rate': 95,
            'respiratory_rate': 22,
            'sugar_level': 110,
            'gcs_score': 15,
            'notes': 'Struggling to breathe'
        })
        self.assertEqual(response.status_code, 302)
        
        self.casualty_case.refresh_from_db()
        self.assertEqual(self.casualty_case.zone, self.orange_zone)
        self.assertEqual(self.casualty_case.assigned_bed, self.orange_bed)

    def test_suggested_zone_logic_yellow(self):
        # Triggering YELLOW (Temp > 102F)
        response = self.client_nurse.post(reverse('triage_patient', args=[self.casualty_case.id]), {
            'chief_complaint': 'High fever and chills',
            'pain_score': 4,
            'bp_systolic': 120,
            'bp_diastolic': 80,
            'temperature': 103.5, # YELLOW trigger
            'oxygen_level': 98,
            'heart_rate': 90,
            'respiratory_rate': 18,
            'sugar_level': 95,
            'gcs_score': 15,
            'notes': 'Fever for 3 days'
        })
        self.assertEqual(response.status_code, 302)
        
        self.casualty_case.refresh_from_db()
        self.assertEqual(self.casualty_case.zone, self.yellow_zone)
        # No bed available in Yellow, so status should be 'Triage Completed'
        self.assertEqual(self.casualty_case.assigned_bed, None)
        self.assertEqual(self.casualty_case.status, 'Triage Completed')

    def test_doctor_evaluation_and_disposition(self):
        # Simulate triage completion first
        triage = EmergencyTriage.objects.create(
            patient=self.patient,
            casualty_case=self.casualty_case,
            triage_nurse=self.nurse,
            chief_complaint='Severe back pain',
            pain_score=9,
            triage_zone=self.red_zone,
            priority_level='Critical',
            bp_systolic=120,
            bp_diastolic=80,
            temperature=98.6,
            oxygen_level=98,
            heart_rate=72,
            respiratory_rate=16,
            gcs_score=15
        )
        self.casualty_case.triage = triage
        self.casualty_case.zone = self.red_zone
        self.casualty_case.assigned_bed = self.red_bed
        self.casualty_case.status = 'Under Emergency Care'
        self.casualty_case.save()
        
        self.red_bed.status = 'Occupied'
        self.red_bed.save()

        # 1. Doctor writes clinical notes
        response = self.client_doctor.post(reverse('emergency_doctor_evaluate', args=[self.casualty_case.id]), {
            'diagnosis': 'Acute Renal Colic',
            'treatment_notes': 'Administered IV analgesia and fluids.'
        })
        self.assertEqual(response.status_code, 302)
        
        record = EmergencyTreatmentRecord.objects.filter(casualty_case=self.casualty_case).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnosis, 'Acute Renal Colic')

        # 2. Doctor disposes the patient (Discharged)
        response = self.client_doctor.get(reverse('emergency_disposition', args=[self.casualty_case.id, 'discharge']))
        self.assertEqual(response.status_code, 302)
        
        self.casualty_case.refresh_from_db()
        self.assertEqual(self.casualty_case.status, 'Discharged')
        self.assertIsNone(self.casualty_case.assigned_bed)
        
        self.red_bed.refresh_from_db()
        self.assertEqual(self.red_bed.status, 'Available') # Freed up successfully

    def test_stat_orders_and_prioritization(self):
        # Create Lab and Radiology Tests
        lab_test = LabTest.objects.create(name="Urgent CBC", price=250.00, active=True)
        rad_test = RadiologyTest.objects.create(name="STAT Chest X-Ray", price=800.00, active=True)
        
        # 1. Order STAT Lab
        response = self.client_doctor.post(reverse('emergency_create_lab_order', args=[self.casualty_case.id]), {
            'tests': [lab_test.id],
            'clinical_notes': 'R/O sepsis'
        })
        self.assertEqual(response.status_code, 302)
        
        order = LabOrder.objects.filter(patient=self.patient, urgency='STAT').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.urgency, 'STAT')

        # 2. Order STAT Radiology
        response = self.client_doctor.post(reverse('emergency_create_radiology_order', args=[self.casualty_case.id]), {
            'tests': [rad_test.id],
            'clinical_notes': 'STAT ruling out thoracic trauma'
        })
        self.assertEqual(response.status_code, 302)
        
        rad_order = RadiologyOrder.objects.filter(patient=self.patient, urgency='STAT').first()
        self.assertIsNotNone(rad_order)
        self.assertEqual(rad_order.urgency, 'STAT')

        # 3. Verify STAT items appear sorted at the top of the lab dashboard
        # Create a routine order afterwards to check ordering
        routine_order = LabOrder.objects.create(
            patient=self.patient,
            ordered_by=self.doctor,
            urgency='Routine',
            status='Pending'
        )
        
        response = self.client_admin.get(reverse('laboratory_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        pending_orders = list(response.context['pending_orders'])
        # Order should be: STAT order first, then Routine order
        self.assertEqual(pending_orders[0].urgency, 'STAT')
