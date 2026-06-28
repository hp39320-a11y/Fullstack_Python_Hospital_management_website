from hospitalapp.models import DoctorNotification, Doctor

def doctor_notifications_processor(request):
    if request.user.is_authenticated and request.user.role == 'doctor':
        try:
            doctor = Doctor.objects.get(user=request.user)
            unread_count = DoctorNotification.objects.filter(doctor=doctor, is_read=False).count()
            return {
                'doctor_unread_notifications_count': unread_count,
            }
        except Doctor.DoesNotExist:
            pass
    return {
        'doctor_unread_notifications_count': 0,
    }
