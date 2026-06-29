
import os
import django

# =========================
# DJANGO SETUP
# =========================
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'hospitalproject.settings'
)

django.setup()

# =========================
# IMPORT MODELS
# =========================
from hospitalapp.models import (
    User,
    Nurse,
    Doctor
)

# =========================
# FIX DOCTOR ROLES
# =========================
print("\n===== FIXING DOCTOR ROLES =====")

for doctor in Doctor.objects.select_related('user').all():

    if doctor.user:

        if doctor.user.role != 'doctor':

            print(
                f"Updating doctor role: "
                f"{doctor.user.username}"
            )

            doctor.user.role = 'doctor'

            doctor.user.save(
                update_fields=['role']
            )

# =========================
# FIX NURSE ROLES
# =========================
print("\n===== FIXING NURSE ROLES =====")

for nurse in Nurse.objects.select_related('user').all():

    if nurse.user:

        if nurse.user.role != 'nurse':

            print(
                f"Updating nurse role: "
                f"{nurse.user.username}"
            )

            nurse.user.role = 'nurse'

            nurse.user.save(
                update_fields=['role']
            )

# =========================
# SHOW ALL USERS
# =========================
print("\n===== ALL USERS =====")

users = User.objects.all().values(
    'username',
    'role'
)

for user in users:
    print(user)

print("\nROLE FIX COMPLETED SUCCESSFULLY ✅")

