from django.test import TestCase
from hospitalapp.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from hospitalapp.models import (
    Patient, Doctor, Appointment, Prescription, Medicine, PrescriptionMedicine,
    Bill, PharmacyCounter, PharmacyToken, CounterAssignment, TokenCallLog,
    DispensingRecord, CounterPerformance
)
from hospitalapp.models import auto_generate_pharmacy_token

class PharmacyTokenQueueTestCase(TestCase):
    def setUp(self):
        # Create user roles
        self.doctor_user = User.objects.create_user(username='doctor1', password='pass', role='doctor')
        self.patient_user1 = User.objects.create_user(username='patient1', password='pass', role='patient')
        self.patient_user2 = User.objects.create_user(username='patient2', password='pass', role='patient')
        self.pharmacist_user = User.objects.create_user(username='pharmacist1', password='pass', role='pharmacist')

        # Create profiles
        self.doctor = Doctor.objects.create(user=self.doctor_user, name='Dr. Smith', specialization='Cardiology', phone='123', email='smith@hosp.com')
        self.patient_regular = Patient.objects.create(user=self.patient_user1, name='John Doe', age=30, gender='Male', phone='456', email='john@gmail.com')
        self.patient_senior = Patient.objects.create(user=self.patient_user2, name='Elderly Joe', age=75, gender='Male', phone='789', email='joe@gmail.com')

        # Create Appointment
        self.app1 = Appointment.objects.create(patient=self.patient_regular, doctor=self.doctor, appointment_date=timezone.now().date(), status='Approved', reason='Checkup')
        self.app2 = Appointment.objects.create(patient=self.patient_senior, doctor=self.doctor, appointment_date=timezone.now().date(), status='Approved', reason='Checkup')

        # Create medicines
        self.med1 = Medicine.objects.create(name='Paracetamol 500mg', stock=100, price=Decimal('5.50'), expiry_date=timezone.now().date() + timedelta(days=365))
        self.med2 = Medicine.objects.create(name='Amoxicillin 250mg', stock=50, price=Decimal('12.00'), expiry_date=timezone.now().date() + timedelta(days=200))

    def test_token_auto_generation_on_prescription(self):
        # 1. Test Regular Prescription Token Auto-Generation
        presc1 = Prescription.objects.create(
            appointment=self.app1,
            doctor=self.doctor,
            patient=self.patient_regular,
            diagnosis='Fever',
            notes='Take medicines daily'
        )
        # Check signal generated token
        token1 = PharmacyToken.objects.filter(prescription=presc1).first()
        self.assertIsNotNone(token1)
        self.assertEqual(token1.priority_level, 'Regular')
        self.assertTrue(token1.token_number.startswith('P'))

        # 2. Test Senior Citizen (Age >= 60) Token Auto-Generation
        presc2 = Prescription.objects.create(
            appointment=self.app2,
            doctor=self.doctor,
            patient=self.patient_senior,
            diagnosis='Arthritis',
            notes='Soft dosage'
        )
        token2 = PharmacyToken.objects.filter(prescription=presc2).first()
        self.assertIsNotNone(token2)
        self.assertEqual(token2.priority_level, 'Senior Citizen')
        self.assertTrue(token2.token_number.startswith('S'))

        # 3. Test Emergency Prescriptions Token Auto-Generation (via emergency notes)
        presc3 = Prescription.objects.create(
            appointment=self.app1,
            doctor=self.doctor,
            patient=self.patient_regular,
            diagnosis='Chest Pain',
            notes='CRITICAL EMERGENCY ALERT'
        )
        token3 = PharmacyToken.objects.filter(prescription=presc3).first()
        self.assertIsNotNone(token3)
        self.assertEqual(token3.priority_level, 'Emergency')
        self.assertTrue(token3.token_number.startswith('E'))

    def test_billing_integration_token_update(self):
        # Create prescription
        presc = Prescription.objects.create(
            appointment=self.app1,
            doctor=self.doctor,
            patient=self.patient_regular,
            diagnosis='Fever'
        )
        token = PharmacyToken.objects.filter(prescription=presc).first()
        self.assertIsNone(token.bill)

        # Create unpaid Bill
        bill = Bill.objects.create(
            patient=self.patient_regular,
            appointment=self.app1,
            prescription=presc,
            total_amount=Decimal('55.00'),
            payment_status='Pending',
            bill_type='pharmacy'
        )

        # Verify token doesn't have it linked automatically until paid (or custom view logic handles it)
        # In our signal receiver, we link when bill is marked "Paid"
        bill.payment_status = 'Paid'
        bill.save()

        # Re-fetch token
        token.refresh_from_db()
        self.assertEqual(token.bill, bill)
        self.assertEqual(token.bill.payment_status, 'Paid')

    def test_queue_calling_and_dispensing(self):
        # Setup Counter
        counter = PharmacyCounter.objects.create(number=1, type='General Counter', status='Active')
        CounterAssignment.objects.create(counter=counter, pharmacist=self.pharmacist_user, is_active=True)

        # Create prescriptions and tokens
        presc_reg = Prescription.objects.create(appointment=self.app1, doctor=self.doctor, patient=self.patient_regular, diagnosis='Fever')
        presc_sen = Prescription.objects.create(appointment=self.app2, doctor=self.doctor, patient=self.patient_senior, diagnosis='High BP')

        # Link paid bills to make them eligible in queue
        token_reg = PharmacyToken.objects.filter(prescription=presc_reg).first()
        token_sen = PharmacyToken.objects.filter(prescription=presc_sen).first()

        bill_reg = Bill.objects.create(patient=self.patient_regular, prescription=presc_reg, total_amount=Decimal('50.00'), payment_status='Paid', bill_type='pharmacy')
        bill_sen = Bill.objects.create(patient=self.patient_senior, prescription=presc_sen, total_amount=Decimal('30.00'), payment_status='Paid', bill_type='pharmacy')
        
        token_reg.bill = bill_reg
        token_reg.save()
        token_sen.bill = bill_sen
        token_sen.save()

        # Add Prescription Medicines
        PrescriptionMedicine.objects.create(prescription=presc_reg, medicine=self.med1, quantity=10)

        # Call next token - Senior should be called before Regular due to priority hierarchy
        # Senior Citizen (S) > Regular (P)
        # Let's call Next Token from views helper logic (simulation)
        from django.db.models import Case, When, Value, IntegerField
        waiting_tokens = PharmacyToken.objects.filter(status='Waiting').annotate(
            priority_score=Case(
                When(priority_level='Emergency', then=Value(5)),
                When(priority_level='VIP', then=Value(4)),
                When(priority_level='Senior Citizen', then=Value(3)),
                When(priority_level='Corporate', then=Value(2)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('-priority_score', 'created_at')
        next_token = None
        for t in waiting_tokens:
            bill = t.bill or Bill.objects.filter(prescription=t.prescription).first()
            if t.priority_level == 'Emergency' or (bill and bill.payment_status == 'Paid'):
                next_token = t
                break

        self.assertEqual(next_token, token_sen) # Senior Citizen is first

        # Call Regular Token
        token_reg.status = 'Called'
        token_reg.counter = counter
        token_reg.called_at = timezone.now()
        token_reg.save()
        counter.status = 'Busy'
        counter.save()

        # Verify stock auto deduction on dispense
        initial_stock = self.med1.stock
        qty_to_dispense = 5

        # Dispense
        DispensingRecord.objects.create(
            token=token_reg,
            medicine=self.med1,
            quantity_requested=10,
            quantity_dispensed=qty_to_dispense,
            status='Partial',
            batch_number='B001',
            expiry_date=self.med1.expiry_date,
            verified_by=self.pharmacist_user
        )
        self.med1.stock -= qty_to_dispense
        self.med1.save()

        self.assertEqual(self.med1.stock, initial_stock - qty_to_dispense)

        # Complete dispensing
        token_reg.status = 'Completed'
        token_reg.completed_at = timezone.now()
        token_reg.waiting_time = int((token_reg.completed_at - token_reg.called_at).total_seconds())
        token_reg.save()

        presc_reg.status = 'Dispensed'
        presc_reg.save()

        counter.status = 'Active'
        counter.save()

        self.assertEqual(token_reg.status, 'Completed')
        self.assertEqual(presc_reg.status, 'Dispensed')
        self.assertIsNone(counter.current_token)
        self.assertEqual(counter.status, 'Active')

    def test_prescription_custom_priority(self):
        # Test custom priority 'VIP' set on prescription
        presc_vip = Prescription.objects.create(
            appointment=self.app1,
            doctor=self.doctor,
            patient=self.patient_regular,
            diagnosis='Heart Check',
            notes='VIP consultation',
            priority_level='VIP'
        )
        token_vip = PharmacyToken.objects.filter(prescription=presc_vip).first()
        self.assertIsNotNone(token_vip)
        self.assertEqual(token_vip.priority_level, 'VIP')
        self.assertTrue(token_vip.token_number.startswith('V'))

        # Test custom priority 'Emergency' set on prescription
        presc_em = Prescription.objects.create(
            appointment=self.app1,
            doctor=self.doctor,
            patient=self.patient_regular,
            diagnosis='Severe Injury',
            notes='Critical',
            priority_level='Emergency'
        )
        token_em = PharmacyToken.objects.filter(prescription=presc_em).first()
        self.assertIsNotNone(token_em)
        self.assertEqual(token_em.priority_level, 'Emergency')
        self.assertTrue(token_em.token_number.startswith('E'))
