from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from hospitalapp.models import (
    Patient, Doctor, Admission, LabOrder, LabTest, LabOrderItem,
    RadiologyOrder, RadiologyTest, RadiologyOrderItem, Bill, IPBill, IPCharge
)
from hospitalapp.views import recalculate_ip_bill

class InpatientBillingMergeTestCase(TestCase):
    def setUp(self):
        # Create Patient
        self.patient = Patient.objects.create(
            name="John Doe",
            age=35,
            gender="Male",
            address="123 Street",
            phone="1234567890",
            email="john@example.com"
        )
        
        # Create Doctor
        self.doctor = Doctor.objects.create(
            name="Dr. Smith",
            specialization="General Medicine",
            phone="9876543210",
            email="smith@example.com",
            availability="9AM-5PM"
        )
        
        # Create Admission (General Ward)
        self.admission = Admission.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            ward_type="General Ward",
            reason="Observation",
            status="Admitted",
            admission_date=timezone.now()
        )
        
        # Create Lab Test and Order
        self.lab_test = LabTest.objects.create(
            name="Complete Blood Count",
            category="Blood",
            price=Decimal("1000.00"),
            active=True
        )
        self.lab_order = LabOrder.objects.create(
            patient=self.patient,
            ordered_by=self.doctor,
            status="Pending"
        )
        self.lab_order_item = LabOrderItem.objects.create(
            order=self.lab_order,
            test=self.lab_test
        )
        self.lab_bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal("1000.00"),
            bill_type="laboratory",
            payment_status="Pending",
            lab_order=self.lab_order
        )
        
        # Create Radiology Test and Order
        self.radiology_test = RadiologyTest.objects.create(
            name="Chest X-Ray",
            price=Decimal("1200.00"),
            description="Lungs scan",
            active=True
        )
        self.radiology_order = RadiologyOrder.objects.create(
            patient=self.patient,
            ordered_by=self.doctor,
            status="Pending"
        )
        self.radiology_order_item = RadiologyOrderItem.objects.create(
            order=self.radiology_order,
            test=self.radiology_test
        )
        self.radiology_bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal("1200.00"),
            bill_type="radiology",
            payment_status="Pending",
            radiology_order=self.radiology_order
        )

    def test_recalculate_ip_bill_merges_bills(self):
        # Trigger billing recalculation
        recalculate_ip_bill(self.admission)
        
        # Verify laboratory charge is created in IPCharge
        lab_charge = IPCharge.objects.filter(
            admission=self.admission,
            charge_type='Laboratory Charge',
            pharmacy_bill=self.lab_bill
        ).first()
        self.assertIsNotNone(lab_charge)
        self.assertEqual(lab_charge.amount, Decimal("1000.00"))
        
        # Verify lab order is now linked to admission
        self.lab_order.refresh_from_db()
        self.assertEqual(self.lab_order.admission, self.admission)
        
        # Verify radiology charge is created in IPCharge
        radiology_charge = IPCharge.objects.filter(
            admission=self.admission,
            charge_type='Radiology Charge',
            pharmacy_bill=self.radiology_bill
        ).first()
        self.assertIsNotNone(radiology_charge)
        self.assertEqual(radiology_charge.amount, Decimal("1200.00"))
        
        # Verify radiology order is now linked to admission
        self.radiology_order.refresh_from_db()
        self.assertEqual(self.radiology_order.admission, self.admission)
        
        # Verify IPBill totals
        ip_bill = IPBill.objects.get(admission=self.admission)
        
        # Room Charge (500) + Nursing Charge (300) + Lab (1000) + Radiology (1200) = 3000
        expected_subtotal = Decimal("3000.00")
        self.assertEqual(ip_bill.subtotal, expected_subtotal)
        
        expected_gst = expected_subtotal * Decimal("0.18")
        self.assertEqual(ip_bill.gst, expected_gst)
        
        expected_grand_total = expected_subtotal + expected_gst
        self.assertEqual(ip_bill.grand_total, expected_grand_total)


from django.contrib.auth import get_user_model
from django.urls import reverse
from hospitalapp.models import Casuality, CasualityReferral, User

class CasualtyAdmissionTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        # Create user accounts
        self.emergency_user = User.objects.create_user(username="em_doc", password="password", role="doctor")
        self.specialist_user = User.objects.create_user(username="spec_doc", password="password", role="doctor")
        self.other_user = User.objects.create_user(username="other_doc", password="password", role="doctor")

        # Create Doctor models
        self.em_doctor = Doctor.objects.create(
            user=self.emergency_user,
            name="Dr. Emergency",
            specialization="Emergency Medicine",
            phone="1111",
            email="em@example.com",
            availability="Always"
        )
        self.spec_doctor = Doctor.objects.create(
            user=self.specialist_user,
            name="Dr. Specialist",
            specialization="Orthopedics",
            phone="2222",
            email="spec@example.com",
            availability="Always"
        )
        self.other_doctor = Doctor.objects.create(
            user=self.other_user,
            name="Dr. Other",
            specialization="Cardiology",
            phone="3333",
            email="other@example.com",
            availability="Always"
        )

        # Create Patient
        self.patient = Patient.objects.create(
            name="Emergency Patient",
            age=40,
            gender="Male",
            address="Street Address",
            phone="5555",
            email="pat@example.com"
        )

        # Create Casualty case
        self.casualty = Casuality.objects.create(
            patient=self.patient,
            doctor=self.em_doctor,
            priority="High",
            emergency_reason="Fracture",
            status="Referred"
        )

        # Create Referral
        self.referral = CasualityReferral.objects.create(
            casualty=self.casualty,
            referred_doctor=self.spec_doctor,
            referred_by=self.em_doctor,
            status="Accepted",
            notes="Please evaluate leg fracture"
        )

    def test_casualty_admission_by_referred_doctor(self):
        # Log in as specialist doctor
        self.client.login(username="spec_doc", password="password")
        
        # Get admit page
        url = reverse('doctor_admit_casuality', args=[self.casualty.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Submit admission request
        post_data = {
            'ward_type': 'General Ward',
            'reason': 'Requires traction'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302) # Redirects to emergency dashboard

        # Verify admission was requested under spec_doctor
        admission = Admission.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(admission)
        self.assertEqual(admission.doctor, self.spec_doctor)
        self.assertEqual(admission.status, 'Pending')

    def test_casualty_admission_by_unauthorized_doctor(self):
        # Log in as other doctor who is not in care team
        self.client.login(username="other_doc", password="password")
        
        url = reverse('doctor_admit_casuality', args=[self.casualty.id])
        response = self.client.get(url)
        # Should redirect back to dashboard due to lack of authorization
        self.assertEqual(response.status_code, 302)

        post_data = {
            'ward_type': 'General Ward',
            'reason': 'Unauthorized admission'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        
        # No admission request should have been created
        self.assertFalse(Admission.objects.filter(patient=self.patient).exists())

    def test_receptionist_approves_admission_adds_specialist_to_care_team(self):
        # Create receptionist user
        User = get_user_model()
        recept_user = User.objects.create_user(username="recept", password="password", role="receptionist")

        # Change casualty status to 'Triage Completed'
        self.casualty.status = 'Triage Completed'
        self.casualty.save()

        # Specialist doctor submits admission request
        self.client.login(username="spec_doc", password="password")
        url_admit = reverse('doctor_admit_casuality', args=[self.casualty.id])
        self.client.post(url_admit, {'ward_type': 'General Ward', 'reason': 'Fracture care'})

        admission = Admission.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(admission)
        self.assertEqual(admission.status, 'Pending')

        # Log in as receptionist
        self.client.login(username="recept", password="password")

        # Get a Bed
        from hospitalapp.models import Bed
        bed = Bed.objects.create(bed_number="BED-100", ward_type="General Ward", status="Available")

        # Approve admission
        url_approve = reverse('approve_admission', args=[admission.admission_id])
        post_data = {
            'ward_type': 'General Ward',
            'bed_id': bed.id
        }
        response = self.client.post(url_approve, post_data)
        self.assertEqual(response.status_code, 302)

        # Verify admission status is Admitted
        admission.refresh_from_db()
        self.assertEqual(admission.status, 'Admitted')

        # Verify casualty status is Admitted
        self.casualty.refresh_from_db()
        self.assertEqual(self.casualty.status, 'Admitted')

        # Verify specialist and casualty doctor are both in AdmissionConsultant care team
        from hospitalapp.models import AdmissionConsultant
        consultants = AdmissionConsultant.objects.filter(admission=admission)
        self.assertEqual(consultants.count(), 2)
        consultant_doctors = [c.doctor for c in consultants]
        self.assertIn(self.spec_doctor, consultant_doctors)
        self.assertIn(self.em_doctor, consultant_doctors)

from unittest.mock import patch

class ConsolidatedBillingAndPaymentsTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.doctor_user = User.objects.create_user(
            username="doc1", password="password", role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            name="Dr. test",
            specialization="General Medicine",
            phone="9999",
            email="doc@test.com"
        )
        self.patient_user = User.objects.create_user(
            username="pat1", password="password", role="patient"
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            name="Test Patient",
            age=25,
            gender="Male",
            address="Test Addr",
            phone="8888",
            email="pat@test.com"
        )
        self.lab_test1 = LabTest.objects.create(
            name="Test 1", category="Blood", price=Decimal("150.00"), active=True
        )
        self.lab_test2 = LabTest.objects.create(
            name="Test 2", category="Urine", price=Decimal("200.00"), active=True
        )

    def test_consolidated_lab_order_and_bill(self):
        self.client.login(username="doc1", password="password")
        url = reverse('doctor_create_lab_order', args=[self.patient.patient_id])
        post_data = {
            'tests': [self.lab_test1.id, self.lab_test2.id],
            'clinical_notes': 'Need both tests'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        # Verify exactly 1 LabOrder is created
        orders = LabOrder.objects.filter(patient=self.patient)
        self.assertEqual(orders.count(), 1)
        order = orders.first()
        self.assertEqual(order.items.count(), 2)

        # Verify exactly 1 Bill is created
        bills = Bill.objects.filter(patient=self.patient, bill_type='laboratory')
        self.assertEqual(bills.count(), 1)
        bill = bills.first()
        self.assertEqual(bill.total_amount, Decimal('350.00'))
        self.assertEqual(bill.lab_order, order)

    @patch('hospitalapp.views.client.order.create')
    def test_pay_multiple_bills(self, mock_create):
        # Setup mock return value for Razorpay order
        mock_create.return_value = {'id': 'order_dummy_123'}

        # Create two pending bills
        bill1 = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal("100.00"),
            bill_type="laboratory",
            payment_status="Pending"
        )
        bill2 = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal("150.00"),
            bill_type="radiology",
            payment_status="Pending"
        )

        # Login as patient to pay
        self.client.login(username="pat1", password="password")

        # Submit multiple bill payment
        url = reverse('pay_multiple_bills')
        post_data = {
            'bill_ids': [bill1.bill_id, bill2.bill_id]
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200) # Renders razorpay checkout page
        self.assertContains(response, 'order_dummy_123')

        # Verify order id is updated on bills
        bill1.refresh_from_db()
        bill2.refresh_from_db()
        self.assertEqual(bill1.razorpay_order_id, 'order_dummy_123')
        self.assertEqual(bill2.razorpay_order_id, 'order_dummy_123')

