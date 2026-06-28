import threading
import urllib.request
import json
from django.conf import settings

def send_webhook_async(url, payload):
    def run():
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Django-Hospital-Webhook'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                response_read = response.read()
                print(f"Webhook response status: {response.status}, body: {response_read}")
        except Exception as e:
            print(f"Webhook sending failed: {e}")

    # Run in a background daemon thread so it doesn't block the request/response flow
    threading.Thread(target=run, daemon=True).start()

def trigger_appointment_webhook(appointment, is_new=False, old_status=None):
    webhook_url = getattr(settings, 'HOSPITAL_BOOKING_WEBHOOK_URL', 'https://asha-hospital.app.n8n.cloud/webhook/hospital-booking')
    if not webhook_url:
        return

    # Gather patient details
    patient = appointment.patient
    patient_data = {
        'patient_id': patient.patient_id,
        'name': patient.name,
        'age': patient.age,
        'gender': patient.gender,
        'phone': patient.phone,
        'email': patient.email,
        'address': patient.address,
    } if patient else {}

    # Gather doctor details
    doctor = appointment.doctor
    doctor_data = {
        'doctor_id': doctor.doctor_id,
        'name': doctor.name,
        'specialization': doctor.specialization,
        'phone': doctor.phone,
        'email': doctor.email,
        'availability': doctor.availability,
    } if doctor else {}

    # Determine event type
    event = 'appointment_booked' if is_new else 'appointment_updated'
    if not is_new and old_status != appointment.status:
        if appointment.status == 'Approved':
            event = 'appointment_approved'
        elif appointment.status == 'Cancelled':
            event = 'appointment_cancelled'
        elif appointment.status == 'Completed':
            event = 'appointment_completed'

    payload = {
        'event': event,
        'appointment_id': appointment.appointment_id,
        'appointment_date': str(appointment.appointment_date),
        'status': appointment.status,
        'reason': appointment.reason,
        'created_at': str(appointment.created_at) if appointment.created_at else None,
        'patient': patient_data,
        'doctor': doctor_data,
        'old_status': old_status
    }

    send_webhook_async(webhook_url, payload)
