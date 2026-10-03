from django import forms
from .models import User, Appointment, Medicine, Prescription, Patient, Doctor, LabTest, RadiologyTest, EmergencyTriage, EmergencyTreatmentRecord

class UserRegistrationForm(forms.ModelForm):

    full_name = forms.CharField(
        max_length=100,
        label="Full Name",
        required=False
    )

    email = forms.EmailField(required=True)

    role = forms.ChoiceField(
        choices=(
            ('patient', 'Patient'),
            ('doctor', 'Doctor'),
            ('lab_technician', 'Laboratory Technician'),
            ('radiologist', 'Radiologist'),
            ('pharmacist', 'Pharmacist'),
            ('senior_pharmacist', 'Senior Pharmacist'),
            ('pharmacy_supervisor', 'Pharmacy Supervisor'),
            ('inventory_manager', 'Inventory Manager'),
            ('store_keeper', 'Store Keeper'),
            ('nursing_superintendent', 'Nursing Superintendent'),
        ),
        label="Register As",
        initial='patient',
        required=False
    )

    password = forms.CharField(
        widget=forms.PasswordInput
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User

        fields = [
            'username',
            'email',
            'role',
        ]

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Passwords do not match"
            )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.email = self.cleaned_data['email']

        user.set_password(
            self.cleaned_data["password"]
        )

        role = self.cleaned_data.get('role')
        if role:
            user.role = role
        elif not user.role:
            user.role = 'patient'

        if commit:
            user.save()

        return user




class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment

        fields = [
            'patient',
            'doctor',
            'appointment_date',
            'reason',
            'status'
        ]

        widgets = {
            'appointment_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # PATIENT DROPDOWN
        self.fields['patient'].label_from_instance = (
            lambda obj: f"PAT-{obj.patient_id} | {obj.name}"
        )

        # DOCTOR DROPDOWN
        self.fields['doctor'].label_from_instance = (
            lambda obj: f"{obj.name} - {obj.specialization}"
        )

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['diagnosis', 'medicines', 'notes']

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'stock', 'price', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'phone', 'email', 'address']

class DoctorForm(forms.ModelForm):

    specialization = forms.ChoiceField(choices=[
        ('General Physician', 'General Physician'),
        ('Cardiologist', 'Cardiologist'),
        ('Dermatologist', 'Dermatologist'),
        ('Pediatrician', 'Pediatrician'),
        ('Neurologist', 'Neurologist'),
        ('Orthopedic', 'Orthopedic'),
        ('Gynecologist', 'Gynecologist'),
        ('Dentist', 'Dentist'),
        ('Psychiatrist', 'Psychiatrist'),
        ('Surgeon', 'Surgeon'),
        ('Emergency Medicine', 'Emergency Medicine'),
        ('Anesthesiologist', 'Anesthesiologist')
        
    ])

    availability = forms.ChoiceField(choices=[
        ('Mon-Fri (9 AM - 1 PM)', 'Mon-Fri (9 AM - 1 PM)'),
        ('Mon-Fri (5 PM - 9 PM)', 'Mon-Fri (5 PM - 9 PM)'),
        ('Mon-Sat (9 AM - 5 PM)', 'Mon-Sat (9 AM - 5 PM)'),
        ('Weekends Only (10 AM - 2 PM)', 'Weekends Only (10 AM - 2 PM)'),
        ('Daily (9 AM - 9 PM)', 'Daily (9 AM - 9 PM)'),
        ('Emergency (24/7)', 'Emergency (24/7)'),
    ])

    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'phone', 'email', 'availability']
class ForgotPasswordForm(forms.Form):
    username = forms.CharField(max_length=50)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


class LabOrderForm(forms.Form):

    tests = forms.ModelMultipleChoiceField(
        queryset=LabTest.objects.filter(
            active=True
        ),
        widget=forms.CheckboxSelectMultiple
    )

    clinical_notes = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows':4}
        ),
        required=False
    )


class RadiologyOrderForm(forms.Form):

    tests = forms.ModelMultipleChoiceField(
        queryset=RadiologyTest.objects.filter(
            active=True
        ),
        widget=forms.CheckboxSelectMultiple
    )

    clinical_notes = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows':4}
        ),
        required=False
    )


class StaffEditForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=(
            ('receptionist', 'Receptionist'),
            ('pharmacist', 'Pharmacist'),
            ('senior_pharmacist', 'Senior Pharmacist'),
            ('pharmacy_supervisor', 'Pharmacy Supervisor'),
            ('inventory_manager', 'Inventory Manager'),
            ('store_keeper', 'Store Keeper'),
            ('lab_technician', 'Laboratory Technician'),
            ('laboratoryist', 'Laboratoryist (Legacy)'),
            ('radiologist', 'Radiologist'),
            ('radiology_technician', 'Radiology Technician'),
            ('nursing_station', 'Nursing Station'),
            ('nursing_superintendent', 'Nursing Superintendent'),
        ),
        label="Role"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']


from .models import NursingStationRequest, NursingMessage

class NursingStationRequestForm(forms.ModelForm):
    class Meta:
        model = NursingStationRequest
        fields = ['request_type', 'patient_type', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Optional clinical notes...'}),
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'patient_type': forms.Select(attrs={'class': 'form-select'}),
        }


class NursingMessageForm(forms.ModelForm):
    class Meta:
        model = NursingMessage
        fields = ['receiver', 'category', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Type your message...'}),
            'receiver': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit receiver to admin, doctors, nurses, nursing_station roles
        self.fields['receiver'].queryset = User.objects.filter(role__in=['admin', 'doctor', 'nurse', 'nursing_station'])
        self.fields['receiver'].label_from_instance = lambda obj: f"{obj.username} ({obj.get_role_display() if hasattr(obj, 'get_role_display') else obj.role})"


class EmergencyTriageForm(forms.ModelForm):
    class Meta:
        model = EmergencyTriage
        fields = [
            'chief_complaint', 'pain_score', 'bp_systolic', 'bp_diastolic',
            'temperature', 'oxygen_level', 'heart_rate', 'respiratory_rate',
            'sugar_level', 'gcs_score', 'notes'
        ]
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Describe chief complaint...'}),
            'pain_score': forms.NumberInput(attrs={'min': 1, 'max': 10, 'class': 'form-control'}),
            'bp_systolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 120'}),
            'bp_diastolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 80'}),
            'temperature': forms.NumberInput(attrs={'step': 0.1, 'class': 'form-control', 'placeholder': 'e.g. 98.6'}),
            'oxygen_level': forms.NumberInput(attrs={'min': 0, 'max': 100, 'class': 'form-control', 'placeholder': 'SpO2 %'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'bpm'}),
            'respiratory_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'breaths/min'}),
            'sugar_level': forms.NumberInput(attrs={'required': False, 'class': 'form-control', 'placeholder': 'mg/dL (optional)'}),
            'gcs_score': forms.NumberInput(attrs={'min': 3, 'max': 15, 'class': 'form-control', 'placeholder': '3 - 15'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'required': False, 'class': 'form-control', 'placeholder': 'Additional triage notes...'}),
        }


class EmergencyTreatmentForm(forms.ModelForm):
    class Meta:
        model = EmergencyTreatmentRecord
        fields = ['diagnosis', 'treatment_notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Enter final/provisional diagnosis...'}),
            'treatment_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Enter treatment details, medications administered, procedures...'}),
        }


from .models import PharmacyCounter, PharmacyToken

class PharmacyCounterForm(forms.ModelForm):
    class Meta:
        model = PharmacyCounter
        fields = ['number', 'type', 'status']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class PharmacyTokenForm(forms.ModelForm):
    class Meta:
        model = PharmacyToken
        fields = ['patient', 'doctor', 'prescription', 'priority_level', 'status', 'counter']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'prescription': forms.Select(attrs={'class': 'form-select'}),
            'priority_level': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'counter': forms.Select(attrs={'class': 'form-select'}),
        }


from django.conf import settings

class AdminRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=100, 
        label="Admin Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter admin username'})
    )
    email = forms.EmailField(
        label="Admin Email", 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )
    full_name = forms.CharField(
        max_length=100, 
        label="Full Name", 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter administrator full name'})
    )
    security_key = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter admin security key (e.g. ashaadmin2026)'}),
        label="Admin Setup Security Key",
        help_text="Required security secret key for registering an admin account when hosted.",
        required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Choose password'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists. Please choose a different username.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        security_key = cleaned_data.get("security_key")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        expected_secret = getattr(settings, 'ADMIN_SETUP_SECRET', 'ashaadmin2026')
        admin_count = User.objects.filter(role='admin').count()

        # Security check: If admins already exist, key is mandatory.
        if admin_count > 0:
            if not security_key:
                raise forms.ValidationError("Admin Setup Security Key is required to create an additional Admin account.")
            elif security_key != expected_secret:
                raise forms.ValidationError("Invalid Admin Setup Security Key. Please verify your secret key.")
        else:
            # Initial setup mode
            if security_key and security_key != expected_secret:
                raise forms.ValidationError("Invalid Admin Setup Security Key.")

        return cleaned_data