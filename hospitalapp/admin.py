from django.contrib import admin
from .models import User, Doctor, Patient, Appointment, Medicine, Prescription, Bill

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_staff', 'is_superuser')
    search_fields = ('username',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'email')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'phone')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock', 'price')

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('patient', 'total_amount', 'payment_status', 'created_at')

from .models import LabTest, LabOrder, LabOrderItem, LabResult
from .models import RadiologyTest, RadiologyOrder, RadiologyOrderItem, RadiologyReport

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'active')

@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'status', 'created_at')

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'technician', 'completed_at')

@admin.register(RadiologyTest)
class RadiologyTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'active')

@admin.register(RadiologyOrder)
class RadiologyOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'status', 'created_at')

@admin.register(RadiologyReport)
class RadiologyReportAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'radiologist', 'reported_at')

from .models import Staff
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'email')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role__in=['receptionist', 'pharmacist', 'lab_technician', 'laboratoryist', 'radiologist', 'radiology_technician'])

from .models import Supplier, InventoryItem, PurchaseRequisition, PurchaseOrder, GoodsReceiptNote, StockIssue, BiomedicalAsset

admin.site.register(Supplier)
admin.site.register(InventoryItem)
admin.site.register(PurchaseRequisition)
admin.site.register(PurchaseOrder)
admin.site.register(GoodsReceiptNote)
admin.site.register(StockIssue)
admin.site.register(BiomedicalAsset)
