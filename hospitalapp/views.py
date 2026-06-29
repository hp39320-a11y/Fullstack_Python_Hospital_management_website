from hospitalapp.models import AuditLog
from hospitalapp.models import LabSample
from hospitalapp.models import LabParameterResult
from hospitalapp.models import RadiologyScheduling
from hospitalapp.models import RadiologyAttachment
from hospitalapp.models import LabTest
from hospitalapp.models import LabTestParameter
from hospitalapp.models import RadiologyTest
from hospitalapp.models import DoctorNotification
from hospitalapp.models import LabOrderItem
from hospitalapp.models import LabResult
from hospitalapp.models import RadiologyOrder
from hospitalapp.models import RadiologyOrderItem
from hospitalapp.models import RadiologyReport
from hospitalapp.models import LabOrder
from hospitalapp.forms import RadiologyOrderForm
from hospitalapp.forms import LabOrderForm
from hospitalapp.models import CasualtyBill
from hospitalapp.models import EmergencyPrescriptionItem
from hospitalapp.models import ClinicalNote
from hospitalapp.models import InvestigationSuggestion
from hospitalapp.models import EmergencyPrescription
from django.db.models.signals import post_save
from django.dispatch import receiver
from hospitalapp.models import AdmissionConsultant
from hospitalapp.models import CasualityReferral
from django.http import request
from hospitalapp.models import MedicationScheduleEntry
from hospitalapp.models import InpatientPrescriptionItem
from hospitalapp.models import InpatientPrescription
from hospitalapp.models import LaundryLog
from hospitalapp.models import SecurityIncident
from hospitalapp.models import VisitorLog
from hospitalapp.models import CleaningLog
from hospitalapp.models import NonStaffShift
from hospitalapp.models import NonStaff
from hospitalapp.models import AmbulanceRequest
from hospitalapp.models import Ambulance
from hospitalapp.models import VitalRecord
from hospitalapp.models import NursePatientAssignment
from hospitalapp.models import EmergencyAlert
from hospitalapp.models import MedicineAdministration
from hospitalapp.models import NurseNote
from hospitalapp.models import NurseShift
from hospitalapp.models import Nurse
from hospitalapp.models import Bed
from hospitalapp.models import Casuality
from hospitalapp.models import IPBill
from hospitalapp.models import IPCharge
from hospitalapp.models import PrescriptionMedicine
from hospitalapp.models import Prescription
from hospitalapp.models import Bill
from django.contrib.auth.models import User
from hospitalapp.models import Patient
from hospitalapp.models import Medicine
from hospitalapp.models import Doctor
from hospitalapp.models import Appointment
from hospitalapp.models import Admission
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from http import client
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hospitalapp.models import *
from hospitalapp.forms import UserRegistrationForm, LoginForm, AppointmentForm, PrescriptionForm, MedicineForm, PatientRegistrationForm, DoctorForm, ForgotPasswordForm, StaffEditForm
from django.http import HttpResponseForbidden
import razorpay
from django.conf import settings
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import io
import os
from django.utils import timezone
from datetime import datetime, time



client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))



# Utility to check roles
def role_required(*roles):

    def decorator(view_func):

        @login_required
        def _wrapped_view(request, *args, **kwargs):

            # CHECK USER ROLE

            if request.user.role in roles or request.user.is_superuser:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            return HttpResponseForbidden(
                "You are not authorized to view this page."
            )

        return _wrapped_view

    return decorator

# Public Views
def home(request):
    return render(request, 'hospitalapp/home.html')

def about(request):
    return render(request, 'hospitalapp/about.html')

def contact(request):
    return render(request, 'hospitalapp/contact.html')

# Authentication
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            full_name = form.cleaned_data.get('full_name')
            # Create profile based on role
            if user.role == 'doctor':
                Doctor.objects.create(user=user, name=full_name, specialization='General')
            elif user.role == 'patient':
                Patient.objects.create(user=user, name=full_name, age=0, gender='Other')
            
            messages.success(request, "Registration successful. Please login.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'hospitalapp/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.role == 'admin': return redirect('admin_dashboard')
                elif user.role == 'doctor': return redirect('doctor_dashboard')
                elif user.role == 'patient': return redirect('patient_dashboard')
                elif user.role in ['pharmacist', 'senior_pharmacist', 'pharmacy_supervisor']: return redirect('pharmacy_dashboard')
                elif user.role in ['inventory_manager', 'store_keeper']: return redirect('admin_inventory_dashboard')
                elif user.role == 'receptionist': return redirect('receptionist_dashboard')
                elif user.role == 'nurse': return redirect('nurse_dashboard')
                elif user.role in ['lab_technician', 'laboratoryist']: return redirect('laboratory_dashboard')
                elif user.role in ['radiologist', 'radiology_technician']: return redirect('radiology_dashboard')
                elif user.role == 'nursing_station': return redirect('nursing_station_dashboard')
                elif user.role == 'nursing_superintendent': return redirect('nursing_superintendent_dashboard')
                return redirect('home')
            messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, 'hospitalapp/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            new_password = form.cleaned_data['new_password']
            try:
                user = User.objects.get(username=username)
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password successfully reset. Please login with your new password.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "User with this username does not exist.")
    else:
        form = ForgotPasswordForm()
    return render(request, 'hospitalapp/forgot_password.html', {'form': form})

# Admin Module
@role_required('admin')
def admin_dashboard(request):
    context = {
        'doctors_count': Doctor.objects.count(),
        'patients_count': Patient.objects.count(),
        'appointments_count': Appointment.objects.count(),
        'medicines_count': Medicine.objects.count(),
    }
    return render(request, 'hospitalapp/admin/dashboard.html', context)



@role_required('admin')
def manage_doctors(request):

    doctors = Doctor.objects.select_related('user').all()

    if request.method == 'POST':

        user_form = UserRegistrationForm(request.POST)
        doctor_form = DoctorForm(request.POST)

        if user_form.is_valid() and doctor_form.is_valid():

            # =========================
            # SAVE USER
            # =========================
            user = user_form.save(commit=False)

            # FORCE ROLE
            user.role = 'doctor'

            user.save()

            # =========================
            # SAVE DOCTOR PROFILE
            # =========================
            doctor = doctor_form.save(commit=False)

            doctor.user = user

            # OPTIONAL AUTO NAME
            doctor.name = (
                user_form.cleaned_data.get('full_name')
                or user.username
            )

            doctor.save()

            messages.success(request, "Doctor added successfully!")

            return redirect('manage_doctors')

        else:

            print(user_form.errors)
            print(doctor_form.errors)

            messages.error(
                request,
                "Please correct the form errors."
            )

    else:

        user_form = UserRegistrationForm()
        doctor_form = DoctorForm()

    context = {
        'doctors': doctors,
        'user_form': user_form,
        'doctor_form': doctor_form
    }

    return render(
        request,
        'hospitalapp/admin/manage_doctors.html',
        context
    )





@role_required('admin')
def update_doctor(request, pk):
    doctor = get_object_or_404(Doctor, doctor_id=pk)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor updated successfully!")
            return redirect('manage_doctors')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'hospitalapp/admin/update_doctor.html', {'form': form, 'doctor': doctor})

@role_required('admin')
def delete_doctor(request, pk):
    doctor = get_object_or_404(Doctor, doctor_id=pk)
    user = doctor.user
    doctor.delete()
    if user:
        user.delete()
    messages.success(request, "Doctor deleted successfully.")
    return redirect('manage_doctors')

@role_required('admin')
def manage_patients(request):
    patients = Patient.objects.all()
    return render(request, 'hospitalapp/admin/manage_patients.html', {'patients': patients})

@role_required('admin')
def manage_medicines(request):
    medicines = Medicine.objects.all()
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine added successfully")
            return redirect('manage_medicines')
    else:
        form = MedicineForm()
    return render(request, 'hospitalapp/admin/manage_medicines.html', {'medicines': medicines, 'form': form})

@role_required('admin')
def update_medicine(request, pk):
    medicine = get_object_or_404(Medicine, medicine_id=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine updated successfully!")
            return redirect('manage_medicines')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'hospitalapp/admin/update_medicine.html', {'form': form, 'medicine': medicine})


# Doctor Module


@role_required('doctor')
def doctor_dashboard(request):
    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    appointments = Appointment.objects.filter(
        doctor=doctor,
        status__in=['Approved', 'Completed']
    ).order_by('-appointment_date')

    for app in appointments:
        admission = Admission.objects.filter(patient=app.patient).order_by('-admission_date').first()
        if admission:
            app.admission_status = admission.status
        else:
            app.admission_status = None

    from django.db.models import Q
    admitted_patients = Admission.objects.filter(
        Q(doctor=doctor) | Q(consultants__doctor=doctor),
        status__in=['Admitted', 'Ready For Discharge']
    ).distinct().order_by('-admission_date')

    specialist_doctors = Doctor.objects.exclude(doctor_id=doctor.doctor_id).order_by('specialization', 'name')

    return render(
        request,
        'hospitalapp/doctor/dashboard.html',
        {
            'appointments': appointments,
            'admitted_patients': admitted_patients,
            'specialist_doctors': specialist_doctors
        }
    )



@role_required('doctor')
def doctor_patients(request):
    doctor, created = Doctor.objects.get_or_create(user=request.user, defaults={'specialization': 'General', 'phone': '', 'address': ''})
    # Patients who have had appointments with this doctor
    patients = Patient.objects.filter(appointment__doctor=doctor).distinct()
    return render(request, 'hospitalapp/doctor/patients.html', {'patients': patients})


@role_required('doctor')
def doctor_search_medicines(request):
    query = request.GET.get('q', '').strip()
    if query:
        medicines = Medicine.objects.filter(name__icontains=query).order_by('name')
    else:
        medicines = Medicine.objects.all().order_by('name')
    return render(request, 'hospitalapp/doctor/search_medicines.html', {'medicines': medicines, 'query': query})

@role_required('doctor')
def doctor_analytics(request):
    return render(request, 'hospitalapp/doctor/analytics.html')

# Patient Module

@role_required('patient')
def patient_dashboard(request):

    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.username,
            'age': 0,
            'gender': 'Other',
            'phone': '',
            'address': ''
        }
    )

    appointments = Appointment.objects.filter(
        patient=patient
    ).order_by('-appointment_date')

    if request.method == 'POST':

        post_data = request.POST.copy()
        post_data['patient'] = patient.patient_id
        post_data['status'] = 'Pending'

        form = AppointmentForm(post_data)

        if form.is_valid():

            appointment = form.save(commit=False)

            # AUTO SET PATIENT
            appointment.patient = patient

            # DEFAULT STATUS
            appointment.status = 'Pending'

            appointment.save()

            messages.success(
                request,
                "Appointment booked successfully!"
            )

            return redirect('patient_dashboard')

    else:

        form = AppointmentForm()

        # HIDE FIELDS
        form.fields.pop('patient')
        form.fields.pop('status')

    return render(
        request,
        'hospitalapp/patient/dashboard.html',
        {
            'form': form,
            'appointments': appointments
        }
    )

# Pharmacist Module

@role_required('pharmacist')
def pharmacist_analytics(request):
    return render(request, 'hospitalapp/pharmacist/analytics.html')

@role_required('pharmacist')
def pharmacist_dashboard(request):
    medicines = Medicine.objects.all()
    return render(request, 'hospitalapp/pharmacist/dashboard.html', {'medicines': medicines})

# Receptionist Module

@role_required('receptionist')
def receptionist_analytics(request):
    return render(request, 'hospitalapp/receptionist/analytics.html')

@role_required('receptionist')
def receptionist_dashboard(request):

    if request.method == 'POST':

        # COPY POST DATA
        post_data = request.POST.copy()

        # AUTO SET ROLE
        post_data['role'] = 'patient'

        user_form = UserRegistrationForm(post_data)
        patient_form = PatientRegistrationForm(request.POST, request.FILES)

        if user_form.is_valid() and patient_form.is_valid():

            # CREATE USER
            user = user_form.save(commit=False)
            user.role = 'patient'
            user.save()

            # CREATE PATIENT
            patient = patient_form.save(commit=False)

            patient.user = user

            # AUTO SAVE EMAIL FROM USER TABLE
            patient.email = user.email

            patient.save()

            messages.success(
                request,
                "Patient registered successfully!"
            )

            # Store registered patient ID in session
            request.session['registered_patient_id'] = patient.patient_id

            return redirect('receptionist_dashboard')

        else:

            print(user_form.errors)
            print(patient_form.errors)

    else:

        user_form = UserRegistrationForm()
        patient_form = PatientRegistrationForm()

    # Load newly registered patient from session if available
    registered_patient_id = request.session.pop('registered_patient_id', None)
    new_patient = None
    if registered_patient_id:
        try:
            new_patient = Patient.objects.get(patient_id=registered_patient_id)
        except Patient.DoesNotExist:
            pass

    # Load recent patients
    recent_patients = Patient.objects.all().order_by('-created_at')[:5]

    return render(
        request,
        'hospitalapp/receptionist/dashboard.html',
        {
            'user_form': user_form,
            'patient_form': patient_form,
            'ages': range(1, 101),
            'new_patient': new_patient,
            'recent_patients': recent_patients
        }
    )


@role_required('receptionist')
def download_patient_id_card(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)

   

    buffer = io.BytesIO()

    # ID Card Size: CR80 standard translated to points (width: 360, height: 220)
    card_width = 360
    card_height = 220

    p = canvas.Canvas(buffer, pagesize=(card_width, card_height))

    # ==========================
    # CARD BACKGROUND & ACCENTS
    # ==========================
    # Draw card border & background
    p.setFillColor(colors.HexColor("#f8f9fa"))
    p.rect(0, 0, card_width, card_height, fill=1, stroke=0)

    # Draw primary accent header block
    p.setFillColor(colors.HexColor("#0b4c8c")) # Asha Blue
    p.rect(0, 160, card_width, 60, fill=1, stroke=0)

    # Draw secondary accent stripe
    p.setFillColor(colors.HexColor("#4caf50")) # Asha Green
    p.rect(0, 155, card_width, 5, fill=1, stroke=0)

    # Draw footer background
    p.setFillColor(colors.HexColor("#0b4c8c"))
    p.rect(0, 0, card_width, 25, fill=1, stroke=0)

    # ==========================
    # HEADER CONTENTS
    # ==========================
    # Logo placement (Hospital logo)
    logo_path = os.path.join(settings.BASE_DIR, 'hospitalapp', 'static', 'hospitalapp', 'images', 'logo.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 15, 165, width=48, height=48, mask='auto')

    # Hospital Name
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(75, 195, "ASHA HOSPITAL")

    # Subtitle
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.HexColor("#e8f5e9"))
    p.drawString(75, 183, "PATIENT IDENTIFICATION CARD")

    # Hospital Tagline
    p.setFont("Helvetica-Oblique", 7)
    p.drawString(75, 172, "Care | Compassion | Commitment")

    # ==========================
    # PATIENT INFO
    # ==========================
    # Decorative elements (e.g., patient photo box placeholder or actual image)
    p.setFillColor(colors.HexColor("#e9ecef"))
    p.roundRect(15, 45, 80, 95, 4, fill=1, stroke=1)
    p.setStrokeColor(colors.HexColor("#ced4da"))

    avatar_path = os.path.join(settings.BASE_DIR, 'hospitalapp', 'static', 'hospitalapp', 'images', 'default_avatar.png')
    if os.path.exists(avatar_path):
        p.drawImage(avatar_path, 15, 45, width=80, height=95)
    else:
        # Fallback if image missing
        p.setFillColor(colors.HexColor("#adb5bd"))
        p.circle(55, 105, 14, fill=1, stroke=0)
        p.ellipse(55, 50, 25, 40, fill=1, stroke=0)
        p.setFillColor(colors.HexColor("#f8f9fa"))
        p.rect(10, 40, 90, 4, fill=1, stroke=0)
        p.rect(10, 141, 90, 5, fill=1, stroke=0)
        p.rect(5, 40, 9, 105, fill=1, stroke=0)
        p.rect(96, 40, 9, 105, fill=1, stroke=0)

    # Draw photo frame border again
    p.setStrokeColor(colors.HexColor("#0b4c8c"))
    p.setLineWidth(1)
    p.roundRect(15, 45, 80, 95, 4, fill=0, stroke=1)

    # Patient details
    p.setFillColor(colors.HexColor("#212529"))

    # ID Number (Large and Bold)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(110, 125, f"ID: PAT-{patient.patient_id}")

    # Name
    p.setFont("Helvetica-Bold", 10)
    p.drawString(110, 108, f"Name: {patient.name.upper()}")

    # Age & Gender
    p.setFont("Helvetica", 9)
    p.drawString(110, 93, f"Age / Gender: {patient.age} / {patient.gender}")

    # Phone
    p.drawString(110, 78, f"Contact: {patient.phone}")

    # Issue Date
    issue_date = patient.created_at.strftime('%d-%m-%Y') if patient.created_at else timezone.now().strftime('%d-%m-%Y')
    p.drawString(110, 63, f"Date of Issue: {issue_date}")

    # Decorative modern barcode lines
    p.setFillColor(colors.HexColor("#212529"))
    barcode_x = 110
    barcode_y = 38
    barcode_w = 230
    barcode_h = 15
    # Let's draw some fake barcode lines for high-tech aesthetic
    import random
    random.seed(patient.patient_id) # reproducible barcodes per patient
    x_offset = barcode_x
    while x_offset < barcode_x + barcode_w:
        line_w = random.choice([1, 2, 3, 4])
        space_w = random.choice([2, 3, 4])
        if x_offset + line_w < barcode_x + barcode_w:
            p.rect(x_offset, barcode_y, line_w, barcode_h, fill=1, stroke=0)
        x_offset += line_w + space_w

    # ==========================
    # FOOTER CONTENTS
    # ==========================
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 7)
    p.drawCentredString(card_width / 2, 14, "If found, please return to Asha Hospital • Phone: +91 9876543210")
    p.setFont("Helvetica", 6.5)
    p.drawCentredString(card_width / 2, 5, "Emergency Helpline: 108  |  Website: www.ashahospital.com")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="patient_id_card_{patient.patient_id}.pdf"'
    return response



# Admin - Manage Appointments
@login_required
def manage_appointments(request):

    # ONLY ADMIN & RECEPTIONIST
    if request.user.role not in ['admin', 'receptionist', 'doctor']:

        return HttpResponseForbidden(
            "You are not authorized to view this page."
        )

    appointments = Appointment.objects.all().order_by(
        '-appointment_date'
    )

    return render(
        request,
        'hospitalapp/admin/manage_appointments.html',
        {
            'appointments': appointments
        }
    )



# Admin - Manage Bills
@role_required('admin')
def manage_bills(request):
    bills = Bill.objects.all().order_by('-created_at')
    return render(request, 'hospitalapp/admin/manage_bills.html', {'bills': bills})

@role_required('admin')
def mark_bill_paid(request, pk):
    bill = get_object_or_404(Bill, bill_id=pk)
    bill.payment_status = 'Paid'
    bill.save()
    messages.success(request, f"Bill #{bill.bill_id} marked as Paid successfully.")
    return redirect('manage_bills')


# Doctor - Add Prescription
@role_required('doctor')
def add_prescription(request, appointment_id):

    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    medicines = Medicine.objects.all()  # for dropdown

    if request.method == 'POST':

        diagnosis = request.POST.get('diagnosis')
        notes = request.POST.get('notes')
        priority_level = request.POST.get('priority_level')

        # 1. Create Prescription
        prescription = Prescription.objects.create(
            appointment=appointment,
            doctor=appointment.doctor,
            patient=appointment.patient,
            diagnosis=diagnosis,
            notes=notes,
            priority_level=priority_level
        )

        # 2. Get medicines + quantity from form
        medicine_ids = request.POST.getlist('medicine_id')
        quantities = request.POST.getlist('quantity')
        dosages = request.POST.getlist('dosage')
        frequencies = request.POST.getlist('frequency')

        # 3. Save into PrescriptionMedicine table
        med_list = []
        for i in range(len(medicine_ids)):

            if medicine_ids[i] and quantities[i]:

                medicine = Medicine.objects.get(medicine_id=medicine_ids[i])
                dosage_val = dosages[i] if i < len(dosages) else ""
                freq_val = frequencies[i] if i < len(frequencies) else ""

                PrescriptionMedicine.objects.create(
                    prescription=prescription,
                    medicine=medicine,
                    quantity=int(quantities[i]),
                    dosage=dosage_val,
                    frequency=freq_val
                )
                details = f"x{quantities[i]}"
                if dosage_val:
                    details += f", {dosage_val}"
                if freq_val:
                    details += f", {freq_val}"
                med_list.append(f"{medicine.name} ({details})")

        if med_list:
            prescription.medicines = ", ".join(med_list)
            prescription.save()

        # 4. Mark appointment completed
        appointment.status = 'Completed'
        appointment.save()

        messages.success(request, "Prescription added successfully!")
        next_url = request.GET.get('next', 'doctor_dashboard')
        return redirect(next_url)

    return render(request, 'hospitalapp/doctor/add_prescription.html', {
        'appointment': appointment,
        'medicines': medicines
    })

# Doctor - Prescription History
@role_required('doctor')
def prescription_history(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    prescriptions = Prescription.objects.filter(doctor=doctor).order_by('-created_at')
    return render(request, 'hospitalapp/doctor/prescriptions_history.html', {'prescriptions': prescriptions})

# Patient - View Prescriptions
@role_required('patient')
def patient_prescriptions(request):
    patient = get_object_or_404(Patient, user=request.user)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    return render(request, 'hospitalapp/patient/prescriptions.html', {'prescriptions': prescriptions})

# Patient - View Bills
@role_required('patient')
def patient_bills(request):
    patient = get_object_or_404(Patient, user=request.user)
    bills = Bill.objects.filter(patient=patient).order_by('-created_at')
    return render(request, 'hospitalapp/patient/bills.html', {'bills': bills})

# Patient - View Laboratory Results
@role_required('patient')
def patient_lab_results(request):
    patient = get_object_or_404(Patient, user=request.user)
    lab_orders = LabOrder.objects.filter(patient=patient).select_related('ordered_by').prefetch_related('items__test').order_by('-created_at')
    return render(request, 'hospitalapp/patient/lab_results.html', {'lab_orders': lab_orders})

# Patient - View Radiology Results
@role_required('patient')
def patient_radiology_results(request):
    patient = get_object_or_404(Patient, user=request.user)
    radiology_orders = RadiologyOrder.objects.filter(patient=patient).select_related('ordered_by').prefetch_related('items__test').order_by('-created_at')
    return render(request, 'hospitalapp/patient/radiology_results.html', {'radiology_orders': radiology_orders})


# Pharmacist - View Prescriptions
@role_required('pharmacist')
def pharmacist_prescriptions(request):
    prescriptions = Prescription.objects.all().order_by('-created_at')
    return render(request, 'hospitalapp/pharmacist/prescriptions.html', {'prescriptions': prescriptions})

# Receptionist - Manage Bills
@role_required('receptionist')
def receptionist_bills(request):
    bills = Bill.objects.all().order_by('-created_at')
    if request.method == 'POST':
        # Simple logic to add a bill
        appointment_id = request.POST.get('appointment_id')
        amount = request.POST.get('amount')
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        Bill.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            total_amount=amount,
            payment_status='Pending',
            bill_type='appointment'
        )
        messages.success(request, "Bill generated successfully!")
        return redirect('receptionist_bills')
    return render(request, 'hospitalapp/receptionist/bills.html', {'bills': bills})
@role_required('admin')
def delete_medicine(request, pk):
    medicine = get_object_or_404(Medicine, medicine_id=pk)
    medicine.delete()
    messages.success(request, "Medicine deleted successfully.")
    return redirect('manage_medicines')


@role_required('receptionist')
def schedule_appointment(request):

    form = AppointmentForm(request.POST or None)

    search_query = request.GET.get('search', '').strip()

    if search_query:
        import re
        pat_match = re.match(r'^pat[-_]?(\d+)$', search_query, re.IGNORECASE)

        queryset = Patient.objects.filter(
            name__icontains=search_query
        ) | Patient.objects.filter(
            phone__icontains=search_query
        )

        if pat_match:
            pid = pat_match.group(1)
            queryset = queryset | Patient.objects.filter(patient_id=pid)
        elif search_query.isdigit():
            queryset = queryset | Patient.objects.filter(patient_id=int(search_query))

        form.fields['patient'].queryset = queryset.distinct()

    # REMOVE STATUS FIELD
    form.fields.pop('status')

    if request.method == 'POST':

        if form.is_valid():

            appointment = form.save(commit=False)

            # AUTO SET STATUS
            appointment.status = 'Pending'

            appointment.save()

            messages.success(
                request,
                "Appointment scheduled successfully."
            )

            return redirect('schedule_appointment')

    return render(
        request,
        'hospitalapp/receptionist/schedule.html',
        {
            'form': form,
            'search_query': search_query
        }
    )

    
@role_required('pharmacist')
def update_stock(request, pk):
    medicine = get_object_or_404(Medicine, medicine_id=pk)
    if request.method == 'POST':
        new_stock = request.POST.get('stock')
        medicine.stock = new_stock
        medicine.save()
        messages.success(request, "Stock updated.")
    return redirect('pharmacist_dashboard')


@role_required('admin')
def add_receptionist(request):

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'receptionist'
            user.save()

            messages.success(request, "Receptionist added successfully!")
            return redirect('admin_dashboard')

    else:
        form = UserRegistrationForm()

    return render(request, 'hospitalapp/admin/add_receptionist.html', {'form': form})

@role_required('admin')
def add_pharmacist(request):

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.role = 'pharmacist'
            user.set_password(form.cleaned_data['password'])

            user.save()

            print("SAVED USER:", user.pk)

            messages.success(request, "Pharmacist added successfully!")
            return redirect('admin_dashboard')

        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = UserRegistrationForm()

    return render(request, 'hospitalapp/admin/add_pharmacist.html', {
        'form': form
    })


@role_required('admin')
def add_laboratoryist(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'lab_technician'
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Laboratoryist added successfully!")
            return redirect('admin_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'hospitalapp/admin/add_laboratoryist.html', {
        'form': form
    })


@role_required('admin')
def add_radiologist(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'radiologist'
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Radiologist added successfully!")
            return redirect('admin_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'hospitalapp/admin/add_radiologist.html', {
        'form': form
    })


@role_required('admin')
def add_nursing_station(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'nursing_station'
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Nursing Station user added successfully!")
            return redirect('manage_staff')
    else:
        form = UserRegistrationForm()
    return render(request, 'hospitalapp/admin/add_nursing_station.html', {
        'form': form
    })


@role_required('admin')
def add_inventory_manager(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'inventory_manager'
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Inventory Manager added successfully!")
            return redirect('manage_staff')
    else:
        form = UserRegistrationForm()
    return render(request, 'hospitalapp/admin/add_inventory_manager.html', {
        'form': form
    })


@role_required('admin')
def add_store_keeper(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'store_keeper'
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Store Keeper added successfully!")
            return redirect('manage_staff')
    else:
        form = UserRegistrationForm()
    return render(request, 'hospitalapp/admin/add_store_keeper.html', {
        'form': form
    })



@role_required('admin')
def manage_staff(request):
    from django.db.models import Q
    staff_members = User.objects.filter(
        Q(role__in=['receptionist', 'pharmacist', 'senior_pharmacist', 'pharmacy_supervisor', 'inventory_manager', 'store_keeper', 'lab_technician', 'laboratoryist', 'radiologist', 'radiology_technician', 'nursing_station']) |
        Q(role='') |
        Q(role__isnull=True)
    ).exclude(role='admin').order_by('-user_id')
    return render(request, 'hospitalapp/admin/manage_staff.html', {
        'staff_members': staff_members
    })


@role_required('admin')
def update_staff(request, pk):
    staff = get_object_or_404(User, user_id=pk)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, f"Staff member {staff.username} updated successfully!")
            return redirect('manage_staff')
    else:
        form = StaffEditForm(instance=staff)
    return render(request, 'hospitalapp/admin/update_staff.html', {
        'form': form,
        'staff': staff
    })


@role_required('admin')
def delete_staff(request, pk):
    staff = get_object_or_404(User, user_id=pk)
    username = staff.username
    staff.delete()
    messages.success(request, f"Staff member {username} deleted successfully!")
    return redirect('manage_staff')


@login_required
def update_appointment_status(request, pk, status):

    # ONLY ADMIN & RECEPTIONIST
    if request.user.role not in ['admin', 'receptionist']:

        return HttpResponseForbidden(
            "You are not authorized."
        )

    appointment = get_object_or_404(
        Appointment,
        appointment_id=pk
    )

    appointment.status = status

    appointment.save()

    messages.success(
        request,
        f"Appointment marked as {status}."
    )

    return redirect('manage_appointments')


# Duplicated approve_appointment view removed


@role_required('receptionist')
def complete_appointment(request, pk):

    appointment = get_object_or_404(Appointment, appointment_id=pk)

    if appointment.status != "Approved":
        messages.error(request, "Only approved appointments can be completed.")
        return redirect('manage_appointments')

    bill = Bill.objects.filter(appointment=appointment, bill_type='appointment').first()
    if bill:
        if bill.payment_status == 'Paid':
            appointment.status = 'Completed'
            appointment.save()
            messages.success(request, "Appointment completed.")
            return redirect('manage_appointments')
        return redirect('create_payment', bill_id=bill.bill_id)
    else:
        messages.error(request, "No bill found for this appointment.")
        return redirect('manage_appointments')

@role_required('receptionist')
def cancel_appointment(request, pk):

    appointment = get_object_or_404(Appointment, appointment_id=pk)

    if appointment.status in ["Completed", "Cancelled"]:
        messages.error(request, "Cannot cancel this appointment.")
        return redirect('manage_appointments')

    appointment.status = 'Cancelled'
    appointment.save()

    messages.success(request, "Appointment cancelled successfully.")
    return redirect('manage_appointments')

@role_required('receptionist')
def delete_appointment(request, pk):

    appointment = get_object_or_404(
        Appointment,
        appointment_id=pk
    )

    appointment.delete()

    messages.success(
        request,
        "Appointment deleted successfully."
    )

    return redirect('manage_appointments')

def manage_prescriptions(request):
    prescriptions = Prescription.objects.all().order_by('-created_at')

    return render(request, 'hospitalapp/pharmacist/prescriptions.html', {
        'prescriptions': prescriptions
    })

def prescription_detail(request, pk):

    prescription = get_object_or_404(Prescription, prescription_id=pk)

    patient = Patient.objects.get(patient_id=prescription.patient_id)
    doctor = Doctor.objects.get(doctor_id=prescription.doctor_id)

    return render(request, 'hospitalapp/pharmacist/prescription_detail.html', {
        'prescription': prescription,
        'patient': patient,
        'doctor': doctor
    })

def dispense_prescription(request, pk):

    prescription = get_object_or_404(Prescription, prescription_id=pk)

    if prescription.status == "Dispensed":
        messages.warning(request, "Already dispensed!")
        return redirect("manage_prescriptions")

    items = PrescriptionMedicine.objects.filter(prescription=prescription)

    # check stock first
    for item in items:
        if item.medicine.stock < item.quantity:
            messages.error(request, f"Not enough stock for {item.medicine.name}")
            return redirect("manage_prescriptions")

    # reduce stock
    for item in items:
        item.medicine.stock -= item.quantity
        item.medicine.save()

    # update status
    prescription.status = "Dispensed"
    prescription.save()

    messages.success(request, "Dispensed successfully + stock updated")
    return redirect("manage_prescriptions")



def delete_prescription(request, pk):

    prescription = get_object_or_404(Prescription, prescription_id=pk)

    prescription.delete()

    messages.success(request, "Prescription deleted successfully!")
    return redirect('prescription_history')

def recalculate_ip_bill(admission):
    # 1. Calculate days admitted
    end_date = admission.discharge_date if admission.discharge_date else timezone.now()
    days = (end_date - admission.admission_date).days
    if days <= 0:
        days = 1  # Minimum 1 day charge
    
    # 2. Define rates
    ward_rates = {
        'General Ward': Decimal('500.00'),
        'Semi Private': Decimal('1000.00'),
        'Private Room': Decimal('2000.00'),
        'ICU': Decimal('5000.00'),
        'Casuality Ward': Decimal('1500.00')
    }
    room_rate = ward_rates.get(admission.ward_type, Decimal('500.00'))
    nursing_rate = Decimal('300.00')
    
    # 3. Create or update Room Charge and Nursing Charge in IPCharge
    room_charge = IPCharge.objects.filter(
        admission=admission,
        charge_type='Room Charge',
        description__startswith='Room Charge ('
    ).first()
    if not room_charge:
        room_charge = IPCharge.objects.create(
            admission=admission,
            charge_type='Room Charge',
            description=f'Room Charge ({admission.ward_type}) x{days} day(s)',
            amount=room_rate * days
        )
    else:
        room_charge.description = f'Room Charge ({admission.ward_type}) x{days} day(s)'
        room_charge.amount = room_rate * days
        room_charge.save()
    
    nursing_charge = IPCharge.objects.filter(
        admission=admission,
        charge_type='Nursing Charge'
    ).first()
    if not nursing_charge:
        nursing_charge = IPCharge.objects.create(
            admission=admission,
            charge_type='Nursing Charge',
            description=f'Nursing Charge x{days} day(s)',
            amount=nursing_rate * days
        )
    else:
        nursing_charge.description = f'Nursing Charge x{days} day(s)'
        nursing_charge.amount = nursing_rate * days
        nursing_charge.save()
    
    # 3b. Catch-up merge: auto-merge any un-merged CasualtyBill charges
    casualty_case = Casuality.objects.filter(patient=admission.patient, status='Admitted').first()
    if casualty_case:
        unbilled = CasualtyBill.objects.filter(casualty=casualty_case, merged_to_ip=False)
        for cb in unbilled:
            IPCharge.objects.create(
                admission=admission,
                charge_type='Pharmacy Bill',
                description=f"[Emergency] {cb.description}",
                amount=cb.amount
            )
            cb.merged_to_ip = True
            cb.save()

    # 3c. Auto-merge any un-merged Lab and Radiology Bills for this patient
    pending_bills = Bill.objects.filter(
        patient=admission.patient,
        bill_type__in=['laboratory', 'radiology'],
        payment_status__in=['Pending', 'Unpaid']
    )
    for bill in pending_bills:
        already_merged = IPCharge.objects.filter(pharmacy_bill=bill).exists()
        if not already_merged:
            charge_type = 'Laboratory Charge' if bill.bill_type == 'laboratory' else 'Radiology Charge'
            
            if bill.bill_type == 'laboratory' and bill.lab_order:
                desc = f"Lab Order #{bill.lab_order.id}"
                bill.lab_order.admission = admission
                bill.lab_order.save()
                
                test_names = [item.test.name for item in bill.lab_order.items.all()]
                if test_names:
                    desc += f" - {', '.join(test_names)}"
            elif bill.bill_type == 'radiology' and bill.radiology_order:
                desc = f"Radiology Order #{bill.radiology_order.id}"
                bill.radiology_order.admission = admission
                bill.radiology_order.save()
                
                test_names = [item.test.name for item in bill.radiology_order.items.all()]
                if test_names:
                    desc += f" - {', '.join(test_names)}"
            else:
                desc = f"{bill.get_bill_type_display()} #{bill.bill_id}"
                
            IPCharge.objects.create(
                admission=admission,
                charge_type=charge_type,
                description=desc,
                amount=bill.total_amount,
                pharmacy_bill=bill
            )

    # Ensure all LabOrders linked directly to this admission are in IPCharge
    for order in LabOrder.objects.filter(admission=admission):
        for item in order.items.all():
            desc = f"Lab Order #{order.id} - {item.test.name}"
            charge_exists = IPCharge.objects.filter(
                admission=admission,
                charge_type='Laboratory Charge',
                description=desc
            ).exists()
            if not charge_exists:
                IPCharge.objects.create(
                    admission=admission,
                    charge_type='Laboratory Charge',
                    description=desc,
                    amount=item.test.price
                )

    # Ensure all RadiologyOrders linked directly to this admission are in IPCharge
    for order in RadiologyOrder.objects.filter(admission=admission):
        for item in order.items.all():
            desc = f"Radiology Order #{order.id} - {item.test.name}"
            charge_exists = IPCharge.objects.filter(
                admission=admission,
                charge_type='Radiology Charge',
                description=desc
            ).exists()
            if not charge_exists:
                IPCharge.objects.create(
                    admission=admission,
                    charge_type='Radiology Charge',
                    description=desc,
                    amount=item.test.price
                )

    # 4. Sum all charges
    charges = IPCharge.objects.filter(admission=admission)
    subtotal = sum(c.amount for c in charges)
    
    # 5. Get IPBill
    ip_bill, _ = IPBill.objects.get_or_create(
        admission=admission,
        defaults={'payment_status': 'Pending'}
    )
    
    # Update IPBill totals
    gst = subtotal * Decimal('0.18')
    ip_bill.subtotal = subtotal
    ip_bill.gst = gst
    ip_bill.grand_total = subtotal + gst - Decimal(str(ip_bill.discount))
    ip_bill.save()


@role_required('pharmacist')
def generate_bill(request, prescription_id):

    prescription = get_object_or_404(
        Prescription,
        prescription_id=prescription_id
    )

    # 🔥 PREVENT DUPLICATE BILL
    existing_bill = Bill.objects.filter(
        prescription=prescription,
        bill_type='pharmacy'
    ).exclude(payment_status='Failed').first()

    if existing_bill:
        messages.warning(request, "Bill already generated for this prescription.")
        return redirect('receptionist_bills')

    items = PrescriptionMedicine.objects.filter(
        prescription=prescription
    )

    subtotal = Decimal('0.00')

    for item in items:
        item_total = Decimal(item.medicine.price) * Decimal(item.quantity)
        subtotal += item_total

    # ✅ FIXED DECIMAL USAGE
    gst = subtotal * Decimal('0.18')
    grand_total = subtotal + gst

    # Check if patient is currently admitted or has a linked admission
    admission = getattr(prescription, 'admission', None)
    if not admission:
        admission = Admission.objects.filter(patient=prescription.patient, status='Admitted').first()
    is_admitted = admission is not None

    if is_admitted:
        # Create Bill without Razorpay order
        bill = Bill.objects.create(
            patient=prescription.patient,
            appointment=prescription.appointment,
            prescription=prescription,
            total_amount=grand_total,
            payment_status='Pending',
            bill_type='pharmacy',
            razorpay_order_id=None
        )
        
        # Link to IPCharge
        IPCharge.objects.create(
            admission=admission,
            charge_type='Pharmacy Bill',
            description=f"Pharmacy Bill #{bill.bill_id} (Prescription #{prescription.prescription_id})",
            amount=grand_total,
            pharmacy_bill=bill
        )
        
        # Recalculate bill
        recalculate_ip_bill(admission)
        
        payment = None
        razorpay_key = None
    else:
        # Razorpay order (safe conversion)
        payment = client.order.create({
            "amount": int(grand_total * 100),
            "currency": "INR",
            "payment_capture": 1
        })

        bill = Bill.objects.create(
            patient=prescription.patient,
            appointment=prescription.appointment,
            prescription=prescription,
            total_amount=grand_total,
            payment_status='Pending',
            bill_type='pharmacy',
            razorpay_order_id=payment['id']
        )
        razorpay_key = settings.RAZORPAY_KEY_ID

    bill_items = []
    for item in items:
        item_total = Decimal(item.medicine.price) * Decimal(item.quantity)
        bill_items.append({
            'name': item.medicine.name,
            'quantity': item.quantity,
            'price': item.medicine.price,
            'subtotal': item_total,
        })

    return render(request, 'hospitalapp/pharmacist/bill.html', {
        'prescription': prescription,
        'bill_items': bill_items,
        'subtotal': subtotal,
        'gst_percentage': 18,
        'gst_amount': gst,
        'total': grand_total,
        'payment': payment,
        'bill': bill,
        'razorpay_key': razorpay_key,
        'is_admitted': is_admitted,
        'admission_id': admission.admission_id if is_admitted else None
    })

# =========================================
# PAYMENT SUCCESS
# =========================================
@login_required
def payment_success(request):
    bill_id = request.GET.get('bill_id')
    order_id = request.GET.get('order_id')
    bill_type = request.GET.get('type')

    from django.http import Http404

    if bill_type == 'ip':
        if bill_id:
            ip_bill = get_object_or_404(IPBill, ip_bill_id=bill_id)
        elif order_id:
            ip_bill = get_object_or_404(IPBill, razorpay_order_id=order_id)
        else:
            raise Http404("Bill not found")

        # Adapt for template compatibility
        ip_bill.bill_id = ip_bill.ip_bill_id
        ip_bill.total_amount = ip_bill.grand_total
        
        class BillDisplayWrapper:
            def __init__(self, obj):
                self.obj = obj
                self.bill_id = obj.ip_bill_id
                self.total_amount = obj.grand_total
                self.patient = obj.admission.patient
                self.created_at = obj.created_at
                self.payment_status = obj.payment_status
                self.admission_id = obj.admission.admission_id
                self.is_ip = True

            def get_bill_type_display(self):
                return "Inpatient Discharge Bill"

        return render(
            request,
            'hospitalapp/pharmacist/payment_success.html',
            {
                'bill': BillDisplayWrapper(ip_bill)
            }
        )

    if bill_id:
        bill = get_object_or_404(
            Bill,
            bill_id=bill_id
        )
        if bill.razorpay_order_id:
            bills = Bill.objects.filter(razorpay_order_id=bill.razorpay_order_id)
        else:
            bills = Bill.objects.filter(bill_id=bill_id)
    elif order_id:
        bills = Bill.objects.filter(
            razorpay_order_id=order_id
        )
        if not bills.exists():
            raise Http404("Bill not found")
        bill = bills.first()
    else:
        raise Http404("Bill not found")

    # Final safety update
    for b in bills:
        if b.payment_status != "Paid":
            b.payment_status = "Paid"
            b.save()

    if bills.count() > 1:
        total_amount = sum(b.total_amount for b in bills)
        bill_ids_str = ", ".join(f"#{b.bill_id}" for b in bills)
        
        class MultiBillDisplayWrapper:
            def __init__(self, main_bill, total_amt, ids_str, all_bills):
                self.bill_id = ids_str
                self.total_amount = total_amt
                self.created_at = main_bill.created_at
                self.payment_status = "Paid"
                self.patient = main_bill.patient
                self.is_ip = False
                self.all_bills = all_bills

            @property
            def consulting_doctor(self):
                for b in self.all_bills:
                    if b.consulting_doctor:
                        return b.consulting_doctor
                return None

            def get_bill_type_display(self):
                return "Consolidated Payment"

        display_bill = MultiBillDisplayWrapper(bill, total_amount, bill_ids_str, bills)
    else:
        display_bill = bill

    return render(
        request,
        'hospitalapp/pharmacist/payment_success.html',
        {
            'bill': display_bill
        }
    )

# =========================================
# DOWNLOAD BILL PDF
# =========================================

def download_bill(request, bill_id):

    bill = get_object_or_404(
        Bill,
        bill_id=bill_id
    )

    appointment = bill.appointment
    prescription = bill.prescription
    doctor = None

    if appointment and appointment.doctor:
        doctor = appointment.doctor
    elif prescription and prescription.doctor:
        doctor = prescription.doctor

    subtotal = 0
    table_data = []
    bill_title_text = "BILL"

    if bill.bill_type == 'appointment':
        # Consultation fee (including 18% GST)
        grand_total = float(bill.total_amount)
        subtotal = grand_total / 1.18
        gst = grand_total - subtotal
        doc_name = f" (Dr. {doctor.name})" if doctor else ""
        table_data.append(["Consultation / Service", "Qty", "Fee", "Total"])
        table_data.append([
            f"Consultation Fee{doc_name}",
            "1",
            f"Rs. {subtotal:.2f}",
            f"Rs. {subtotal:.2f}"
        ])
        bill_title_text = "CONSULTATION BILL"

    elif bill.bill_type == 'laboratory':
        import datetime
        order = bill.lab_order
        if not order:
            order = LabOrder.objects.filter(
                patient=bill.patient,
                created_at__lte=bill.created_at + datetime.timedelta(seconds=5),
                created_at__gte=bill.created_at - datetime.timedelta(seconds=5)
            ).first()
            if not order:
                order = LabOrder.objects.filter(patient=bill.patient).order_by('-created_at').first()

        if order and order.ordered_by:
            doctor = order.ordered_by

        table_data.append(["Investigation Test", "Qty", "Price", "Total"])
        if order:
            for item in order.items.all():
                test_price = float(item.test.price) / 1.18
                table_data.append([
                    item.test.name,
                    "1",
                    f"Rs. {test_price:.2f}",
                    f"Rs. {test_price:.2f}"
                ])
        
        grand_total = float(bill.total_amount)
        subtotal = grand_total / 1.18
        gst = grand_total - subtotal

        if not order or not order.items.exists():
            table_data.append([
                "Laboratory Investigation Charges",
                "1",
                f"Rs. {subtotal:.2f}",
                f"Rs. {subtotal:.2f}"
            ])
        bill_title_text = "LABORATORY BILL"

    elif bill.bill_type == 'radiology':
        import datetime
        order = bill.radiology_order
        if not order:
            order = RadiologyOrder.objects.filter(
                patient=bill.patient,
                created_at__lte=bill.created_at + datetime.timedelta(seconds=5),
                created_at__gte=bill.created_at - datetime.timedelta(seconds=5)
            ).first()
            if not order:
                order = RadiologyOrder.objects.filter(patient=bill.patient).order_by('-created_at').first()

        if order and order.ordered_by:
            doctor = order.ordered_by

        table_data.append(["Radiology Procedure", "Qty", "Price", "Total"])
        if order:
            for item in order.items.all():
                test_price = float(item.test.price) / 1.18
                table_data.append([
                    item.test.name,
                    "1",
                    f"Rs. {test_price:.2f}",
                    f"Rs. {test_price:.2f}"
                ])

        grand_total = float(bill.total_amount)
        subtotal = grand_total / 1.18
        gst = grand_total - subtotal

        if not order or not order.items.exists():
            table_data.append([
                "Radiology Investigation Charges",
                "1",
                f"Rs. {subtotal:.2f}",
                f"Rs. {subtotal:.2f}"
            ])
        bill_title_text = "RADIOLOGY BILL"

    else:
        # Pharmacy bill
        if not prescription:
            if appointment:
                prescription = Prescription.objects.filter(
                    appointment=appointment
                ).first()
            if not prescription:
                prescription = Prescription.objects.filter(
                    patient=bill.patient
                ).order_by('-created_at').first()

        if prescription and prescription.doctor:
            doctor = prescription.doctor

        medicines = []
        if prescription:
            medicines = PrescriptionMedicine.objects.filter(
                prescription=prescription
            )

        table_data.append(["Medicine", "Qty", "Price", "Total"])
        for item in medicines:
            medicine_name = item.medicine.name
            quantity = item.quantity
            price = float(item.medicine.price)
            total = quantity * price
            subtotal += total
            table_data.append([
                medicine_name,
                str(quantity),
                f"Rs. {price:.2f}",
                f"Rs. {total:.2f}"
            ])

        if subtotal == 0:
            grand_total = float(bill.total_amount)
            subtotal = grand_total / 1.18
            gst = grand_total - subtotal
            table_data.append([
                "Pharmacy Medicines / Supplies",
                "1",
                f"Rs. {subtotal:.2f}",
                f"Rs. {subtotal:.2f}"
            ])
        else:
            gst = subtotal * 0.18
            grand_total = subtotal + gst
        bill_title_text = "MEDICINE BILL"

    import io
    buffer = io.BytesIO()

    p = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # ======================================
    # BACKGROUND HEADER (Clean Premium White with Bottom Border)
    # ======================================
    p.setFillColor(colors.white)
    p.rect(0, 750, width, 100, fill=1)
    
    # Draw top/bottom accent line
    p.setFillColor(colors.HexColor("#0b4c8c")) # Asha Blue
    p.rect(0, 845, width, 5, fill=1)
    p.setFillColor(colors.HexColor("#4caf50")) # Asha Green
    p.rect(0, 750, width, 3, fill=1)

    # Logo Image on Left
    import os
    from django.conf import settings
    logo_path = os.path.join(settings.BASE_DIR, 'hospitalapp', 'static', 'hospitalapp', 'images', 'logo.png')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 40, 758, width=80, height=80, mask='auto')

    # Hospital Name and Details on Right
    p.setFillColor(colors.HexColor("#0b4c8c")) # ASHA Blue
    p.setFont("Helvetica-Bold", 24)
    p.drawString(135, 815, "ASHA HOSPITAL")

    p.setFillColor(colors.HexColor("#4caf50")) # ASHA Green
    p.setFont("Helvetica-Bold", 10)
    p.drawString(135, 800, "Care | Compassion | Commitment")

    p.setFillColor(colors.HexColor("#555555"))
    p.setFont("Helvetica", 10)
    p.drawString(135, 785, "Thodupuzha P.O, Idukki, Kerala")
    p.drawString(135, 770, "Phone : +91 9876543210  |  Email: contact@ashahospital.com")

    # ======================================
    # BILL TITLE
    # ======================================

    p.setFillColor(colors.HexColor("#198754"))

    p.roundRect(
        180,
        720,
        230,
        30,
        8,
        fill=1
    )

    p.setFillColor(colors.white)

    p.setFont("Helvetica-Bold", 16)

    p.drawCentredString(
        width / 2,
        730,
        bill_title_text
    )

    # ======================================
    # BILL DETAILS BOX
    # ======================================

    p.setFillColor(colors.HexColor("#f8f9fa"))

    p.roundRect(
        40,
        560,
        520,
        130,
        10,
        fill=1
    )

    p.setFillColor(colors.black)

    p.setFont("Helvetica-Bold", 12)

    p.drawString(
        60,
        660,
        f"Bill ID : #{bill.bill_id}"
    )

    p.drawString(
        60,
        635,
        f"Patient : {bill.patient.name}"
    )

    doc_name = f"Dr. {doctor.name}" if doctor else "N/A"
    p.drawString(
        60,
        610,
        f"Doctor : {doc_name}"
    )

    p.drawString(
        60,
        585,
        f"Date : {bill.created_at.strftime('%d-%m-%Y')}"
    )

    p.drawString(
        330,
        660,
        f"Payment : {bill.payment_status}"
    )

    # ======================================
    # TABLE
    # ======================================

    table = Table(
        table_data,
        colWidths=[230, 70, 100, 100]
    )

    style = TableStyle([

        # HEADER
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),

        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('FONTSIZE', (0, 0), (-1, 0), 12),

        # BODY
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),

        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),

        ('GRID', (0, 0), (-1, -1), 1, colors.grey),

        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        ('TOPPADDING', (0, 1), (-1, -1), 8),

        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

    ])

    table.setStyle(style)

    table.wrapOn(p, width, height)

    table.drawOn(
        p,
        50,
        350
    )

    # ======================================
    # TOTAL SECTION
    # ======================================

    p.setFillColor(colors.HexColor("#e9f7ef"))

    p.roundRect(
        300,
        240,
        240,
        90,
        10,
        fill=1
    )

    p.setFillColor(colors.black)

    p.setFont("Helvetica-Bold", 13)

    p.drawString(
        320,
        300,
        f"Sub Total : Rs. {subtotal:.2f}"
    )

    p.drawString(
        320,
        275,
        f"GST (18%) : Rs. {gst:.2f}"
    )

    p.setFillColor(colors.HexColor("#198754"))

    p.setFont("Helvetica-Bold", 15)

    p.drawString(
        320,
        248,
        f"Grand Total : Rs. {grand_total:.2f}"
    )

    # ======================================
    # FOOTER
    # ======================================

    p.setFillColor(colors.HexColor("#0d6efd"))

    p.rect(0, 0, width, 70, fill=1)

    p.setFillColor(colors.white)

    p.setFont("Helvetica-Bold", 12)

    p.drawCentredString(
        width / 2,
        45,
        "Thank You For Choosing ASHA HOSPITAL"
    )

    p.setFont("Helvetica", 10)

    p.drawCentredString(
        width / 2,
        25,
        "Get Well Soon • Stay Healthy"
    )

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="ASHA_Hospital_Bill_{bill.bill_id}.pdf"'
    )

    return response






# Duplicated receptionist_bills view removed



CONSULTATION_FEE = 500

CONSULTATION_FEE = 500

@role_required('receptionist')
def approve_appointment(request, pk):

    appointment = get_object_or_404(Appointment, appointment_id=pk)

    if appointment.status == "Approved":
        messages.warning(request, "Already approved")
        return redirect('manage_appointments')

    appointment.status = "Approved"
    appointment.save()

    if not Bill.objects.filter(appointment=appointment, bill_type='appointment').exists():

        Bill.objects.create(
            patient=appointment.patient,
            appointment=appointment,
            total_amount=CONSULTATION_FEE,
            bill_type='appointment',
            payment_status='Pending'
        )

    messages.success(request, "Appointment approved & bill created")
    return redirect('manage_appointments')


@login_required
def create_payment(request, bill_id):

    bill = get_object_or_404(
        Bill,
        bill_id=bill_id
    )

    # Prevent duplicate payment
    if bill.payment_status == "Paid":

        messages.info(
            request,
            "This bill is already paid."
        )

        return redirect(
            f'/payment-success/?bill_id={bill.bill_id}'
        )

    # Convert amount to paisa
    amount = int(
        Decimal(bill.total_amount) * 100
    )

    # Create Razorpay Order
    order = client.order.create({

        "amount": amount,

        "currency": "INR",

        "payment_capture": 1

    })

    # Save Razorpay Order ID
    bill.razorpay_order_id = order['id']
    bill.save()

    return render(

        request,

        "hospitalapp/payment/razorpay_payment.html",

        {

            "bill": bill,

            "order_id": order['id'],

            "razorpay_key":
                settings.RAZORPAY_KEY_ID,

            "amount": amount

        }

    )


@login_required
def pay_multiple_bills(request):
    if request.method == 'POST':
        bill_ids = request.POST.getlist('bill_ids')
        if not bill_ids:
            messages.error(request, "No bills selected for payment.")
            return redirect('receptionist_bills' if request.user.role == 'receptionist' else 'patient_bills')

        bills = Bill.objects.filter(bill_id__in=bill_ids, payment_status='Pending')
        if not bills.exists():
            messages.error(request, "Selected bills are already paid or invalid.")
            return redirect('receptionist_bills' if request.user.role == 'receptionist' else 'patient_bills')

        # Ensure all selected bills belong to the same patient
        patient_ids = bills.values_list('patient_id', flat=True).distinct()
        if len(patient_ids) > 1:
            messages.error(request, "Cannot pay bills of multiple patients together.")
            return redirect('receptionist_bills' if request.user.role == 'receptionist' else 'patient_bills')

        total_amount = sum(bill.total_amount for bill in bills)
        amount_in_paisa = int(Decimal(total_amount) * 100)

        # Create Razorpay Order
        order = client.order.create({
            "amount": amount_in_paisa,
            "currency": "INR",
            "payment_capture": 1
        })

        # Save Razorpay Order ID to all bills
        for bill in bills:
            bill.razorpay_order_id = order['id']
            bill.save()

        # Build a wrapper display bill for the payment screen
        class DummyDoctor:
            name = "N/A"
        class DummyAppointment:
            doctor = DummyDoctor()

        class MultiBillDisplayWrapper:
            def __init__(self, main_bill, total_amt, ids_str, all_bills):
                self.bill_id = ids_str
                self.total_amount = total_amt
                self.created_at = main_bill.created_at
                self.payment_status = "Pending"
                self.patient = main_bill.patient
                self.is_ip = False
                self.all_bills = all_bills
                self.appointment = DummyAppointment()

            @property
            def consulting_doctor(self):
                for b in self.all_bills:
                    if b.consulting_doctor:
                        return b.consulting_doctor
                return None

            def get_bill_type_display(self):
                return "Consolidated Payment"

        bill_ids_str = ", ".join(str(b.bill_id) for b in bills)
        display_bill = MultiBillDisplayWrapper(bills.first(), total_amount, bill_ids_str, bills)

        return render(
            request,
            "hospitalapp/payment/razorpay_payment.html",
            {
                "bill": display_bill,
                "order_id": order['id'],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": amount_in_paisa
            }
        )
    else:
        messages.error(request, "Invalid request method.")
        return redirect('receptionist_bills' if request.user.role == 'receptionist' else 'patient_bills')


@csrf_exempt
def verify_payment(request):

    if request.method != "POST":

        return JsonResponse({

            "status": "failed"

        })

    try:

        data = json.loads(request.body)

        razorpay_order_id = data.get(
            'razorpay_order_id'
        )

        razorpay_payment_id = data.get(
            'razorpay_payment_id'
        )

        razorpay_signature = data.get(
            'razorpay_signature'
        )

        # Verify Signature
        client.utility.verify_payment_signature({

            "razorpay_order_id":
                razorpay_order_id,

            "razorpay_payment_id":
                razorpay_payment_id,

            "razorpay_signature":
                razorpay_signature

        })

        # Find Bills
        bills = Bill.objects.filter(
            razorpay_order_id=razorpay_order_id
        )

        if not bills.exists():

            return JsonResponse({

                "status": "failed"

            })

        # Avoid duplicate updates
        for bill in bills:
            if bill.payment_status != "Paid":

                bill.razorpay_payment_id = (
                    razorpay_payment_id
                )

                bill.payment_status = "Paid"

                bill.save()

                if bill.bill_type == 'appointment' and bill.appointment:
                    bill.appointment.status = 'Completed'
                    bill.appointment.save()

        return JsonResponse({

            "status": "success",

            "redirect_url":
                f"/payment-success/?order_id={razorpay_order_id}"

        })

    except Exception as e:

        print("VERIFY PAYMENT ERROR:", e)

        return JsonResponse({

            "status": "failed"

        })


def departments(request):
    specializations = Doctor.objects.values_list(
        'specialization',
        flat=True
    ).distinct()

    return render(request, 'hospitalapp/departments.html', {
        'specializations': specializations
    })

def doctors_by_specialization(request, spec):
    doctors = Doctor.objects.filter(
        specialization=spec
    )

    return render(request, 'hospitalapp/doctors_by_specialization.html', {
        'doctors': doctors,
        'specialization': spec
    })

@role_required('doctor')
def patient_history(request, patient_id):

    patient = get_object_or_404(Patient, patient_id=patient_id)

    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')

    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')

    bills = Bill.objects.filter(patient=patient).order_by('-created_at')

    lab_orders = LabOrder.objects.filter(patient=patient).prefetch_related('items', 'items__labresult').order_by('-created_at')
    radiology_orders = RadiologyOrder.objects.filter(patient=patient).prefetch_related('items', 'items__radiologyreport').order_by('-created_at')

    return render(request, 'hospitalapp/doctor/patient_history.html', {
        'patient': patient,
        'appointments': appointments,
        'prescriptions': prescriptions,
        'bills': bills,
        'lab_orders': lab_orders,
        'radiology_orders': radiology_orders
    })


@role_required('receptionist')
def casuality_dashboard(request):
    if request.method == 'POST':
        patient_option = request.POST.get('patient_option')
        doctor_id = request.POST.get('doctor_id')
        priority = request.POST.get('priority', 'Medium')
        emergency_reason = request.POST.get('emergency_reason')

        doctor = get_object_or_404(Doctor, doctor_id=doctor_id)

        if patient_option == 'new':
            name = request.POST.get('name')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            phone = request.POST.get('phone')

            # Create User profile
            import random
            username = name.lower().replace(" ", "") + str(random.randint(100, 999))
            while User.objects.filter(username=username).exists():
                username = name.lower().replace(" ", "") + str(random.randint(100, 999))

            user = User.objects.create_user(
                username=username,
                password='Password@123',
                role='patient',
                email=f"{username}@ashahospital.com"
            )

            # Create Patient profile
            patient = Patient.objects.create(
                user=user,
                name=name,
                age=int(age) if age else 0,
                gender=gender,
                phone=phone,
                email=user.email
            )
        else:
            patient_id = request.POST.get('existing_patient_id')
            patient = get_object_or_404(Patient, patient_id=patient_id)

        # Create Approved appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now().date(),
            status='Approved',
            reason=f"Emergency: {emergency_reason}"
        )

        # Create Casuality Entry
        Casuality.objects.create(
            patient=patient,
            doctor=doctor,
            priority=priority,
            emergency_reason=emergency_reason,
            status='Pending'
        )

        messages.success(request, f"Emergency entry created for {patient.name}.")
        return redirect('casuality_dashboard')

    patients = Patient.objects.all().order_by('name')
    # Filter only Emergency doctors for Casualty
    doctors = Doctor.objects.filter(specialization='Emergency Medicine').order_by('name')
    queue = Casuality.objects.filter(status__in=['Pending', 'Under Emergency Care', 'Stabilized', 'Referred']).order_by('-created_at')

    return render(request, 'hospitalapp/receptionist/casuality.html', {
        'patients': patients,
        'doctors': doctors,
        'queue': queue
    })


@role_required('receptionist')
def update_casuality_status(request, pk, status):
    case = get_object_or_404(Casuality, id=pk)
    case.status = status
    case.save()
    messages.success(request, f"Casuality status updated to {status}.")
    return redirect('casuality_dashboard')


@role_required('doctor')
def doctor_emergency_dashboard(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    
    from django.db.models import Q, Sum
    queue = Casuality.objects.filter(
        Q(doctor=doctor) | Q(referrals__referred_doctor=doctor, referrals__status='Accepted'),
        status__in=['Pending', 'Under Emergency Care', 'Stabilized', 'Referred']
    ).distinct().annotate(
        total_bill=Sum('casualty_bills__amount')
    ).order_by('-created_at')

    # Attach vital flags to each case in the queue
    for case in queue:
        latest_vital = case.vitals.order_by('-recorded_at').first()
        case.latest_vital = latest_vital
        case.is_critical_vitals = latest_vital and latest_vital.patient_condition == 'Critical'
    
    specialist_doctors = Doctor.objects.exclude(specialization='Emergency Medicine').order_by('specialization', 'name')
    
    return render(request, 'hospitalapp/doctor/emergency.html', {
        'queue': queue,
        'specialist_doctors': specialist_doctors
    })


@role_required('doctor')
def doctor_send_critical_alert(request, casualty_id):
    case = get_object_or_404(Casuality, id=casualty_id)
    doctor = get_object_or_404(Doctor, user=request.user)
    
    # Verify authorization
    is_in_team = (case.doctor == doctor) or CasualityReferral.objects.filter(
        casualty=case, referred_doctor=doctor, status='Accepted'
    ).exists()
    
    if not is_in_team:
        return HttpResponseForbidden("Not authorized to manage this emergency case.")

    if request.method == 'POST':
        message = request.POST.get('critical_message', '').strip()
        if message:
            ClinicalNote.objects.create(
                casualty=case,
                doctor=doctor,
                note_text=f"CRITICAL MEDICAL ALERT: {message}"
            )
            case.status = 'Under Emergency Care'
            case.priority = 'Critical'
            case.save()
            messages.success(request, f"Critical alert sent and care started for {case.patient.name}.")
        else:
            messages.error(request, "Alert message cannot be empty.")
    return redirect('doctor_emergency_dashboard')



@role_required('doctor')
def update_casuality_status_doctor(request, pk, status):
    case = get_object_or_404(Casuality, id=pk)
    doctor = get_object_or_404(Doctor, user=request.user)
    
    is_in_team = (case.doctor == doctor) or CasualityReferral.objects.filter(
        casualty=case, referred_doctor=doctor, status='Accepted'
    ).exists()
    
    if not is_in_team:
        return HttpResponseForbidden("Not authorized to manage this emergency case.")
        
    case.status = status
    case.save()
    messages.success(request, f"Emergency status updated to {status}.")
    return redirect('doctor_emergency_dashboard')
# Refer specialist is defined at the bottom of the file in a consolidated version


@role_required('doctor')
def doctor_refer_inpatient(request, admission_id):
    if request.method == 'POST':
        admission = get_object_or_404(Admission, admission_id=admission_id)
        doctor = get_object_or_404(Doctor, user=request.user)

        specialist_id = request.POST.get('specialist_id')
        specialist = get_object_or_404(Doctor, doctor_id=specialist_id)
        notes = request.POST.get('referral_notes', '')

        # Create Appointment for Specialist
        reason = (
            f"Inpatient Referral from Dr. {doctor.name}. "
            f"Ward: {admission.ward_type}, Bed: {admission.bed_number}. "
            f"Reason: {admission.reason}. Notes: {notes}"
        )
        Appointment.objects.create(
            patient=admission.patient,
            doctor=specialist,
            appointment_date=timezone.now().date(),
            status='Approved',
            reason=reason
        )

        # Immediately link to AdmissionConsultant care team
        AdmissionConsultant.objects.get_or_create(
            admission=admission,
            doctor=specialist
        )

        messages.success(request, f"Patient {admission.patient.name} referred to Dr. {specialist.name} ({specialist.specialization}). Specialist is now part of the collaborative care team.")
    return redirect('doctor_dashboard')




@role_required('doctor')
def doctor_add_prescription_casuality(request, casuality_id):
    case = get_object_or_404(Casuality, id=casuality_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    if case.status not in ['Pending', 'Under Emergency Care', 'Stabilized', 'Referred']:
        messages.error(request, "Emergency prescriptions can only be created for active Casualty patients. If admitted, please use Inpatient Prescriptions.")
        return redirect('doctor_emergency_dashboard')

    # Permission check: must be the primary doctor or assigned specialist
    is_assigned = (case.doctor == doctor) or CasualityReferral.objects.filter(
        casualty=case, referred_doctor=doctor, status='Accepted'
    ).exists()
    if not is_assigned:
        return HttpResponseForbidden("Not authorized to prescribe to this patient.")

    if request.method == 'POST':
        notes = request.POST.get('notes', '').strip()
        medicine_ids = request.POST.getlist('medicine_id')
        dosages = request.POST.getlist('dosage')
        frequencies = request.POST.getlist('frequency')
        durations = request.POST.getlist('duration_days')

        if not medicine_ids:
            messages.error(request, "Please prescribe at least one medicine.")
            return redirect('doctor_add_prescription_casuality', casuality_id=casuality_id)

        try:
            with transaction.atomic():
                prescription = EmergencyPrescription.objects.create(
                    casualty=case,
                    doctor=doctor,
                    notes=notes
                )

                for idx, med_id in enumerate(medicine_ids):
                    if med_id and dosages[idx] and frequencies[idx] and durations[idx]:
                        medicine = get_object_or_404(Medicine, medicine_id=med_id)
                        EmergencyPrescriptionItem.objects.create(
                            prescription=prescription,
                            medicine=medicine,
                            dosage=dosages[idx],
                            frequency=frequencies[idx],
                            duration_days=int(durations[idx])
                        )
                
                if case.status == 'Pending':
                    case.status = 'Under Emergency Care'
                    case.save()

                messages.success(request, f"Emergency prescription logged successfully for {case.patient.name}.")
                return redirect('doctor_emergency_dashboard')
        except Exception as e:
            messages.error(request, f"Prescription Error: {str(e)}")
            return redirect('doctor_add_prescription_casuality', casuality_id=casuality_id)

    medicines = Medicine.objects.filter(stock__gt=0).order_by('name')
    return render(request, 'hospitalapp/doctor/add_emergency_prescription.html', {
        'case': case,
        'medicines': medicines
    })



@role_required('doctor')
def doctor_admit_patient(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    if request.method == 'POST':
        ward_type = request.POST.get('ward_type')
        reason = request.POST.get('reason')

        Admission.objects.create(
            patient=appointment.patient,
            doctor=appointment.doctor,
            ward_type=ward_type,
            reason=reason,
            status='Pending'
        )
        messages.success(request, f"Admission request submitted for {appointment.patient.name}.")
        return redirect('doctor_dashboard')

    return render(request, 'hospitalapp/doctor/admit_patient.html', {
        'patient': appointment.patient,
        'from_casuality': False
    })


@role_required('doctor')
def doctor_admit_casuality(request, casuality_id):
    case = get_object_or_404(Casuality, id=casuality_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    # Check if admitting doctor is authorized (must be casualty doctor or accepted specialist)
    is_in_team = (case.doctor == doctor) or CasualityReferral.objects.filter(
        casualty=case, referred_doctor=doctor, status='Accepted'
    ).exists()

    if not is_in_team:
        messages.error(request, "You are not assigned to this patient's care team.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        ward_type = request.POST.get('ward_type')
        reason = request.POST.get('reason')

        Admission.objects.create(
            patient=case.patient,
            doctor=doctor,
            ward_type=ward_type,
            reason=reason,
            status='Pending'
        )
        messages.success(request, f"Admission request submitted for emergency patient {case.patient.name}.")
        return redirect('doctor_emergency_dashboard')

    referrals = CasualityReferral.objects.filter(casualty=case, status='Accepted')
    return render(request, 'hospitalapp/doctor/admit_patient.html', {
        'patient': case.patient,
        'from_casuality': True,
        'referrals': referrals
    })


@role_required('receptionist')
def admissions_dashboard(request):
    pending_requests = Admission.objects.filter(status='Pending').order_by('-admission_date')
    active_admissions = Admission.objects.filter(status__in=['Admitted', 'Ready For Discharge']).order_by('-admission_date')
    
    for adm in active_admissions:
        recalculate_ip_bill(adm)
        bill = IPBill.objects.filter(admission=adm).first()
        adm.bill_subtotal = bill.subtotal if bill else Decimal('0.00')
        adm.bill_grand_total = bill.grand_total if bill else Decimal('0.00')

    return render(request, 'hospitalapp/receptionist/admissions.html', {
        'pending_requests': pending_requests,
        'active_admissions': active_admissions
    })


@role_required('receptionist')
def approve_admission(request, pk):
    admission = get_object_or_404(Admission, admission_id=pk)
    if request.method == 'POST':
        ward_type = request.POST.get('ward_type')
        bed_id = request.POST.get('bed_id')

        # Link bed object and mark it Occupied
        bed_obj = None
        bed_label = 'N/A'
        if bed_id:
            bed_obj = Bed.objects.filter(id=bed_id, status='Available').first()
            if bed_obj:
                bed_obj.status = 'Occupied'
                bed_obj.patient = admission.patient
                bed_obj.save()
                bed_label = bed_obj.bed_number

        admission.ward_type = ward_type
        admission.bed = bed_obj
        admission.bed_number = bed_label
        admission.status = 'Admitted'
        admission.admission_date = timezone.now()
        admission.save()

        # Create IP Bill
        IPBill.objects.create(
            admission=admission,
            subtotal=Decimal('0.00'),
            gst=Decimal('0.00'),
            grand_total=Decimal('0.00'),
            payment_status='Pending'
        )

        casuality_case = Casuality.objects.filter(patient=admission.patient).exclude(status__in=['Admitted', 'Discharged', 'OT Transfer', 'ICU Transfer']).first()
        
        if casuality_case:
            casuality_case.status = 'Admitted'
            casuality_case.save()
            IPCharge.objects.create(
                admission=admission,
                charge_type='Emergency Charge',
                description='Emergency Room Admission Fee',
                amount=Decimal('1000.00')
            )
            
            # Ensure the casualty doctor and any accepted specialists are added to the care team
            if admission.doctor != casuality_case.doctor:
                AdmissionConsultant.objects.get_or_create(
                    admission=admission,
                    doctor=casuality_case.doctor
                )
            for referral in CasualityReferral.objects.filter(casualty=casuality_case, status='Accepted'):
                AdmissionConsultant.objects.get_or_create(
                    admission=admission,
                    doctor=referral.referred_doctor
                )

        else:
            IPCharge.objects.create(
                admission=admission,
                charge_type='Emergency Charge',
                description='Standard Inpatient Admission Fee',
                amount=Decimal('500.00')
            )

        # Merge all outstanding CasualtyBill charges into IP Bill immediately
        if casuality_case:
            unbilled = CasualtyBill.objects.filter(casualty=casuality_case, merged_to_ip=False)
            for cb in unbilled:
                IPCharge.objects.create(
                    admission=admission,
                    charge_type='Pharmacy Bill',
                    description=f"[Emergency] {cb.description}",
                    amount=cb.amount
                )
                cb.merged_to_ip = True
                cb.save()

        recalculate_ip_bill(admission)

        messages.success(request, f"Admission approved. Patient allocated to bed {bed_label}.")
        return redirect('admissions_dashboard')

    # GET: pre-load available beds for the admission's ward type
    available_beds = Bed.objects.filter(status='Available', ward_type=admission.ward_type)
    return render(request, 'hospitalapp/receptionist/admissions.html', {
        'pending_requests': Admission.objects.filter(status='Pending').order_by('-admission_date'),
        'active_admissions': Admission.objects.filter(status__in=['Admitted', 'Ready For Discharge']).order_by('-admission_date'),
        'approve_target': admission,
        'available_beds': available_beds,
    })


@role_required('receptionist')
def reject_admission(request, pk):
    admission = get_object_or_404(Admission, admission_id=pk)
    admission.status = 'Rejected'
    admission.save()
    messages.success(request, f"Admission request for {admission.patient.name} rejected.")
    return redirect('admissions_dashboard')


@role_required('receptionist')
def manage_ip_charges(request, pk):
    admission = get_object_or_404(Admission, admission_id=pk)
    
    if request.method == 'POST':
        charge_type = request.POST.get('charge_type')
        description = request.POST.get('description')
        amount = request.POST.get('amount')

        IPCharge.objects.create(
            admission=admission,
            charge_type=charge_type,
            description=description,
            amount=Decimal(amount)
        )
        recalculate_ip_bill(admission)
        messages.success(request, "Charge added successfully.")
        return redirect('manage_ip_charges', pk=pk)

    recalculate_ip_bill(admission)
    charges = IPCharge.objects.filter(admission=admission).order_by('created_at')
    bill = IPBill.objects.filter(admission=admission).first()

    return render(request, 'hospitalapp/receptionist/manage_charges.html', {
        'admission': admission,
        'charges': charges,
        'bill': bill
    })


@role_required('doctor')
def doctor_discharge_ready(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    admission.status = 'Ready For Discharge'
    admission.save()
    messages.success(request, f"Patient {admission.patient.name} marked as Ready For Discharge.")
    return redirect('doctor_dashboard')


@role_required('receptionist')
def discharge_billing(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    recalculate_ip_bill(admission)
    
    charges = IPCharge.objects.filter(admission=admission).order_by('created_at')
    bill = IPBill.objects.filter(admission=admission).first()

    amount_paisa = int(bill.grand_total * 100)
    
    if amount_paisa > 0:
        order = client.order.create({
            "amount": amount_paisa,
            "currency": "INR",
            "payment_capture": 1
        })
        order_id = order['id']
        bill.razorpay_order_id = order_id
        bill.save()
    else:
        order_id = ""

    return render(request, 'hospitalapp/receptionist/final_bill.html', {
        'admission': admission,
        'charges': charges,
        'bill': bill,
        'amount_paisa': amount_paisa,
        'order_id': order_id,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    })


@role_required('receptionist')
def apply_discharge_discount(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    bill = get_object_or_404(IPBill, admission=admission)
    
    if request.method == 'POST':
        discount = request.POST.get('discount', '0.00')
        bill.discount = Decimal(discount)
        bill.save()
        recalculate_ip_bill(admission)
        messages.success(request, "Discount applied successfully.")
        
    return redirect('discharge_billing', admission_id=admission_id)


@csrf_exempt
def verify_ip_payment(request):
    if request.method != "POST":
        return JsonResponse({"status": "failed"})

    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        admission_id = data.get('admission_id')

        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

        admission = get_object_or_404(Admission, admission_id=admission_id)
        bill = get_object_or_404(IPBill, admission=admission)

        if bill.payment_status != "Paid":
            bill.razorpay_payment_id = razorpay_payment_id
            bill.payment_status = "Paid"
            bill.save()

            admission.status = 'Discharged'
            admission.discharge_date = timezone.now()
            admission.save()

            # Auto-release the allocated bed
            if admission.bed:
                admission.bed.status = 'Available'
                admission.bed.patient = None
                admission.bed.save()

            linked_charges = IPCharge.objects.filter(admission=admission, pharmacy_bill__isnull=False)
            for charge in linked_charges:
                charge.pharmacy_bill.payment_status = 'Paid'
                charge.pharmacy_bill.save()

        return JsonResponse({
            "status": "success",
            "redirect_url": f"/payment-success/?bill_id={bill.ip_bill_id}&type=ip"
        })

    except Exception as e:
        print("VERIFY IP PAYMENT ERROR:", e)
        return JsonResponse({"status": "failed"})


def download_discharge_summary(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    charges = IPCharge.objects.filter(admission=admission).order_by('created_at')
    bill = IPBill.objects.filter(admission=admission).first()
    
    # Fetch care team details
    consultants = AdmissionConsultant.objects.filter(admission=admission).select_related('doctor')
    consultant_names = [f"Dr. {c.doctor.name} ({c.doctor.specialization})" for c in consultants]
    all_consultants_str = ", ".join(consultant_names) if consultant_names else "None assigned"
    
    # Fetch clinical and nursing records
    clinical_notes = ClinicalNote.objects.filter(admission=admission).order_by('created_at')
    nurse_notes = NurseNote.objects.filter(admission=admission).order_by('created_at')
    vitals = VitalRecord.objects.filter(admission=admission).order_by('recorded_at')
    meds_administered = MedicineAdministration.objects.filter(admission=admission).order_by('administered_at')
    
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Helper to draw a consistent header on every page
    def draw_page_decorations(canvas_obj, page_num):
        # Header block
        canvas_obj.setFillColor(colors.HexColor("#0b4c8c"))
        canvas_obj.rect(0, 750, width, 100, fill=1, stroke=0)
        canvas_obj.setFillColor(colors.HexColor("#4caf50"))
        canvas_obj.rect(0, 745, width, 5, fill=1, stroke=0)
        
        logo_path = os.path.join(settings.BASE_DIR, 'hospitalapp', 'static', 'hospitalapp', 'images', 'logo.png')
        if os.path.exists(logo_path):
            canvas_obj.drawImage(logo_path, 40, 760, width=70, height=70, mask='auto')
        
        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 24)
        canvas_obj.drawString(130, 810, "ASHA HOSPITAL")
        
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.setFillColor(colors.HexColor("#e8f5e9"))
        canvas_obj.drawString(130, 795, "Care | Compassion | Commitment")
        
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(130, 782, "Thodupuzha P.O, Idukki, Kerala  |  Phone: +91 9876543210")
        canvas_obj.drawString(130, 770, "Email: contact@ashahospital.com  |  Web: www.ashahospital.com")
        
        canvas_obj.setFillColor(colors.HexColor("#0b4c8c"))
        canvas_obj.setFont("Helvetica-Bold", 15)
        canvas_obj.drawCentredString(width / 2, 715, "COLLABORATIVE INPATIENT DISCHARGE SUMMARY")
        
        # Footer
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#64748b"))
        canvas_obj.drawCentredString(width / 2, 20, f"Page {page_num}  |  This is a collaborative clinical summary. Asha Hospital Management System.")
        canvas_obj.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(40, 32, width - 40, 32)
        
    # Add a subtle horizontal rule after the header for visual separation
    p.setStrokeColor(colors.HexColor("#cbd5e1"))
    p.setLineWidth(0.8)
    p.line(40, 730, width - 40, 730)
    
    page = 1
    draw_page_decorations(p, page)
    
    # Patient & Admission details card
    p.setFillColor(colors.HexColor("#f8f9fa"))
    p.roundRect(40, 560, 520, 135, 8, fill=1, stroke=1)
    p.setStrokeColor(colors.HexColor("#cbd5e1"))
    p.roundRect(40, 560, 520, 135, 8, fill=0, stroke=1)
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(55, 680, "PATIENT INFORMATION")
    p.drawString(300, 680, "ADMISSION INFORMATION")
    
    p.setFont("Helvetica", 9)
    p.drawString(55, 660, f"Patient Name: {admission.patient.name}")
    p.drawString(55, 645, f"Patient ID: PAT-{admission.patient.patient_id}")
    p.drawString(55, 630, f"Age / Gender: {admission.patient.age} / {admission.patient.gender}")
    p.drawString(55, 615, f"Contact Phone: {admission.patient.phone}")
    
    adm_date_str = admission.admission_date.strftime('%d-%m-%Y %H:%M')
    dis_date_str = admission.discharge_date.strftime('%d-%m-%Y %H:%M') if admission.discharge_date else 'Active'
    
    p.drawString(300, 660, f"Admission ID: ADM-{admission.admission_id}")
    p.drawString(300, 645, f"Admitting Doctor: Dr. {admission.doctor.name}")
    p.drawString(300, 630, f"Ward / Bed: {admission.ward_type} (Bed: {admission.bed_number})")
    p.drawString(300, 615, f"Admit Date: {adm_date_str}")
    p.drawString(300, 600, f"Discharge Date: {dis_date_str}")
    
    p.setFont("Helvetica-Bold", 9)
    p.drawString(55, 575, f"Care Team Specialists: {all_consultants_str}")
    
    y = 530
    
    # 1. CLINICAL NOTES (aggregated from all treating doctors)
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.HexColor("#0b4c8c"))
    p.drawString(40, y, "COLLABORATIVE CLINICAL CLINICAL NOTES & TIMELINE")
    y -= 15
    
    p.setFillColor(colors.black)
    if clinical_notes.exists():
        for note in clinical_notes:
            if y < 80:
                p.showPage()
                page += 1
                draw_page_decorations(p, page)
                y = 690
            
            p.setFont("Helvetica-Bold", 9)
            p.drawString(50, y, f"[{note.created_at.strftime('%d-%m-%Y %H:%M')}] Dr. {note.doctor.name} ({note.doctor.specialization}):")
            y -= 12
            
            p.setFont("Helvetica", 9)
            note_lines = note.note_text.split('\n')
            for line in note_lines:
                if y < 80:
                    p.showPage()
                    page += 1
                    draw_page_decorations(p, page)
                    y = 690
                # wrap lines manually for reportlab
                words = line.split()
                cur_line = ""
                for w in words:
                    if len(cur_line + " " + w) < 95:
                        cur_line += " " + w
                    else:
                        p.drawString(60, y, cur_line.strip())
                        y -= 11
                        cur_line = w
                if cur_line:
                    p.drawString(60, y, cur_line.strip())
                    y -= 11
            y -= 5
    else:
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, y, f"Initial Admitting Reason: {admission.reason}")
        y -= 15
        
    y -= 10
    
    # Page Break for Nursing Logs & Vitals History if y is low
    if y < 200:
        p.showPage()
        page += 1
        draw_page_decorations(p, page)
        y = 690
        
    # 2. NURSING CARE LOGS & PATIENT VITALS TIMELINE
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.HexColor("#0b4c8c"))
    p.drawString(40, y, "NURSING NOTES & CLINICAL RECORD HISTORY")
    y -= 15
    
    p.setFillColor(colors.black)
    if nurse_notes.exists():
        for note in nurse_notes[:6]: # Limit to prevent extreme multi-page overflow
            if y < 80:
                p.showPage()
                page += 1
                draw_page_decorations(p, page)
                y = 690
            p.setFont("Helvetica-Bold", 8.5)
            p.drawString(50, y, f"[{note.created_at.strftime('%d-%m-%Y %H:%M')}] Nurse {note.nurse.name}:")
            y -= 11
            p.setFont("Helvetica", 8.5)
            p.drawString(60, y, note.note_text[:95])
            y -= 13
    else:
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, y, "No clinical nurse notes logged.")
        y -= 15
        
    y -= 10
    
    # 3. MEDICATION HISTORY
    if y < 150:
        p.showPage()
        page += 1
        draw_page_decorations(p, page)
        y = 690
        
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.HexColor("#0b4c8c"))
    p.drawString(40, y, "MEDICATION ADMINISTRATION RECORD (MAR)")
    y -= 15
    
    if meds_administered.exists():
        med_data = [["Time Administered", "Medicine Name", "Dosage Given", "Nurse Notes"]]
        for med in meds_administered[:10]:
            med_data.append([
                med.administered_at.strftime('%d-%m-%Y %H:%M'),
                med.medicine_name,
                med.dosage,
                med.notes or "Administered"
            ])
        t_med = Table(med_data, colWidths=[120, 150, 80, 170])
        t_med.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
        ]))
        t_w, t_h = t_med.wrap(width - 80, y)
        y -= t_h
        t_med.drawOn(p, 40, y)
        y -= 15
    else:
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, y, "No medications administered during stay.")
        y -= 15
        
    # 4. FINAL COLLABORATIVE BILLING
    if y < 180:
        p.showPage()
        page += 1
        draw_page_decorations(p, page)
        y = 690
        
    y -= 10
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.HexColor("#0b4c8c"))
    p.drawString(40, y, "COLLABORATIVE INPATIENT BILLING & CHARGES SUMMARY")
    y -= 15
    
    bill_data = [["Charge Item", "Description", "Amount"]]
    for chg in charges:
        bill_data.append([chg.charge_type, chg.description, f"Rs. {chg.amount}"])
        
    if bill:
        bill_data.append(["Subtotal", "", f"Rs. {bill.subtotal}"])
        bill_data.append(["GST (18%)", "", f"Rs. {bill.gst}"])
        if bill.discount > 0:
            bill_data.append(["Discount", "", f"- Rs. {bill.discount}"])
        bill_data.append(["Grand Total", "", f"Rs. {bill.grand_total}"])
        bill_data.append(["Payment Status", "", bill.payment_status])
        
    t_bill = Table(bill_data, colWidths=[150, 250, 100])
    t_bill.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, -4), (-1, -1), 'Helvetica-Bold') if bill and bill.discount > 0 else ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
    ]))
    
    t_w, t_h = t_bill.wrap(width - 80, y)
    y -= t_h
    t_bill.drawOn(p, 40, y)
    
    # 5. SIGNATURES
    if y < 100:
        p.showPage()
        page += 1
        draw_page_decorations(p, page)
        y = 690
        
    p.setFont("Helvetica-Bold", 8.5)
    p.drawString(40, 50, "Authorized Signatory")
    p.drawCentredString(width / 2, 50, "Patient Signature")
    p.drawString(width - 160, 50, "Attending Consultant(s)")
    
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    p.line(40, 95, 140, 95)
    p.line(width / 2 - 50, 95, width / 2 + 50, 95)
    p.line(width - 160, 95, width - 40, 95)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Collaborative_Discharge_Summary_ADM_{admission.admission_id}.pdf"'
    return response



# ─────────────────────────────────────────────
#  BED MANAGEMENT VIEWS
# ─────────────────────────────────────────────

@role_required('admin')
def bed_management(request):
    """
    Admin Bed Management Dashboard:
    - View all beds grouped by ward
    - Add / edit beds
    - Toggle bed status (Maintenance / Available)
    """
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_bed':
            bed_number = request.POST.get('bed_number', '').strip()
            ward_type  = request.POST.get('ward_type')
            notes      = request.POST.get('notes', '').strip()

            if bed_number and ward_type:
                if Bed.objects.filter(bed_number=bed_number).exists():
                    messages.error(request, f"Bed '{bed_number}' already exists.")
                else:
                    Bed.objects.create(
                        bed_number=bed_number,
                        ward_type=ward_type,
                        status='Available',
                        notes=notes or None
                    )
                    messages.success(request, f"Bed '{bed_number}' added to {ward_type}.")
            else:
                messages.error(request, "Bed number and ward type are required.")

        elif action == 'toggle_status':
            bed_id    = request.POST.get('bed_id')
            new_status = request.POST.get('new_status')
            bed = get_object_or_404(Bed, id=bed_id)

            # Only allow toggling Available ↔ Maintenance (Occupied is auto-managed)
            if bed.status == 'Occupied':
                messages.error(request, f"Bed {bed.bed_number} is currently Occupied. Discharge patient first.")
            elif new_status in ['Available', 'Maintenance']:
                bed.status = new_status
                if new_status == 'Available':
                    bed.patient = None
                bed.save()
                messages.success(request, f"Bed {bed.bed_number} status set to {new_status}.")

        elif action == 'delete_bed':
            bed_id = request.POST.get('bed_id')
            bed = get_object_or_404(Bed, id=bed_id)
            if bed.status == 'Occupied':
                messages.error(request, f"Cannot delete an occupied bed ({bed.bed_number}).")
            else:
                bed.delete()
                messages.success(request, f"Bed deleted successfully.")

        elif action == 'edit_bed':
            bed_id     = request.POST.get('bed_id')
            bed        = get_object_or_404(Bed, id=bed_id)
            new_number = request.POST.get('bed_number', '').strip()
            new_ward   = request.POST.get('ward_type')
            new_notes  = request.POST.get('notes', '').strip()

            if new_number and new_ward:
                dup = Bed.objects.filter(bed_number=new_number).exclude(id=bed_id).first()
                if dup:
                    messages.error(request, f"Bed number '{new_number}' already used.")
                else:
                    bed.bed_number = new_number
                    bed.ward_type  = new_ward
                    bed.notes      = new_notes or None
                    bed.save()
                    messages.success(request, f"Bed updated successfully.")

        return redirect('bed_management')

    # Aggregate stats
    all_beds   = Bed.objects.all()
    from hospitalapp.models import EmergencyBed
    emergency_beds = EmergencyBed.objects.select_related('zone').all()
    
    total      = all_beds.count() + emergency_beds.count()
    available  = all_beds.filter(status='Available').count() + emergency_beds.filter(status='Available').count()
    occupied   = all_beds.filter(status='Occupied').count() + emergency_beds.filter(status='Occupied').count()
    maintenance= all_beds.filter(status='Maintenance').count() + emergency_beds.filter(status='Maintenance').count()

    # Group by ward
    wards = {}
    for bed in all_beds:
        wards.setdefault(bed.ward_type, []).append(bed)

    for bed in emergency_beds:
        bed.is_emergency = True
        bed.notes = f"Monitor: {'Available' if bed.monitor_available else 'Not Available'} | Ventilator: {'Available' if bed.ventilator_available else 'Not Available'}"
        if bed.status == 'Occupied':
            # Get active casualty case assigned to this bed
            active_casualty = Casuality.objects.filter(
                assigned_bed=bed
            ).exclude(
                status__in=['Discharged', 'Admitted', 'ICU Transfer', 'OT Transfer']
            ).select_related('patient').first()
            if active_casualty:
                bed.patient = active_casualty.patient
        wards.setdefault(f"Emergency Zone - {bed.zone.zone_name}", []).append(bed)

    return render(request, 'hospitalapp/admin/beds.html', {
        'all_beds'   : all_beds,
        'wards'      : wards,
        'total'      : total,
        'available'  : available,
        'occupied'   : occupied,
        'maintenance': maintenance,
        'ward_choices': Bed.WARD_CHOICES,
    })


@role_required('receptionist', 'admin')
def bed_available_json(request):
    """AJAX: return available beds for a given ward_type."""
    ward_type = request.GET.get('ward_type', '')
    beds = Bed.objects.filter(status='Available', ward_type=ward_type).values('id', 'bed_number')
    return JsonResponse({'beds': list(beds)})


# ─────────────────────────────────────────────
#  ADMIN: NURSE MANAGEMENT
# ─────────────────────────────────────────────

@role_required('admin')
def manage_nurses(request):
    nurses = Nurse.objects.filter(user__role='nurse').select_related('user').all().order_by('assigned_ward', 'name')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_nurse':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            qualification = request.POST.get('qualification', '').strip()
            assigned_ward = request.POST.get('assigned_ward')
            is_head = request.POST.get('is_head_nurse') == 'on'

            if not all([username, password, name, assigned_ward]):
                messages.error(request, "Required fields are missing.")
                return redirect('manage_nurses')

            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists.")
                return redirect('manage_nurses')

            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        role='nurse',
                        email=email
                    )

                    Nurse.objects.create(
                        user=user,
                        name=name,
                        phone=phone,
                        email=email,
                        qualification=qualification,
                        assigned_ward=assigned_ward,
                        is_head_nurse=is_head
                    )

                messages.success(request, f"Nurse '{name}' registered successfully.")

            except Exception as e:
                messages.error(request, f"Error creating nurse: {str(e)}")

            return redirect('manage_nurses')

        elif action == 'promote_head_nurse':
            nurse_id = request.POST.get('nurse_id')
            nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            nurse.is_head_nurse = True
            nurse.save()
            messages.success(request, f"Nurse '{nurse.name}' promoted to Head Nurse.")
            return redirect('manage_nurses')

        elif action == 'demote_staff_nurse':
            nurse_id = request.POST.get('nurse_id')
            nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            nurse.is_head_nurse = False
            nurse.save()
            messages.success(request, f"Head Nurse '{nurse.name}' demoted to Staff Nurse.")
            return redirect('manage_nurses')

        elif action == 'promote_superintendent':
            nurse_id = request.POST.get('nurse_id')
            nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            if nurse.user:
                nurse.user.role = 'nursing_superintendent'
                nurse.user.save()
                messages.success(request, f"Head Nurse '{nurse.name}' has been promoted to Nursing Superintendent!")
            else:
                messages.error(request, "Associated user account not found.")
            return redirect('manage_nurses')

        elif action == 'demote_superintendent':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, user_id=user_id)
            user.role = 'nurse'
            user.save()
            nurse = Nurse.objects.filter(user=user).first()
            if nurse:
                nurse.is_head_nurse = True
                nurse.save()
                messages.success(request, f"Nursing Superintendent '{nurse.name}' demoted to Head Nurse.")
            else:
                Nurse.objects.create(
                    user=user,
                    name=user.username,
                    phone='0000000000',
                    email=user.email or '',
                    qualification='Promoted',
                    assigned_ward='General Ward',
                    is_head_nurse=True
                )
                messages.success(request, f"Nursing Superintendent '{user.username}' demoted to Head Nurse.")
            return redirect('manage_nurses')

    nursing_superintendents = User.objects.filter(role='nursing_superintendent').order_by('username')
    nursing_stations = User.objects.filter(role='nursing_station').order_by('username')

    return render(request, 'hospitalapp/admin/manage_nurses.html', {
        'nurses': nurses,
        'nursing_superintendents': nursing_superintendents,
        'nursing_stations': nursing_stations,
        'ward_choices': Bed.WARD_CHOICES,
    })




@role_required('admin')
def delete_nurse(request, pk):
    nurse = get_object_or_404(Nurse, nurse_id=pk)
    user = nurse.user

    try:
        nurse.delete()

        if user:
            user.delete()

        messages.success(request, "Nurse deleted successfully.")

    except Exception as e:
        messages.error(request, f"Error deleting nurse: {str(e)}")

    return redirect('manage_nurses')


# ─────────────────────────────────────────────
#  NURSING MODULE VIEWS
# ─────────────────────────────────────────────

@role_required('nurse')
def nurse_dashboard(request):

    nurse = get_object_or_404(Nurse, user=request.user)

    today = timezone.now().date()
    now = timezone.now()

    shift = NurseShift.objects.filter(
        nurse=nurse,
        shift_date=today
    ).first()

    # =====================================================
    # AUTO MARK MISSED MEDICATIONS (OPTIMIZED)
    # =====================================================
    MedicationScheduleEntry.objects.filter(
        admission__nursing_assignments__nurse=nurse,
        scheduled_time__lt=now - timedelta(hours=2),
        status='Pending'
    ).update(status='Missed')

    # =====================================================
    # POST ACTIONS
    # =====================================================
    if request.method == 'POST':

        action = request.POST.get('action')

        # ---------------- CHECK IN ----------------
        if action == 'check_in':
            if not shift:
                messages.error(request, "No shift scheduled for today.")
                return redirect('nurse_dashboard')

            shift.attendance_status = 'Present'
            shift.check_in = timezone.now()
            shift.save()

            messages.success(request, "Checked in successfully.")
            return redirect('nurse_dashboard')

        # ---------------- CHECK OUT ----------------
        elif action == 'check_out':
            if shift and shift.check_in:
                shift.check_out = timezone.now()
                shift.save()

                messages.success(request, "Checked out successfully.")

            return redirect('nurse_dashboard')

        # ---------------- ADD NOTE (IP Admission) ----------------
        elif action == 'add_note':
            admission_id = request.POST.get('admission_id')
            note_text = request.POST.get('note_text', '').strip()

            admission = get_object_or_404(Admission, admission_id=admission_id)

            if note_text:
                NurseNote.objects.create(
                    admission=admission,
                    nurse=nurse,
                    note_text=note_text
                )

                messages.success(request, "Note added successfully.")

            return redirect('nurse_dashboard')

        # ---------------- ADD NOTE (Emergency Casualty) ----------------
        elif action == 'add_casualty_note':
            casualty_id = request.POST.get('casualty_id')
            note_text = request.POST.get('note_text', '').strip()

            casualty = get_object_or_404(Casuality, id=casualty_id)

            if note_text:
                NurseNote.objects.create(
                    casualty=casualty,
                    nurse=nurse,
                    note_text=note_text
                )
                messages.success(request, "Casualty nursing note recorded.")

            return redirect('nurse_dashboard')

        # ---------------- ADMINISTER EMERGENCY MED ----------------
        elif action == 'administer_emergency_med':
            casualty_id = request.POST.get('casualty_id')
            medicine_id = request.POST.get('medicine_id')
            quantity = request.POST.get('quantity', '1')
            notes = request.POST.get('notes', '').strip()

            casualty = get_object_or_404(Casuality, id=casualty_id)
            medicine = get_object_or_404(Medicine, medicine_id=medicine_id)

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Invalid quantity.")
                return redirect('nurse_dashboard')

            if medicine.stock < quantity:
                messages.error(request, f"Insufficient stock for {medicine.name}.")
                return redirect('nurse_dashboard')

            try:
                with transaction.atomic():
                    medicine.stock -= quantity
                    medicine.save()

                    MedicineAdministration.objects.create(
                        casualty=casualty,
                        nurse=nurse,
                        medicine=medicine,
                        quantity=quantity,
                        medicine_name=medicine.name,
                        dosage=str(quantity),
                        notes=notes
                    )

                messages.success(request, f"{medicine.name} administered to emergency patient {casualty.patient.name}.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

            return redirect('nurse_dashboard')

        # ---------------- ADMINISTER MEDS ----------------
        elif action == 'administer_meds':
            admission_id = request.POST.get('admission_id')
            medicine_id = request.POST.get('medicine_id')
            quantity = request.POST.get('quantity', '1')
            notes = request.POST.get('notes', '').strip()

            admission = get_object_or_404(Admission, admission_id=admission_id)
            medicine = get_object_or_404(Medicine, medicine_id=medicine_id)

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Invalid quantity.")
                return redirect('nurse_dashboard')

            if medicine.stock < quantity:
                messages.error(
                    request,
                    f"Only {medicine.stock} stock left for {medicine.name}."
                )
                return redirect('nurse_dashboard')

            try:
                with transaction.atomic():

                    medicine.stock -= quantity
                    medicine.save()

                    MedicineAdministration.objects.create(
                        admission=admission,
                        nurse=nurse,
                        medicine=medicine,
                        quantity=quantity,
                        medicine_name=medicine.name,
                        dosage=str(quantity),
                        notes=notes
                    )

                    IPCharge.objects.create(
                        admission=admission,
                        charge_type='Pharmacy Bill',
                        description=f"{medicine.name} x{quantity}",
                        amount=medicine.price * quantity
                    )

                messages.success(
                    request,
                    f"{medicine.name} administered successfully."
                )

            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

            return redirect('nurse_dashboard')

        # ---------------- TRIGGER ALERT ----------------
        elif action == 'trigger_alert':
            admission_id = request.POST.get('admission_id')
            alert_message = request.POST.get('alert_message', '').strip()

            admission = get_object_or_404(Admission, admission_id=admission_id)

            if alert_message:
                EmergencyAlert.objects.create(
                    admission=admission,
                    triggered_by_nurse=nurse,
                    alert_message=alert_message
                )

                messages.error(request, "Emergency alert triggered.")

            return redirect('nurse_dashboard')

        # ---------------- RESOLVE ALERT ----------------
        elif action == 'resolve_alert':
            alert_id = request.POST.get('alert_id')

            alert = get_object_or_404(EmergencyAlert, id=alert_id)
            alert.is_resolved = True
            alert.resolved_at = timezone.now()
            alert.save()

            messages.success(request, "Emergency alert resolved.")
            return redirect('nurse_dashboard')

    # =====================================================
    # BASE QUERYSET (IMPORTANT OPTIMIZATION)
    # =====================================================
    base_qs = MedicationScheduleEntry.objects.filter(
        admission__ward_type=nurse.assigned_ward,
        admission__status__in=['Pending', 'Admitted', 'Ready For Discharge']
    )

    # =====================================================
    # ASSIGNMENTS
    # =====================================================
    assignments = NursePatientAssignment.objects.filter(
        nurse=nurse,
        admission__status__in=['Admitted', 'Ready For Discharge']
    ).select_related('admission', 'admission__patient')

    # =====================================================
    # ACTIVE ALERTS
    # =====================================================
    active_alerts = EmergencyAlert.objects.filter(
        admission__ward_type=nurse.assigned_ward,
        is_resolved=False
    ).order_by('-created_at')

    # =====================================================
    # PAST SHIFTS
    # =====================================================
    past_shifts = NurseShift.objects.filter(
        nurse=nurse
    ).order_by('-shift_date')[:10]

    # =====================================================
    # AVAILABLE MEDICINES
    # =====================================================
    available_medicines = Medicine.objects.filter(
        stock__gt=0
    ).order_by('name')

    # =====================================================
    # TODAY SCHEDULE (FIXED + OPTIMIZED)
    # =====================================================
    from datetime import datetime, time
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    end_of_day = timezone.make_aware(datetime.combine(today, time.max))

    today_schedule = MedicationScheduleEntry.objects.filter(
        admission__ward_type=nurse.assigned_ward,
        admission__status__in=['Pending', 'Admitted', 'Ready For Discharge'],
        scheduled_time__range=(start_of_day, end_of_day)
    ).select_related(
        'prescription_item',
        'prescription_item__medicine',
        'prescription_item__prescription',
        'prescription_item__prescription__doctor',
        'admission',
        'admission__patient',
        'administered_by'
    ).distinct().order_by('scheduled_time')

    print("TODAY SCHEDULE COUNT =", today_schedule.count())

    # =====================================================
    # DELAYED MEDS (FIXED LOGIC)
    # =====================================================
    delayed_meds_count = base_qs.filter(
        scheduled_time__lt=now,
        status='Pending'
    ).count()

    # =====================================================
    # MISSED MEDS
    # =====================================================
    missed_meds_count = base_qs.filter(
        scheduled_time__range=(start_of_day, end_of_day),
        status='Missed'
    ).count()

    # =====================================================
    # ACTIVE EMERGENCY CASES (Casualty in nurse's ward - only for Casuality Ward nurses)
    # =====================================================
    if nurse.assigned_ward == 'Casuality Ward':
        active_emergency_cases = Casuality.objects.filter(
            status__in=['Pending', 'Under Emergency Care', 'Stabilized', 'Referred']
        ).select_related('patient', 'doctor').prefetch_related(
            'emergency_prescriptions__items__medicine',
            'emergency_prescriptions__doctor'
        ).order_by('-created_at')

        # Emergency prescription items pending nurse execution
        emergency_med_count = EmergencyPrescription.objects.filter(
            casualty__status__in=['Pending', 'Under Emergency Care', 'Stabilized']
        ).count()
    else:
        active_emergency_cases = Casuality.objects.none()
        emergency_med_count = 0

    # =====================================================
    # RENDER
    # =====================================================
    return render(
        request,
        'hospitalapp/nurse/nurse_dashboard.html',
        {
            'nurse': nurse,
            'shift': shift,
            'assignments': assignments,
            'active_alerts': active_alerts,
            'past_shifts': past_shifts,
            'available_medicines': available_medicines,
            'today_schedule': today_schedule,
            'delayed_meds_count': delayed_meds_count,
            'missed_meds_count': missed_meds_count,
            'active_emergency_cases': active_emergency_cases,
            'emergency_med_count': emergency_med_count,
        }
    )

@role_required('nurse')
def nurse_analytics(request):
    nurse = get_object_or_404(Nurse, user=request.user)
    return render(request, 'hospitalapp/nurse/analytics.html', {'nurse': nurse})

@role_required('nurse')
def head_nurse_dashboard(request):
    nurse = get_object_or_404(Nurse, user=request.user)
    if not nurse.is_head_nurse:
        return HttpResponseForbidden("Access restricted to Head Nurses only.")

    today = timezone.now().date()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'schedule_shift':
            nurse_id = request.POST.get('nurse_id')
            shift_date_str = request.POST.get('shift_date')
            shift_type = request.POST.get('shift_type')
            allocate_one_week = request.POST.get('allocate_one_week') == 'on'
            weekly_pattern = request.POST.get('weekly_pattern', 'same_shift')
            
            target_nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            if target_nurse.assigned_ward != nurse.assigned_ward:
                messages.error(request, "You can only schedule shifts for nurses assigned to your ward.")
            else:
                from datetime import datetime, timedelta
                start_date = datetime.strptime(shift_date_str, '%Y-%m-%d').date()
                
                created_count = 0
                updated_count = 0
                deleted_count = 0
                
                if allocate_one_week:
                    dates = [start_date + timedelta(days=i) for i in range(7)]
                    
                    # Compute shifts list for the 7 days based on pattern
                    shift_types_by_day = []
                    if weekly_pattern == 'same_shift':
                        shift_types_by_day = [shift_type] * 7
                    elif weekly_pattern == 'rotating_shift':
                        rot_seq = ['Morning', 'Evening', 'Night']
                        try:
                            start_idx = rot_seq.index(shift_type)
                        except ValueError:
                            start_idx = 0
                        shift_types_by_day = [rot_seq[(start_idx + i) % 3] for i in range(7)]
                    elif weekly_pattern == 'rotating_shift_off':
                        rot_seq = ['Morning', 'Evening', 'Night', 'Off']
                        try:
                            start_idx = rot_seq.index(shift_type)
                        except ValueError:
                            start_idx = 0
                        shift_types_by_day = [rot_seq[(start_idx + i) % 4] for i in range(7)]
                    elif weekly_pattern == 'custom':
                        for i in range(7):
                            day_shift = request.POST.get(f'day_{i}_shift', 'Off')
                            shift_types_by_day.append(day_shift)
                    else:
                        shift_types_by_day = [shift_type] * 7
                        
                    for idx, s_date in enumerate(dates):
                        s_type = shift_types_by_day[idx]
                        if s_type == 'Off':
                            deleted, _ = NurseShift.objects.filter(nurse=target_nurse, shift_date=s_date).delete()
                            if deleted:
                                deleted_count += 1
                        else:
                            exists = NurseShift.objects.filter(nurse=target_nurse, shift_date=s_date).first()
                            if exists:
                                exists.shift_type = s_type
                                exists.save()
                                updated_count += 1
                            else:
                                NurseShift.objects.create(
                                    nurse=target_nurse, shift_date=s_date, shift_type=s_type, attendance_status='Off'
                                )
                                created_count += 1
                                
                    messages.success(
                        request, 
                        f"Weekly shifts rostered for {target_nurse.name} from {start_date} to {dates[-1]}. "
                        f"({created_count} created, {updated_count} updated, {deleted_count} marked Off)."
                    )
                else:
                    if shift_type == 'Off':
                        deleted, _ = NurseShift.objects.filter(nurse=target_nurse, shift_date=start_date).delete()
                        if deleted:
                            messages.success(request, f"Set {target_nurse.name} to Off for {start_date} (removed shift).")
                        else:
                            messages.success(request, f"{target_nurse.name} is already Off on {start_date}.")
                    else:
                        exists = NurseShift.objects.filter(nurse=target_nurse, shift_date=start_date).first()
                        if exists:
                            exists.shift_type = shift_type
                            exists.save()
                            messages.success(request, f"Updated shift for {target_nurse.name} to {shift_type} on {start_date}.")
                        else:
                            NurseShift.objects.create(
                                nurse=target_nurse, shift_date=start_date, shift_type=shift_type, attendance_status='Off'
                            )
                            messages.success(request, f"Scheduled {shift_type} shift for {target_nurse.name} on {start_date}.")
            return redirect('head_nurse_dashboard')

        elif action == 'assign_patient':
            nurse_id = request.POST.get('nurse_id')
            admission_id = request.POST.get('admission_id')
            notes = request.POST.get('notes', '').strip()

            target_nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            admission = get_object_or_404(Admission, admission_id=admission_id)
            
            # Create assignment
            NursePatientAssignment.objects.create(nurse=target_nurse, admission=admission, notes=notes)
            messages.success(request, f"Patient {admission.patient.name} assigned to Nurse {target_nurse.name}.")
            return redirect('head_nurse_dashboard')

        elif action == 'update_shift_details':
            shift_id = request.POST.get('shift_id')
            shift_type = request.POST.get('shift_type')
            status = request.POST.get('attendance_status')
            
            shift_record = get_object_or_404(NurseShift, id=shift_id)
            shift_record.shift_type = shift_type
            shift_record.attendance_status = status
            shift_record.save()
            messages.success(request, f"Shift details updated for {shift_record.nurse.name}.")
            return redirect('head_nurse_dashboard')

        elif action == 'delete_shift':
            shift_id = request.POST.get('shift_id')
            shift_record = get_object_or_404(NurseShift, id=shift_id)
            nurse_name = shift_record.nurse.name
            shift_date = shift_record.shift_date
            shift_record.delete()
            messages.success(request, f"Deleted shift for {nurse_name} on {shift_date}.")
            return redirect('head_nurse_dashboard')

    # Ward analytics
    ward_beds = Bed.objects.filter(ward_type=nurse.assigned_ward)
    total_beds = ward_beds.count()
    occupied_beds = ward_beds.filter(status='Occupied').count()
    available_beds = ward_beds.filter(status='Available').count()
    
    ward_admissions = Admission.objects.filter(
        ward_type=nurse.assigned_ward, status__in=['Admitted', 'Ready For Discharge']
    )
    
    # Active nurses in this ward
    ward_nurses = Nurse.objects.filter(assigned_ward=nurse.assigned_ward)
    
    # Todays scheduled shifts in this ward
    todays_shifts = NurseShift.objects.filter(
        nurse__assigned_ward=nurse.assigned_ward, shift_date=today
    )

    # Weekly Roster (next 7 days starting from today)
    from datetime import timedelta
    date_list = [today + timedelta(days=i) for i in range(7)]
    shifts_in_week = NurseShift.objects.filter(
        nurse__in=ward_nurses,
        shift_date__range=(today, today + timedelta(days=6))
    ).select_related('nurse')

    shift_map = {(s.nurse_id, s.shift_date): s for s in shifts_in_week}

    weekly_roster = []
    for n in ward_nurses:
        nurse_shifts = []
        for d in date_list:
            shift_record = shift_map.get((n.nurse_id, d))
            nurse_shifts.append({
                'date': d,
                'shift': shift_record
            })
        weekly_roster.append({
            'nurse': n,
            'shifts': nurse_shifts
        })

    # All future/allocated shifts (starting from today)
    all_allocated_shifts = NurseShift.objects.filter(
        nurse__assigned_ward=nurse.assigned_ward,
        shift_date__gte=today
    ).select_related('nurse').order_by('shift_date', 'shift_type')
    
    # Active alerts in this ward
    ward_alerts = EmergencyAlert.objects.filter(
        admission__ward_type=nurse.assigned_ward, is_resolved=False
    )

    # Critical patients count: patients currently admitted in this ward whose latest vital condition is Critical
    critical_admissions = []
    for adm in ward_admissions:
        latest_vital = VitalRecord.objects.filter(admission=adm).order_by('-recorded_at').first()
        if latest_vital and latest_vital.patient_condition == 'Critical':
            critical_admissions.append(adm)
            
    critical_count = len(critical_admissions)

    return render(request, 'hospitalapp/nurse/head_nurse_dashboard.html', {
        'nurse': nurse,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'ward_admissions': ward_admissions,
        'ward_nurses': ward_nurses,
        'todays_shifts': todays_shifts,
        'weekly_roster': weekly_roster,
        'date_list': date_list,
        'all_allocated_shifts': all_allocated_shifts,
        'ward_alerts': ward_alerts,
        'critical_count': critical_count,
        'today': today,
    })


@role_required('nurse')
def nurse_log_vitals(request, admission_id):

    admission = get_object_or_404(
        Admission,
        admission_id=admission_id
    )

    nurse = get_object_or_404(Nurse, user=request.user)

    if request.method == 'POST':

        try:
            vital = VitalRecord.objects.create(
                admission=admission,
                recorded_by=nurse,
                bp_systolic=int(request.POST.get('bp_systolic')),
                bp_diastolic=int(request.POST.get('bp_diastolic')),
                temperature=Decimal(request.POST.get('temperature')),
                oxygen_level=int(request.POST.get('oxygen_level')),
                heart_rate=int(request.POST.get('heart_rate')),
                sugar_level=int(request.POST.get('sugar_level'))
                if request.POST.get('sugar_level') else None,
                respiratory_rate=int(request.POST.get('respiratory_rate')),
                patient_condition=request.POST.get('patient_condition')
            )

            messages.success(request, "Vitals logged successfully.")

            if vital.patient_condition == 'Critical':

                EmergencyAlert.objects.create(
                    admission=admission,
                    triggered_by_nurse=nurse,
                    alert_message=(
                        f"Critical vitals detected for "
                        f"{admission.patient.name}"
                    )
                )

                messages.error(
                    request,
                    "Critical alert triggered automatically."
                )

        except Exception as e:
            messages.error(request, str(e))

        return redirect('nurse_dashboard')

    return render(request, 'hospitalapp/nurse/log_vitals.html', {
        'admission': admission,
        'conditions': VitalRecord.CONDITION_CHOICES,
    })


@role_required('nurse')
def nurse_log_casualty_vitals(request, casualty_id):
    casualty = get_object_or_404(Casuality, id=casualty_id)
    nurse = get_object_or_404(Nurse, user=request.user)

    if request.method == 'POST':
        try:
            VitalRecord.objects.create(
                casualty=casualty,
                recorded_by=nurse,
                bp_systolic=int(request.POST.get('bp_systolic')),
                bp_diastolic=int(request.POST.get('bp_diastolic')),
                temperature=Decimal(request.POST.get('temperature')),
                oxygen_level=int(request.POST.get('oxygen_level')),
                heart_rate=int(request.POST.get('heart_rate')),
                sugar_level=int(request.POST.get('sugar_level')) if request.POST.get('sugar_level') else None,
                respiratory_rate=int(request.POST.get('respiratory_rate')),
                patient_condition=request.POST.get('patient_condition')
            )
            messages.success(request, f"Vitals logged successfully for emergency patient {casualty.patient.name}.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect('nurse_dashboard')

    return render(request, 'hospitalapp/nurse/log_casualty_vitals.html', {
        'casualty': casualty,
        'conditions': VitalRecord.CONDITION_CHOICES,
    })


@role_required('nurse')
def nurse_administer_emergency_item(request, item_id):
    item = get_object_or_404(EmergencyPrescriptionItem, id=item_id)
    nurse = get_object_or_404(Nurse, user=request.user)

    if request.method == 'POST':
        if item.is_administered:
            messages.warning(request, "This prescription line has already been administered.")
            return redirect('nurse_dashboard')

        medicine = item.medicine
        if medicine.stock < 1:
            messages.error(request, f"Insufficient stock for {medicine.name}. (Stock: {medicine.stock})")
            return redirect('nurse_dashboard')

        try:
            with transaction.atomic():
                casualty = item.prescription.casualty

                # 1. Deduct stock
                medicine.stock -= 1
                medicine.save()

                # 2. Mark prescription item as administered
                item.is_administered = True
                item.administered_at = timezone.now()
                item.administered_by = nurse
                item.save()

                # 3. Create administration log entry
                MedicineAdministration.objects.create(
                    casualty=casualty,
                    nurse=nurse,
                    medicine=medicine,
                    medicine_name=medicine.name,
                    dosage=item.dosage,
                    quantity=1,
                    notes=f"Administered emergency prescription item (Dr. {item.prescription.doctor.name})",
                    emergency_prescription_item=item
                )

                # 4. Bill the medicine to the patient's casualty account
                CasualtyBill.objects.create(
                    casualty=casualty,
                    charge_type='Medicine',
                    description=f"{medicine.name} ({item.dosage}) x1 — Emergency Rx by Dr. {item.prescription.doctor.name}",
                    amount=medicine.price,
                    medicine=medicine,
                    administered_by=nurse,
                    emergency_prescription_item=item
                )

                # 5. If patient is already admitted, merge charge into IP Bill immediately
                active_admission = Admission.objects.filter(
                    patient=casualty.patient,
                    status__in=['Admitted', 'Ready For Discharge']
                ).first()
                if active_admission:
                    from hospitalapp.models import IPCharge as IPChargeModel
                    IPCharge.objects.create(
                        admission=active_admission,
                        charge_type='Pharmacy Bill',
                        description=f"[Emergency] {medicine.name} ({item.dosage}) x1",
                        amount=medicine.price
                    )
                    # Mark as already merged
                    cb = CasualtyBill.objects.filter(
                        casualty=casualty, emergency_prescription_item=item
                    ).last()
                    if cb:
                        cb.merged_to_ip = True
                        cb.save()
                    recalculate_ip_bill(active_admission)

            messages.success(
                request,
                f"✓ {medicine.name} administered to {casualty.patient.name}. "
                f"Rs. {medicine.price} charged to casualty bill."
            )
        except Exception as e:
            messages.error(request, f"Administration error: {str(e)}")

    return redirect('nurse_dashboard')
# ─────────────────────────────────────────────
#  VITAL MONITORING & ICU MONITORING DASHBOARD
# ─────────────────────────────────────────────

@login_required
def icu_dashboard(request):
    """
    ICU Dashboard: Live monitoring of all ICU ward beds and active patients.
    Available to Doctors, Nurses, Admins, and Receptionists.
    """
    icu_beds = Bed.objects.filter(ward_type='ICU')
    active_alerts = EmergencyAlert.objects.filter(is_resolved=False).order_by('-created_at')

    # Construct status details for each ICU bed
    bed_details = []
    for bed in icu_beds:
        detail = {
            'bed': bed,
            'admission': None,
            'latest_vitals': None,
            'alerts': None
        }
        if bed.status == 'Occupied' and bed.patient:
            admission = Admission.objects.filter(
                patient=bed.patient, status__in=['Admitted', 'Ready For Discharge']
            ).order_by('-admission_date').first()
            
            if admission:
                detail['admission'] = admission
                detail['latest_vitals'] = VitalRecord.objects.filter(admission=admission).order_by('-recorded_at').first()
                detail['alerts'] = EmergencyAlert.objects.filter(admission=admission, is_resolved=False)
        bed_details.append(detail)

    return render(request, 'hospitalapp/nurse/icu_dashboard.html', {
        'bed_details': bed_details,
        'active_alerts': active_alerts,
    })


@login_required
def patient_vitals_history(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    vitals = VitalRecord.objects.filter(admission=admission).order_by('-recorded_at')
    notes = NurseNote.objects.filter(admission=admission).order_by('-created_at')
    meds = MedicineAdministration.objects.filter(admission=admission).order_by('-administered_at')

    return render(request, 'hospitalapp/nurse/vitals_history.html', {
        'admission': admission,
        'vitals': vitals,
        'notes': notes,
        'meds': meds,
    })


# ─────────────────────────────────────────────
#  AMBULANCE MANAGEMENT MODULE
# ─────────────────────────────────────────────

@role_required('receptionist', 'admin')
def ambulance_dashboard(request):
    ambulances = Ambulance.objects.all().order_by('plate_number')
    requests = AmbulanceRequest.objects.all().order_by('-requested_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'register_ambulance':
            plate = request.POST.get('plate_number', '').strip().upper()
            driver = request.POST.get('driver_name', '').strip()
            phone = request.POST.get('driver_phone', '').strip()
            model = request.POST.get('vehicle_model', '').strip()

            if plate and driver and phone and model:
                if Ambulance.objects.filter(plate_number=plate).exists():
                    messages.error(request, f"Ambulance '{plate}' is already registered.")
                else:
                    Ambulance.objects.create(plate_number=plate, driver_name=driver, driver_phone=phone, vehicle_model=model)
                    messages.success(request, f"Ambulance {plate} registered successfully.")
            else:
                messages.error(request, "All fields are required.")
            return redirect('ambulance_dashboard')

        elif action == 'request_ambulance':
            caller = request.POST.get('caller_name', '').strip()
            phone = request.POST.get('caller_phone', '').strip()
            pickup = request.POST.get('pickup_location', '').strip()
            priority = request.POST.get('emergency_priority')

            if caller and phone and pickup:
                AmbulanceRequest.objects.create(
                    caller_name=caller, caller_phone=phone, pickup_location=pickup, emergency_priority=priority
                )
                messages.success(request, f"Emergency request logged for {caller}.")
            else:
                messages.error(request, "Caller details and location are required.")
            return redirect('ambulance_dashboard')

        elif action == 'assign_ambulance':
            req_id = request.POST.get('request_id')
            amb_id = request.POST.get('ambulance_id')

            req_obj = get_object_or_404(AmbulanceRequest, id=req_id)
            amb_obj = get_object_or_404(Ambulance, id=amb_id)

            if amb_obj.status != 'Available':
                messages.error(request, f"Ambulance {amb_obj.plate_number} is currently {amb_obj.status}.")
            else:
                # Update status
                req_obj.status = 'Assigned'
                req_obj.assigned_ambulance = amb_obj
                req_obj.save()

                amb_obj.status = 'Busy'
                amb_obj.save()
                messages.success(request, f"Ambulance {amb_obj.plate_number} assigned to request #{req_obj.id}.")
            return redirect('ambulance_dashboard')

        elif action == 'complete_request':
            req_id = request.POST.get('request_id')
            req_obj = get_object_or_404(AmbulanceRequest, id=req_id)
            
            if req_obj.assigned_ambulance:
                amb = req_obj.assigned_ambulance
                amb.status = 'Available'
                amb.save()
            
            req_obj.status = 'Completed'
            req_obj.completed_at = timezone.now()
            req_obj.save()
            messages.success(request, f"Ambulance request #{req_obj.id} marked as completed.")
            return redirect('ambulance_dashboard')

        elif action == 'toggle_ambulance_maintenance':
            amb_id = request.POST.get('ambulance_id')
            new_status = request.POST.get('status')
            amb = get_object_or_404(Ambulance, id=amb_id)
            
            if amb.status == 'Busy' and new_status == 'Maintenance':
                messages.error(request, "Ambulance is busy on a call. Cannot place in maintenance.")
            else:
                amb.status = new_status
                amb.save()
                messages.success(request, f"Ambulance status set to {new_status}.")
            return redirect('ambulance_dashboard')

    available_ambulances = Ambulance.objects.filter(status='Available')

    return render(request, 'hospitalapp/receptionist/ambulance.html', {
        'ambulances': ambulances,
        'requests': requests,
        'available_ambulances': available_ambulances,
        'priorities': AmbulanceRequest.PRIORITY_CHOICES,
    })


# ─────────────────────────────────────────────
#  NON-STAFF, CLEANING, SECURITY & LAUNDRY
# ─────────────────────────────────────────────

@role_required('receptionist', 'admin')
def non_staff_dashboard(request):
    staff = NonStaff.objects.all().order_by('role', 'name')
    shifts = NonStaffShift.objects.filter(shift_date=timezone.now().date())
    
    # Logs
    cleaning = CleaningLog.objects.all().order_by('-logged_at')[:20]
    visitors = VisitorLog.objects.all().order_by('-entry_time')[:20]
    incidents = SecurityIncident.objects.all().order_by('-created_at')[:20]
    laundry = LaundryLog.objects.all().order_by('-received_at')[:20]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_staff':
            name = request.POST.get('name', '').strip()
            role = request.POST.get('role')
            phone = request.POST.get('phone', '').strip()
            salary = request.POST.get('salary')

            if name and role and phone and salary:
                NonStaff.objects.create(name=name, role=role, phone=phone, salary=Decimal(salary))
                messages.success(request, f"Staff member '{name}' registered successfully.")
            else:
                messages.error(request, "All fields are required.")
            return redirect('non_staff_dashboard')

        elif action == 'allocate_shift':
            staff_id = request.POST.get('staff_id')
            shift_date = request.POST.get('shift_date')
            shift_type = request.POST.get('shift_type')
            status = request.POST.get('attendance_status', 'Present')

            member = get_object_or_404(NonStaff, id=staff_id)
            exists = NonStaffShift.objects.filter(staff=member, shift_date=shift_date).first()
            if exists:
                exists.shift_type = shift_type
                exists.attendance_status = status
                exists.save()
                messages.success(request, f"Updated shift for {member.name}.")
            else:
                NonStaffShift.objects.create(staff=member, shift_date=shift_date, shift_type=shift_type, attendance_status=status)
                messages.success(request, f"Rostered shift for {member.name}.")
            return redirect('non_staff_dashboard')

        elif action == 'log_cleaning':
            area = request.POST.get('area_name', '').strip()
            cleaner_id = request.POST.get('cleaner_id')
            cleaner = get_object_or_404(NonStaff, id=cleaner_id, role='Cleaning')

            if area:
                CleaningLog.objects.create(area_name=area, cleaner=cleaner, status='Pending')
                messages.success(request, f"Cleaning log created for {area}.")
            else:
                messages.error(request, "Area name is required.")
            return redirect('non_staff_dashboard')

        elif action == 'complete_cleaning':
            log_id = request.POST.get('log_id')
            log = get_object_or_404(CleaningLog, id=log_id)
            log.status = 'Completed'
            log.completed_at = timezone.now()
            log.save()
            messages.success(request, f"Sanitation log for {log.area_name} completed.")
            return redirect('non_staff_dashboard')

        elif action == 'log_visitor':
            name = request.POST.get('visitor_name', '').strip()
            phone = request.POST.get('visitor_phone', '').strip()
            purpose = request.POST.get('purpose', '').strip()
            patient = request.POST.get('patient_name', '').strip()

            if name and phone and purpose and patient:
                VisitorLog.objects.create(visitor_name=name, visitor_phone=phone, purpose=purpose, patient_name=patient)
                messages.success(request, f"Visitor {name} entry logged.")
            else:
                messages.error(request, "Visitor details are required.")
            return redirect('non_staff_dashboard')

        elif action == 'log_visitor_exit':
            log_id = request.POST.get('log_id')
            log = get_object_or_404(VisitorLog, id=log_id)
            log.exit_time = timezone.now()
            log.save()
            messages.success(request, f"Visitor {log.visitor_name} exit recorded.")
            return redirect('non_staff_dashboard')

        elif action == 'log_incident':
            title = request.POST.get('title', '').strip()
            desc = request.POST.get('description', '').strip()
            reporter = request.POST.get('reported_by', '').strip()

            if title and desc and reporter:
                SecurityIncident.objects.create(title=title, description=desc, reported_by=reporter)
                messages.error(request, f"Security Alert: Incident '{title}' logged!")
            else:
                messages.error(request, "All details are required.")
            return redirect('non_staff_dashboard')

        elif action == 'resolve_incident':
            inc_id = request.POST.get('incident_id')
            inc = get_object_or_404(SecurityIncident, id=inc_id)
            inc.is_resolved = True
            inc.save()
            messages.success(request, f"Incident '{inc.title}' resolved.")
            return redirect('non_staff_dashboard')

        elif action == 'log_laundry':
            item = request.POST.get('item_type')
            qty = request.POST.get('quantity')

            if item and qty:
                LaundryLog.objects.create(item_type=item, quantity=int(qty), status='Pending')
                messages.success(request, f"Laundry batch received for {item} (x{qty}).")
            else:
                messages.error(request, "Item type and quantity required.")
            return redirect('non_staff_dashboard')

        elif action == 'update_laundry':
            log_id = request.POST.get('log_id')
            status = request.POST.get('status')
            log = get_object_or_404(LaundryLog, id=log_id)
            log.status = status
            if status == 'Completed':
                log.completed_at = timezone.now()
            log.save()
            messages.success(request, f"Laundry log status updated to {status}.")
            return redirect('non_staff_dashboard')

    cleaners = NonStaff.objects.filter(role='Cleaning', duty_status='Available')

    return render(request, 'hospitalapp/receptionist/non_staff.html', {
        'staff': staff,
        'shifts': shifts,
        'cleaning': cleaning,
        'visitors': visitors,
        'incidents': incidents,
        'laundry': laundry,
        'cleaners': cleaners,
        'non_staff_roles': NonStaff.ROLE_CHOICES,
        'laundry_items': LaundryLog.ITEM_CHOICES,
    })


# ─────────────────────────────────────────────
#  PROFESSIONAL MEDICATION MANAGEMENT SYSTEM
# ─────────────────────────────────────────────

from datetime import datetime, timedelta
from django.db import transaction

@role_required('doctor')
def doctor_inpatient_prescription(request, admission_id):

    admission = get_object_or_404(
        Admission,
        admission_id=admission_id
    )

    doctor = get_object_or_404(
    Doctor,
    user=request.user
)


    # -----------------------------------
    # PERMISSION CHECK
    # -----------------------------------

    is_primary = (
    admission.doctor == doctor
)

    is_consultant = AdmissionConsultant.objects.filter(
    admission=admission,
    doctor=doctor
).exists()
    if not (is_primary or is_consultant):
        messages.error(
            request,
            "You are not assigned to this patient."
        )
        return redirect('doctor_dashboard')
    # -----------------------------------
    # PRESCRIPTION LOGIC
    # -----------------------------------

    if request.method == 'POST':

        medicine_ids = request.POST.getlist('medicine_ids[]')
        dosages = request.POST.getlist('dosages[]')
        frequencies = request.POST.getlist('frequencies[]')
        routes = request.POST.getlist('routes[]')
        durations = request.POST.getlist('durations[]')
        instructions_list = request.POST.getlist('instructions[]')

        diagnosis_notes = request.POST.get(
            'diagnosis_notes',
            ''
        ).strip()

        if not medicine_ids:

            messages.error(
                request,
                "Please add at least one medicine."
            )

            return redirect(
                'doctor_inpatient_prescription',
                admission_id=admission_id
            )

        freq_time_map = {
            'OD': ['08:00'],
            'BD': ['08:00', '20:00'],
            'TID': ['08:00', '14:00', '20:00'],
            'QID': ['06:00', '12:00', '18:00', '00:00'],
        }

        try:

            with transaction.atomic():

                ip_prescription = InpatientPrescription.objects.create(
                    admission=admission,
                    doctor=doctor,
                    diagnosis_notes=diagnosis_notes
                )

                now = timezone.now()
                today = now.date()

                for idx, med_id in enumerate(medicine_ids):

                    medicine = get_object_or_404(
                        Medicine,
                        medicine_id=med_id
                    )

                    dosage = dosages[idx].strip()
                    frequency = frequencies[idx]
                    route = routes[idx]
                    duration = int(durations[idx])
                    instruction = instructions_list[idx].strip()

                    times = freq_time_map.get(
                        frequency,
                        ['08:00']
                    )

                    item = InpatientPrescriptionItem.objects.create(
                        prescription=ip_prescription,
                        medicine=medicine,
                        dosage=dosage,
                        frequency=frequency,
                        route=route,
                        duration_days=duration,
                        instructions=instruction,
                        timing=' - '.join(times)
                    )

                    for d in range(duration):

                        dose_date = today + timedelta(days=d)

                        for time_str in times:

                            hour, minute = map(
                                int,
                                time_str.split(':')
                            )

                            naive_dt = datetime.combine(
                                dose_date,
                                datetime.min.time().replace(
                                    hour=hour,
                                    minute=minute
                                )
                            )

                            scheduled_dt = timezone.make_aware(
                                naive_dt,
                                timezone.get_current_timezone()
                            )

                            if d == 0 and scheduled_dt <= now:
                                scheduled_dt = now

                            MedicationScheduleEntry.objects.create(
                                prescription_item=item,
                                admission=admission,
                                scheduled_time=scheduled_dt,
                                status='Pending'
                            )

                messages.success(
                    request,
                    f"Prescription added by Dr. {doctor.name}"
                )

                return redirect(
                    'patient_details',
                    admission_id=admission.admission_id
                )

        except Exception as e:

            messages.error(
                request,
                f"Prescription error: {str(e)}"
            )

            return redirect(
                'doctor_inpatient_prescription',
                admission_id=admission_id
            )

    medicines = Medicine.objects.filter(
        stock__gt=0
    ).order_by('name')

    routes = [
        'Tablet',
        'Injection',
        'IV',
        'Syrup',
        'Drops',
        'Nebulization'
    ]

    frequencies = [
        'OD',
        'BD',
        'TID',
        'QID'
    ]

    consultants = AdmissionConsultant.objects.filter(
        admission=admission
    ).select_related('doctor')

    return render(
        request,
        'hospitalapp/doctor/ip_prescription.html',
        {
            'admission': admission,
            'medicines': medicines,
            'routes': routes,
            'frequencies': frequencies,
            'consultants': consultants,
            'primary_doctor': admission.doctor
        }
    )
@role_required('nurse')
def nurse_administer_item(request, entry_id):

    entry = get_object_or_404(
        MedicationScheduleEntry.objects.select_related(
            'prescription_item',
            'prescription_item__medicine',
            'admission'
        ),
        id=entry_id
    )

    nurse = get_object_or_404(Nurse, user=request.user)

    if request.method == 'POST':

        notes = request.POST.get('notes', '').strip()
        action_type = request.POST.get(
            'action_type',
            'Administered'
        )

        # REFUSED
        if action_type == 'Refused':

            entry.status = 'Refused'
            entry.administered_by = nurse
            entry.administered_at = timezone.now()
            entry.notes = notes
            entry.save()

            messages.info(
                request,
                "Medication marked as refused."
            )

            return redirect('nurse_dashboard')

        medicine = entry.prescription_item.medicine

        if medicine.stock < 1:
            messages.error(
                request,
                f"{medicine.name} is out of stock."
            )
            return redirect('nurse_dashboard')

        try:
            with transaction.atomic():

                medicine.stock -= 1
                medicine.save()

                now = timezone.now()

                if now > entry.scheduled_time + timedelta(hours=1):
                    entry.status = 'Delayed'
                else:
                    entry.status = 'Administered'

                entry.administered_by = nurse
                entry.administered_at = now
                entry.notes = notes
                entry.save()

                MedicineAdministration.objects.create(
                    admission=entry.admission,
                    nurse=nurse,
                    medicine_name=medicine.name,
                    dosage=entry.prescription_item.dosage,
                    notes=notes,
                    schedule_entry=entry,
                    medicine=medicine,
                    quantity=1
                )

                IPCharge.objects.create(
                    admission=entry.admission,
                    charge_type='Pharmacy Bill',
                    description=f"{medicine.name} x1",
                    amount=medicine.price
                )

                messages.success(
                    request,
                    f"{medicine.name} administered successfully."
                )

        except Exception as e:
            messages.error(request, str(e))

    return redirect('nurse_dashboard')


@role_required('nurse')
def nurse_medication_log(request):

    nurse = get_object_or_404(Nurse, user=request.user)

    logs = MedicineAdministration.objects.filter(
        admission__ward_type=nurse.assigned_ward
    ).select_related(
        'admission',
        'admission__patient',
        'medicine'
    ).order_by('-administered_at')

    return render(request, 'hospitalapp/nurse/medication_log.html', {
        'logs': logs,
        'nurse': nurse
    })


@role_required('doctor')
def doctor_refer_specialist(request, casualty_id):
    casualty = get_object_or_404(Casuality, id=casualty_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        specialist_ids = request.POST.getlist('specialist_ids') or request.POST.getlist('specialists')
        referral_notes = request.POST.get('referral_notes', '').strip()

        for spec_id in specialist_ids:
            specialist = get_object_or_404(Doctor, doctor_id=spec_id)
            CasualityReferral.objects.get_or_create(
                casualty=casualty,
                referred_doctor=specialist,
                referred_by=doctor,
                defaults={
                    'status': 'Pending',
                    'notes': referral_notes
                }
            )

        casualty.status = 'Referred'
        casualty.save()

        messages.success(request, f"Patient successfully referred to {len(specialist_ids)} specialist(s).")
        return redirect('doctor_emergency_dashboard')

    return redirect('doctor_emergency_dashboard')

# Aliases for compatibility
create_referral = doctor_refer_specialist
refer_specialist = doctor_refer_specialist


@role_required('doctor')
def referral_inbox(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    referrals = CasualityReferral.objects.filter(
        referred_doctor=doctor,
        status='Pending'
    ).select_related('casualty', 'casualty__patient', 'referred_by')

    return render(
        request,
        'hospitalapp/doctor/referral_inbox.html',
        {
            'referrals': referrals
        }
    )


@role_required('doctor')
def specialist_referrals(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    referrals = CasualityReferral.objects.filter(
        referred_doctor=doctor
    ).select_related('casualty', 'casualty__patient', 'referred_by')

    # Attach lab and radiology orders for each referred patient (emergency – no admission)
    referral_data = []
    for referral in referrals:
        patient = referral.casualty.patient
        lab_orders = LabOrder.objects.filter(
            patient=patient,
            admission__isnull=True
        ).prefetch_related('items__test', 'items__labresult__parameter_results__parameter')
        radiology_orders = RadiologyOrder.objects.filter(
            patient=patient,
            admission__isnull=True
        ).prefetch_related('items__test', 'items__radiologyreport')
        referral_data.append({
            'referral': referral,
            'lab_orders': lab_orders,
            'radiology_orders': radiology_orders,
        })

    return render(
        request,
        'hospitalapp/doctor/specialist_referrals.html',
        {
            'referrals': referrals,
            'referral_data': referral_data,
        }
    )


@role_required('doctor')
def accept_referral(request, referral_id):
    referral = get_object_or_404(CasualityReferral, id=referral_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    if referral.referred_doctor != doctor:
        messages.error(request, "Unauthorized to accept this referral.")
        return redirect('doctor_dashboard')

    referral.status = 'Accepted'
    referral.save()

    messages.success(request, "Referral accepted. You are now part of the patient's care team.")
    return redirect('specialist_referrals')


@role_required('doctor')
def reject_referral(request, referral_id):
    referral = get_object_or_404(CasualityReferral, id=referral_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    if referral.referred_doctor != doctor:
        messages.error(request, "Unauthorized to reject this referral.")
        return redirect('doctor_dashboard')

    referral.status = 'Rejected'
    referral.save()

    messages.success(request, "Referral rejected.")
    return redirect('specialist_referrals')


@role_required('doctor')
def admit_referred_patient(request, casualty_id):
    casualty = get_object_or_404(Casuality, id=casualty_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    # Admitting doctor must be in care team
    is_in_team = (casualty.doctor == doctor) or CasualityReferral.objects.filter(
        casualty=casualty, referred_doctor=doctor, status='Accepted'
    ).exists()

    if not is_in_team:
        messages.error(request, "You are not assigned to this patient's care team.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        ward_type = request.POST.get('ward_type')
        bed_id = request.POST.get('bed_id')
        reason = request.POST.get('reason', casualty.emergency_reason)

        bed = get_object_or_404(Bed, id=bed_id, status='Available')

        admission = Admission.objects.create(
            patient=casualty.patient,
            doctor=doctor,
            ward_type=ward_type,
            bed=bed,
            bed_number=bed.bed_number,
            status='Admitted',
            reason=reason
        )

        bed.status = 'Occupied'
        bed.patient = casualty.patient
        bed.save()

        # Link all doctors from the care team to AdmissionConsultant
        AdmissionConsultant.objects.get_or_create(
            admission=admission,
            doctor=casualty.doctor
        )

        if doctor != casualty.doctor:
            AdmissionConsultant.objects.get_or_create(
                admission=admission,
                doctor=doctor
            )

        accepted_referrals = CasualityReferral.objects.filter(
            casualty=casualty,
            status='Accepted'
        )
        for referral in accepted_referrals:
            AdmissionConsultant.objects.get_or_create(
                admission=admission,
                doctor=referral.referred_doctor
            )

        casualty.status = 'Admitted'
        casualty.save()

        # Create IP Bill & Charges
        IPBill.objects.create(
            admission=admission,
            subtotal=Decimal('0.00'),
            gst=Decimal('0.00'),
            grand_total=Decimal('0.00'),
            payment_status='Pending'
        )

        IPCharge.objects.create(
            admission=admission,
            charge_type='Emergency Charge',
            description='Collaborative Inpatient Admission Fee',
            amount=Decimal('1000.00')
        )

        recalculate_ip_bill(admission)

        messages.success(request, f"Patient admitted to {ward_type} (Bed: {bed.bed_number}) successfully.")
        return redirect('patient_details', admission_id=admission.admission_id)

    beds = Bed.objects.filter(status='Available')
    return render(
        request,
        'hospitalapp/doctor/admit_patient.html',
        {
            'casualty': casualty,
            'beds': beds
        }
    )

# Alias for compatibility
specialist_admit_patient = admit_referred_patient


@role_required('doctor')
def transfer_to_icu(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        return HttpResponseForbidden("Not authorized.")

    if request.method == 'POST':
        bed_id = request.POST.get('icu_bed')
        if not bed_id:
            messages.error(request, "Please select a valid ICU bed.")
            return redirect('patient_details', admission_id=admission_id)
        
        try:
            icu_bed = Bed.objects.get(id=bed_id, status='Available', ward_type='ICU')
        except Bed.DoesNotExist:
            messages.error(request, "Selected ICU bed is no longer available. Please select another bed.")
            return redirect('patient_details', admission_id=admission_id)

        old_bed = admission.bed
        if old_bed:
            old_bed.status = 'Available'
            old_bed.patient = None
            old_bed.save()

        admission.ward_type = 'ICU'
        admission.bed = icu_bed
        admission.bed_number = icu_bed.bed_number
        admission.save()

        icu_bed.status = 'Occupied'
        icu_bed.patient = admission.patient
        icu_bed.save()

        # Log a clinical note automatically for the state change
        ClinicalNote.objects.create(
            admission=admission,
            doctor=doctor,
            note_text=f"*** STATE CHANGE: PATIENT TRANSFERRED TO ICU ***\nReason: Transferred to ICU Bed {icu_bed.bed_number} by Dr. {doctor.name}."
        )

        IPCharge.objects.create(
            admission=admission,
            charge_type='Room Charge',
            description='ICU Daily Charge',
            amount=Decimal('2000.00')
        )
        recalculate_ip_bill(admission)

        messages.success(request, "Patient successfully transferred to ICU. All consultants retain access.")
    return redirect('patient_details', admission_id=admission_id)


@role_required('doctor')
def transfer_patient(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        return HttpResponseForbidden("Not authorized.")

    if request.method == 'POST':
        new_bed_id = request.POST.get('bed_id')
        if not new_bed_id:
            messages.error(request, "Please select a valid bed.")
            return redirect('transfer_patient', admission_id=admission_id)

        try:
            new_bed = Bed.objects.get(id=new_bed_id, status='Available')
        except Bed.DoesNotExist:
            messages.error(request, "Selected bed is no longer available. Please select another bed.")
            return redirect('transfer_patient', admission_id=admission_id)

        new_ward = new_bed.ward_type

        old_bed = admission.bed
        if old_bed:
            old_bed.status = 'Available'
            old_bed.patient = None
            old_bed.save()

        admission.ward_type = new_ward
        admission.bed = new_bed
        admission.bed_number = new_bed.bed_number
        admission.save()

        new_bed.status = 'Occupied'
        new_bed.patient = admission.patient
        new_bed.save()

        # Log a clinical note automatically for the state change
        ClinicalNote.objects.create(
            admission=admission,
            doctor=doctor,
            note_text=f"*** STATE CHANGE: TRANSFERRED TO {new_ward.upper()} ***\nReason: Patient stabilized and shifted to {new_ward} Bed {new_bed.bed_number} by Dr. {doctor.name}."
        )

        IPCharge.objects.create(
            admission=admission,
            charge_type='Room Charge',
            description=f"Shifted to {new_ward} Bed {new_bed.bed_number}",
            amount=Decimal('800.00')
        )
        recalculate_ip_bill(admission)

        messages.success(request, f"Patient successfully shifted to {new_ward}.")
        return redirect('patient_details', admission_id=admission_id)

    beds = Bed.objects.filter(status='Available')
    return render(
        request,
        'hospitalapp/doctor/transfer_patient.html',
        {
            'admission': admission,
            'beds': beds
        }
    )


@role_required('doctor')
def discharge_patient(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        return HttpResponseForbidden("Not authorized.")

    admission.status = 'Discharged'
    admission.discharge_date = timezone.now()
    admission.save()

    if admission.bed:
        admission.bed.status = 'Available'
        admission.bed.patient = None
        admission.bed.save()

    ClinicalNote.objects.create(
        admission=admission,
        doctor=doctor,
        note_text=f"*** PATIENT DISCHARGED ***\nPatient discharged by Dr. {doctor.name}."
    )

    # Merge any outstanding CasualtyBill charges into the IP Bill (safety net)
    from django.db.models import Sum
    casualty_case = Casuality.objects.filter(patient=admission.patient, status='Admitted').first()
    if casualty_case:
        unbilled = CasualtyBill.objects.filter(casualty=casualty_case, merged_to_ip=False)
        for cb in unbilled:
            IPCharge.objects.create(
                admission=admission,
                charge_type='Pharmacy Bill',
                description=f"[Emergency] {cb.description}",
                amount=cb.amount
            )
            cb.merged_to_ip = True
            cb.save()
        # Recalculate IP Bill total
        recalculate_ip_bill(admission)

    messages.success(request, f"Patient {admission.patient.name} discharged successfully.")
    return redirect('doctor_dashboard')


@role_required('doctor')
def patient_care_details(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    # Must be in care team
    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        messages.error(request, "You are not assigned to this patient's care team.")
        return redirect('doctor_dashboard')

    vitals = VitalRecord.objects.filter(admission=admission).order_by('-recorded_at')
    medications = MedicineAdministration.objects.filter(admission=admission).order_by('-administered_at')
    clinical_notes = ClinicalNote.objects.filter(admission=admission).order_by('-created_at')
    nursing_notes = NurseNote.objects.filter(admission=admission).order_by('-created_at')
    investigations = InvestigationSuggestion.objects.filter(admission=admission).order_by('-created_at')
    
    # Get all consultants in care team
    consultants = AdmissionConsultant.objects.filter(admission=admission).select_related('doctor')
    specialist_doctors = Doctor.objects.exclude(doctor_id=doctor.doctor_id).order_by('specialization', 'name')
    available_beds = Bed.objects.filter(status='Available')

    # Casualty/Emergency history for this patient
    from django.db.models import Sum
    casualty_case = Casuality.objects.filter(patient=admission.patient).order_by('-created_at').first()
    casualty_vitals = VitalRecord.objects.filter(casualty=casualty_case).order_by('-recorded_at') if casualty_case else []
    casualty_bills = CasualtyBill.objects.filter(casualty=casualty_case).order_by('created_at') if casualty_case else []
    casualty_total = CasualtyBill.objects.filter(casualty=casualty_case).aggregate(t=Sum('amount'))['t'] or 0 if casualty_case else 0

    lab_orders = LabOrder.objects.filter(patient=admission.patient).prefetch_related('items', 'items__labresult').order_by('-created_at')
    radiology_orders = RadiologyOrder.objects.filter(patient=admission.patient).prefetch_related('items', 'items__radiologyreport').order_by('-created_at')

    return render(
        request,
        'hospitalapp/doctor/patient_care.html',
        {
            'admission': admission,
            'vitals': vitals,
            'medications': medications,
            'clinical_notes': clinical_notes,
            'nursing_notes': nursing_notes,
            'investigations': investigations,
            'consultants': consultants,
            'specialist_doctors': specialist_doctors,
            'available_beds': available_beds,
            'casualty_case': casualty_case,
            'casualty_vitals': casualty_vitals,
            'casualty_bills': casualty_bills,
            'casualty_total': casualty_total,
            'lab_orders': lab_orders,
            'radiology_orders': radiology_orders,
        }
    )


@role_required('doctor')
def add_clinical_note(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        return HttpResponseForbidden("Not authorized.")

    if request.method == 'POST':
        note_text = request.POST.get('note_text', '').strip()
        if note_text:
            ClinicalNote.objects.create(
                admission=admission,
                doctor=doctor,
                note_text=note_text
            )
            messages.success(request, "Clinical note added successfully.")

    return redirect('patient_details', admission_id=admission_id)


@role_required('doctor')
def suggest_investigation(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        return HttpResponseForbidden("Not authorized.")

    if request.method == 'POST':
        investigation_name = request.POST.get('investigation_name', '').strip()
        notes = request.POST.get('notes', '').strip()

        if investigation_name:
            InvestigationSuggestion.objects.create(
                admission=admission,
                doctor=doctor,
                investigation_name=investigation_name,
                notes=notes
            )
            messages.success(request, f"Investigation '{investigation_name}' suggested successfully.")

    return redirect('patient_details', admission_id=admission_id)


@role_required('doctor')
def doctor_add_discharge_prescription(request, admission_id):
    admission = get_object_or_404(Admission, admission_id=admission_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    is_assigned = (admission.doctor == doctor) or AdmissionConsultant.objects.filter(
        admission=admission, doctor=doctor
    ).exists()

    if not is_assigned:
        messages.error(request, "You are not assigned to this patient's care team.")
        return redirect('doctor_dashboard')

    medicines = Medicine.objects.all()

    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis', '').strip()
        notes = request.POST.get('notes', '').strip()

        medicine_ids = request.POST.getlist('medicine_id')
        quantities = request.POST.getlist('quantity')

        if not medicine_ids:
            messages.error(request, "Please add at least one medicine.")
            return redirect('doctor_add_discharge_prescription', admission_id=admission_id)

        try:
            with transaction.atomic():
                prescription = Prescription.objects.create(
                    admission=admission,
                    appointment=None,
                    doctor=doctor,
                    patient=admission.patient,
                    diagnosis=diagnosis,
                    notes=notes,
                    status='Pending'
                )

                med_list = []
                for i in range(len(medicine_ids)):
                    if medicine_ids[i] and quantities[i]:
                        medicine = get_object_or_404(Medicine, medicine_id=medicine_ids[i])
                        PrescriptionMedicine.objects.create(
                            prescription=prescription,
                            medicine=medicine,
                            quantity=int(quantities[i])
                        )
                        med_list.append(f"{medicine.name} (x{quantities[i]})")

                if med_list:
                    prescription.medicines = ", ".join(med_list)
                    prescription.save()

                messages.success(request, f"Take-Home Prescription created successfully for {admission.patient.name}!")
                
                # Log a clinical note for the take-home prescription
                ClinicalNote.objects.create(
                    admission=admission,
                    doctor=doctor,
                    note_text=f"*** TAKE-HOME PRESCRIPTION CREATED ***\nPrescribed take-home medicines: {', '.join(med_list)}."
                )

                return redirect('patient_details', admission_id=admission_id)

        except Exception as e:
            messages.error(request, f"Prescription error: {str(e)}")
            return redirect('doctor_add_discharge_prescription', admission_id=admission_id)

    return render(request, 'hospitalapp/doctor/add_discharge_prescription.html', {
        'admission': admission,
        'medicines': medicines
    })


@role_required('doctor')
def doctor_create_lab_order(
    request,
    patient_id
):

    patient = get_object_or_404(
        Patient,
        patient_id=patient_id
    )

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    if request.method == 'POST':

        form = LabOrderForm(
            request.POST
        )

        if form.is_valid():

            active_admission = Admission.objects.filter(
                patient=patient,
                status='Admitted'
            ).first()

            with transaction.atomic():
                tests = form.cleaned_data['tests']
                if tests:
                    order = LabOrder.objects.create(
                        patient=patient,
                        ordered_by=doctor,
                        clinical_notes=form.cleaned_data['clinical_notes']
                    )
                    total_price = Decimal('0.00')
                    test_names = []
                    for test in tests:
                        LabOrderItem.objects.create(
                            order=order,
                            test=test
                        )
                        total_price += test.price
                        test_names.append(test.name)

                    if active_admission:
                        order.admission = active_admission
                        order.save()
                        # IP: Add as a charge to the discharge bill
                        IPCharge.objects.create(
                            admission=active_admission,
                            charge_type='Laboratory Charge',
                            description=f"Lab Order #{order.id} - {', '.join(test_names)}",
                            amount=total_price
                        )
                    else:
                        # OP: Create a standalone bill referencing this lab order
                        Bill.objects.create(
                            patient=patient,
                            total_amount=total_price,
                            bill_type='laboratory',
                            payment_status='Pending',
                            lab_order=order
                        )

            if active_admission:
                recalculate_ip_bill(active_admission)
                messages.success(
                    request,
                    'Laboratory order created successfully.'
                )
                return redirect(
                    'patient_details',
                    admission_id=active_admission.admission_id
                )
            else:
                messages.success(
                    request,
                    'Laboratory order created successfully.'
                )
                return redirect(
                    'patient_history',
                    patient_id=patient.patient_id
                )

    else:

        form = LabOrderForm()

    return render(
        request,
        'hospitalapp/doctor/create_lab_order.html',
        {
            'patient': patient,
            'form': form
        }
    )

@role_required('doctor')
def doctor_create_radiology_order(
    request,
    patient_id
):

    patient = get_object_or_404(
        Patient,
        patient_id=patient_id
    )

    doctor = get_object_or_404(
        Doctor,
        user=request.user
    )

    if request.method == 'POST':

        form = RadiologyOrderForm(
            request.POST
        )

        if form.is_valid():

            active_admission = Admission.objects.filter(
                patient=patient,
                status='Admitted'
            ).first()

            with transaction.atomic():
                tests = form.cleaned_data['tests']
                if tests:
                    order = RadiologyOrder.objects.create(
                        patient=patient,
                        ordered_by=doctor,
                        clinical_notes=form.cleaned_data['clinical_notes']
                    )
                    total_price = Decimal('0.00')
                    test_names = []
                    for test in tests:
                        RadiologyOrderItem.objects.create(
                            order=order,
                            test=test
                        )
                        total_price += test.price
                        test_names.append(test.name)

                    if active_admission:
                        order.admission = active_admission
                        order.save()
                        # IP: Add as a charge to the discharge bill
                        IPCharge.objects.create(
                            admission=active_admission,
                            charge_type='Radiology Charge',
                            description=f"Radiology Order #{order.id} - {', '.join(test_names)}",
                            amount=total_price
                        )
                    else:
                        # OP: Create a standalone bill referencing this radiology order
                        Bill.objects.create(
                            patient=patient,
                            total_amount=total_price,
                            bill_type='radiology',
                            payment_status='Pending',
                            radiology_order=order
                        )

            if active_admission:
                recalculate_ip_bill(active_admission)
                messages.success(
                    request,
                    'Radiology request created successfully.'
                )
                return redirect(
                    'patient_details',
                    admission_id=active_admission.admission_id
                )
            else:
                messages.success(
                    request,
                    'Radiology request created successfully.'
                )
                return redirect(
                    'patient_history',
                    patient_id=patient.patient_id
                )

    else:

        form = RadiologyOrderForm()

    return render(
        request,
        'hospitalapp/doctor/create_radiology_order.html',
        {
            'patient': patient,
            'form': form
        }
    )




# ============================================================
# UTILITY: Audit Logging
# ============================================================

def log_audit(request, action, model_name, object_id, details=''):
    AuditLog.objects.create(
        action=action,
        model_name=model_name,
        object_id=object_id,
        created_by=request.user,
        details=details
    )


# ============================================================
# LABORATORY VIEWS
# ============================================================

@role_required('lab_technician', 'admin')
def laboratory_dashboard(request):
    from django.utils.timezone import localdate, make_aware
    from datetime import datetime, time
    today = localdate()
    start_of_day = make_aware(datetime.combine(today, time.min))
    end_of_day = make_aware(datetime.combine(today, time.max))

    from django.db.models import Case, When, Value, IntegerField
    pending_orders = LabOrder.objects.filter(
        status__in=['Pending', 'Collected', 'Processing', 'Result Entered']
    ).select_related('patient', 'ordered_by', 'admission').prefetch_related('items__test').annotate(
        urgency_priority=Case(
            When(urgency='STAT', then=Value(1)),
            When(urgency='Urgent', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('urgency_priority', '-created_at')

    completed_orders = LabOrder.objects.filter(
        status='Verified'
    ).select_related('patient', 'ordered_by').order_by('-updated_at')[:30]

    total_orders_today = LabOrder.objects.filter(created_at__range=(start_of_day, end_of_day)).count()
    pending_samples = LabOrder.objects.filter(status='Pending').count()
    processing_tests = LabOrder.objects.filter(status__in=['Collected', 'Processing']).count()
    completed_reports_today = LabOrder.objects.filter(status='Verified', updated_at__range=(start_of_day, end_of_day)).count()

    critical_results_today = LabParameterResult.objects.filter(
        is_critical=True,
        result__completed_at__range=(start_of_day, end_of_day)
    ).count()

    from django.db.models import Sum
    daily_revenue_today = LabOrder.objects.filter(
        created_at__range=(start_of_day, end_of_day)
    ).aggregate(rev=Sum('items__test__price'))['rev'] or 0

    recent_critical_results = LabParameterResult.objects.filter(
        is_critical=True
    ).select_related('result__order_item__order__patient', 'result__order_item__test').order_by('-result__completed_at')[:5]

    return render(request, 'hospitalapp/laboratory/dashboard.html', {
        'total_orders_today': total_orders_today,
        'pending_samples': pending_samples,
        'processing_tests': processing_tests,
        'completed_reports_today': completed_reports_today,
        'critical_results_today': critical_results_today,
        'daily_revenue_today': daily_revenue_today,
        'recent_critical_results': recent_critical_results,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
    })


@role_required('lab_technician', 'admin')
def laboratory_samples(request):
    from django.db.models import Case, When, Value, IntegerField
    pending_orders = LabOrder.objects.filter(
        status='Pending'
    ).select_related('patient', 'ordered_by', 'admission').prefetch_related('items__test').annotate(
        urgency_priority=Case(
            When(urgency='STAT', then=Value(1)),
            When(urgency='Urgent', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('urgency_priority', '-created_at')

    return render(request, 'hospitalapp/laboratory/samples.html', {
        'pending_orders': pending_orders,
    })


@role_required('lab_technician', 'admin')
def laboratory_pipeline(request):
    from django.db.models import Case, When, Value, IntegerField
    active_orders = LabOrder.objects.filter(
        status__in=['Collected', 'Processing', 'Result Entered']
    ).select_related('patient', 'ordered_by', 'admission').prefetch_related('items__test').annotate(
        urgency_priority=Case(
            When(urgency='STAT', then=Value(1)),
            When(urgency='Urgent', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('urgency_priority', '-created_at')

    return render(request, 'hospitalapp/laboratory/pipeline.html', {
        'pending_orders': active_orders,  # Keep template variables simple
    })


@role_required('lab_technician', 'admin')
def laboratory_completed(request):
    completed_orders = LabOrder.objects.filter(
        status='Verified'
    ).select_related('patient', 'ordered_by').order_by('-updated_at')[:100]

    return render(request, 'hospitalapp/laboratory/completed.html', {
        'completed_orders': completed_orders,
    })


@role_required('lab_technician', 'admin')
def laboratory_collect_sample(request, order_id):
    order = get_object_or_404(LabOrder, id=order_id)

    if request.method == 'POST':
        sample_type = request.POST.get('sample_type', 'Blood')
        remarks = request.POST.get('remarks', '')
        barcode = request.POST.get('barcode', '').strip()
        if not barcode:
            import time
            barcode = f"BAR-{order.id}-{int(time.time())}"

        LabSample.objects.update_or_create(
            order=order,
            defaults={
                'sample_type': sample_type,
                'collected_by': request.user,
                'collection_time': timezone.now(),
                'remarks': remarks,
                'barcode': barcode,
            }
        )
        order.status = 'Collected'
        order.modified_by = request.user
        order.save()

        log_audit(request, 'Sample Collected', 'LabOrder', order.id, f'Type: {sample_type}')
        messages.success(request, f'Sample collected for Order #LAB-{order.id}.')
        return redirect('laboratory_pipeline')

    tests = order.items.select_related('test').all()
    return render(request, 'hospitalapp/laboratory/collect_sample.html', {
        'order': order,
        'tests': tests,
    })


@role_required('lab_technician', 'admin')
def laboratory_start_processing(request, order_id):
    order = get_object_or_404(LabOrder, id=order_id)
    order.status = 'Processing'
    order.modified_by = request.user
    order.save()
    log_audit(request, 'Processing Started', 'LabOrder', order.id)
    messages.success(request, f'Order #LAB-{order.id} marked as Processing.')
    return redirect('laboratory_pipeline')


@role_required('lab_technician', 'admin')
def enter_lab_result(request, item_id):
    item = get_object_or_404(LabOrderItem, id=item_id)
    order = item.order
    parameters = item.test.parameters.all()

    result, _ = LabResult.objects.get_or_create(
        order_item=item,
        defaults={'technician': request.user}
    )

    if request.method == 'POST':
        result.result_value = request.POST.get('result_value', '')
        result.remarks = request.POST.get('remarks', '')
        result.technician = request.user
        result.completed_at = timezone.now()
        result.is_verified = False
        result.save()

        # Save parameter-level results
        for param in parameters:
            val = request.POST.get(f'param_{param.id}', '').strip()
            if val:
                is_abnormal = False
                is_critical = False
                try:
                    fval = float(val)
                    if param.min_value is not None and param.max_value is not None:
                        if fval < float(param.min_value) or fval > float(param.max_value):
                            is_abnormal = True
                    if param.critical_min is not None and param.critical_max is not None:
                        if fval < float(param.critical_min) or fval > float(param.critical_max):
                            is_critical = True
                except (ValueError, TypeError):
                    pass

                LabParameterResult.objects.update_or_create(
                    result=result,
                    parameter=param,
                    defaults={
                        'value': val,
                        'is_abnormal': is_abnormal,
                        'is_critical': is_critical,
                    }
                )

        if order.status not in ['Result Entered', 'Verified']:
            order.status = 'Result Entered'
            order.modified_by = request.user
            order.save()

        log_audit(request, 'Result Entered', 'LabOrderItem', item.id)
        messages.success(request, f'Results saved for {item.test.name}.')
        return redirect('enter_all_lab_results', order_id=order.id)

    param_results = {pr.parameter_id: pr for pr in result.parameter_results.all()}
    parameters_data = []
    for param in parameters:
        parameters_data.append({
            'parameter': param,
            'result': param_results.get(param.id),
        })
    return render(request, 'hospitalapp/laboratory/enter_result.html', {
        'item': item,
        'order': order,
        'result': result,
        'parameters_data': parameters_data,
    })


@role_required('lab_technician', 'admin')
def enter_all_lab_results(request, order_id):
    order = get_object_or_404(LabOrder, id=order_id)
    items = order.items.select_related('test').prefetch_related(
        'test__parameters', 'labresult__parameter_results__parameter'
    ).all()

    items_data = []
    for item in items:
        try:
            result = item.labresult
        except LabResult.DoesNotExist:
            result = None
        param_results = {}
        if result:
            param_results = {pr.parameter_id: pr for pr in result.parameter_results.all()}
        
        parameters_data = []
        for param in item.test.parameters.all():
            parameters_data.append({
                'parameter': param,
                'result': param_results.get(param.id),
            })
            
        items_data.append({
            'item': item,
            'result': result,
            'parameters_data': parameters_data,
        })

    if request.method == 'POST':
        for item in items:
            result, _ = LabResult.objects.get_or_create(
                order_item=item,
                defaults={'technician': request.user}
            )
            result.result_value = request.POST.get(f'result_value_{item.id}', '')
            result.remarks = request.POST.get(f'remarks_{item.id}', '')
            result.technician = request.user
            result.completed_at = timezone.now()
            result.is_verified = False
            result.save()

            for param in item.test.parameters.all():
                val = request.POST.get(f'param_{item.id}_{param.id}', '').strip()
                if val:
                    is_abnormal = False
                    is_critical = False
                    try:
                        fval = float(val)
                        if param.min_value is not None and param.max_value is not None:
                            if fval < float(param.min_value) or fval > float(param.max_value):
                                is_abnormal = True
                        if param.critical_min is not None and param.critical_max is not None:
                            if fval < float(param.critical_min) or fval > float(param.critical_max):
                                is_critical = True
                    except (ValueError, TypeError):
                        pass

                    LabParameterResult.objects.update_or_create(
                        result=result,
                        parameter=param,
                        defaults={
                            'value': val,
                            'is_abnormal': is_abnormal,
                            'is_critical': is_critical,
                        }
                    )

        order.status = 'Result Entered'
        order.modified_by = request.user
        order.save()

        log_audit(request, 'All Results Entered', 'LabOrder', order.id)
        messages.success(request, 'All results saved. Ready for verification.')
        return redirect('laboratory_pipeline')

    return render(request, 'hospitalapp/laboratory/enter_all_results.html', {
        'order': order,
        'items_data': items_data,
    })


@role_required('lab_technician', 'admin')
def verify_lab_result(request, order_id):
    order = get_object_or_404(LabOrder, id=order_id)
    results = LabResult.objects.filter(order_item__order=order)

    has_critical = LabParameterResult.objects.filter(
        result__order_item__order=order,
        is_critical=True
    ).exists()

    for result in results:
        result.is_verified = True
        result.verified_by = request.user
        result.verified_at = timezone.now()
        result.save()

    order.status = 'Verified'
    order.modified_by = request.user
    order.save()

    # Notify ordering doctor
    if order.ordered_by:
        notif_title = 'Lab Results Ready'
        notif_msg = f'Lab results for patient {order.patient.name} are verified and ready.'
        notif_type = 'Lab Report'
        if has_critical:
            notif_title = 'CRITICAL Lab Result Alert'
            notif_msg = f'CRITICAL values found in lab results for patient {order.patient.name}!'
            notif_type = 'Critical Lab Result'

        DoctorNotification.objects.create(
            doctor=order.ordered_by,
            title=notif_title,
            message=notif_msg,
            notification_type=notif_type,
            link=f'/laboratory/print-report/{order.id}/'
        )

    log_audit(request, 'Results Verified', 'LabOrder', order.id, f'Critical: {has_critical}')
    messages.success(request, f'Order #LAB-{order.id} verified and signed off.')
    return redirect('laboratory_completed')


@login_required
def print_lab_report(request, order_id):
    order = get_object_or_404(LabOrder, id=order_id)
    items = order.items.select_related('test').prefetch_related(
        'test__parameters', 'labresult__parameter_results__parameter'
    ).all()

    for item in items:
        item.test_name = item.test.name
        item.category = item.test.category
        try:
            item.result = item.labresult
        except LabResult.DoesNotExist:
            item.result = None

    return render(request, 'hospitalapp/laboratory/print_lab_report.html', {
        'order': order,
        'items': items,
    })


@login_required
def download_lab_report_pdf(request, order_id):
    order = get_object_or_404(LabOrder, id=order_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFillColor(colors.HexColor('#1a3c6e'))
    p.rect(0, height - 80, width, 80, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 18)
    p.drawString(40, height - 40, 'Asha Hospital')
    p.setFont('Helvetica', 10)
    p.drawString(40, height - 58, 'Laboratory Report')
    p.setFont('Helvetica', 9)
    p.drawRightString(width - 40, height - 40, f'Report ID: LAB-{order.id}')
    p.drawRightString(width - 40, height - 55, f'Date: {timezone.now().strftime("%d %b %Y, %H:%M")}')

    # Patient Info Box
    y = height - 110
    p.setFillColor(colors.HexColor('#f0f4f8'))
    p.rect(30, y - 50, width - 60, 50, fill=1, stroke=0)
    p.setFillColor(colors.HexColor('#1a3c6e'))
    p.setFont('Helvetica-Bold', 10)
    p.drawString(40, y - 15, f'Patient: {order.patient.name}')
    p.setFont('Helvetica', 9)
    p.setFillColor(colors.HexColor('#444444'))
    p.drawString(40, y - 30, f'Age/Gender: {order.patient.age}y / {order.patient.gender}')
    if order.ordered_by:
        p.drawString(250, y - 15, f'Ordered By: Dr. {order.ordered_by.name}')
    p.drawString(250, y - 30, f'Status: {order.status}')

    y = y - 70
    items = order.items.select_related('test').prefetch_related(
        'test__parameters', 'labresult__parameter_results__parameter'
    ).all()

    for item in items:
        p.setFillColor(colors.HexColor('#1a3c6e'))
        p.setFont('Helvetica-Bold', 11)
        p.drawString(40, y, f'Test: {item.test.name}')
        y -= 5
        p.setFillColor(colors.HexColor('#1a3c6e'))
        p.setStrokeColor(colors.HexColor('#1a3c6e'))
        p.line(40, y, width - 40, y)
        y -= 15

        try:
            result = item.labresult
            pr_list = result.parameter_results.select_related('parameter').all()

            # Table Header
            data = [['Parameter', 'Value', 'Unit', 'Reference Range', 'Flag']]
            for pr in pr_list:
                flag = ''
                if pr.is_critical:
                    flag = 'CRITICAL'
                elif pr.is_abnormal:
                    flag = 'Abnormal'
                data.append([
                    pr.parameter.name,
                    pr.value,
                    pr.parameter.unit or '-',
                    pr.parameter.reference_range or '-',
                    flag
                ])

            if len(data) > 1:
                col_widths = [150, 80, 60, 140, 70]
                tbl = Table(data, colWidths=col_widths)
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3c6e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('TEXTCOLOR', (-1, 1), (-1, -1), colors.HexColor('#d32f2f')),
                ]))
                tbl.wrapOn(p, width - 80, height)
                tbl.drawOn(p, 40, y - (len(data) * 18))
                y -= (len(data) * 18) + 10

            if result.remarks:
                p.setFont('Helvetica-Oblique', 9)
                p.setFillColor(colors.HexColor('#555555'))
                p.drawString(40, y, f'Remarks: {result.remarks}')
                y -= 15

            if result.is_verified and result.verified_by:
                p.setFont('Helvetica', 8)
                p.setFillColor(colors.HexColor('#2e7d32'))
                p.drawString(40, y, f'Verified by: {result.verified_by.username}  |  {result.verified_at.strftime("%d %b %Y %H:%M") if result.verified_at else ""}')
                y -= 20
        except LabResult.DoesNotExist:
            p.setFont('Helvetica-Oblique', 9)
            p.setFillColor(colors.grey)
            p.drawString(40, y, 'Result not yet entered.')
            y -= 20

        y -= 15
        if y < 80:
            p.showPage()
            y = height - 60

    # Footer
    p.setFont('Helvetica', 8)
    p.setFillColor(colors.grey)
    p.drawCentredString(width / 2, 30, 'Asha Hospital  |  This is a computer-generated report.')
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="lab_report_{order.id}.pdf"'
    })


# ============================================================
# RADIOLOGY VIEWS
# ============================================================

@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_dashboard(request):
    from django.utils.timezone import localdate, make_aware
    from datetime import datetime, time
    from django.db.models import Sum
    today = localdate()
    start_of_day = make_aware(datetime.combine(today, time.min))
    end_of_day = make_aware(datetime.combine(today, time.max))

    from django.db.models import Case, When, Value, IntegerField
    pending_orders = RadiologyOrder.objects.filter(
        status__in=['Pending', 'Scheduled', 'Arrived', 'Scanning', 'Scanned']
    ).select_related('patient', 'ordered_by', 'admission').prefetch_related(
        'items__test', 'scheduling'
    ).annotate(
        urgency_priority=Case(
            When(urgency='STAT', then=Value(1)),
            When(urgency='Urgent', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('urgency_priority', '-created_at')

    completed_orders = RadiologyOrder.objects.filter(
        status='Reported'
    ).select_related('patient', 'ordered_by').order_by('-updated_at')[:30]

    pending_scans = RadiologyOrder.objects.filter(status='Pending').count()
    scheduled_scans = RadiologyOrder.objects.filter(status='Scheduled').count()
    active_cases = RadiologyOrder.objects.filter(status__in=['Arrived', 'Scanning']).count()
    completed_scans_today = RadiologyOrder.objects.filter(
        status__in=['Scanned', 'Reported'], updated_at__range=(start_of_day, end_of_day)
    ).count()
    critical_findings_today = RadiologyReport.objects.filter(
        is_critical=True,
        reported_at__range=(start_of_day, end_of_day)
    ).count()
    daily_revenue_today = RadiologyOrder.objects.filter(
        created_at__range=(start_of_day, end_of_day)
    ).aggregate(rev=Sum('items__test__price'))['rev'] or 0

    recent_critical_reports = RadiologyReport.objects.filter(
        is_critical=True
    ).select_related('order_item__order__patient', 'order_item__test').order_by('-reported_at')[:5]

    return render(request, 'hospitalapp/radiology/dashboard.html', {
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'pending_scans': pending_scans,
        'scheduled_scans': scheduled_scans,
        'active_cases': active_cases,
        'completed_scans_today': completed_scans_today,
        'critical_findings_today': critical_findings_today,
        'daily_revenue_today': daily_revenue_today,
        'recent_critical_reports': recent_critical_reports,
    })


@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_schedule_queue(request):
    from django.db.models import Case, When, Value, IntegerField
    pending_orders = RadiologyOrder.objects.filter(
        status='Pending'
    ).select_related('patient', 'ordered_by', 'admission').prefetch_related(
        'items__test', 'scheduling'
    ).annotate(
        urgency_priority=Case(
            When(urgency='STAT', then=Value(1)),
            When(urgency='Urgent', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('urgency_priority', '-created_at')

    return render(request, 'hospitalapp/radiology/schedule_queue.html', {
        'pending_orders': pending_orders,
    })


@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_active_queue(request):
    from django.db.models import Case, When, Value, IntegerField
    active_orders = RadiologyOrder.objects.filter(
        status__in=['Scheduled', 'Arrived', 'Scanning', 'Scanned']
    ).select_related('patient', 'ordered_by', 'admission').prefetch_related(
        'items__test', 'scheduling', 'attachments'
    ).annotate(
        urgency_priority=Case(
            When(urgency='STAT', then=Value(1)),
            When(urgency='Urgent', then=Value(2)),
            default=Value(3),
            output_field=IntegerField()
        )
    ).order_by('urgency_priority', '-created_at')

    return render(request, 'hospitalapp/radiology/active_queue.html', {
        'pending_orders': active_orders,  # Keep template variables simple
    })


@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_completed(request):
    reported_orders = RadiologyOrder.objects.filter(
        status='Reported'
    ).select_related('patient', 'ordered_by').order_by('-updated_at')[:100]

    return render(request, 'hospitalapp/radiology/completed.html', {
        'reported_orders': reported_orders,
    })


@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_schedule_scan(request, order_id):
    order = get_object_or_404(RadiologyOrder, id=order_id)

    if request.method == 'POST':
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        machine = request.POST.get('machine', '')
        priority = request.POST.get('priority', 'Routine')
        tech_id = request.POST.get('technician')

        assigned_tech = request.user
        if tech_id:
            try:
                assigned_tech = User.objects.get(id=tech_id)
            except User.DoesNotExist:
                pass

        RadiologyScheduling.objects.update_or_create(
            order=order,
            defaults={
                'scheduled_date': scheduled_date,
                'scheduled_time': scheduled_time,
                'machine': machine,
                'technician': assigned_tech,
                'priority': priority,
            }
        )
        order.status = 'Scheduled'
        order.modified_by = request.user
        order.save()

        log_audit(request, 'Scan Scheduled', 'RadiologyOrder', order.id, f'Date: {scheduled_date}')
        messages.success(request, f'Scan for Order #RAD-{order.id} scheduled successfully.')
        return redirect('radiology_active_queue')

    technicians = User.objects.filter(role__in=['radiology_technician', 'radiologist', 'admin'])
    return render(request, 'hospitalapp/radiology/schedule_scan.html', {
        'order': order,
        'technicians': technicians,
    })


@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_update_scan_status(request, order_id, status):
    order = get_object_or_404(RadiologyOrder, id=order_id)
    valid_statuses = ['Pending', 'Scheduled', 'Arrived', 'Scanning', 'Scanned', 'Completed', 'Reported']
    if status in valid_statuses:
        order.status = status
        order.modified_by = request.user
        order.save()
        log_audit(request, f'Status Updated: {status}', 'RadiologyOrder', order.id)
        messages.success(request, f'Order #RAD-{order.id} status updated to {status}.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('radiology_active_queue')


@role_required('radiology_technician', 'radiologist', 'admin')
def radiology_upload_attachment(request, order_id):
    order = get_object_or_404(RadiologyOrder, id=order_id)
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        file_type = f.name.rsplit('.', 1)[-1].upper() if '.' in f.name else 'FILE'
        RadiologyAttachment.objects.create(
            order=order,
            file=f,
            file_type=file_type,
            uploaded_by=request.user
        )
        log_audit(request, 'Scan File Uploaded', 'RadiologyOrder', order.id, f'File: {f.name}')
        messages.success(request, f'Scan file "{f.name}" uploaded successfully.')
    else:
        messages.error(request, 'No file selected for upload.')
    return redirect('radiology_active_queue')


@role_required('radiologist', 'admin')
def create_radiology_report(request, item_id):
    item = get_object_or_404(RadiologyOrderItem, id=item_id)
    order = item.order

    if request.method == 'POST':
        findings = request.POST.get('findings', '').strip()
        impression = request.POST.get('impression', '').strip()
        clinical_history = request.POST.get('clinical_history', '').strip()
        recommendations = request.POST.get('recommendations', '').strip()
        is_critical = request.POST.get('is_critical') == 'on'
        report_file = request.FILES.get('report_file')

        report, _ = RadiologyReport.objects.update_or_create(
            order_item=item,
            defaults={
                'findings': findings,
                'impression': impression,
                'clinical_history': clinical_history,
                'recommendations': recommendations,
                'is_critical': is_critical,
                'radiologist': request.user,
                'reported_at': timezone.now(),
            }
        )
        if report_file:
            report.report_file = report_file
            report.save()

        order.status = 'Reported'
        order.modified_by = request.user
        order.save()

        if order.ordered_by:
            title = 'CRITICAL Radiology Finding' if is_critical else 'Radiology Report Ready'
            msg = (
                f'CRITICAL FINDINGS in radiology report for {order.patient.name} ({item.test.name})!'
                if is_critical
                else f'Radiology report for {order.patient.name} ({item.test.name}) is ready.'
            )
            DoctorNotification.objects.create(
                doctor=order.ordered_by,
                title=title,
                message=msg,
                notification_type='Critical Radiology Finding' if is_critical else 'Radiology Report',
                link=f'/radiology/print-report/{order.id}/'
            )

        log_audit(request, 'Radiology Report Created', 'RadiologyOrder', order.id, f'Critical: {is_critical}')
        messages.success(request, f'Radiology report for {item.test.name} submitted.')
        return redirect('radiology_completed')

    attachments = order.attachments.all()
    try:
        existing = item.radiologyreport
    except RadiologyReport.DoesNotExist:
        existing = None

    return render(request, 'hospitalapp/radiology/create_report.html', {
        'item': item,
        'order': order,
        'attachments': attachments,
        'existing': existing,
    })


@login_required
def print_radiology_report(request, order_id):
    order = get_object_or_404(RadiologyOrder, id=order_id)
    items = order.items.select_related('test').prefetch_related('radiologyreport').all()
    for item in items:
        item.test_name = item.test.name
        try:
            item.report = item.radiologyreport
        except RadiologyReport.DoesNotExist:
            item.report = None
    attachments = order.attachments.all()

    return render(request, 'hospitalapp/radiology/print_radiology_report.html', {
        'order': order,
        'items': items,
        'attachments': attachments,
    })


@login_required
def download_radiology_report_pdf(request, order_id):
    order = get_object_or_404(RadiologyOrder, id=order_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    p.setFillColor(colors.HexColor('#1a3c6e'))
    p.rect(0, height - 80, width, 80, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 18)
    p.drawString(40, height - 40, 'Asha Hospital')
    p.setFont('Helvetica', 10)
    p.drawString(40, height - 58, 'Radiology Report')
    p.setFont('Helvetica', 9)
    p.drawRightString(width - 40, height - 40, f'Report ID: RAD-{order.id}')
    p.drawRightString(width - 40, height - 55, f'Date: {timezone.now().strftime("%d %b %Y, %H:%M")}')

    y = height - 110
    p.setFillColor(colors.HexColor('#f0f4f8'))
    p.rect(30, y - 50, width - 60, 50, fill=1, stroke=0)
    p.setFillColor(colors.HexColor('#1a3c6e'))
    p.setFont('Helvetica-Bold', 10)
    p.drawString(40, y - 15, f'Patient: {order.patient.name}')
    p.setFont('Helvetica', 9)
    p.setFillColor(colors.HexColor('#444444'))
    p.drawString(40, y - 30, f'Age/Gender: {order.patient.age}y / {order.patient.gender}')
    if order.ordered_by:
        p.drawString(250, y - 15, f'Ordered By: Dr. {order.ordered_by.name}')

    y -= 70
    items = order.items.select_related('test').all()
    for item in items:
        p.setFillColor(colors.HexColor('#1a3c6e'))
        p.setFont('Helvetica-Bold', 11)
        p.drawString(40, y, f'Scan: {item.test.name}')
        y -= 5
        p.line(40, y, width - 40, y)
        y -= 15

        try:
            report = item.radiologyreport
            sections = [
                ('Clinical History', report.clinical_history),
                ('Findings', report.findings),
                ('Impression', report.impression),
                ('Recommendations', report.recommendations),
            ]
            for label, text in sections:
                if text:
                    p.setFont('Helvetica-Bold', 9)
                    p.setFillColor(colors.HexColor('#333333'))
                    p.drawString(40, y, f'{label}:')
                    y -= 12
                    p.setFont('Helvetica', 9)
                    p.setFillColor(colors.HexColor('#555555'))
                    # Wrap long text
                    words = text.split()
                    line_buf = ''
                    for word in words:
                        if len(line_buf + ' ' + word) > 90:
                            p.drawString(50, y, line_buf.strip())
                            y -= 12
                            line_buf = word
                            if y < 80:
                                p.showPage()
                                y = height - 60
                        else:
                            line_buf += ' ' + word
                    if line_buf:
                        p.drawString(50, y, line_buf.strip())
                        y -= 12

            if report.is_critical:
                p.setFillColor(colors.HexColor('#d32f2f'))
                p.setFont('Helvetica-Bold', 10)
                p.drawString(40, y, '*** CRITICAL FINDINGS ***')
                y -= 15

            if report.radiologist:
                p.setFont('Helvetica', 8)
                p.setFillColor(colors.HexColor('#2e7d32'))
                p.drawString(40, y, f'Reported by: {report.radiologist.username}')
                y -= 20
        except RadiologyReport.DoesNotExist:
            p.setFont('Helvetica-Oblique', 9)
            p.setFillColor(colors.grey)
            p.drawString(40, y, 'Report not yet created.')
            y -= 20

        y -= 15
        if y < 80:
            p.showPage()
            y = height - 60

    p.setFont('Helvetica', 8)
    p.setFillColor(colors.grey)
    p.drawCentredString(width / 2, 30, 'Asha Hospital  |  This is a computer-generated report.')
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="radiology_report_{order.id}.pdf"'
    })


# ============================================================
# ADMIN: Lab Test & Parameter Masters
# ============================================================

@role_required('admin')
def admin_manage_lab_tests(request):
    tests = LabTest.objects.all().order_by('category', 'name')

    if request.method == 'POST':
        action = request.POST.get('action')
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'General').strip()
        price = request.POST.get('price', 0)
        normal_range = request.POST.get('normal_range', '').strip()
        active = request.POST.get('active') == 'on'

        if action == 'create' and name:
            LabTest.objects.create(
                name=name, category=category, price=price,
                normal_range=normal_range, active=True
            )
            messages.success(request, f"Lab Test '{name}' created.")
        elif action == 'update':
            test_id = request.POST.get('test_id')
            test = get_object_or_404(LabTest, id=test_id)
            test.name = name
            test.category = category
            test.price = price
            test.normal_range = normal_range
            test.active = active
            test.save()
            messages.success(request, f"Lab Test '{name}' updated.")
        elif action == 'delete':
            test_id = request.POST.get('test_id')
            test = get_object_or_404(LabTest, id=test_id)
            test.delete()
            messages.success(request, 'Lab Test deleted.')

        return redirect('admin_manage_lab_tests')

    categories = tests.values_list('category', flat=True).distinct()
    return render(request, 'hospitalapp/admin/manage_lab_tests.html', {
        'tests': tests,
        'categories': categories,
    })


@role_required('admin')
def admin_manage_lab_parameters(request, test_id):
    test = get_object_or_404(LabTest, id=test_id)
    parameters = test.parameters.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        name = request.POST.get('name', '').strip()
        unit = request.POST.get('unit', '').strip()
        reference_range = request.POST.get('reference_range', '').strip()
        min_value = request.POST.get('min_value') or None
        max_value = request.POST.get('max_value') or None
        critical_min = request.POST.get('critical_min') or None
        critical_max = request.POST.get('critical_max') or None

        if action == 'create' and name:
            LabTestParameter.objects.create(
                test=test, name=name, unit=unit,
                reference_range=reference_range,
                min_value=min_value, max_value=max_value,
                critical_min=critical_min, critical_max=critical_max,
            )
            messages.success(request, f"Parameter '{name}' added.")
        elif action == 'update':
            param_id = request.POST.get('param_id')
            param = get_object_or_404(LabTestParameter, id=param_id, test=test)
            param.name = name
            param.unit = unit
            param.reference_range = reference_range
            param.min_value = min_value
            param.max_value = max_value
            param.critical_min = critical_min
            param.critical_max = critical_max
            param.save()
            messages.success(request, f"Parameter '{name}' updated.")
        elif action == 'delete':
            param_id = request.POST.get('param_id')
            param = get_object_or_404(LabTestParameter, id=param_id, test=test)
            param.delete()
            messages.success(request, 'Parameter deleted.')

        return redirect('admin_manage_lab_parameters', test_id=test_id)

    return render(request, 'hospitalapp/admin/manage_lab_parameters.html', {
        'test': test,
        'parameters': parameters,
    })


@role_required('admin')
def admin_manage_radiology_tests(request):
    tests = RadiologyTest.objects.all().order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', 0)
        active = request.POST.get('active') == 'on'

        if action == 'create' and name:
            RadiologyTest.objects.create(name=name, description=description, price=price, active=True)
            messages.success(request, f"Radiology Test '{name}' created.")
        elif action == 'update':
            test_id = request.POST.get('test_id')
            test = get_object_or_404(RadiologyTest, id=test_id)
            test.name = name
            test.description = description
            test.price = price
            test.active = active
            test.save()
            messages.success(request, f"Radiology Test '{name}' updated.")
        elif action == 'delete':
            test_id = request.POST.get('test_id')
            test = get_object_or_404(RadiologyTest, id=test_id)
            test.delete()
            messages.success(request, 'Radiology Test deleted.')

        return redirect('admin_manage_radiology_tests')

    return render(request, 'hospitalapp/admin/manage_radiology_tests.html', {
        'tests': tests,
    })


# ============================================================
# DOCTOR NOTIFICATION VIEWS
# ============================================================

@role_required('doctor')
def doctor_notifications(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    notifications = doctor.notifications.all().order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'hospitalapp/doctor/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@role_required('doctor')
def mark_notification_read(request, notification_id):
    doctor = get_object_or_404(Doctor, user=request.user)
    notification = get_object_or_404(DoctorNotification, id=notification_id, doctor=doctor)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('doctor_notifications')


# ============================================================
# NURSING STATION VIEWS
# ============================================================
from hospitalapp.models import (
    NursingStationRequest, NursingTaskAssignment, NurseAvailability,
    NursingNotification, NursingMessage, NursingAuditLog
)
from hospitalapp.forms import NursingStationRequestForm, NursingMessageForm

@role_required('nursing_station')
def nursing_station_dashboard(request):
    # Ensure all nurses have an availability record
    for n in Nurse.objects.all():
        NurseAvailability.objects.get_or_create(nurse=n)

    today = timezone.now().date()
    
    # 1. Requests grouped by patient type
    op_requests = NursingStationRequest.objects.filter(patient_type='OP').order_by('-created_at')
    ip_requests = NursingStationRequest.objects.filter(patient_type='IP').order_by('-created_at')
    icu_requests = NursingStationRequest.objects.filter(patient_type='ICU').order_by('-created_at')
    emergency_requests = NursingStationRequest.objects.filter(patient_type='Emergency').order_by('-created_at')
    
    # 2. Emergency Alerts (Unresolved and resolved)
    emergency_alerts = EmergencyAlert.objects.all().order_by('-created_at')
    active_alerts = emergency_alerts.filter(is_resolved=False)
    
    # 3. Nurse Availability Board
    nurses_avail = NurseAvailability.objects.all().select_related('nurse')
    available_nurses = nurses_avail.filter(status='Available')
    busy_nurses = nurses_avail.filter(status='Busy')
    emergency_duty_nurses = nurses_avail.filter(status='Emergency Duty')
    off_duty_nurses = nurses_avail.filter(status='Off Duty')
    
    # 4. Global Counts / Live Stats
    active_req_count = NursingStationRequest.objects.exclude(status__in=['Completed', 'Rejected']).count()
    emergency_req_count = active_alerts.count()
    icu_alerts_count = active_alerts.filter(alert_type='Critical Patient').count()
    pending_procedures = InvestigationSuggestion.objects.filter(status='Suggested').count()
    pending_meds = MedicationScheduleEntry.objects.filter(status='Pending').count()
    
    # 5. Active Task Assignments Queue
    active_assignments = NursingTaskAssignment.objects.exclude(status__in=['Completed', 'Rejected']).order_by('-assigned_at')
    
    # 6. Notifications for Nursing Station role
    notifications = NursingNotification.objects.filter(receiver=request.user).order_by('-created_at')[:10]

    # Handle Post Actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Action: Assign Nurse to a request
        if action == 'assign_nurse':
            req_id = request.POST.get('request_id')
            nurse_id = request.POST.get('nurse_id')
            notes = request.POST.get('notes', '')
            
            n_req = get_object_or_404(NursingStationRequest, id=req_id)
            nurse_obj = get_object_or_404(Nurse, nurse_id=nurse_id)
            
            # Check if task already assigned
            assignment, created = NursingTaskAssignment.objects.get_or_create(
                request=n_req,
                nurse=nurse_obj,
                defaults={'status': 'Assigned', 'notes': notes}
            )
            if not created:
                assignment.status = 'Assigned'
                assignment.notes = notes
                assignment.save()
                
            n_req.status = 'Assigned'
            n_req.save()
            
            # Update availability status
            avail = NurseAvailability.objects.get(nurse=nurse_obj)
            avail.status = 'Busy'
            avail.current_assignment = f"Request #{n_req.id} ({n_req.request_type})"
            avail.save()
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Assign Nurse",
                performed_by=request.user,
                details=f"Assigned Nurse {nurse_obj.name} to Request #{n_req.id} ({n_req.request_type})"
            )
            
            # Notify Nurse
            if nurse_obj.user:
                patient_name = n_req.patient.name if n_req.patient else 'General Support'
                NursingNotification.objects.create(
                    sender=request.user,
                    receiver=nurse_obj.user,
                    title="New Task Assignment",
                    message=f"You have been assigned to task: {n_req.request_type} for patient {patient_name}."
                )
                
            messages.success(request, f"Assigned nurse {nurse_obj.name} to request successfully.")
            return redirect('nursing_station_dashboard')
            
        # Action: Reassign Nurse
        elif action == 'reassign_nurse':
            assignment_id = request.POST.get('assignment_id')
            new_nurse_id = request.POST.get('new_nurse_id')
            notes = request.POST.get('notes', '')
            
            assignment = get_object_or_404(NursingTaskAssignment, id=assignment_id)
            new_nurse = get_object_or_404(Nurse, nurse_id=new_nurse_id)
            
            # Free old nurse
            old_nurse = assignment.nurse
            old_avail = NurseAvailability.objects.get(nurse=old_nurse)
            old_avail.status = 'Available'
            old_avail.current_assignment = None
            old_avail.save()
            
            # Notify old nurse
            if old_nurse.user:
                NursingNotification.objects.create(
                    sender=request.user,
                    receiver=old_nurse.user,
                    title="Task Revoked",
                    message=f"Your assignment to task #{assignment.request.id} has been revoked."
                )
            
            # Update Assignment
            assignment.nurse = new_nurse
            assignment.status = 'Assigned'
            assignment.notes = notes
            assignment.save()
            
            # Update new nurse availability
            new_avail = NurseAvailability.objects.get(nurse=new_nurse)
            new_avail.status = 'Busy'
            new_avail.current_assignment = f"Request #{assignment.request.id} ({assignment.request.request_type})"
            new_avail.save()
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Reassign Nurse",
                performed_by=request.user,
                details=f"Reassigned Request #{assignment.request.id} from {old_nurse.name} to {new_nurse.name}"
            )
            
            # Notify new nurse
            if new_nurse.user:
                patient_name = assignment.request.patient.name if assignment.request.patient else 'General Support'
                NursingNotification.objects.create(
                    sender=request.user,
                    receiver=new_nurse.user,
                    title="New Task Assignment (Reassigned)",
                    message=f"You have been assigned to task: {assignment.request.request_type} for patient {patient_name}."
                )
                
            messages.success(request, f"Reassigned request to {new_nurse.name} successfully.")
            return redirect('nursing_station_dashboard')
            
        # Action: Cancel Request
        elif action == 'cancel_request':
            req_id = request.POST.get('request_id')
            n_req = get_object_or_404(NursingStationRequest, id=req_id)
            n_req.status = 'Rejected'
            n_req.save()
            
            # Free assigned nurses
            for assign in n_req.assignments.exclude(status__in=['Completed', 'Rejected']):
                assign.status = 'Rejected'
                assign.save()
                
                avail = NurseAvailability.objects.get(nurse=assign.nurse)
                avail.status = 'Available'
                avail.current_assignment = None
                avail.save()
                
            # Audit Log
            NursingAuditLog.objects.create(
                action="Cancel Request",
                performed_by=request.user,
                details=f"Cancelled Request #{n_req.id} ({n_req.request_type})"
            )
            
            messages.warning(request, f"Request #{n_req.id} has been cancelled.")
            return redirect('nursing_station_dashboard')
            
        # Action: Escalate / Create Emergency Alert (Code Blue, Trauma, etc.)
        elif action == 'escalate_emergency':
            alert_type = request.POST.get('alert_type', 'Code Blue')
            alert_message = request.POST.get('alert_message', '')
            admission_id = request.POST.get('admission_id')
            
            admission = None
            if admission_id:
                admission = get_object_or_404(Admission, admission_id=admission_id)
                
            alert = EmergencyAlert.objects.create(
                admission=admission,
                alert_type=alert_type,
                alert_message=alert_message,
                is_resolved=False
            )
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Escalate Emergency Alert",
                performed_by=request.user,
                details=f"Triggered Emergency Alert: {alert_type} - {alert_message}"
            )
            
            # Broadcast to all available nurses
            for n_avail in available_nurses:
                if n_avail.nurse.user:
                    NursingNotification.objects.create(
                        sender=request.user,
                        receiver=n_avail.nurse.user,
                        title=f"ALERT: {alert_type}",
                        message=alert_message
                    )
            
            messages.error(request, f"CRITICAL ALERT: {alert_type} broadcasted successfully!")
            return redirect('nursing_station_dashboard')
            
        # Action: Allocate Nurse to Emergency Alert
        elif action == 'allocate_emergency_nurse':
            alert_id = request.POST.get('alert_id')
            nurse_id = request.POST.get('nurse_id')
            
            alert = get_object_or_404(EmergencyAlert, id=alert_id)
            nurse_obj = get_object_or_404(Nurse, nurse_id=nurse_id)
            
            alert.assigned_nurse = nurse_obj
            alert.save()
            
            # Update availability to Emergency Duty
            avail = NurseAvailability.objects.get(nurse=nurse_obj)
            avail.status = 'Emergency Duty'
            avail.current_assignment = f"EMERGENCY: {alert.alert_type} (#{alert.id})"
            avail.save()
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Allocate Emergency Nurse",
                performed_by=request.user,
                details=f"Allocated Nurse {nurse_obj.name} to Emergency Alert #{alert.id} ({alert.alert_type})"
            )
            
            # Notify Nurse
            if nurse_obj.user:
                NursingNotification.objects.create(
                    sender=request.user,
                    receiver=nurse_obj.user,
                    title="EMERGENCY ASSIGNMENT",
                    message=f"Report immediately to emergency alert #{alert.id}: {alert.alert_type}. Message: {alert.alert_message}"
                )
                
            messages.success(request, f"Allocated nurse {nurse_obj.name} to Emergency Alert #{alert.id}.")
            return redirect('nursing_station_dashboard')
            
        # Action: Resolve Emergency Alert
        elif action == 'resolve_emergency':
            alert_id = request.POST.get('alert_id')
            emergency_log = request.POST.get('emergency_log', '')
            
            alert = get_object_or_404(EmergencyAlert, id=alert_id)
            alert.is_resolved = True
            alert.resolved_at = timezone.now()
            alert.emergency_log = emergency_log
            
            # Calculate response time in seconds
            dt = alert.resolved_at - alert.created_at
            alert.response_time = int(dt.total_seconds())
            alert.save()
            
            # Free up nurse
            if alert.assigned_nurse:
                avail = NurseAvailability.objects.get(nurse=alert.assigned_nurse)
                avail.status = 'Available'
                avail.current_assignment = None
                avail.save()
                
            # Audit Log
            NursingAuditLog.objects.create(
                action="Resolve Emergency Alert",
                performed_by=request.user,
                details=f"Resolved Emergency Alert #{alert.id} ({alert.alert_type}) in {alert.response_time} seconds."
            )
            
            messages.success(request, f"Emergency alert #{alert.id} resolved successfully. Response time: {alert.response_time} seconds.")
            return redirect('nursing_station_dashboard')

    # Admissions for dropdown in escalate emergency alert
    admissions = Admission.objects.filter(status__in=['Admitted', 'Ready For Discharge']).select_related('patient')

    return render(request, 'hospitalapp/nursing_station/dashboard.html', {
        'op_requests': op_requests,
        'ip_requests': ip_requests,
        'icu_requests': icu_requests,
        'emergency_requests': emergency_requests,
        'emergency_alerts': emergency_alerts,
        'active_alerts': active_alerts,
        'nurses_avail': nurses_avail,
        'available_nurses': available_nurses,
        'busy_nurses': busy_nurses,
        'emergency_duty_nurses': emergency_duty_nurses,
        'off_duty_nurses': off_duty_nurses,
        'active_req_count': active_req_count,
        'emergency_req_count': emergency_req_count,
        'icu_alerts_count': icu_alerts_count,
        'pending_procedures': pending_procedures,
        'pending_meds': pending_meds,
        'active_assignments': active_assignments,
        'notifications': notifications,
        'admissions': admissions,
        'today': today,
    })


# ============================================================
# DOCTOR NURSING ASSISTANCE REQUEST VIEW
# ============================================================
@role_required('doctor')
def doctor_nursing_requests(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    my_requests = NursingStationRequest.objects.filter(doctor=doctor).order_by('-created_at')
    
    if request.method == 'POST':
        form = NursingStationRequestForm(request.POST)
        if form.is_valid():
            n_req = form.save(commit=False)
            n_req.doctor = doctor
            n_req.status = 'Pending'
            n_req.save()
            
            # Audit Log
            patient_name = n_req.patient.name if n_req.patient else 'General Support'
            NursingAuditLog.objects.create(
                action="Create Request",
                performed_by=request.user,
                details=f"Dr. {doctor.name} created Nursing Request #{n_req.id} ({n_req.request_type}) for patient {patient_name}"
            )
            
            # Send Notification to Nursing Station Users
            ns_users = User.objects.filter(role='nursing_station')
            for u in ns_users:
                NursingNotification.objects.create(
                    sender=request.user,
                    receiver=u,
                    title="New Assistance Request",
                    message=f"Dr. {doctor.name} requested {n_req.request_type} for patient {patient_name} ({n_req.patient_type})."
                )
                
            messages.success(request, "Assistance request logged successfully at the Central Nursing Station.")
            return redirect('doctor_nursing_requests')
    else:
        form = NursingStationRequestForm()
        
    return render(request, 'hospitalapp/doctor/nursing_requests.html', {
        'form': form,
        'requests': my_requests,
    })


# ============================================================
# STAFF NURSE TASK BOARD VIEW
# ============================================================
@role_required('nurse')
def nurse_tasks(request):
    nurse = get_object_or_404(Nurse, user=request.user)
    
    # Roster status update
    NurseAvailability.objects.get_or_create(nurse=nurse)
    
    my_assignments = NursingTaskAssignment.objects.filter(nurse=nurse).order_by('-assigned_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        assignment_id = request.POST.get('assignment_id')
        assignment = get_object_or_404(NursingTaskAssignment, id=assignment_id, nurse=nurse)
        
        # Action: Accept Task
        if action == 'accept':
            assignment.status = 'Accepted'
            assignment.accepted_at = timezone.now()
            assignment.save()
            
            assignment.request.status = 'Accepted'
            assignment.request.save()
            
            # Update Availability
            avail = NurseAvailability.objects.get(nurse=nurse)
            avail.status = 'Busy'
            avail.save()
            
            # Notify Doctor & Nursing Station
            NursingNotification.objects.create(
                sender=request.user,
                receiver=assignment.request.doctor.user,
                title="Task Accepted",
                message=f"Nurse {nurse.name} has accepted your request for {assignment.request.request_type}."
            )
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Accept Task",
                performed_by=request.user,
                details=f"Nurse {nurse.name} accepted Task Assignment #{assignment.id}"
            )
            messages.info(request, "Task accepted.")
            
        # Action: Start Task (In Progress)
        elif action == 'start':
            assignment.status = 'In Progress'
            assignment.save()
            
            assignment.request.status = 'In Progress'
            assignment.request.save()
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Start Task",
                performed_by=request.user,
                details=f"Nurse {nurse.name} started Task Assignment #{assignment.id}"
            )
            messages.info(request, "Task in progress.")
            
        # Action: Complete Task
        elif action == 'complete':
            notes = request.POST.get('completion_notes', '')
            assignment.status = 'Completed'
            assignment.completed_at = timezone.now()
            assignment.notes = notes
            
            # Compute duration in minutes
            dt = assignment.completed_at - assignment.assigned_at
            assignment.duration = max(1, int(dt.total_seconds() / 60))
            assignment.save()
            
            assignment.request.status = 'Completed'
            assignment.request.notes = f"Completed by {nurse.name}. Notes: {notes}"
            assignment.request.save()
            
            # Reset Availability
            avail = NurseAvailability.objects.get(nurse=nurse)
            avail.status = 'Available'
            avail.current_assignment = None
            avail.save()
            
            # Notify Doctor & Nursing Station
            patient_name = assignment.request.patient.name if assignment.request.patient else 'General Support'
            NursingNotification.objects.create(
                sender=request.user,
                receiver=assignment.request.doctor.user,
                title="Task Completed Notification",
                message=f"Nurse {nurse.name} completed your request for {assignment.request.request_type} (Patient: {patient_name})."
            )
            
            # Audit Log
            NursingAuditLog.objects.create(
                action="Complete Task",
                performed_by=request.user,
                details=f"Nurse {nurse.name} completed Task Assignment #{assignment.id} in {assignment.duration} minutes."
            )
            messages.success(request, "Task marked as Completed successfully.")
            
        # Action: Reject Task
        elif action == 'reject':
            reason = request.POST.get('reject_reason', '')
            assignment.status = 'Rejected'
            assignment.rejected_at = timezone.now()
            assignment.notes = f"Rejected: {reason}"
            assignment.save()
            
            assignment.request.status = 'Pending'  # Put back to Pending to reassign
            assignment.request.save()
            
            # Reset Availability
            avail = NurseAvailability.objects.get(nurse=nurse)
            avail.status = 'Available'
            avail.current_assignment = None
            avail.save()
            
            # Notify Nursing Station
            ns_users = User.objects.filter(role='nursing_station')
            for u in ns_users:
                NursingNotification.objects.create(
                    sender=request.user,
                    receiver=u,
                    title="Task Rejected",
                    message=f"Nurse {nurse.name} rejected Task Assignment #{assignment.id}. Reason: {reason}"
                )
                
            # Audit Log
            NursingAuditLog.objects.create(
                action="Reject Task",
                performed_by=request.user,
                details=f"Nurse {nurse.name} rejected Task Assignment #{assignment.id}. Reason: {reason}"
            )
            messages.warning(request, "Task rejected. Nursing Station has been notified.")
            
        return redirect('nurse_tasks')
        
    return render(request, 'hospitalapp/nurse/nursing_station_tasks.html', {
        'assignments': my_assignments,
    })


# ============================================================
# THREE-WAY COMMUNICATION / CHAT WINDOW
# ============================================================
@login_required
def nursing_station_messages(request):
    if request.user.role not in ['admin', 'doctor', 'nurse', 'nursing_station']:
        return HttpResponseForbidden("Access Denied.")
        
    # Get all messages
    if request.user.role == 'nursing_station' or request.user.role == 'admin':
        messages_list = NursingMessage.objects.all().order_by('-created_at')
    else:
        # Doctors and Nurses see messages sent by them or received by them
        messages_list = NursingMessage.objects.filter(
            models.Q(sender=request.user) | models.Q(receiver=request.user)
        ).order_by('-created_at')

    if request.method == 'POST':
        form = NursingMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            
            # Notify Receiver
            NursingNotification.objects.create(
                sender=request.user,
                receiver=msg.receiver,
                title=f"New Message ({msg.category})",
                message=f"You received a message from {request.user.username}: {msg.message[:50]}..."
            )
            
            messages.success(request, "Message sent successfully.")
            return redirect('nursing_station_messages')
    else:
        form = NursingMessageForm()
        
    return render(request, 'hospitalapp/nursing_station/messages.html', {
        'messages_list': messages_list,
        'form': form,
    })


# ============================================================
# PERFORMANCE REPORTS & ANALYTICS VIEWS
# ============================================================
@login_required
def nursing_station_reports(request):
    if request.user.role not in ['admin', 'nursing_station'] and not (request.user.role == 'nurse' and getattr(request.user, 'nurse_set', None) and request.user.nurse_set.first().is_head_nurse):
        # Allow admin, nursing station, or Head Nurse
        # Let's check head nurse status
        is_allowed = False
        if request.user.is_superuser:
            is_allowed = True
        elif request.user.role == 'nurse':
            nurse_obj = Nurse.objects.filter(user=request.user).first()
            if nurse_obj and nurse_obj.is_head_nurse:
                is_allowed = True
        if not is_allowed:
            return HttpResponseForbidden("Access restricted to Supervisor roles.")

    # 1. Total Completed Tasks
    completed_assignments = NursingTaskAssignment.objects.filter(status='Completed')
    total_completed = completed_assignments.count()
    
    # 2. Daily Tasks Completed
    today = timezone.now().date()
    from datetime import datetime, time
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    completed_today = completed_assignments.filter(completed_at__range=(start_dt, end_dt)).count()
    
    # 3. Emergency Calls resolved
    resolved_emergencies = EmergencyAlert.objects.filter(is_resolved=True)
    total_emergencies = resolved_emergencies.count()
    
    # 4. Average response times in minutes (task duration)
    avg_task_duration = completed_assignments.aggregate(models.Avg('duration'))['duration__avg'] or 0
    avg_emergency_response = resolved_emergencies.aggregate(models.Avg('response_time'))['response_time__avg'] or 0
    # convert emergency response to seconds/minutes
    avg_emergency_response_min = round(avg_emergency_response / 60, 2)
    
    # 5. Nurse Workload / Utilization (Count of completed tasks by nurse)
    nurse_workload = []
    for n in Nurse.objects.all():
        count = NursingTaskAssignment.objects.filter(nurse=n, status='Completed').count()
        nurse_workload.append({
            'nurse': n,
            'completed_count': count
        })
        
    # Sort by workload descending
    nurse_workload = sorted(nurse_workload, key=lambda x: x['completed_count'], reverse=True)
    
    # 6. Audit logs
    audit_logs = NursingAuditLog.objects.all().order_by('-timestamp')[:50]

    return render(request, 'hospitalapp/nursing_station/reports.html', {
        'total_completed': total_completed,
        'completed_today': completed_today,
        'total_emergencies': total_emergencies,
        'avg_task_duration': round(avg_task_duration, 1),
        'avg_emergency_response_min': avg_emergency_response_min,
        'nurse_workload': nurse_workload,
        'audit_logs': audit_logs,
    })


# ============================================================
# CASUALTY / EMERGENCY ZONE VIEWS
# ============================================================

from hospitalapp.forms import EmergencyTriageForm, EmergencyTreatmentForm

@role_required('nurse', 'nursing_station', 'admin')
def emergency_triage_dashboard(request):
    waiting_cases = Casuality.objects.filter(status='Pending').order_by('-created_at')
    active_cases = Casuality.objects.exclude(status__in=['Pending', 'Discharged', 'Admitted', 'ICU Transfer', 'OT Transfer', 'Stabilized', 'Referred']).order_by('-created_at')
    
    return render(request, 'hospitalapp/nurse/triage_dashboard.html', {
        'waiting_cases': waiting_cases,
        'active_cases': active_cases
    })


@role_required('nurse', 'nursing_station', 'admin')
def triage_patient(request, casualty_id):
    casualty = get_object_or_404(Casuality, id=casualty_id)
    nurse = Nurse.objects.filter(user=request.user).first()
    if not nurse:
        nurse = Nurse.objects.first()
        if not nurse:
            nurse = Nurse.objects.create(
                user=request.user,
                name=request.user.username,
                phone='123456',
                email='nurse@hospital.com',
                qualification='BSC Nursing',
                assigned_ward='General Ward'
            )
            
    if request.method == 'POST':
        form = EmergencyTriageForm(request.POST)
        if form.is_valid():
            triage_obj = form.save(commit=False)
            triage_obj.casualty_case = casualty
            triage_obj.patient = casualty.patient
            triage_obj.triage_nurse = nurse
            
            # Vitals zone rules
            gcs = form.cleaned_data['gcs_score']
            spo2 = form.cleaned_data['oxygen_level']
            bp_systolic = form.cleaned_data['bp_systolic']
            temp = float(form.cleaned_data['temperature'])
            
            if gcs <= 8 or spo2 < 90 or bp_systolic < 90:
                zone_name, priority, response_time = 'RED', 'Critical', 0
            elif gcs <= 12 or spo2 <= 94:
                zone_name, priority, response_time = 'ORANGE', 'Very Urgent', 15
            elif gcs <= 14 or temp > 102.0:
                zone_name, priority, response_time = 'YELLOW', 'Urgent', 60
            else:
                zone_name, priority, response_time = 'GREEN', 'Non-Urgent', 120
                
            zone = get_object_or_404(EmergencyZone, zone_name=zone_name)
            triage_obj.triage_zone = zone
            triage_obj.priority_level = priority
            triage_obj.save()
            
            # Bed Assignment
            bed = EmergencyBed.objects.filter(zone=zone, status='Available').first()
            
            casualty.triage = triage_obj
            casualty.zone = zone
            casualty.arrival_time = timezone.now()
            
            if bed:
                bed.status = 'Occupied'
                bed.save()
                casualty.assigned_bed = bed
                casualty.status = 'Under Emergency Care'
                messages.success(request, f"Triage complete. Patient assigned to {zone_name} Zone, Bed {bed.bed_number}.")
            else:
                casualty.status = 'Triage Completed'
                messages.warning(request, f"Triage complete. Patient assigned to {zone_name} Zone, but NO beds are currently available. Added to waiting list.")
                
            casualty.save()
            return redirect('emergency_triage_dashboard')
    else:
        form = EmergencyTriageForm()
        
    return render(request, 'hospitalapp/receptionist/triage.html', {
        'form': form,
        'casualty': casualty
    })


@role_required('doctor', 'admin')
def emergency_doctor_workspace(request):
    active_cases = Casuality.objects.exclude(
        status__in=['Pending', 'Discharged', 'Admitted', 'ICU Transfer', 'OT Transfer', 'Stabilized', 'Referred']
    ).select_related('patient', 'triage', 'zone', 'assigned_bed')

    if request.user.role == 'doctor':
        doctor = Doctor.objects.filter(user=request.user).first()
        if doctor:
            from django.db.models import Q
            active_cases = active_cases.filter(
                Q(doctor=doctor) | Q(referrals__referred_doctor=doctor, referrals__status='Accepted')
            ).distinct()
        else:
            active_cases = active_cases.none()

    active_cases = active_cases.order_by('zone__priority_level', '-created_at')
    
    # Group by Zone for easier dashboard display
    red_cases = active_cases.filter(zone__zone_name='RED')
    orange_cases = active_cases.filter(zone__zone_name='ORANGE')
    yellow_cases = active_cases.filter(zone__zone_name='YELLOW')
    green_cases = active_cases.filter(zone__zone_name='GREEN')
    
    # Available beds count
    beds_count = EmergencyBed.objects.filter(status='Available').count()
    
    # Specialist doctors for referral
    specialist_doctors = Doctor.objects.exclude(user=request.user).order_by('specialization', 'name')
    
    return render(request, 'hospitalapp/doctor/emergency_workspace.html', {
        'active_cases': active_cases,
        'red_cases': red_cases,
        'orange_cases': orange_cases,
        'yellow_cases': yellow_cases,
        'green_cases': green_cases,
        'available_beds_count': beds_count,
        'specialist_doctors': specialist_doctors,
    })


@role_required('doctor', 'admin')
def emergency_doctor_evaluate(request, casualty_id):
    casualty = get_object_or_404(Casuality, id=casualty_id)
    doctor = Doctor.objects.filter(user=request.user).first()
    if not doctor:
        doctor = Doctor.objects.first()
        if not doctor:
            doctor = Doctor.objects.create(
                user=request.user,
                name=request.user.username,
                specialization='Emergency Medicine',
                phone='123',
                email='doc@h.com',
                availability='Emergency (24/7)'
            )
            
    treatment_record = EmergencyTreatmentRecord.objects.filter(casualty_case=casualty).first()
    
    if request.method == 'POST':
        form = EmergencyTreatmentForm(request.POST, instance=treatment_record)
        if form.is_valid():
            record = form.save(commit=False)
            record.casualty_case = casualty
            record.doctor = doctor
            record.treatment_completed = timezone.now()
            record.save()
            
            casualty.status = 'Under Emergency Care'
            casualty.save()
            
            messages.success(request, "Evaluation and treatment notes saved successfully.")
            return redirect('emergency_doctor_workspace')
    else:
        form = EmergencyTreatmentForm(instance=treatment_record)
        
    return render(request, 'hospitalapp/doctor/emergency_evaluate.html', {
        'form': form,
        'casualty': casualty,
        'treatment_record': treatment_record
    })


@role_required('doctor', 'admin')
def emergency_create_lab_order(request, casualty_id):
    from django.db import transaction
    casualty = get_object_or_404(Casuality, id=casualty_id)
    doctor = Doctor.objects.filter(user=request.user).first() or Doctor.objects.first()
    
    if request.method == 'POST':
        form = LabOrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                tests = form.cleaned_data['tests']
                if tests:
                    order = LabOrder.objects.create(
                        patient=casualty.patient,
                        ordered_by=doctor,
                        clinical_notes=form.cleaned_data['clinical_notes'],
                        urgency='STAT',
                        created_by=request.user
                    )
                    total_price = Decimal('0.00')
                    for test in tests:
                        LabOrderItem.objects.create(order=order, test=test)
                        total_price += test.price
                    
                    Bill.objects.create(
                        patient=casualty.patient,
                        total_amount=total_price,
                        bill_type='laboratory',
                        payment_status='Pending',
                        lab_order=order
                    )
            messages.success(request, 'STAT Laboratory order created successfully.')
            return redirect('emergency_doctor_workspace')
    else:
        form = LabOrderForm()
        
    return render(request, 'hospitalapp/doctor/emergency_order_lab.html', {
        'form': form,
        'casualty': casualty
    })


@role_required('doctor', 'admin')
def emergency_create_radiology_order(request, casualty_id):
    from django.db import transaction
    casualty = get_object_or_404(Casuality, id=casualty_id)
    doctor = Doctor.objects.filter(user=request.user).first() or Doctor.objects.first()
    
    if request.method == 'POST':
        form = RadiologyOrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                tests = form.cleaned_data['tests']
                if tests:
                    order = RadiologyOrder.objects.create(
                        patient=casualty.patient,
                        ordered_by=doctor,
                        clinical_notes=form.cleaned_data['clinical_notes'],
                        urgency='STAT',
                        created_by=request.user
                    )
                    total_price = Decimal('0.00')
                    for test in tests:
                        RadiologyOrderItem.objects.create(order=order, test=test)
                        total_price += test.price
                    
                    Bill.objects.create(
                        patient=casualty.patient,
                        total_amount=total_price,
                        bill_type='radiology',
                        payment_status='Pending',
                        radiology_order=order
                    )
            messages.success(request, 'STAT Radiology order created successfully.')
            return redirect('emergency_doctor_workspace')
    else:
        form = RadiologyOrderForm()
        
    return render(request, 'hospitalapp/doctor/emergency_order_radiology.html', {
        'form': form,
        'casualty': casualty
    })


@role_required('doctor', 'admin')
def emergency_disposition(request, casualty_id, disposition_type):
    casualty = get_object_or_404(Casuality, id=casualty_id)
    bed = casualty.assigned_bed
    
    if disposition_type == 'icu':
        Admission.objects.create(
            patient=casualty.patient,
            doctor=casualty.doctor,
            ward_type='ICU',
            status='Admitted',
            reason=f"Emergency ICU Transfer from Casualty Zone: {casualty.zone.zone_name if casualty.zone else 'Unknown'}"
        )
        casualty.status = 'ICU Transfer'
    elif disposition_type == 'ot':
        casualty.status = 'OT Transfer'
    elif disposition_type == 'admission':
        Admission.objects.create(
            patient=casualty.patient,
            doctor=casualty.doctor,
            ward_type='General Ward',
            status='Admitted',
            reason=f"Emergency Ward Admission from Casualty Zone: {casualty.zone.zone_name if casualty.zone else 'Unknown'}"
        )
        casualty.status = 'Admitted'
    elif disposition_type == 'discharge':
        casualty.status = 'Discharged'
    else:
        messages.error(request, "Invalid disposition type.")
        return redirect('emergency_doctor_workspace')
        
    if bed:
        bed.status = 'Available'
        bed.save()
        casualty.assigned_bed = None
        
    casualty.save()
    messages.success(request, f"Patient successfully transferred/discharged: {disposition_type.upper()}")
    return redirect('emergency_doctor_workspace')


@role_required('admin', 'nursing_station', 'doctor')
def emergency_reports(request):
    from django.utils.timezone import now
    from datetime import datetime, time
    today = now().date()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    
    total_today = Casuality.objects.filter(created_at__range=(start_dt, end_dt)).count()
    
    red_count = Casuality.objects.filter(zone__zone_name='RED', created_at__range=(start_dt, end_dt)).count()
    orange_count = Casuality.objects.filter(zone__zone_name='ORANGE', created_at__range=(start_dt, end_dt)).count()
    yellow_count = Casuality.objects.filter(zone__zone_name='YELLOW', created_at__range=(start_dt, end_dt)).count()
    green_count = Casuality.objects.filter(zone__zone_name='GREEN', created_at__range=(start_dt, end_dt)).count()
    
    admitted_count = Casuality.objects.filter(status='Admitted', created_at__range=(start_dt, end_dt)).count()
    icu_count = Casuality.objects.filter(status='ICU Transfer', created_at__range=(start_dt, end_dt)).count()
    ot_count = Casuality.objects.filter(status='OT Transfer', created_at__range=(start_dt, end_dt)).count()
    discharged_count = Casuality.objects.filter(status='Discharged', created_at__range=(start_dt, end_dt)).count()
    
    admission_conversion_rate = 0
    if total_today > 0:
        admission_conversion_rate = round(((admitted_count + icu_count + ot_count) / total_today) * 100, 1)
        
    treatment_records = EmergencyTreatmentRecord.objects.filter(treatment_completed__isnull=False, treatment_started__range=(start_dt, end_dt))
    total_time = 0
    count = 0
    for rec in treatment_records:
        diff = rec.treatment_completed - rec.treatment_started
        total_time += diff.total_seconds()
        count += 1
    avg_treatment_time_min = round((total_time / 60) / count, 1) if count > 0 else 0

    return render(request, 'hospitalapp/admin/emergency_reports.html', {
        'total_today': total_today,
        'red_count': red_count,
        'orange_count': orange_count,
        'yellow_count': yellow_count,
        'green_count': green_count,
        'admitted_count': admitted_count,
        'icu_count': icu_count,
        'ot_count': ot_count,
        'discharged_count': discharged_count,
        'admission_conversion_rate': admission_conversion_rate,
        'avg_treatment_time_min': avg_treatment_time_min,
    })


@csrf_exempt
def trigger_emergency_broadcast_alert(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            alert_type = data.get('alert_type', 'Critical Patient')
            message = data.get('message', 'Emergency team requested immediately!')
            
            alert = EmergencyAlert.objects.create(
                alert_type=alert_type,
                message=message,
                is_resolved=False
            )
            return JsonResponse({'status': 'success', 'alert_id': alert.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@role_required('nursing_superintendent')
def nursing_superintendent_dashboard(request):
    # Auto-create availability records if missing
    for n in Nurse.objects.all():
        NurseAvailability.objects.get_or_create(nurse=n)

    today = timezone.now().date()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_head_nurse':
            nurse_id = request.POST.get('nurse_id')
            target_nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            target_nurse.is_head_nurse = not target_nurse.is_head_nurse
            target_nurse.save()
            status_str = "promoted to Head Nurse" if target_nurse.is_head_nurse else "demoted to regular Nurse"
            messages.success(request, f"{target_nurse.name} was successfully {status_str}.")
            return redirect('nursing_superintendent_dashboard')

        elif action == 'assign_ward':
            nurse_id = request.POST.get('nurse_id')
            ward = request.POST.get('assigned_ward')
            target_nurse = get_object_or_404(Nurse, nurse_id=nurse_id)
            target_nurse.assigned_ward = ward
            target_nurse.save()
            messages.success(request, f"Assigned {target_nurse.name} to {ward} ward.")
            return redirect('nursing_superintendent_dashboard')

        elif action == 'add_nurse':
            username = request.POST.get('username')
            email = request.POST.get('email')
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            qualification = request.POST.get('qualification')
            assigned_ward = request.POST.get('assigned_ward')
            is_head_nurse = request.POST.get('is_head_nurse') == 'on'
            password = request.POST.get('password', 'Pass1234')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password, role='nurse')
                Nurse.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    email=email,
                    qualification=qualification,
                    assigned_ward=assigned_ward,
                    is_head_nurse=is_head_nurse
                )
                messages.success(request, f"Nurse profile and account created for {name}.")
            return redirect('nursing_superintendent_dashboard')

        elif action == 'send_message':
            receiver_id = request.POST.get('receiver_id')
            message_text = request.POST.get('message')
            category = request.POST.get('category', 'Normal')

            receiver = get_object_or_404(User, user_id=receiver_id)
            NursingMessage.objects.create(
                sender=request.user,
                receiver=receiver,
                category=category,
                message=message_text
            )
            messages.success(request, f"Message sent successfully to {receiver.username}.")
            return redirect('nursing_superintendent_dashboard')

    # Get directory lists
    nurses = Nurse.objects.all().select_related('user').order_by('-is_head_nurse', 'name')
    nursing_stations = User.objects.filter(role='nursing_station')
    
    # Active doctor-initiated requests
    procedures = NursingStationRequest.objects.all().select_related('doctor', 'patient').order_by('-created_at')

    # Shifts date filter
    shift_date_str = request.GET.get('shift_date')
    if shift_date_str:
        try:
            from datetime import datetime
            shift_date = datetime.strptime(shift_date_str, '%Y-%m-%d').date()
        except Exception:
            shift_date = today
    else:
        shift_date = today

    shifts = NurseShift.objects.filter(shift_date=shift_date).select_related('nurse')

    # KPI counts
    total_nurses = nurses.count()
    head_nurses_count = nurses.filter(is_head_nurse=True).count()
    active_requests_count = procedures.exclude(status__in=['Completed', 'Rejected']).count()
    
    from hospitalapp.models import Bed
    occupied_beds = Bed.objects.filter(status='Occupied').count()
    total_beds = Bed.objects.count()

    context = {
        'nurses': nurses,
        'nursing_stations': nursing_stations,
        'procedures': procedures,
        'shifts': shifts,
        'shift_date': shift_date,
        'total_nurses': total_nurses,
        'head_nurses_count': head_nurses_count,
        'active_requests_count': active_requests_count,
        'occupied_beds': occupied_beds,
        'total_beds': total_beds,
        'ward_choices': Bed.WARD_CHOICES,
    }

    return render(request, 'hospitalapp/nursing_superintendent/dashboard.html', context)


@login_required
def inventory_dashboard(request):
    # Authorization check
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import Supplier, InventoryItem, PurchaseRequisition, PurchaseOrder, GoodsReceiptNote, StockIssue, BiomedicalAsset
    from django.db.models import Sum, F
    from decimal import Decimal

    items = InventoryItem.objects.all().order_by('name')
    purchase_orders = PurchaseOrder.objects.all().order_by('-created_at')
    stock_issues = StockIssue.objects.all().order_by('-created_at')

    # Dashboard Calculations
    total_val = sum(i.current_stock * i.purchase_price for i in items)
    total_items = items.count()
    low_stock_count = items.filter(current_stock__lte=F('reorder_level')).count()
    out_of_stock_count = items.filter(current_stock=0).count()
    pending_po_count = PurchaseRequisition.objects.filter(status='Pending').count()
    
    # Expiry mockup / calculation using Medicine model
    from hospitalapp.models import Medicine
    from datetime import timedelta
    thirty_days_later = timezone.now().date() + timedelta(days=30)
    expiring_soon_count = Medicine.objects.filter(expiry_date__lte=thirty_days_later, expiry_date__gte=timezone.now().date()).count()
    expired_count = Medicine.objects.filter(expiry_date__lt=timezone.now().date()).count()

    context = {
        'items': items,
        'stock_issues': stock_issues,
        'total_val': total_val,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
        'pending_po_count': pending_po_count,
        'active_tab': 'dashboard',
    }

    return render(request, 'hospitalapp/admin/inventory_dashboard.html', context)


@login_required
def inventory_items(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import Supplier, InventoryItem
    from django.db.models import F
    from decimal import Decimal

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_item':
            item_code = request.POST.get('item_code')
            name = request.POST.get('name')
            category = request.POST.get('category')
            uom = request.POST.get('uom', 'Units')
            purchase_price = Decimal(request.POST.get('purchase_price', '0.00'))
            selling_price = Decimal(request.POST.get('selling_price', '0.00'))
            reorder_level = int(request.POST.get('reorder_level', '10'))
            current_stock = int(request.POST.get('current_stock', '0'))
            supplier_id = request.POST.get('supplier')
            
            supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None
            
            InventoryItem.objects.create(
                item_code=item_code,
                name=name,
                category=category,
                uom=uom,
                purchase_price=purchase_price,
                selling_price=selling_price,
                reorder_level=reorder_level,
                current_stock=current_stock,
                supplier=supplier
            )
            messages.success(request, f"Item '{name}' added successfully to Item Master.")
        return redirect('inventory_items')

    items = InventoryItem.objects.all().order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    low_stock_count = items.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'items': items,
        'suppliers': suppliers,
        'low_stock_count': low_stock_count,
        'active_tab': 'items',
    }
    return render(request, 'hospitalapp/admin/inventory_items.html', context)


@login_required
def inventory_suppliers(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import Supplier, InventoryItem
    from django.db.models import F

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_supplier':
            name = request.POST.get('name')
            contact_person = request.POST.get('contact_person')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            gst_number = request.POST.get('gst_number')
            
            if Supplier.objects.filter(name__iexact=name).exists():
                messages.error(request, f"Supplier with name '{name}' already exists.")
            else:
                Supplier.objects.create(
                    name=name,
                    contact_person=contact_person,
                    phone=phone,
                    email=email,
                    gst_number=gst_number
                )
                messages.success(request, f"Supplier '{name}' registered successfully.")
        return redirect('inventory_suppliers')

    suppliers = Supplier.objects.all().order_by('name')
    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'suppliers': suppliers,
        'low_stock_count': low_stock_count,
        'active_tab': 'suppliers',
    }
    return render(request, 'hospitalapp/admin/inventory_suppliers.html', context)


@login_required
def inventory_purchase(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import Supplier, InventoryItem, PurchaseRequisition, PurchaseOrder
    from django.db.models import F

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_requisition':
            item_id = request.POST.get('item')
            quantity = int(request.POST.get('quantity', '1'))
            department = request.POST.get('department')
            
            item = get_object_or_404(InventoryItem, id=item_id)
            
            # Auto generate requisition number
            import random
            req_num = f"REQ-{random.randint(10000, 99999)}"
            
            PurchaseRequisition.objects.create(
                req_number=req_num,
                department=department,
                requested_by=request.user,
                item=item,
                quantity=quantity,
                status='Pending'
            )
            messages.success(request, f"Purchase Requisition {req_num} created.")

        elif action == 'create_po':
            supplier_id = request.POST.get('supplier')
            req_id = request.POST.get('requisition')
            expected_delivery = request.POST.get('expected_delivery')
            
            supplier = get_object_or_404(Supplier, id=supplier_id)
            req = PurchaseRequisition.objects.filter(id=req_id).first() if req_id else None
            
            import random
            po_num = f"PO-{random.randint(10000, 99999)}"
            
            PurchaseOrder.objects.create(
                po_number=po_num,
                supplier=supplier,
                requisition=req,
                expected_delivery=expected_delivery,
                requested_by=request.user,
                status='Ordered'
            )
            if req:
                req.status = 'Ordered'
                req.save()
            messages.success(request, f"Purchase Order {po_num} generated.")
        return redirect('inventory_purchase')

    items = InventoryItem.objects.all().order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    requisitions = PurchaseRequisition.objects.all().order_by('-created_at')
    purchase_orders = PurchaseOrder.objects.all().order_by('-created_at')
    low_stock_count = items.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'items': items,
        'suppliers': suppliers,
        'requisitions': requisitions,
        'purchase_orders': purchase_orders,
        'low_stock_count': low_stock_count,
        'active_tab': 'purchase',
    }
    return render(request, 'hospitalapp/admin/inventory_purchase.html', context)


@login_required
def inventory_grn(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import InventoryItem, PurchaseOrder, GoodsReceiptNote
    from django.db.models import F
    from decimal import Decimal

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_grn':
            po_id = request.POST.get('purchase_order')
            invoice_number = request.POST.get('invoice_number')
            invoice_amount = Decimal(request.POST.get('invoice_amount', '0.00'))
            
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            import random
            grn_num = f"GRN-{random.randint(10000, 99999)}"
            
            GoodsReceiptNote.objects.create(
                grn_number=grn_num,
                purchase_order=po,
                received_by=request.user,
                invoice_number=invoice_number,
                invoice_amount=invoice_amount
            )
            
            # If PO is linked to a requisition, increase stock of that item
            if po.requisition and po.requisition.item:
                item = po.requisition.item
                item.current_stock += po.requisition.quantity
                item.save()
            
            po.status = 'Completed'
            po.save()
            messages.success(request, f"Goods Receipt Note {grn_num} completed. Stock levels updated.")
        return redirect('inventory_grn')

    purchase_orders = PurchaseOrder.objects.all().order_by('-created_at')
    goods_receipt_notes = GoodsReceiptNote.objects.all().order_by('-received_date')
    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'purchase_orders': purchase_orders,
        'goods_receipt_notes': goods_receipt_notes,
        'low_stock_count': low_stock_count,
        'active_tab': 'grn',
    }
    return render(request, 'hospitalapp/admin/inventory_grn.html', context)


@login_required
def inventory_expiry(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import InventoryItem, Medicine
    from django.db.models import F
    from datetime import timedelta

    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()
    thirty_days_later = timezone.now().date() + timedelta(days=30)
    expiring_soon_count = Medicine.objects.filter(expiry_date__lte=thirty_days_later, expiry_date__gte=timezone.now().date()).count()
    expired_count = Medicine.objects.filter(expiry_date__lt=timezone.now().date()).count()

    context = {
        'low_stock_count': low_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
        'active_tab': 'expiry',
    }
    return render(request, 'hospitalapp/admin/inventory_expiry.html', context)


@login_required
def inventory_issue(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import InventoryItem, StockIssue
    from django.db.models import F

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_issue':
            item_id = request.POST.get('item')
            quantity = int(request.POST.get('quantity', '1'))
            department = request.POST.get('department')
            remarks = request.POST.get('remarks')
            
            item = get_object_or_404(InventoryItem, id=item_id)
            if item.current_stock < quantity:
                messages.error(request, f"Insufficient stock for {item.name}. Current stock: {item.current_stock}")
            else:
                import random
                issue_num = f"SLIP-{random.randint(10000, 99999)}"
                
                StockIssue.objects.create(
                    issue_number=issue_num,
                    department=department,
                    requested_by=request.user,
                    item=item,
                    quantity=quantity,
                    remarks=remarks
                )
                item.current_stock -= quantity
                item.save()
                messages.success(request, f"Stock Issue {issue_num} completed successfully.")
        return redirect('inventory_issue')

    items = InventoryItem.objects.all().order_by('name')
    stock_issues = StockIssue.objects.all().order_by('-created_at')
    low_stock_count = items.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'items': items,
        'stock_issues': stock_issues,
        'low_stock_count': low_stock_count,
        'active_tab': 'issue',
    }
    return render(request, 'hospitalapp/admin/inventory_issue.html', context)


@login_required
def inventory_biomedical(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import InventoryItem, BiomedicalAsset
    from django.db.models import F

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_asset':
            asset_id = request.POST.get('asset_id')
            name = request.POST.get('name')
            manufacturer = request.POST.get('manufacturer')
            model_number = request.POST.get('model_number')
            serial_number = request.POST.get('serial_number')
            purchase_date = request.POST.get('purchase_date') or None
            assigned_department = request.POST.get('assigned_department')
            
            BiomedicalAsset.objects.create(
                asset_id=asset_id,
                name=name,
                manufacturer=manufacturer,
                model_number=model_number,
                serial_number=serial_number,
                purchase_date=purchase_date,
                assigned_department=assigned_department
            )
            messages.success(request, f"Biomedical asset '{name}' registered.")
        return redirect('inventory_biomedical')

    biomedical_assets = BiomedicalAsset.objects.all().order_by('name')
    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'biomedical_assets': biomedical_assets,
        'low_stock_count': low_stock_count,
        'active_tab': 'biomedical',
    }
    return render(request, 'hospitalapp/admin/inventory_biomedical.html', context)


@login_required
def inventory_emergency(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import InventoryItem
    from django.db.models import F

    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'low_stock_count': low_stock_count,
        'active_tab': 'emergency',
    }
    return render(request, 'hospitalapp/admin/inventory_emergency.html', context)


@login_required
def inventory_reports(request):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import InventoryItem
    from django.db.models import F

    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'low_stock_count': low_stock_count,
        'active_tab': 'reports',
    }
    return render(request, 'hospitalapp/admin/inventory_reports.html', context)


@login_required
def update_supplier(request, pk):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to edit suppliers.")

    from hospitalapp.models import Supplier, InventoryItem
    from django.db.models import F
    
    supplier = get_object_or_404(Supplier, id=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        gst_number = request.POST.get('gst_number')
        rating = request.POST.get('rating', '5.0')
        is_active = request.POST.get('is_active') == 'on'

        # Validation: check for duplicate names (excluding current supplier)
        if Supplier.objects.filter(name__iexact=name).exclude(id=pk).exists():
            messages.error(request, f"Supplier with name '{name}' already exists.")
        else:
            supplier.name = name
            supplier.contact_person = contact_person
            supplier.phone = phone
            supplier.email = email
            supplier.gst_number = gst_number
            try:
                supplier.rating = float(rating)
            except ValueError:
                pass
            supplier.is_active = is_active
            supplier.save()
            messages.success(request, f"Supplier '{name}' updated successfully.")
            return redirect('inventory_suppliers')

    low_stock_count = InventoryItem.objects.filter(current_stock__lte=F('reorder_level')).count()

    context = {
        'supplier': supplier,
        'low_stock_count': low_stock_count,
        'active_tab': 'suppliers',
    }
    return render(request, 'hospitalapp/admin/inventory_update_supplier.html', context)


@login_required
def delete_supplier(request, pk):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to delete suppliers.")

    from hospitalapp.models import Supplier
    supplier = get_object_or_404(Supplier, id=pk)
    name = supplier.name
    supplier.delete()
    messages.success(request, f"Supplier '{name}' deleted successfully.")
    return redirect('inventory_suppliers')


@login_required
def export_inventory_report(request, report_type, format_type):
    allowed_roles = [
        'admin', 'inventory_manager', 'store_keeper', 
        'pharmacy_supervisor', 'laboratory_supervisor', 
        'radiology_supervisor', 'nursing_supervisor'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to view the Inventory Module.")

    from hospitalapp.models import StockIssue, InventoryItem, Medicine
    from datetime import date
    import csv
    from reportlab.pdfgen import canvas
    from io import BytesIO

    # Gather data based on report type
    if report_type == 'movement':
        title = "Stock Movement Log"
        headers = ["Issue Slip No", "Department", "Item Name", "Quantity", "Issued By", "Date"]
        data_rows = []
        issues = StockIssue.objects.all().order_by('-created_at')
        for issue in issues:
            data_rows.append([
                issue.issue_number,
                issue.department,
                issue.item.name,
                f"{issue.quantity} {issue.item.uom}",
                issue.requested_by.username,
                issue.created_at.strftime("%Y-%m-%d %H:%M")
            ])
    elif report_type == 'valuation':
        title = "Inventory Valuation Report"
        headers = ["Item Code", "Item Name", "Category", "Current Stock", "Purchase Price", "Total Value"]
        data_rows = []
        items = InventoryItem.objects.all().order_by('name')
        for item in items:
            total_val = item.current_stock * item.purchase_price
            data_rows.append([
                item.item_code,
                item.name,
                item.category,
                f"{item.current_stock} {item.uom}",
                f"Rs. {item.purchase_price:.2f}",
                f"Rs. {total_val:.2f}"
            ])
    elif report_type == 'expiry':
        title = "Expired & Expiring Stock Ledger"
        headers = ["Medicine Name", "Expiry Date", "Status"]
        data_rows = []
        from datetime import timedelta
        from django.utils import timezone
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        medicines = Medicine.objects.filter(expiry_date__lte=thirty_days_later).order_by('expiry_date')
        for med in medicines:
            status = "Expired" if med.expiry_date < today else "Expiring Soon"
            data_rows.append([
                med.name,
                med.expiry_date.strftime("%Y-%m-%d"),
                status
            ])
    else:
        return HttpResponse("Invalid report type.", status=400)

    # Export CSV format
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{date.today()}.csv"'
        writer = csv.writer(response)
        writer.writerow([title])
        writer.writerow([])
        writer.writerow(headers)
        for row in data_rows:
            writer.writerow(row)
        return response

    # Export PDF format
    elif format_type == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setTitle(title)
        
        # Draw Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, title)
        p.setFont("Helvetica", 10)
        p.drawString(50, 730, f"Generated Date: {date.today()}")
        
        y = 690
        p.setFont("Helvetica-Bold", 9)
        # Draw Headers
        x_offsets = [50, 140, 240, 340, 440, 520]
        for i, header in enumerate(headers):
            if i < len(x_offsets):
                p.drawString(x_offsets[i], y, header)
        p.line(50, y-5, 570, y-5)
        
        y -= 20
        p.setFont("Helvetica", 9)
        for row in data_rows:
            if y < 50:
                p.showPage()
                y = 750
                p.setFont("Helvetica-Bold", 9)
                for i, header in enumerate(headers):
                    if i < len(x_offsets):
                        p.drawString(x_offsets[i], y, header)
                p.line(50, y-5, 570, y-5)
                y -= 20
                p.setFont("Helvetica", 9)
                
            for i, val in enumerate(row):
                if i < len(x_offsets):
                    p.drawString(x_offsets[i], y, str(val))
            y -= 15
            
        p.showPage()
        p.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{date.today()}.pdf"'
        return response
    else:
        return HttpResponse("Invalid format type.", status=400)


@login_required
def request_inventory_item(request):
    allowed_roles = [
        'admin', 'doctor', 'pharmacist', 'senior_pharmacist', 'pharmacy_supervisor',
        'lab_technician', 'laboratoryist', 'laboratory_supervisor',
        'radiologist', 'radiology_technician', 'radiology_supervisor',
        'nurse', 'nursing_station', 'nursing_superintendent', 'nursing_supervisor',
        'receptionist'
    ]
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to request inventory items.")

    from hospitalapp.models import InventoryItem, PurchaseRequisition
    from django.db.models import F

    if request.method == 'POST':
        item_id = request.POST.get('item')
        quantity = int(request.POST.get('quantity', '1'))
        department = request.POST.get('department')
        if not department:
            if request.user.role in ['pharmacist', 'senior_pharmacist', 'pharmacy_supervisor']:
                department = 'Pharmacy'
            elif request.user.role in ['lab_technician', 'laboratoryist', 'laboratory_supervisor']:
                department = 'Laboratory'
            elif request.user.role in ['radiologist', 'radiology_technician', 'radiology_supervisor']:
                department = 'Radiology'
            elif request.user.role in ['nurse', 'nursing_station', 'nursing_superintendent', 'nursing_supervisor']:
                department = 'Wards'
            elif request.user.role == 'receptionist':
                department = 'Casualty'
            else:
                department = 'General'

        item = get_object_or_404(InventoryItem, id=item_id)
        
        # Auto generate requisition number
        import random
        req_num = f"REQ-{random.randint(10000, 99999)}"
        
        PurchaseRequisition.objects.create(
            req_number=req_num,
            department=department,
            requested_by=request.user,
            item=item,
            quantity=quantity,
            status='Pending'
        )
        messages.success(request, f"Purchase Requisition {req_num} sent to Store Keeper.")
        return redirect('request_inventory_item')

    items = InventoryItem.objects.all().order_by('name')
    my_requisitions = PurchaseRequisition.objects.filter(requested_by=request.user).order_by('-created_at')

    context = {
        'items': items,
        'my_requisitions': my_requisitions,
    }
    return render(request, 'hospitalapp/inventory/request_item.html', context)


@login_required
def approve_requisition(request, pk):
    allowed_roles = ['admin', 'inventory_manager', 'store_keeper']
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to approve requisitions.")
    
    from hospitalapp.models import PurchaseRequisition
    req = get_object_or_404(PurchaseRequisition, id=pk)
    req.status = 'Approved'
    req.save()
    messages.success(request, f"Requisition {req.req_number} has been approved.")
    return redirect('inventory_purchase')


@login_required
def reject_requisition(request, pk):
    allowed_roles = ['admin', 'inventory_manager', 'store_keeper']
    if request.user.role not in allowed_roles:
        return HttpResponseForbidden("You are not authorized to reject requisitions.")
    
    from hospitalapp.models import PurchaseRequisition
    req = get_object_or_404(PurchaseRequisition, id=pk)
    req.status = 'Rejected'
    req.save()
    messages.success(request, f"Requisition {req.req_number} has been rejected.")
    return redirect('inventory_purchase')






