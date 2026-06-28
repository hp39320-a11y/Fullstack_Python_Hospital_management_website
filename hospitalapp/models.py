from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, role='patient', **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser):

    user_id = models.AutoField(primary_key=True)

    username = models.CharField(
        max_length=100,
        unique=True
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    last_login = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    is_superuser = models.BooleanField(default=False)

    ROLE_CHOICES = (
        ('admin', 'admin'),
        ('doctor', 'doctor'),
        ('receptionist', 'receptionist'),
        ('pharmacist', 'pharmacist'),
        ('senior_pharmacist', 'Senior Pharmacist'),
        ('pharmacy_supervisor', 'Pharmacy Supervisor'),
        ('inventory_manager', 'Inventory Manager'),
        ('patient', 'patient'),
        ('nurse', 'nurse'),
        ('nursing_station', 'Nursing Station'),
        ('nursing_superintendent', 'Nursing Superintendent'),
        ('lab_technician', 'Lab Technician'),
        ('laboratoryist', 'Laboratoryist'),
        ('radiology_technician', 'Radiology Technician'),
        ('radiologist', 'Radiologist'),
        ('store_keeper', 'Store Keeper'),
        ('laboratory_supervisor', 'Laboratory Supervisor'),
        ('radiology_supervisor', 'Radiology Supervisor'),
        ('nursing_supervisor', 'Nursing Supervisor'),
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['role']

    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.role == 'admin'

    def has_module_perms(self, app_label):
        return self.is_superuser or self.role == 'admin'

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username


class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'patients'

class Doctor(models.Model):
    doctor_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=100)
    availability = models.CharField(max_length=100)

    class Meta:
        db_table = 'doctors'

    def save(self, *args, **kwargs):
        if self.name:
            raw_name = self.name.strip()
            cleaned = raw_name
            for prefix in ['dr. ', 'dr ', 'dr.']:
                if cleaned.lower().startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
                    break
            self.name = f"Dr. {cleaned}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='doctor_id')
    appointment_date = models.DateField()
    status = models.CharField(max_length=20, choices=(
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ), default='Pending')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointments'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Appointment.objects.get(pk=self.pk).status
            except Appointment.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        try:
            from .utils import trigger_appointment_webhook
            trigger_appointment_webhook(self, is_new=is_new, old_status=old_status)
        except Exception as e:
            print(f"Failed to trigger appointment webhook: {e}")

class Prescription(models.Model):
    prescription_id = models.AutoField(primary_key=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, db_column='appointment_id', null=True, blank=True)
    admission = models.ForeignKey('Admission', on_delete=models.CASCADE, db_column='admission_id', null=True, blank=True, related_name='discharge_prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='doctor_id')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id')
    diagnosis = models.TextField()
    medicines = models.TextField(null=True, blank=True)  # Text field as per SQL
    notes = models.TextField(null=True, blank=True)
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('Regular', 'Regular'),
            ('Senior Citizen', 'Senior Citizen'),
            ('VIP', 'VIP'),
            ('Emergency', 'Emergency'),
            ('Corporate', 'Corporate'),
        ],
        null=True,
        blank=True
    )
    status = models.CharField(
    max_length=20,
    choices=[
        ('Pending', 'Pending'),
        ('Dispensed', 'Dispensed')
    ],
    default='Pending'
)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prescriptions'

class Medicine(models.Model):
    medicine_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medicines'

    def __str__(self):
        return self.name

class PrescriptionMedicine(models.Model):
    id = models.AutoField(primary_key=True)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, db_column='prescription_id')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, db_column='medicine_id')
    quantity = models.IntegerField()
    dosage = models.CharField(max_length=100, blank=True, null=True)
    frequency = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'prescription_medicines'


class Bill(models.Model):

    BILL_TYPES = (
        ('appointment', 'Appointment'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
    )

    bill_id = models.AutoField(
        primary_key=True
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id'
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        db_column='appointment_id',
        null=True,
        blank=True
    )

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_status = models.CharField(
        max_length=20,
        choices=(
            ('Paid', 'Paid'),
            ('Unpaid', 'Unpaid'),
            ('Pending', 'Pending'),
        ),
        default='Pending'
    )

    # ADD THIS

    bill_type = models.CharField(
        max_length=20,
        choices=BILL_TYPES,
        default='appointment'
    )

    lab_order = models.ForeignKey(
        'LabOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    radiology_order = models.ForeignKey(
        'RadiologyOrder',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    razorpay_order_id = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    razorpay_payment_id = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'bills'
        

    @property
    def consulting_doctor(self):
        if self.appointment and self.appointment.doctor:
            return self.appointment.doctor
        if self.prescription and self.prescription.doctor:
            return self.prescription.doctor
        if self.lab_order and self.lab_order.ordered_by:
            return self.lab_order.ordered_by
        if self.radiology_order and self.radiology_order.ordered_by:
            return self.radiology_order.ordered_by
        return None

    def __str__(self):

        return f"Bill #{self.bill_id}"
class HospitalStats(models.Model):
    total_patients = models.IntegerField()
    total_doctors = models.IntegerField()
    total_appointments = models.IntegerField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospital_stats'


class Casuality(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='doctor_id')
    priority = models.CharField(max_length=20, choices=(
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ), default='Medium')
    emergency_reason = models.TextField()
    status = models.CharField(max_length=30, choices=(
        ('Pending', 'Pending'),
        ('Triage Completed', 'Triage Completed'),
        ('Under Emergency Care', 'Under Emergency Care'),
        ('In Observation', 'In Observation'),
        ('Stabilized', 'Stabilized'),
        ('Referred', 'Referred'),
        ('Admitted', 'Admitted'),
        ('Discharged', 'Discharged'),
        ('OT Transfer', 'OT Transfer'),
        ('ICU Transfer', 'ICU Transfer'),
    ), default='Pending')
    
    triage = models.OneToOneField('EmergencyTriage', on_delete=models.SET_NULL, null=True, blank=True, related_name='casualty_link')
    assigned_bed = models.ForeignKey('EmergencyBed', on_delete=models.SET_NULL, null=True, blank=True, related_name='allocated_casualties')
    zone = models.ForeignKey('EmergencyZone', on_delete=models.SET_NULL, null=True, blank=True, related_name='casualties')
    arrival_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'casuality'

    def __str__(self):
        return f"CAS-{self.id} | {self.patient.name}"


class CasualityReferral(models.Model):
    casualty = models.ForeignKey(
        Casuality,
        on_delete=models.CASCADE,
        related_name='referrals'
    )

    referred_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='received_referrals'
    )

    referred_by = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='sent_referrals'
    )

    status = models.CharField(
        max_length=20,
        choices=(
            ('Pending','Pending'),
            ('Accepted','Accepted'),
            ('Rejected','Rejected')
        ),
        default='Pending'
    )

    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'casuality_referrals'







class EmergencyPrescription(models.Model):

    casualty = models.ForeignKey(
        Casuality,
        on_delete=models.CASCADE,
        related_name='emergency_prescriptions'
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )

    notes = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )


class EmergencyPrescriptionItem(models.Model):

    prescription = models.ForeignKey(
        EmergencyPrescription,
        on_delete=models.CASCADE,
        related_name='items'
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE
    )

    dosage = models.CharField(max_length=50)

    frequency = models.CharField(max_length=50)

    duration_days = models.IntegerField()

    is_administered = models.BooleanField(default=False)

    administered_at = models.DateTimeField(null=True, blank=True)

    administered_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_administrations'
    )



class Bed(models.Model):
    WARD_CHOICES = (
        ('General Ward', 'General Ward'),
        ('ICU', 'ICU'),
        ('Semi Private', 'Semi Private'),
        ('Private Room', 'Private Room'),
        ('Casuality Ward', 'Casuality Ward'),
    )
    STATUS_CHOICES = (
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Maintenance', 'Maintenance'),
    )

    id = models.AutoField(primary_key=True)
    bed_number = models.CharField(max_length=20, unique=True)
    ward_type = models.CharField(max_length=50, choices=WARD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='allocated_beds')
    notes = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'beds'
        ordering = ['ward_type', 'bed_number']

    def __str__(self):
        return f"{self.bed_number} ({self.ward_type}) - {self.status}"


class Admission(models.Model):
    admission_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='doctor_id')
    admission_date = models.DateTimeField(auto_now_add=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    ward_type = models.CharField(max_length=50, choices=(
        ('General Ward', 'General Ward'),
        ('ICU', 'ICU'),
        ('Semi Private', 'Semi Private'),
        ('Private Room', 'Private Room'),
        ('Casuality Ward', 'Casuality Ward'),
    ))
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions')
    bed_number = models.CharField(max_length=20, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=(
        ('Pending', 'Pending'),
        ('Admitted', 'Admitted'),
        ('Ready For Discharge', 'Ready For Discharge'),
        ('Discharged', 'Discharged'),
        ('Rejected', 'Rejected'),
    ), default='Pending')

    class Meta:
        db_table = 'admissions'

    def __str__(self):
        return f"ADM-{self.admission_id} | {self.patient.name}"



class AdmissionConsultant(models.Model):

    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name='consultants'
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'admission_consultants'


class IPBill(models.Model):
    ip_bill_id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, db_column='admission_id')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=(
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    ), default='Pending')
    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ip_bills'

    def __str__(self):
        return f"IPBill #{self.ip_bill_id} (ADM-{self.admission.admission_id})"


class IPCharge(models.Model):
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='charges')
    charge_type = models.CharField(max_length=50, choices=(
        ('Room Charge', 'Room Charge'),
        ('Doctor Visit', 'Doctor Visit'),
        ('Nursing Charge', 'Nursing Charge'),
        ('Procedure Charge', 'Procedure Charge'),
        ('Pharmacy Bill', 'Pharmacy Bill'),
        ('Emergency Charge', 'Emergency Charge'),
        ('Laboratory Charge', 'Laboratory Charge'),
        ('Radiology Charge', 'Radiology Charge'),
    ))
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    pharmacy_bill = models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_ip_charges')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ip_charges'

    def __str__(self):
        return f"{self.charge_type} - Rs.{self.amount} for ADM-{self.admission.admission_id}"


class Nurse(models.Model):
    nurse_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=100)
    qualification = models.CharField(max_length=100)
    assigned_ward = models.CharField(max_length=50, choices=Bed.WARD_CHOICES)
    is_head_nurse = models.BooleanField(default=False)

    class Meta:
        db_table = 'nurses'

    def __str__(self):
        role_str = "Head Nurse" if self.is_head_nurse else "Nurse"
        return f"{self.name} ({role_str} - {self.assigned_ward})"


class NurseShift(models.Model):
    SHIFT_CHOICES = (
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
        ('Night', 'Night'),
    )
    ATTENDANCE_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Off', 'Off'),
    )
    id = models.AutoField(primary_key=True)
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, related_name='shifts')
    shift_date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES, default='Present')
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'nurse_shifts'


class NursePatientAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, related_name='assignments')
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='nursing_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'nurse_patient_assignments'


class VitalRecord(models.Model):
    CONDITION_CHOICES = (
        ('Stable', 'Stable'),
        ('Observation', 'Observation'),
        ('Serious', 'Serious'),
        ('Critical', 'Critical'),
    )
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='vitals', null=True, blank=True)
    casualty = models.ForeignKey(Casuality, on_delete=models.CASCADE, related_name='vitals', null=True, blank=True)
    recorded_by = models.ForeignKey(Nurse, on_delete=models.SET_NULL, null=True, blank=True)
    bp_systolic = models.IntegerField()
    bp_diastolic = models.IntegerField()
    temperature = models.DecimalField(max_digits=5, decimal_places=1)  # e.g. 98.6
    oxygen_level = models.IntegerField()  # e.g. 98 (%)
    heart_rate = models.IntegerField()  # bpm
    sugar_level = models.IntegerField(null=True, blank=True)  # mg/dL
    respiratory_rate = models.IntegerField()  # bpm
    patient_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='Stable')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vital_records'


class MedicineAdministration(models.Model):
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='administered_medicines', null=True, blank=True)
    casualty = models.ForeignKey(Casuality, on_delete=models.CASCADE, related_name='administered_medicines', null=True, blank=True)
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE)
    medicine_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=50)  # e.g. '500mg'
    administered_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)
    schedule_entry = models.ForeignKey('MedicationScheduleEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='administrations')
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True, related_name='administrations')
    quantity = models.IntegerField(default=1)
    emergency_prescription_item = models.ForeignKey(EmergencyPrescriptionItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='administrations')

    class Meta:
        db_table = 'medicine_administrations'


class NurseNote(models.Model):
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='nursing_notes', null=True, blank=True)
    casualty = models.ForeignKey(Casuality, on_delete=models.CASCADE, related_name='nursing_notes', null=True, blank=True)
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE)
    note_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nurse_notes'


class EmergencyAlert(models.Model):
    ALERT_TYPES = (
        ('Critical Patient', 'Critical Patient'),
        ('Code Blue', 'Code Blue'),
        ('Trauma', 'Trauma'),
        ('Cardiac Emergency', 'Cardiac Emergency'),
    )
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='emergency_alerts', null=True, blank=True)
    triggered_by_nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES, default='Critical Patient')
    alert_message = models.TextField()
    assigned_nurse = models.ForeignKey(Nurse, on_delete=models.SET_NULL, related_name='assigned_emergencies', null=True, blank=True)
    response_time = models.IntegerField(null=True, blank=True, help_text="Response time in seconds")
    emergency_log = models.TextField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emergency_alerts'


class Ambulance(models.Model):
    STATUS_CHOICES = (
        ('Available', 'Available'),
        ('Busy', 'Busy'),
        ('Maintenance', 'Maintenance'),
    )
    id = models.AutoField(primary_key=True)
    plate_number = models.CharField(max_length=30, unique=True)
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    vehicle_model = models.CharField(max_length=100)

    class Meta:
        db_table = 'ambulances'

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_model}) - {self.driver_name}"


class AmbulanceRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
    )
    PRIORITY_CHOICES = (
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    )
    id = models.AutoField(primary_key=True)
    caller_name = models.CharField(max_length=100)
    caller_phone = models.CharField(max_length=15)
    pickup_location = models.CharField(max_length=255)
    emergency_priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    assigned_ambulance = models.ForeignKey(Ambulance, on_delete=models.SET_NULL, null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ambulance_requests'


class NonStaff(models.Model):
    ROLE_CHOICES = (
        ('Cleaning', 'Cleaning'),
        ('Laundry', 'Laundry'),
        ('Security', 'Security'),
        ('Maintenance', 'Maintenance'),
    )
    STATUS_CHOICES = (
        ('Available', 'Available'),
        ('Busy', 'Busy'),
        ('Off-duty', 'Off-duty'),
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    duty_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')

    class Meta:
        db_table = 'non_staff'

    def __str__(self):
        return f"{self.name} ({self.role})"


class NonStaffShift(models.Model):
    SHIFT_CHOICES = (
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
        ('Night', 'Night'),
    )
    ATTENDANCE_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Off', 'Off'),
    )
    id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(NonStaff, on_delete=models.CASCADE, related_name='shifts')
    shift_date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_CHOICES, default='Present')

    class Meta:
        db_table = 'non_staff_shifts'


class CleaningLog(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    )
    id = models.AutoField(primary_key=True)
    area_name = models.CharField(max_length=100)  # Room, ICU Ward etc.
    cleaner = models.ForeignKey(NonStaff, on_delete=models.CASCADE, limit_choices_to={'role': 'Cleaning'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    logged_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cleaning_logs'


class VisitorLog(models.Model):
    id = models.AutoField(primary_key=True)
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=15)
    purpose = models.CharField(max_length=255)
    patient_name = models.CharField(max_length=100)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'visitor_logs'


class SecurityIncident(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    description = models.TextField()
    reported_by = models.CharField(max_length=100)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'security_incidents'


class LaundryLog(models.Model):
    ITEM_CHOICES = (
        ('Bedsheet', 'Bedsheet'),
        ('Uniform', 'Uniform'),
        ('Patient Clothes', 'Patient Clothes'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Washing', 'Washing'),
        ('Completed', 'Completed'),
    )
    id = models.AutoField(primary_key=True)
    item_type = models.CharField(max_length=30, choices=ITEM_CHOICES)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    received_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'laundry_logs'


class InpatientPrescription(models.Model):
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='inpatient_prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    diagnosis_notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'inpatient_prescriptions'


class InpatientPrescriptionItem(models.Model):
    ROUTE_CHOICES = (
        ('Tablet', 'Tablet'),
        ('Injection', 'Injection'),
        ('IV', 'IV'),
        ('Syrup', 'Syrup'),
        ('Drops', 'Drops'),
        ('Nebulization', 'Nebulization'),
    )
    id = models.AutoField(primary_key=True)
    prescription = models.ForeignKey(InpatientPrescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=50)        # e.g. "650mg"
    frequency = models.CharField(max_length=50)     # e.g. "OD", "BD", "TID", "QID"
    route = models.CharField(max_length=30, choices=ROUTE_CHOICES)
    duration_days = models.IntegerField()
    instructions = models.TextField(null=True, blank=True)      # e.g. "After food"
    timing = models.CharField(max_length=100, null=True, blank=True)            # e.g. "8AM-2PM-8PM"

    class Meta:
        db_table = 'inpatient_prescription_items'


class MedicationScheduleEntry(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Administered', 'Administered'),
        ('Missed', 'Missed'),
        ('Delayed', 'Delayed'),
        ('Refused', 'Refused'),
    )
    id = models.AutoField(primary_key=True)
    prescription_item = models.ForeignKey(InpatientPrescriptionItem, on_delete=models.CASCADE, related_name='schedule_entries')
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='medication_schedules')
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    administered_by = models.ForeignKey(Nurse, on_delete=models.SET_NULL, null=True, blank=True)
    administered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'medication_schedule_entries'


class ClinicalNote(models.Model):
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='clinical_notes', null=True, blank=True)
    casualty = models.ForeignKey(Casuality, on_delete=models.CASCADE, related_name='clinical_notes', null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    note_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clinical_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by Dr. {self.doctor.name} on {self.created_at}"


class InvestigationSuggestion(models.Model):
    id = models.AutoField(primary_key=True)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='investigations', null=True, blank=True)
    casualty = models.ForeignKey(Casuality, on_delete=models.CASCADE, related_name='investigations', null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    investigation_name = models.CharField(max_length=150)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=(
        ('Suggested', 'Suggested'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ), default='Suggested')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'investigation_suggestions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Investigation {self.investigation_name} suggested by Dr. {self.doctor.name}"


class CasualtyBill(models.Model):
    """
    Tracks individual charges (medicines, procedures) incurred by a casualty/emergency
    patient before they are formally admitted. When the patient is admitted, these
    charges are transferred to the main IPBill.
    """
    CHARGE_TYPE_CHOICES = (
        ('Medicine', 'Medicine'),
        ('Procedure', 'Procedure'),
        ('Consultation', 'Consultation'),
        ('Investigation', 'Investigation'),
        ('Other', 'Other'),
    )

    id = models.AutoField(primary_key=True)
    casualty = models.ForeignKey(
        Casuality,
        on_delete=models.CASCADE,
        related_name='casualty_bills'
    )
    charge_type = models.CharField(max_length=50, choices=CHARGE_TYPE_CHOICES, default='Medicine')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='casualty_charges'
    )
    administered_by = models.ForeignKey(
        Nurse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    emergency_prescription_item = models.ForeignKey(
        EmergencyPrescriptionItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    merged_to_ip = models.BooleanField(default=False)

    class Meta:
        db_table = 'casualty_bills'
        ordering = ['-created_at']

    def __str__(self):
        return f"CasualtyBill #{self.id} | {self.charge_type} - Rs.{self.amount} | CAS-{self.casualty.id}"



class LabTest(models.Model):

    name = models.CharField(
        max_length=200
    )

    category = models.CharField(
        max_length=100
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    normal_range = models.CharField(
        max_length=200,
        blank=True
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name

class LabOrder(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Collected', 'Collected'),
        ('Processing', 'Processing'),
        ('Result Entered', 'Result Entered'),
        ('Completed', 'Completed'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )

    urgency = models.CharField(
        max_length=20,
        choices=[
            ('STAT', 'STAT'),
            ('Urgent', 'Urgent'),
            ('Routine', 'Routine')
        ],
        default='Routine'
    )

    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    ordered_by = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True
    )

    clinical_notes = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lab_orders'
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_lab_orders'
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"LAB-{self.id}"

class LabOrderItem(models.Model):

    order = models.ForeignKey(
        LabOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE
    )


class LabResult(models.Model):

    order_item = models.OneToOneField(
        LabOrderItem,
        on_delete=models.CASCADE
    )

    result_value = models.TextField()

    remarks = models.TextField(
        blank=True
    )

    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    completed_at = models.DateTimeField(
        auto_now=True
    )

    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_lab_results'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def get_param_value(self, name):
        p_res = self.parameter_results.filter(parameter__name__icontains=name).first()
        if p_res:
            return p_res.value
        return ""

    @property
    def is_cbc(self):
        return 'Complete Blood Count (CBC)' in self.order_item.test.name or 'CBC' in self.order_item.test.name

    @property
    def cbc_data(self):
        if not self.is_cbc:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def cbc_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('Hemoglobin (Hb)', '13–17 g/dL (Male)', self.get_param_value('Hemoglobin')),
                ('Total WBC Count', '4,000–11,000 /µL', self.get_param_value('WBC')),
                ('Platelet Count', '1.5–4.5 lakh /µL', self.get_param_value('Platelet')),
                ('RBC Count', '4.5–5.9 million/µL', self.get_param_value('RBC')),
                ('Hematocrit (PCV)', '40–50%', self.get_param_value('Hematocrit') or self.get_param_value('PCV')),
                ('Neutrophils', '40–70%', self.get_param_value('Neutrophils')),
                ('Lymphocytes', '20–40%', self.get_param_value('Lymphocytes')),
                ('Monocytes', '2–8%', self.get_param_value('Monocytes')),
                ('Eosinophils', '1–6%', self.get_param_value('Eosinophils')),
                ('Basophils', '0–1%', self.get_param_value('Basophils')),
            ]
        data = self.cbc_data or {}
        fields = [
            ('Hemoglobin (Hb)', '13–17 g/dL (Male)', data.get('Hemoglobin (Hb)', '')),
            ('Total WBC Count', '4,000–11,000 /µL', data.get('Total WBC Count', '')),
            ('Platelet Count', '1.5–4.5 lakh /µL', data.get('Platelet Count', '')),
            ('RBC Count', '4.5–5.9 million/µL', data.get('RBC Count', '')),
            ('Hematocrit (PCV)', '40–50%', data.get('Hematocrit (PCV)', '')),
            ('Neutrophils', '40–70%', data.get('Neutrophils', '')),
            ('Lymphocytes', '20–40%', data.get('Lymphocytes', '')),
            ('Monocytes', '2–8%', data.get('Monocytes', '')),
            ('Eosinophils', '1–6%', data.get('Eosinophils', '')),
            ('Basophils', '0–1%', data.get('Basophils', '')),
        ]
        return fields


    @property
    def is_lipid(self):
        return 'Lipid Profile' in self.order_item.test.name or 'Lipid' in self.order_item.test.name

    @property
    def lipid_data(self):
        if not self.is_lipid:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def lipid_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('Total Cholesterol', '< 200 mg/dL', self.get_param_value('Total Cholesterol')),
                ('Triglycerides (TG)', '< 150 mg/dL', self.get_param_value('Triglycerides') or self.get_param_value('TG')),
                ('HDL Cholesterol', '> 40 mg/dL (M), > 50 mg/dL (F)', self.get_param_value('HDL')),
                ('LDL Cholesterol', '< 100 mg/dL', self.get_param_value('LDL')),
                ('VLDL Cholesterol', '5–40 mg/dL', self.get_param_value('VLDL')),
                ('Cholesterol/HDL Ratio', '< 5', self.get_param_value('Ratio') or self.get_param_value('Cholesterol/HDL')),
            ]
        data = self.lipid_data or {}
        fields = [
            ('Total Cholesterol', '< 200 mg/dL', data.get('Total Cholesterol', '')),
            ('Triglycerides (TG)', '< 150 mg/dL', data.get('Triglycerides (TG)', '')),
            ('HDL Cholesterol', '> 40 mg/dL (M), > 50 mg/dL (F)', data.get('HDL Cholesterol', '')),
            ('LDL Cholesterol', '< 100 mg/dL', data.get('LDL Cholesterol', '')),
            ('VLDL Cholesterol', '5–40 mg/dL', data.get('VLDL Cholesterol', '')),
            ('Cholesterol/HDL Ratio', '< 5', data.get('Cholesterol/HDL Ratio', '')),
        ]
        return fields

    @property
    def is_thyroid(self):
        return 'Thyroid Profile' in self.order_item.test.name or 'Thyroid' in self.order_item.test.name

    @property
    def thyroid_data(self):
        if not self.is_thyroid:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def thyroid_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('T3 (Triiodothyronine)', '0.8 – 2.0 ng/mL', self.get_param_value('T3')),
                ('T4 (Thyroxine)', '5.0 – 12.0 µg/dL', self.get_param_value('T4')),
                ('TSH (Thyroid Stimulating Hormone)', '0.4 – 4.5 µIU/mL', self.get_param_value('TSH')),
            ]
        data = self.thyroid_data or {}
        fields = [
            ('T3 (Triiodothyronine)', '0.8 – 2.0 ng/mL', data.get('T3 (Triiodothyronine)', '')),
            ('T4 (Thyroxine)', '5.0 – 12.0 µg/dL', data.get('T4 (Thyroxine)', '')),
            ('TSH (Thyroid Stimulating Hormone)', '0.4 – 4.5 µIU/mL', data.get('TSH (Thyroid Stimulating Hormone)', '')),
        ]
        return fields

    @property
    def is_lft(self):
        return 'Liver Function Test' in self.order_item.test.name or 'LFT' in self.order_item.test.name

    @property
    def lft_data(self):
        if not self.is_lft:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def lft_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('Total Bilirubin', '0.3 – 1.2 mg/dL', self.get_param_value('Total Bilirubin')),
                ('Direct Bilirubin', '0.0 – 0.3 mg/dL', self.get_param_value('Direct Bilirubin')),
                ('Indirect Bilirubin', '0.2 – 0.9 mg/dL', self.get_param_value('Indirect Bilirubin')),
                ('SGOT (AST)', '10 – 40 U/L', self.get_param_value('SGOT') or self.get_param_value('AST')),
                ('SGPT (ALT)', '7 – 56 U/L', self.get_param_value('SGPT') or self.get_param_value('ALT')),
                ('Alkaline Phosphatase (ALP)', '44 – 147 U/L', self.get_param_value('Alkaline Phosphatase') or self.get_param_value('ALP')),
                ('Total Protein', '6.0 – 8.3 g/dL', self.get_param_value('Total Protein')),
                ('Albumin', '3.5 – 5.0 g/dL', self.get_param_value('Albumin')),
                ('Globulin', '2.0 – 3.5 g/dL', self.get_param_value('Globulin')),
                ('A/G Ratio', '1.0 – 2.2', self.get_param_value('A/G Ratio') or self.get_param_value('Ratio')),
            ]
        data = self.lft_data or {}
        fields = [
            ('Total Bilirubin', '0.3 – 1.2 mg/dL', data.get('Total Bilirubin', '')),
            ('Direct Bilirubin', '0.0 – 0.3 mg/dL', data.get('Direct Bilirubin', '')),
            ('Indirect Bilirubin', '0.2 – 0.9 mg/dL', data.get('Indirect Bilirubin', '')),
            ('SGOT (AST)', '10 – 40 U/L', data.get('SGOT (AST)', '')),
            ('SGPT (ALT)', '7 – 56 U/L', data.get('SGPT (ALT)', '')),
            ('Alkaline Phosphatase (ALP)', '44 – 147 U/L', data.get('Alkaline Phosphatase (ALP)', '')),
            ('Total Protein', '6.0 – 8.3 g/dL', data.get('Total Protein', '')),
            ('Albumin', '3.5 – 5.0 g/dL', data.get('Albumin', '')),
            ('Globulin', '2.0 – 3.5 g/dL', data.get('Globulin', '')),
            ('A/G Ratio', '1.0 – 2.2', data.get('A/G Ratio', '')),
        ]
        return fields

    @property
    def is_kft(self):
        return 'Kidney Function Test' in self.order_item.test.name or 'KFT' in self.order_item.test.name

    @property
    def kft_data(self):
        if not self.is_kft:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def kft_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('Blood Urea', '15 – 40 mg/dL', self.get_param_value('Blood Urea') or self.get_param_value('Urea')),
                ('Serum Creatinine', '0.6 – 1.3 mg/dL', self.get_param_value('Creatinine')),
                ('Uric Acid', '3.5 – 7.2 mg/dL', self.get_param_value('Uric Acid')),
                ('Sodium (Na⁺)', '135 – 145 mEq/L', self.get_param_value('Sodium') or self.get_param_value('Na')),
                ('Potassium (K⁺)', '3.5 – 5.0 mEq/L', self.get_param_value('Potassium') or self.get_param_value('K')),
                ('Chloride (Cl⁻)', '98 – 107 mEq/L', self.get_param_value('Chloride') or self.get_param_value('Cl')),
                ('Calcium', '8.5 – 10.5 mg/dL', self.get_param_value('Calcium') or self.get_param_value('Ca')),
                ('eGFR', '> 90 mL/min/1.73m²', self.get_param_value('eGFR')),
            ]
        data = self.kft_data or {}
        fields = [
            ('Blood Urea', '15 – 40 mg/dL', data.get('Blood Urea', '')),
            ('Serum Creatinine', '0.6 – 1.3 mg/dL', data.get('Serum Creatinine', '')),
            ('Uric Acid', '3.5 – 7.2 mg/dL', data.get('Uric Acid', '')),
            ('Sodium (Na⁺)', '135 – 145 mEq/L', data.get('Sodium (Na⁺)', '')),
            ('Potassium (K⁺)', '3.5 – 5.0 mEq/L', data.get('Potassium (K⁺)', '')),
            ('Chloride (Cl⁻)', '98 – 107 mEq/L', data.get('Chloride (Cl⁻)', '')),
            ('Calcium', '8.5 – 10.5 mg/dL', data.get('Calcium', '')),
            ('eGFR', '> 90 mL/min/1.73m²', data.get('eGFR', '')),
        ]
        return fields

    @property
    def is_blood_sugar(self):
        name = self.order_item.test.name
        return ('Blood Sugar' in name or 'FBS' in name or 'PPBS' in name or
                'Fasting Blood' in name or 'Post-Prandial' in name)

    @property
    def blood_sugar_data(self):
        if not self.is_blood_sugar:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def blood_sugar_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('Fasting Blood Sugar (FBS)', '70 – 99 mg/dL', self.get_param_value('Fasting') or self.get_param_value('FBS')),
                ('Post-Prandial Blood Sugar (PPBS)', '< 140 mg/dL', self.get_param_value('Post-Prandial') or self.get_param_value('PPBS') or self.get_param_value('Post Prandial')),
            ]
        data = self.blood_sugar_data or {}
        fields = [
            ('Fasting Blood Sugar (FBS)', '70 – 99 mg/dL', data.get('Fasting Blood Sugar (FBS)', '')),
            ('Post-Prandial Blood Sugar (PPBS)', '< 140 mg/dL', data.get('Post-Prandial Blood Sugar (PPBS)', '')),
        ]
        return fields

    @property
    def is_hba1c(self):
        name = self.order_item.test.name
        return 'HbA1c' in name or 'Glycated Hemoglobin' in name or 'Haemoglobin A1c' in name

    @property
    def hba1c_data(self):
        if not self.is_hba1c:
            return None
        if self.parameter_results.exists():
            return {pr.parameter.name: pr.value for pr in self.parameter_results.all()}
        if not self.result_value:
            return None
        import json
        try:
            return json.loads(self.result_value)
        except Exception:
            return None

    @property
    def hba1c_fields_with_results(self):
        if self.parameter_results.exists():
            return [
                ('HbA1c (Glycated Hemoglobin)', '< 5.7%', self.get_param_value('HbA1c')),
            ]
        data = self.hba1c_data or {}
        fields = [
            ('HbA1c (Glycated Hemoglobin)', '< 5.7%', data.get('HbA1c (Glycated Hemoglobin)', '')),
        ]
        return fields


class RadiologyTest(models.Model):

    name = models.CharField(
        max_length=200
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name

class RadiologyOrder(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Scheduled', 'Scheduled'),
        ('Arrived', 'Arrived'),
        ('Scanning', 'Scanning'),
        ('Scanned', 'Scanned'),
        ('Completed', 'Completed'),
        ('Reported', 'Reported'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )

    urgency = models.CharField(
        max_length=20,
        choices=[
            ('STAT', 'STAT'),
            ('Urgent', 'Urgent'),
            ('Routine', 'Routine')
        ],
        default='Routine'
    )

    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    ordered_by = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True
    )

    clinical_notes = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_radiology_orders'
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_radiology_orders'
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

class RadiologyOrderItem(models.Model):

    order = models.ForeignKey(
        RadiologyOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    test = models.ForeignKey(
        RadiologyTest,
        on_delete=models.CASCADE
    )


class RadiologyReport(models.Model):

    order_item = models.OneToOneField(
        RadiologyOrderItem,
        on_delete=models.CASCADE
    )

    clinical_history = models.TextField(blank=True, null=True)
    findings = models.TextField()
    impression = models.TextField()
    recommendations = models.TextField(blank=True, null=True)
    is_critical = models.BooleanField(default=False)

    report_file = models.FileField(
        upload_to='radiology_reports/',
        blank=True,
        null=True
    )

    radiologist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    reported_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'radiology_reports'

class LabTestParameter(models.Model):
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, blank=True, null=True)
    reference_range = models.CharField(max_length=100, blank=True, null=True)
    
    # Numerical validation ranges
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Gender specific validation ranges
    male_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    male_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    female_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    female_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Age specific validation ranges
    child_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    child_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Critical ranges
    critical_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    critical_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'lab_test_parameters'

    def __str__(self):
        return f"{self.test.name} - {self.name}"

class LabSample(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='samples')
    sample_type = models.CharField(max_length=50, choices=(
        ('Blood', 'Blood'),
        ('Urine', 'Urine'),
        ('Stool', 'Stool'),
        ('Sputum', 'Sputum'),
        ('Swab', 'Swab'),
        ('Tissue Sample', 'Tissue Sample'),
    ))
    collection_time = models.DateTimeField(auto_now_add=True)
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'lab_samples'

class LabParameterResult(models.Model):
    id = models.AutoField(primary_key=True)
    result = models.ForeignKey(LabResult, on_delete=models.CASCADE, related_name='parameter_results')
    parameter = models.ForeignKey(LabTestParameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    is_abnormal = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)

    class Meta:
        db_table = 'lab_parameter_results'

class RadiologyScheduling(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(RadiologyOrder, on_delete=models.CASCADE, related_name='scheduling')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    machine = models.CharField(max_length=100)
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='scheduled_scans')
    priority = models.CharField(max_length=20, choices=(
        ('Routine', 'Routine'),
        ('Urgent', 'Urgent'),
        ('Emergency', 'Emergency'),
    ), default='Routine')

    class Meta:
        db_table = 'radiology_schedulings'

class RadiologyAttachment(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(RadiologyOrder, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='radiology_scans/')
    file_type = models.CharField(max_length=50, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'radiology_attachments'

class DoctorNotification(models.Model):
    id = models.AutoField(primary_key=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=50, choices=(
        ('Lab Report', 'Lab Report'),
        ('Radiology Report', 'Radiology Report'),
        ('Critical Lab Result', 'Critical Lab Result'),
        ('Critical Radiology Finding', 'Critical Radiology Finding'),
    ))
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'doctor_notifications'

class AuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'audit_logs'


class Staff(User):
    class Meta:
        proxy = True
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Manage Staffs'


class NursingStationRequest(models.Model):
    id = models.AutoField(primary_key=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='nursing_requests')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, related_name='nursing_requests', null=True, blank=True)
    request_type = models.CharField(max_length=50, choices=(
        ('Vitals Check', 'Vitals Check'),
        ('ECG Setup', 'ECG Setup'),
        ('Blood Collection', 'Blood Collection'),
        ('Injection', 'Injection'),
        ('IV Cannulation', 'IV Cannulation'),
        ('Nebulization', 'Nebulization'),
        ('Dressing', 'Dressing'),
        ('Wheelchair Support', 'Wheelchair Support'),
        ('Doctor Support', 'Doctor Support'),
    ))
    status = models.CharField(max_length=20, choices=(
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Accepted', 'Accepted'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    ), default='Pending')
    patient_type = models.CharField(max_length=20, choices=(
        ('OP', 'OP'),
        ('IP', 'IP'),
        ('ICU', 'ICU'),
        ('Emergency', 'Emergency'),
    ), default='OP')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nursing_station_requests'


class NursingTaskAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    request = models.ForeignKey(NursingStationRequest, on_delete=models.CASCADE, related_name='assignments')
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, related_name='task_assignments')
    status = models.CharField(max_length=20, choices=(
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Accepted', 'Accepted'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    ), default='Assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True, help_text="Duration in minutes")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'nursing_task_assignments'


class NurseAvailability(models.Model):
    id = models.AutoField(primary_key=True)
    nurse = models.OneToOneField(Nurse, on_delete=models.CASCADE, related_name='availability')
    status = models.CharField(max_length=20, choices=(
        ('Available', 'Available'),
        ('Busy', 'Busy'),
        ('Emergency Duty', 'Emergency Duty'),
        ('Off Duty', 'Off Duty'),
    ), default='Available')
    current_assignment = models.CharField(max_length=255, blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nurse_availability'


class NursingNotification(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_nursing_notifications', null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_nursing_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nursing_notifications'


class NursingMessage(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_nursing_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_nursing_messages')
    category = models.CharField(max_length=20, choices=(
        ('Normal', 'Normal'),
        ('Urgent', 'Urgent'),
        ('Emergency', 'Emergency'),
    ), default='Normal')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nursing_messages'


class NursingAuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.CharField(max_length=255)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nursing_audit_logs'


class EmergencyZone(models.Model):
    id = models.AutoField(primary_key=True)
    zone_name = models.CharField(max_length=50) # RED, ORANGE, YELLOW, GREEN
    color_code = models.CharField(max_length=20) # e.g., danger, warning, warning-yellow, success
    priority_level = models.IntegerField() # 1 to 4
    target_response_time = models.IntegerField() # in minutes

    class Meta:
        db_table = 'emergency_zones'

    def __str__(self):
        return f"{self.zone_name} Zone (Priority {self.priority_level})"


class EmergencyBed(models.Model):
    id = models.AutoField(primary_key=True)
    zone = models.ForeignKey(EmergencyZone, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Available', 'Available'),
            ('Occupied', 'Occupied'),
            ('Maintenance', 'Maintenance')
        ],
        default='Available'
    )
    monitor_available = models.BooleanField(default=False)
    ventilator_available = models.BooleanField(default=False)

    class Meta:
        db_table = 'emergency_beds'

    def __str__(self):
        return f"Bed {self.bed_number} - {self.zone.zone_name} Zone ({self.status})"


class EmergencyTriage(models.Model):
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    casualty_case = models.ForeignKey('Casuality', on_delete=models.CASCADE, related_name='triages')
    triage_nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE)
    triage_time = models.DateTimeField(auto_now_add=True)
    chief_complaint = models.TextField()
    pain_score = models.IntegerField() # 1-10
    triage_zone = models.ForeignKey(EmergencyZone, on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=50) # Critical, Very Urgent, Urgent, Non-Urgent
    
    # Vitals
    bp_systolic = models.IntegerField()
    bp_diastolic = models.IntegerField()
    temperature = models.DecimalField(max_digits=5, decimal_places=1)
    oxygen_level = models.IntegerField() # SpO2
    heart_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    sugar_level = models.IntegerField(null=True, blank=True)
    gcs_score = models.IntegerField() # 3-15
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'emergency_triages'

    def __str__(self):
        return f"Triage {self.id} for CAS-{self.casualty_case.id} (Zone: {self.triage_zone.zone_name})"


class EmergencyTreatmentRecord(models.Model):
    id = models.AutoField(primary_key=True)
    casualty_case = models.ForeignKey('Casuality', on_delete=models.CASCADE, related_name='treatment_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    treatment_started = models.DateTimeField(auto_now_add=True)
    treatment_completed = models.DateTimeField(null=True, blank=True)
    diagnosis = models.TextField()
    treatment_notes = models.TextField()

    class Meta:
        db_table = 'emergency_treatment_records'

    def __str__(self):
        return f"Treatment {self.id} by {self.doctor.name} for CAS-{self.casualty_case.id}"


class EmergencyObservation(models.Model):
    id = models.AutoField(primary_key=True)
    casualty_case = models.ForeignKey('Casuality', on_delete=models.CASCADE, related_name='observations')
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE)
    observation_start = models.DateTimeField(auto_now_add=True)
    observation_end = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField()

    class Meta:
        db_table = 'emergency_observations'

    def __str__(self):
        return f"Observation {self.id} for CAS-{self.casualty_case.id}"


class PharmacyCounter(models.Model):
    COUNTER_TYPES = (
        ('General Counter', 'General Counter'),
        ('Insurance Counter', 'Insurance Counter'),
        ('Senior Citizen Counter', 'Senior Citizen Counter'),
        ('Corporate Counter', 'Corporate Counter'),
        ('Emergency Fast Track Counter', 'Emergency Fast Track Counter'),
    )
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Busy', 'Busy'),
        ('Closed', 'Closed'),
        ('Break', 'Break'),
    )

    counter_id = models.AutoField(primary_key=True)
    number = models.IntegerField(unique=True)
    type = models.CharField(max_length=50, choices=COUNTER_TYPES, default='General Counter')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Closed')

    class Meta:
        db_table = 'pharmacy_counters'

    def __str__(self):
        return f"Counter {self.number} ({self.type}) - {self.status}"

    @property
    def current_token(self):
        return self.tokens.filter(status__in=['Called', 'Processing']).first()

    @property
    def active_assignment(self):
        return self.assignments.filter(is_active=True).first()


class PharmacyToken(models.Model):
    PRIORITY_LEVELS = (
        ('Regular', 'Regular'),
        ('Senior Citizen', 'Senior Citizen'),
        ('Corporate', 'Corporate'),
        ('VIP', 'VIP'),
        ('Emergency', 'Emergency'),
    )
    STATUS_CHOICES = (
        ('Waiting', 'Waiting'),
        ('Called', 'Called'),
        ('Processing', 'Processing'),
        ('Dispensed', 'Dispensed'),
        ('Completed', 'Completed'),
        ('Skipped', 'Skipped'),
        ('Cancelled', 'Cancelled'),
    )

    token_id = models.AutoField(primary_key=True)
    token_number = models.CharField(max_length=20)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True)
    priority_level = models.CharField(max_length=30, choices=PRIORITY_LEVELS, default='Regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Waiting')
    
    counter = models.ForeignKey(PharmacyCounter, on_delete=models.SET_NULL, null=True, blank=True, related_name='tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    waiting_time = models.IntegerField(null=True, blank=True) # waiting time in seconds

    class Meta:
        db_table = 'pharmacy_tokens'

    def __str__(self):
        return f"{self.token_number} - {self.patient.name} ({self.status})"


class CounterAssignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    counter = models.ForeignKey(PharmacyCounter, on_delete=models.CASCADE, related_name='assignments')
    pharmacist = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'counter_assignments'

    def __str__(self):
        return f"{self.pharmacist.username} assigned to Counter {self.counter.number}"


class TokenCallLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    token = models.ForeignKey(PharmacyToken, on_delete=models.CASCADE, related_name='call_logs')
    counter = models.ForeignKey(PharmacyCounter, on_delete=models.CASCADE)
    called_by = models.ForeignKey(User, on_delete=models.CASCADE)
    called_at = models.DateTimeField(auto_now_add=True)
    recall_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'token_call_logs'


class DispensingRecord(models.Model):
    STATUS_CHOICES = (
        ('Full', 'Full'),
        ('Partial', 'Partial'),
        ('Substituted', 'Substituted'),
        ('Held', 'Held'),
    )

    record_id = models.AutoField(primary_key=True)
    token = models.ForeignKey(PharmacyToken, on_delete=models.CASCADE, related_name='dispensing_records')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    quantity_dispensed = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Full')
    substituted_medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True, related_name='substituted_dispensings')
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE)
    dispensed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dispensing_records'


class QueueTransfer(models.Model):
    transfer_id = models.AutoField(primary_key=True)
    token = models.ForeignKey(PharmacyToken, on_delete=models.CASCADE, related_name='transfers')
    from_counter = models.ForeignKey(PharmacyCounter, on_delete=models.CASCADE, related_name='transfers_from')
    to_counter = models.ForeignKey(PharmacyCounter, on_delete=models.CASCADE, related_name='transfers_to')
    transferred_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'queue_transfers'


class VoiceAnnouncementLog(models.Model):
    LANGUAGES = (
        ('English', 'English'),
        ('Malayalam', 'Malayalam'),
        ('Hindi', 'Hindi'),
        ('Arabic', 'Arabic'),
    )

    log_id = models.AutoField(primary_key=True)
    token = models.ForeignKey(PharmacyToken, on_delete=models.CASCADE)
    counter = models.ForeignKey(PharmacyCounter, on_delete=models.CASCADE)
    announcement_text = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGES, default='English')
    played_at = models.DateTimeField(auto_now_add=True)
    is_played = models.BooleanField(default=False)

    class Meta:
        db_table = 'voice_announcement_logs'


class CounterPerformance(models.Model):
    perf_id = models.AutoField(primary_key=True)
    counter = models.ForeignKey(PharmacyCounter, on_delete=models.CASCADE)
    pharmacist = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_served = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)
    total_skipped = models.IntegerField(default=0)
    average_serving_time = models.IntegerField(default=0) # in seconds

    class Meta:
        db_table = 'counter_performances'


class PharmacyAuditLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pharmacy_audit_logs'


def auto_generate_pharmacy_token(prescription, priority_level=None):
    # Avoid duplicate tokens
    if PharmacyToken.objects.filter(prescription=prescription).exists():
        return PharmacyToken.objects.filter(prescription=prescription).first()
        
    patient = prescription.patient
    if not priority_level:
        if hasattr(prescription, 'priority_level') and prescription.priority_level:
            priority_level = prescription.priority_level
        elif patient.age >= 60:
            priority_level = 'Senior Citizen'
        elif hasattr(prescription, 'casualty') or (prescription.notes and 'emergency' in prescription.notes.lower()):
            priority_level = 'Emergency'
        else:
            priority_level = 'Regular'

    prefix_map = {
        'Regular': 'P',
        'Senior Citizen': 'S',
        'Corporate': 'C',
        'VIP': 'V',
        'Emergency': 'E'
    }
    prefix = prefix_map.get(priority_level, 'P')
    
    # Get sequence number
    from datetime import datetime, time
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    today_tokens_count = PharmacyToken.objects.filter(
        created_at__range=(start_dt, end_dt),
        priority_level=priority_level
    ).count()
    token_number = f"{prefix}{today_tokens_count + 1:03d}"

    # Check for billing
    bill = Bill.objects.filter(prescription=prescription).first()

    token = PharmacyToken.objects.create(
        token_number=token_number,
        patient=patient,
        doctor=prescription.doctor,
        prescription=prescription,
        bill=bill,
        priority_level=priority_level,
        status='Waiting'
    )
    
    PharmacyAuditLog.objects.create(
        action="Token Generated",
        details=f"Token {token_number} generated automatically for prescription #{prescription.prescription_id}",
        user=None
    )
    return token


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Prescription)
def handle_prescription_created(sender, instance, created, **kwargs):
    if created:
        try:
            auto_generate_pharmacy_token(instance, priority_level=instance.priority_level)
        except Exception as e:
            print("Error auto-generating pharmacy token on prescription save:", e)

@receiver(post_save, sender=Bill)
def handle_bill_saved(sender, instance, **kwargs):
    # Link pharmacy bill to token when created/updated
    if instance.bill_type == 'pharmacy' and instance.prescription:
        try:
            token = PharmacyToken.objects.filter(prescription=instance.prescription).first()
            if token:
                if token.bill != instance:
                    token.bill = instance
                    token.save()
            elif instance.payment_status == 'Paid':
                # If no token existed (unlikely but possible) and paid, create one
                auto_generate_pharmacy_token(instance.prescription)
        except Exception as e:
            print("Error linking/creating pharmacy token on bill saved:", e)


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'suppliers'

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    item_code = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=150)
    generic_name = models.CharField(max_length=150, blank=True, null=True)
    brand_name = models.CharField(max_length=150, blank=True, null=True)
    category = models.CharField(max_length=100)
    uom = models.CharField(max_length=50, verbose_name="Unit of Measure")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="GST %", default=0.00)
    reorder_level = models.IntegerField(default=10)
    min_stock = models.IntegerField(default=5)
    max_stock = models.IntegerField(default=100)
    current_stock = models.IntegerField(default=0)
    storage_location = models.CharField(max_length=100, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_items'

    def __str__(self):
        return f"{self.name} ({self.item_code})"


class PurchaseRequisition(models.Model):
    req_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisitions_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisitions_approved')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=30, choices=(
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Ordered', 'Ordered')
    ), default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_requisitions'

    def __str__(self):
        return self.req_number


class PurchaseOrder(models.Model):
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True)
    expected_delivery = models.DateField(blank=True, null=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pos_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_approved')
    status = models.CharField(max_length=30, choices=(
        ('Draft', 'Draft'),
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Ordered', 'Ordered'),
        ('Partially Received', 'Partially Received'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ), default='Pending Approval')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_orders'

    def __str__(self):
        return self.po_number


class GoodsReceiptNote(models.Model):
    grn_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    received_date = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'goods_receipt_notes'

    def __str__(self):
        return self.grn_number


class StockIssue(models.Model):
    issue_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_issues_requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_issues_approved')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_issues'

    def __str__(self):
        return self.issue_number


class BiomedicalAsset(models.Model):
    asset_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    amc_details = models.TextField(blank=True, null=True)
    current_location = models.CharField(max_length=100, blank=True, null=True)
    assigned_department = models.CharField(max_length=100, blank=True, null=True)
    next_service_date = models.DateField(blank=True, null=True)
    service_history = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'biomedical_assets'

    def __str__(self):
        return f"{self.name} ({self.asset_id})"



