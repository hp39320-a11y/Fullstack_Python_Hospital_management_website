from django.urls import path
from . import views
from . import pharmacy_views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('departments/', views.departments, name='departments'),
    path('departments/<str:spec>/',views.doctors_by_specialization,name='doctors_by_specialization'),  
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('hospital-admin/doctors/', views.manage_doctors, name='manage_doctors'),
    path('hospital-admin/doctors/update/<int:pk>/', views.update_doctor, name='update_doctor'),
    path('hospital-admin/doctors/delete/<int:pk>/', views.delete_doctor, name='delete_doctor'),
    path('hospital-admin/patients/', views.manage_patients, name='manage_patients'),
    path('hospital-admin/appointments/', views.manage_appointments, name='manage_appointments'),
    path('hospital-admin/medicines/', views.manage_medicines, name='manage_medicines'),
    path('hospital-admin/medicines/update/<int:pk>/', views.update_medicine, name='update_medicine'),
    path('hospital-admin/medicines/delete/<int:pk>/', views.delete_medicine, name='delete_medicine'),
    path('hospital-admin/bills/', views.manage_bills, name='manage_bills'),
    path('hospital-admin/bills/mark-paid/<int:pk>/', views.mark_bill_paid, name='mark_bill_paid'),
    path('add-receptionist/', views.add_receptionist, name='add_receptionist'),
    path('add-pharmacist/', views.add_pharmacist, name='add_pharmacist'),
    path('add-laboratoryist/', views.add_laboratoryist, name='add_laboratoryist'),
    path('add-radiologist/', views.add_radiologist, name='add_radiologist'),
    path('add-nursing-station/', views.add_nursing_station, name='add_nursing_station'),
    path('add-inventory-manager/', views.add_inventory_manager, name='add_inventory_manager'),
    path('add-store-keeper/', views.add_store_keeper, name='add_store_keeper'),
    path('hospital-admin/staff/', views.manage_staff, name='manage_staff'),
    path('hospital-admin/inventory/', views.inventory_dashboard, name='admin_inventory_dashboard'),
    path('hospital-admin/inventory/items/', views.inventory_items, name='inventory_items'),
    path('hospital-admin/inventory/suppliers/', views.inventory_suppliers, name='inventory_suppliers'),
    path('hospital-admin/inventory/suppliers/update/<int:pk>/', views.update_supplier, name='update_supplier'),
    path('hospital-admin/inventory/suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),
    path('hospital-admin/inventory/purchase/', views.inventory_purchase, name='inventory_purchase'),
    path('hospital-admin/inventory/grn/', views.inventory_grn, name='inventory_grn'),
    path('hospital-admin/inventory/expiry/', views.inventory_expiry, name='inventory_expiry'),
    path('hospital-admin/inventory/issue/', views.inventory_issue, name='inventory_issue'),
    path('hospital-admin/inventory/biomedical/', views.inventory_biomedical, name='inventory_biomedical'),
    path('hospital-admin/inventory/emergency/', views.inventory_emergency, name='inventory_emergency'),
    path('hospital-admin/inventory/reports/', views.inventory_reports, name='inventory_reports'),
    path('hospital-admin/inventory/reports/export/<str:report_type>/<str:format_type>/', views.export_inventory_report, name='export_inventory_report'),
    path('hospital-admin/inventory/request-item/', views.request_inventory_item, name='request_inventory_item'),
    path('hospital-admin/inventory/request-item/approve/<int:pk>/', views.approve_requisition, name='approve_requisition'),
    path('hospital-admin/inventory/request-item/reject/<int:pk>/', views.reject_requisition, name='reject_requisition'),
    path('hospital-admin/staff/update/<int:pk>/', views.update_staff, name='update_staff'),
    path('hospital-admin/staff/delete/<int:pk>/', views.delete_staff, name='delete_staff'),
    
    # Doctor
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/search-medicines/', views.doctor_search_medicines, name='doctor_search_medicines'),
    path('doctor/prescriptions/', views.prescription_history, name='prescription_history'),
    path('doctor/add-prescription/<int:appointment_id>/', views.add_prescription, name='add_prescription'),
    path('prescription/delete/<int:pk>/', views.delete_prescription, name='delete_prescription'),
    path('doctor/patient-history/<int:patient_id>/',views.patient_history,name='patient_history'),
    path('doctor/analytics/', views.doctor_analytics, name='doctor_analytics'),
    # Patient
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/bills/', views.patient_bills, name='patient_bills'),
    path('patient/lab-results/', views.patient_lab_results, name='patient_lab_results'),
    path('patient/radiology-results/', views.patient_radiology_results, name='patient_radiology_results'),
    
    # Pharmacist
    path('pharmacist-dashboard/', views.pharmacist_dashboard, name='pharmacist_dashboard'),
    path('pharmacist/analytics/', views.pharmacist_analytics, name='pharmacist_analytics'),
    path('pharmacist/prescriptions/', views.pharmacist_prescriptions, name='pharmacist_prescriptions'),
    path('pharmacist/update-stock/<int:pk>/', views.update_stock, name='update_stock'),
    path('prescriptions/', views.manage_prescriptions, name='manage_prescriptions'),
    path('prescription/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescription/dispense/<int:pk>/', views.dispense_prescription, name='dispense_prescription'),
    path('bill/<int:prescription_id>/', views.generate_bill, name='generate_bill'),
    path('generate-bill/<int:prescription_id>/', views.generate_bill,name='generate_bill'),
    path('payment-success/', views.payment_success,name='payment_success'),
    path('download-bill/<int:bill_id>/', views.download_bill,name='download_bill'),
    path('payment/<int:bill_id>/', views.create_payment, name='create_payment'),
    path('payment/multiple/', views.pay_multiple_bills, name='pay_multiple_bills'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
    # Receptionist
    path('receptionist-dashboard/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('receptionist/analytics/', views.receptionist_analytics, name='receptionist_analytics'),
    path('receptionist/schedule/', views.schedule_appointment, name='schedule_appointment'),
    path('receptionist/bills/', views.receptionist_bills, name='receptionist_bills'),
    path('receptionist/patient-id-card/<int:patient_id>/', views.download_patient_id_card, name='download_patient_id_card'),
    path('appointment-status/<int:pk>/<str:status>/',views.update_appointment_status,name='update_appointment_status'),
    path('appointments/approve/<int:pk>/',views.approve_appointment,name='approve_appointment'),
    path('appointments/complete/<int:pk>/',views.complete_appointment,name='complete_appointment'),
    path('appointments/cancel/<int:pk>/',views.cancel_appointment,name='cancel_appointment'),
    path('appointments/delete/<int:pk>/',views.delete_appointment,name='delete_appointment'),

    # Emergency (Casuality)
    path('receptionist/casuality/', views.casuality_dashboard, name='casuality_dashboard'),
    path('receptionist/casuality/update/<int:pk>/<str:status>/', views.update_casuality_status, name='update_casuality_status'),
    path('doctor/emergency/', views.doctor_emergency_dashboard, name='doctor_emergency_dashboard'),
    path('doctor/emergency/update/<int:pk>/<str:status>/', views.update_casuality_status_doctor, name='update_casuality_status_doctor'),
    path('doctor/emergency/refer/<int:casualty_id>/', views.doctor_refer_specialist, name='doctor_refer_specialist'),
    path('doctor/emergency/prescription/<int:casuality_id>/', views.doctor_add_prescription_casuality, name='doctor_add_prescription_casuality'),
    path('doctor/emergency/critical-alert/<int:casualty_id>/', views.doctor_send_critical_alert, name='doctor_send_critical_alert'),
    path('doctor/admit-patient/<int:appointment_id>/', views.doctor_admit_patient, name='doctor_admit_patient'),
    path('doctor/admit-casuality/<int:casuality_id>/', views.doctor_admit_casuality, name='doctor_admit_casuality'),
    path('doctor/refer-inpatient/<int:admission_id>/', views.doctor_refer_inpatient, name='doctor_refer_inpatient'),

    # Admissions & Inpatient (IP) Billing
    path('receptionist/admissions/', views.admissions_dashboard, name='admissions_dashboard'),
    path('receptionist/admissions/approve/<int:pk>/', views.approve_admission, name='approve_admission'),
    path('receptionist/admissions/reject/<int:pk>/', views.reject_admission, name='reject_admission'),
    path('receptionist/admissions/charges/<int:pk>/', views.manage_ip_charges, name='manage_ip_charges'),
    path('doctor/discharge-ready/<int:admission_id>/', views.doctor_discharge_ready, name='doctor_discharge_ready'),
    path('receptionist/discharge/<int:admission_id>/', views.discharge_billing, name='discharge_billing'),
    path('receptionist/discharge/discount/<int:admission_id>/', views.apply_discharge_discount, name='apply_discharge_discount'),
    path('payment/ip-bill/verify/', views.verify_ip_payment, name='verify_ip_payment'),
    path('download-discharge-summary/<int:admission_id>/', views.download_discharge_summary, name='download_discharge_summary'),

    # Bed Management
    path('hospital-admin/beds/', views.bed_management, name='bed_management'),
    path('api/beds/available/', views.bed_available_json, name='bed_available_json'),

    # Admin Nurse Management
    path('hospital-admin/nurses/', views.manage_nurses, name='manage_nurses'),
    path('hospital-admin/nurses/delete/<int:pk>/', views.delete_nurse, name='delete_nurse'),

    # Nurse Workspaces
    path('nurse/dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('nurse/analytics/', views.nurse_analytics, name='nurse_analytics'),
    path('nurse/head-dashboard/', views.head_nurse_dashboard, name='head_nurse_dashboard'),
    path('nurse/log-vitals/<int:admission_id>/', views.nurse_log_vitals, name='nurse_log_vitals'),
    path('nurse/log-casualty-vitals/<int:casualty_id>/', views.nurse_log_casualty_vitals, name='nurse_log_casualty_vitals'),
    path('nurse/administer-item/<int:entry_id>/', views.nurse_administer_item, name='nurse_administer_item'),
    path('nurse/administer-emergency-item/<int:item_id>/', views.nurse_administer_emergency_item, name='nurse_administer_emergency_item'),
    path('nurse/medication-log/', views.nurse_medication_log, name='nurse_medication_log'),

    # Doctor Inpatient Prescriptions
    path('doctor/ip-prescription/<int:admission_id>/', views.doctor_inpatient_prescription, name='doctor_inpatient_prescription'),

    # Vitals & ICU Monitoring
    path('icu-dashboard/', views.icu_dashboard, name='icu_dashboard'),
    path('patient-vitals-history/<int:admission_id>/', views.patient_vitals_history, name='patient_vitals_history'),

    # Ambulance Management
    path('receptionist/ambulance/', views.ambulance_dashboard, name='ambulance_dashboard'),

    # Non-Staff, Laundry, Security & Cleaning Management
    path('receptionist/non-staff/', views.non_staff_dashboard, name='non_staff_dashboard'),



path(
    'doctor/referral/create/<int:casualty_id>/',
    views.create_referral,
    name='create_referral'
),

path(
    'doctor/referral/inbox/',
    views.referral_inbox,
    name='referral_inbox'
),

path(
    'doctor/referral/accept/<int:referral_id>/',
    views.accept_referral,
    name='accept_referral'
),

path(
    'doctor/referral/reject/<int:referral_id>/',
    views.reject_referral,
    name='reject_referral'
),

path(
    'doctor/admit/<int:casuality_id>/',
    views.admit_referred_patient,
    name='admit_referred_patient'
),

path(
    'doctor/icu-transfer/<int:admission_id>/',
    views.transfer_to_icu,
    name='transfer_to_icu'
),

path(
    'doctor/transfer/<int:admission_id>/',
    views.transfer_patient,
    name='transfer_patient'
),

path(
    'doctor/discharge/<int:admission_id>/',
    views.discharge_patient,
    name='discharge_patient'
),

path(
    'doctor/discharge-prescription/<int:admission_id>/',
    views.doctor_add_discharge_prescription,
    name='doctor_add_discharge_prescription'
),

# Collaborative Patient Care Workspace
path(
    'doctor/patient-care/<int:admission_id>/',
    views.patient_care_details,
    name='patient_details'
),
path(
    'doctor/patient-care/<int:admission_id>/add-note/',
    views.add_clinical_note,
    name='add_clinical_note'
),
path(
    'doctor/patient-care/<int:admission_id>/suggest-investigation/',
    views.suggest_investigation,
    name='suggest_investigation'
),

# Referral Inbox (for specialists to view & accept pending referrals)
path(
    'doctor/referral/specialist-list/',
    views.specialist_referrals,
    name='specialist_referrals'
),

# Laboratory

path(
    'doctor/lab-order/<int:patient_id>/',
    views.doctor_create_lab_order,
    name='doctor_create_lab_order'
),

path(
    'laboratory/dashboard/',
    views.laboratory_dashboard,
    name='laboratory_dashboard'
),
path(
    'laboratory/samples/',
    views.laboratory_samples,
    name='laboratory_samples'
),
path(
    'laboratory/pipeline/',
    views.laboratory_pipeline,
    name='laboratory_pipeline'
),
path(
    'laboratory/completed/',
    views.laboratory_completed,
    name='laboratory_completed'
),

path(
    'laboratory/collect-sample/<int:order_id>/',
    views.laboratory_collect_sample,
    name='laboratory_collect_sample'
),

path(
    'laboratory/start-processing/<int:order_id>/',
    views.laboratory_start_processing,
    name='laboratory_start_processing'
),

path(
    'laboratory/result/<int:item_id>/',
    views.enter_lab_result,
    name='enter_lab_result'
),

path(
    'laboratory/order-results/<int:order_id>/',
    views.enter_all_lab_results,
    name='enter_all_lab_results'
),

path(
    'laboratory/verify/<int:order_id>/',
    views.verify_lab_result,
    name='verify_lab_result'
),

# Radiology

path(
    'doctor/radiology-order/<int:patient_id>/',
    views.doctor_create_radiology_order,
    name='doctor_create_radiology_order'
),

path(
    'radiology/dashboard/',
    views.radiology_dashboard,
    name='radiology_dashboard'
),
path(
    'radiology/schedule-queue/',
    views.radiology_schedule_queue,
    name='radiology_schedule_queue'
),
path(
    'radiology/active-queue/',
    views.radiology_active_queue,
    name='radiology_active_queue'
),
path(
    'radiology/completed/',
    views.radiology_completed,
    name='radiology_completed'
),

path(
    'radiology/schedule/<int:order_id>/',
    views.radiology_schedule_scan,
    name='radiology_schedule_scan'
),

path(
    'radiology/update-scan-status/<int:order_id>/<str:status>/',
    views.radiology_update_scan_status,
    name='radiology_update_scan_status'
),

path(
    'radiology/upload-attachment/<int:order_id>/',
    views.radiology_upload_attachment,
    name='radiology_upload_attachment'
),

path(
    'radiology/report/<int:item_id>/',
    views.create_radiology_report,
    name='create_radiology_report'
),

# Printable / Downloadable Reports
path(
    'laboratory/print-report/<int:order_id>/',
    views.print_lab_report,
    name='print_lab_report'
),

path(
    'laboratory/download-pdf/<int:order_id>/',
    views.download_lab_report_pdf,
    name='download_lab_report_pdf'
),

path(
    'radiology/print-report/<int:order_id>/',
    views.print_radiology_report,
    name='print_radiology_report'
),

path(
    'radiology/download-pdf/<int:order_id>/',
    views.download_radiology_report_pdf,
    name='download_radiology_report_pdf'
),

# Admin Masters
path(
    'hospital-admin/lab-tests/',
    views.admin_manage_lab_tests,
    name='admin_manage_lab_tests'
),

path(
    'hospital-admin/lab-tests/<int:test_id>/parameters/',
    views.admin_manage_lab_parameters,
    name='admin_manage_lab_parameters'
),

path(
    'hospital-admin/radiology-tests/',
    views.admin_manage_radiology_tests,
    name='admin_manage_radiology_tests'
),

# Doctor Notifications
path(
    'doctor/notifications/',
    views.doctor_notifications,
    name='doctor_notifications'
),

path(
    'doctor/notifications/mark-read/<int:notification_id>/',
    views.mark_notification_read,
    name='mark_notification_read'
),

# Nursing Station
path('nursing-station/dashboard/', views.nursing_station_dashboard, name='nursing_station_dashboard'),
path('doctor/nursing-requests/', views.doctor_nursing_requests, name='doctor_nursing_requests'),
path('nurse/nursing-tasks/', views.nurse_tasks, name='nurse_tasks'),
path('nursing-station/messages/', views.nursing_station_messages, name='nursing_station_messages'),
path('nursing-station/reports/', views.nursing_station_reports, name='nursing_station_reports'),

    # Emergency / Casualty Zone paths
    path('emergency/triage-dashboard/', views.emergency_triage_dashboard, name='emergency_triage_dashboard'),
    path('emergency/triage/<int:casualty_id>/', views.triage_patient, name='triage_patient'),
    path('emergency/doctor-workspace/', views.emergency_doctor_workspace, name='emergency_doctor_workspace'),
    path('emergency/evaluate/<int:casualty_id>/', views.emergency_doctor_evaluate, name='emergency_doctor_evaluate'),
    path('emergency/order-lab/<int:casualty_id>/', views.emergency_create_lab_order, name='emergency_create_lab_order'),
    path('emergency/order-radiology/<int:casualty_id>/', views.emergency_create_radiology_order, name='emergency_create_radiology_order'),
    path('emergency/disposition/<int:casualty_id>/<str:disposition_type>/', views.emergency_disposition, name='emergency_disposition'),
    path('emergency/reports/', views.emergency_reports, name='emergency_reports'),
    path('emergency/broadcast-alert/', views.trigger_emergency_broadcast_alert, name='trigger_emergency_broadcast_alert'),

    # OP Pharmacy & Multi-Counter Management System
    path('pharmacy/dashboard/', pharmacy_views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('pharmacy/tokens/', pharmacy_views.token_management, name='token_management'),
    path('pharmacy/counters/', pharmacy_views.counter_management, name='counter_management'),
    path('pharmacy/dispensing/<int:counter_id>/', pharmacy_views.dispensing_counter, name='dispensing_counter'),
    path('pharmacy/dispensing/call-next/<int:counter_id>/', pharmacy_views.call_next_token, name='call_next_token'),
    path('pharmacy/dispensing/recall/<int:token_id>/', pharmacy_views.recall_token, name='recall_token'),
    path('pharmacy/dispensing/skip/<int:token_id>/', pharmacy_views.skip_token, name='skip_token'),
    path('pharmacy/dispensing/transfer/<int:token_id>/', pharmacy_views.transfer_token, name='transfer_token'),
    path('pharmacy/dispensing/item/<int:token_id>/', pharmacy_views.dispense_medication_item, name='dispense_medication_item'),
    path('pharmacy/dispensing/complete/<int:token_id>/', pharmacy_views.complete_dispensing, name='complete_dispensing'),
    path('pharmacy/digital-display/', pharmacy_views.digital_display, name='digital_display'),
    path('pharmacy/fast-track/', pharmacy_views.fast_track_queue, name='fast_track_queue'),
    path('pharmacy/billing-verification/', pharmacy_views.billing_verification, name='billing_verification'),
    path('pharmacy/inventory/', pharmacy_views.inventory_dashboard, name='inventory_dashboard'),
    path('pharmacy/reports/', pharmacy_views.pharmacy_reports, name='pharmacy_reports'),
    path('pharmacy/supervisor/', pharmacy_views.supervisor_dashboard, name='supervisor_dashboard'),
    path('pharmacy/api/serving-tokens/', pharmacy_views.api_serving_tokens, name='api_serving_tokens'),
    path('pharmacy/api/play-voice/', pharmacy_views.api_play_voice, name='api_play_voice'),

    # Nursing Superintendent Dashboard
    path('nursing-superintendent/dashboard/', views.nursing_superintendent_dashboard, name='nursing_superintendent_dashboard'),

]

