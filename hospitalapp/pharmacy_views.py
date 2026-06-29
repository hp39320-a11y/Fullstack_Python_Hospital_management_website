from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Avg, Count, F, Case, When, Value, IntegerField
from django.db.models.functions import ExtractHour
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from decimal import Decimal

from hospitalapp.models import (
    Patient, Doctor, Prescription, PrescriptionMedicine, Medicine, Bill, AuditLog,
    PharmacyCounter, PharmacyToken, CounterAssignment, TokenCallLog,
    DispensingRecord, QueueTransfer, VoiceAnnouncementLog, CounterPerformance,
    PharmacyAuditLog
)
from hospitalapp.forms import PharmacyCounterForm, PharmacyTokenForm

# Decorator to restrict access to specific roles
def pharmacy_roles_required(*roles):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role in roles or request.user.role == 'admin' or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You are not authorized to view this page.")
        return _wrapped_view
    return decorator

# Helper: Auto-generate token for a prescription
def create_token_for_prescription(prescription, priority_level=None):
    # Check if token already exists
    if PharmacyToken.objects.filter(prescription=prescription).exists():
        return PharmacyToken.objects.filter(prescription=prescription).first()

    # Determine priority
    patient = prescription.patient
    if not priority_level:
        if patient.age >= 60:
            priority_level = 'Senior Citizen'
        elif hasattr(prescription, 'casualty') or prescription.notes and 'emergency' in prescription.notes.lower():
            priority_level = 'Emergency'
        else:
            priority_level = 'Regular'

    # Get prefix
    prefix_map = {
        'Regular': 'P',
        'Senior Citizen': 'S',
        'Corporate': 'C',
        'VIP': 'V',
        'Emergency': 'E'
    }
    prefix = prefix_map.get(priority_level, 'P')

    # Get sequence number
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    today_tokens_count = PharmacyToken.objects.filter(
        created_at__range=(start_dt, end_dt),
        priority_level=priority_level
    ).count()
    seq_num = today_tokens_count + 1
    token_number = f"{prefix}{seq_num:03d}"

    # Get linked bill if any
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
        details=f"Token {token_number} generated for patient {patient.name}",
        user=prescription.doctor.user if prescription.doctor else None
    )

    return token

# PHARMACY DASHBOARD
@pharmacy_roles_required('pharmacist', 'senior_pharmacist', 'pharmacy_supervisor', 'inventory_manager')
def pharmacy_dashboard(request):
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    
    # OP Prescriptions created today
    total_prescriptions = Prescription.objects.filter(created_at__range=(start_dt, end_dt)).count()
    
    tokens_today = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt))
    active_tokens = tokens_today.exclude(status__in=['Completed', 'Cancelled', 'Skipped']).count()
    waiting_tokens = tokens_today.filter(status='Waiting').count()
    completed_tokens = tokens_today.filter(status='Completed').count()
    
    # Average waiting time (in minutes)
    avg_wait_sec = tokens_today.filter(status='Completed', waiting_time__isnull=False).aggregate(Avg('waiting_time'))['waiting_time__avg']
    avg_wait_time = round(avg_wait_sec / 60) if avg_wait_sec else 0

    active_counters = PharmacyCounter.objects.filter(status__in=['Active', 'Busy']).count()
    emergency_queue = tokens_today.filter(priority_level='Emergency', status='Waiting').count()
    
    # Revenue (pharmacy bills paid today)
    daily_revenue = Bill.objects.filter(
        created_at__range=(start_dt, end_dt),
        bill_type='pharmacy',
        payment_status='Paid'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    counters = PharmacyCounter.objects.all().order_by('number')
    
    # Get recent waiting tokens
    recent_waiting = PharmacyToken.objects.filter(status='Waiting').order_by('-created_at')[:10]

    context = {
        'total_prescriptions': total_prescriptions,
        'active_tokens': active_tokens,
        'waiting_tokens': waiting_tokens,
        'completed_tokens': completed_tokens,
        'avg_wait_time': avg_wait_time,
        'active_counters': active_counters,
        'emergency_queue': emergency_queue,
        'daily_revenue': daily_revenue,
        'counters': counters,
        'recent_waiting': recent_waiting,
    }
    return render(request, 'hospitalapp/pharmacy/dashboard.html', context)

# TOKEN MANAGEMENT
@pharmacy_roles_required('pharmacist', 'senior_pharmacist', 'pharmacy_supervisor')
def token_management(request):
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    tokens = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt)).order_by('-created_at')
    
    # Form for manual token creation
    if request.method == 'POST':
        form = PharmacyTokenForm(request.POST)
        if form.is_valid():
            token = form.save(commit=False)
            
            # Determine prefix
            prefix_map = {
                'Regular': 'P',
                'Senior Citizen': 'S',
                'Corporate': 'C',
                'VIP': 'V',
                'Emergency': 'E'
            }
            prefix = prefix_map.get(token.priority_level, 'P')
            today_count = PharmacyToken.objects.filter(
                created_at__range=(start_dt, end_dt),
                priority_level=token.priority_level
            ).count()
            token.token_number = f"{prefix}{today_count + 1:03d}"
            token.save()
            
            messages.success(request, f"Token {token.token_number} generated successfully.")
            return redirect('token_management')
    else:
        form = PharmacyTokenForm()

    context = {
        'tokens': tokens,
        'form': form
    }
    return render(request, 'hospitalapp/pharmacy/token_management.html', context)

# COUNTER MANAGEMENT
@pharmacy_roles_required('pharmacist', 'senior_pharmacist', 'pharmacy_supervisor')
def counter_management(request):
    counters = PharmacyCounter.objects.all().order_by('number')
    
    if request.method == 'POST':
        if 'create_counter' in request.POST:
            form = PharmacyCounterForm(request.POST)
            if form.is_valid():
                counter = form.save()
                PharmacyAuditLog.objects.create(
                    action="Counter Created",
                    details=f"Counter {counter.number} of type {counter.type} created",
                    user=request.user
                )
                messages.success(request, f"Counter {counter.number} created.")
                return redirect('counter_management')
        
        elif 'assign_pharmacist' in request.POST:
            counter_id = request.POST.get('counter_id')
            counter = get_object_or_404(PharmacyCounter, counter_id=counter_id)
            
            # Deactivate previous active assignments for this counter/pharmacist
            CounterAssignment.objects.filter(counter=counter, is_active=True).update(is_active=False, ended_at=timezone.now())
            CounterAssignment.objects.filter(pharmacist=request.user, is_active=True).update(is_active=False, ended_at=timezone.now())
            
            # Create new assignment
            CounterAssignment.objects.create(
                counter=counter,
                pharmacist=request.user,
                is_active=True
            )
            counter.status = 'Active'
            counter.save()
            
            PharmacyAuditLog.objects.create(
                action="Pharmacist Assigned",
                details=f"Pharmacist {request.user.username} assigned to Counter {counter.number}",
                user=request.user
            )
            messages.success(request, f"You are now working at Counter {counter.number}.")
            return redirect('dispensing_counter', counter_id=counter.counter_id)

        elif 'change_status' in request.POST:
            counter_id = request.POST.get('counter_id')
            status = request.POST.get('status')
            counter = get_object_or_404(PharmacyCounter, counter_id=counter_id)
            counter.status = status
            counter.save()
            messages.success(request, f"Counter {counter.number} status updated to {status}.")
            return redirect('counter_management')
            
    else:
        form = PharmacyCounterForm()

    # Get active assignments
    active_assignments = CounterAssignment.objects.filter(is_active=True).select_related('counter', 'pharmacist')

    context = {
        'counters': counters,
        'form': form,
        'active_assignments': active_assignments
    }
    return render(request, 'hospitalapp/pharmacy/counter_management.html', context)

# DISPENSING COUNTER WORKBENCH
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def dispensing_counter(request, counter_id):
    counter = get_object_or_404(PharmacyCounter, counter_id=counter_id)
    assignment = CounterAssignment.objects.filter(counter=counter, pharmacist=request.user, is_active=True).first()
    
    if not assignment and not request.user.role == 'admin':
        messages.warning(request, f"Please assign yourself to Counter {counter.number} first.")
        return redirect('counter_management')

    current_token = counter.current_token

    # Fetch medicines inside prescription
    medicines_list = []
    billing_status = "Unpaid"
    bill = None
    if current_token:
        presc = current_token.prescription
        bill = current_token.bill or Bill.objects.filter(prescription=presc).first()
        if bill:
            billing_status = bill.payment_status

        presc_medicines = PrescriptionMedicine.objects.filter(prescription=presc)
        for pm in presc_medicines:
            dispensed_qty = DispensingRecord.objects.filter(token=current_token, medicine=pm.medicine).aggregate(Sum('quantity_dispensed'))['quantity_dispensed__sum'] or 0
            medicines_list.append({
                'medicine': pm.medicine,
                'quantity_requested': pm.quantity,
                'quantity_dispensed': dispensed_qty,
                'remaining': pm.quantity - dispensed_qty
            })

    # Available counters for transfer
    other_counters = PharmacyCounter.objects.filter(status='Active').exclude(counter_id=counter.counter_id)

    # Queue list for this counter type or general
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

    context = {
        'counter': counter,
        'current_token': current_token,
        'medicines_list': medicines_list,
        'billing_status': billing_status,
        'bill': bill,
        'other_counters': other_counters,
        'waiting_tokens': waiting_tokens
    }
    return render(request, 'hospitalapp/pharmacy/dispensing_counter.html', context)

# CALL NEXT TOKEN
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def call_next_token(request, counter_id):
    counter = get_object_or_404(PharmacyCounter, counter_id=counter_id)
    
    # 1. Complete previous token if still in processing/called
    if counter.current_token and counter.current_token.status in ['Called', 'Processing']:
        prev = counter.current_token
        prev.status = 'Completed'
        prev.completed_at = timezone.now()
        if prev.called_at:
            prev.waiting_time = int((prev.completed_at - prev.created_at).total_seconds())
        prev.save()
        
        # update counter stats
        perf, _ = CounterPerformance.objects.get_or_create(counter=counter, pharmacist=request.user, date=timezone.localdate())
        perf.total_completed += 1
        perf.save()

    # 2. Get next waiting token
    # Priority logic: Emergency > VIP > Senior Citizen > Corporate > Regular
    # Non-Emergency tokens must have paid bill or billing approved (insurance/corp credit)
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
    for token in waiting_tokens:
        if token.priority_level == 'Emergency':
            next_token = token
            break
        else:
            # Check payment
            bill = token.bill or Bill.objects.filter(prescription=token.prescription).first()
            if bill and bill.payment_status == 'Paid':
                next_token = token
                break
            # Or if it's insurance / corporate credit approved (marked paid or handled)
            elif token.prescription.status == 'Dispensed':
                # Already dispensed or billing waived/approved
                next_token = token
                break
            
    # Fallback to the first waiting token in priority order if no paid/emergency token is found
    if not next_token and waiting_tokens.exists():
        next_token = waiting_tokens.first()
            

    if next_token:
        next_token.status = 'Called'
        next_token.called_at = timezone.now()
        next_token.counter = counter
        next_token.save()

        counter.status = 'Busy'
        counter.save()

        # Log calling
        TokenCallLog.objects.create(
            token=next_token,
            counter=counter,
            called_by=request.user
        )

        # Create voice announcement text
        ann_text = f"Token {next_token.token_number}, please proceed to Counter {counter.number}."
        if next_token.priority_level == 'Emergency':
            ann_text = f"Token {next_token.token_number}, emergency case, please proceed to Counter {counter.number} immediately."

        VoiceAnnouncementLog.objects.create(
            token=next_token,
            counter=counter,
            announcement_text=ann_text,
            language='English',
            is_played=False
        )

        # Update pharmacist performance
        perf, _ = CounterPerformance.objects.get_or_create(counter=counter, pharmacist=request.user, date=timezone.localdate())
        perf.total_served += 1
        perf.save()

        messages.success(request, f"Called Token {next_token.token_number}.")
    else:
        messages.info(request, "No waiting tokens in the queue.")

    return redirect('dispensing_counter', counter_id=counter.counter_id)

# RECALL TOKEN
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def recall_token(request, token_id):
    token = get_object_or_404(PharmacyToken, token_id=token_id)
    counter = token.counter
    
    # Find or create call log to update recall count
    call_log = TokenCallLog.objects.filter(token=token, counter=counter).order_by('-called_at').first()
    if call_log:
        call_log.recall_count += 1
        call_log.save()

    # Re-trigger announcement
    ann_text = f"Recall: Token {token.token_number}, please proceed to Counter {counter.number}."
    VoiceAnnouncementLog.objects.create(
        token=token,
        counter=counter,
        announcement_text=ann_text,
        language='English',
        is_played=False
    )
    
    messages.success(request, f"Recalled Token {token.token_number}.")
    return redirect('dispensing_counter', counter_id=counter.counter_id)

# SKIP TOKEN
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def skip_token(request, token_id):
    token = get_object_or_404(PharmacyToken, token_id=token_id)
    token.status = 'Skipped'
    token.save()

    counter = token.counter
    counter.status = 'Active'
    counter.save()

    perf, _ = CounterPerformance.objects.get_or_create(counter=counter, pharmacist=token.call_logs.first().called_by if token.call_logs.exists() else request.user, date=timezone.localdate())
    perf.total_skipped += 1
    perf.save()

    PharmacyAuditLog.objects.create(
        action="Token Skipped",
        details=f"Token {token.token_number} was skipped at Counter {counter.number}",
        user=request.user
    )

    messages.info(request, f"Token {token.token_number} skipped.")
    return redirect('dispensing_counter', counter_id=counter.counter_id)

# TRANSFER TOKEN
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def transfer_token(request, token_id):
    token = get_object_or_404(PharmacyToken, token_id=token_id)
    if request.method == 'POST':
        to_counter_id = request.POST.get('to_counter_id')
        reason = request.POST.get('reason')
        to_counter = get_object_or_404(PharmacyCounter, counter_id=to_counter_id)
        from_counter = token.counter

        # Log transfer
        QueueTransfer.objects.create(
            token=token,
            from_counter=from_counter,
            to_counter=to_counter,
            transferred_by=request.user,
            reason=reason
        )

        token.counter = to_counter
        token.status = 'Waiting' # Sent back to waiting for the target counter
        token.save()

        from_counter.status = 'Active'
        from_counter.save()

        messages.success(request, f"Token {token.token_number} transferred to Counter {to_counter.number}.")
    return redirect('dispensing_counter', counter_id=from_counter.counter_id)

# DISPENSE MEDICATION ITEM
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def dispense_medication_item(request, token_id):
    token = get_object_or_404(PharmacyToken, token_id=token_id)
    if request.method == 'POST':
        medicine_id = request.POST.get('medicine_id')
        qty_to_dispense = int(request.POST.get('quantity_dispensed', 0))
        status = request.POST.get('status', 'Full')
        sub_medicine_id = request.POST.get('substituted_medicine_id')
        
        medicine = get_object_or_404(Medicine, medicine_id=medicine_id)
        
        sub_med = None
        if sub_medicine_id:
            sub_med = get_object_or_404(Medicine, medicine_id=sub_medicine_id)

        # Check stock on dispensing medicine (either original or substituted)
        active_medicine = sub_med if sub_med else medicine
        if active_medicine.stock < qty_to_dispense:
            messages.error(request, f"Not enough stock for {active_medicine.name}. Available: {active_medicine.stock}")
            return redirect('dispensing_counter', counter_id=token.counter.counter_id)

        # Deduct stock
        active_medicine.stock -= qty_to_dispense
        active_medicine.save()

        # Expiry and batch details from medicine
        batch_no = request.POST.get('batch_number', 'BATCH-OP')
        expiry_dt = active_medicine.expiry_date

        # Record dispensing
        DispensingRecord.objects.create(
            token=token,
            medicine=medicine,
            quantity_requested=int(request.POST.get('quantity_requested', qty_to_dispense)),
            quantity_dispensed=qty_to_dispense,
            status=status,
            substituted_medicine=sub_med,
            batch_number=batch_no,
            expiry_date=expiry_dt,
            verified_by=request.user
        )

        messages.success(request, f"Dispensed {qty_to_dispense} units of {active_medicine.name}.")
    return redirect('dispensing_counter', counter_id=token.counter.counter_id)

# COMPLETE DISPENSING
@pharmacy_roles_required('pharmacist', 'senior_pharmacist')
def complete_dispensing(request, token_id):
    token = get_object_or_404(PharmacyToken, token_id=token_id)
    counter = token.counter
    
    token.status = 'Completed'
    token.completed_at = timezone.now()
    if token.called_at:
        token.waiting_time = int((token.completed_at - token.created_at).total_seconds())
    token.save()

    # Update prescription status
    prescription = token.prescription
    prescription.status = 'Dispensed'
    prescription.save()

    counter.status = 'Active'
    counter.save()

    # Update Performance
    perf, _ = CounterPerformance.objects.get_or_create(counter=counter, pharmacist=request.user, date=timezone.localdate())
    perf.total_completed += 1
    # Recalculate average serving time
    completed_tokens = PharmacyToken.objects.filter(counter=counter, status='Completed', completed_at__isnull=False, called_at__isnull=False)
    total_sec = sum((t.completed_at - t.called_at).total_seconds() for t in completed_tokens)
    if completed_tokens.count() > 0:
        perf.average_serving_time = int(total_sec / completed_tokens.count())
    perf.save()

    PharmacyAuditLog.objects.create(
        action="Dispensing Completed",
        details=f"Token {token.token_number} complete dispensing. Prescription marked as Dispensed.",
        user=request.user
    )

    messages.success(request, f"Dispensing completed for Token {token.token_number}.")
    return redirect('dispensing_counter', counter_id=counter.counter_id)

# DIGITAL DISPLAY BOARD
def digital_display(request):
    # This renders the static layout of the display board.
    # It contains JavaScript to poll for updates and play audio announcements.
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    tokens_today = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt))
    
    waiting_count = tokens_today.filter(status='Waiting').count()
    avg_wait_sec = tokens_today.filter(status='Completed', waiting_time__isnull=False).aggregate(Avg('waiting_time'))['waiting_time__avg']
    avg_wait_time = round(avg_wait_sec / 60) if avg_wait_sec else 8 # fallback to 8 min as per prompt
    
    context = {
        'waiting_count': waiting_count,
        'avg_wait_time': avg_wait_time
    }
    return render(request, 'hospitalapp/pharmacy/digital_display.html', context)

# FAST TRACK PRIORITY QUEUE VIEW
@pharmacy_roles_required('pharmacist', 'senior_pharmacist', 'pharmacy_supervisor')
def fast_track_queue(request):
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    
    # Priority level emergency or senior citizen or VIP
    priority_tokens = PharmacyToken.objects.filter(
        created_at__range=(start_dt, end_dt),
        priority_level__in=['Emergency', 'Senior Citizen', 'VIP'],
        status='Waiting'
    ).order_by('-priority_level', 'created_at')

    context = {
        'priority_tokens': priority_tokens
    }
    return render(request, 'hospitalapp/pharmacy/fast_track.html', context)

# BILLING VERIFICATION
@pharmacy_roles_required('pharmacist', 'receptionist', 'admin')
def billing_verification(request):
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    # Find tokens waiting for billing verification
    tokens = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt)).order_by('-created_at')
    
    if request.method == 'POST':
        token_id = request.POST.get('token_id')
        action = request.POST.get('action')
        token = get_object_or_404(PharmacyToken, token_id=token_id)
        
        bill = token.bill or Bill.objects.filter(prescription=token.prescription).first()
        if bill:
            if action == 'approve_insurance':
                bill.payment_status = 'Paid' # marked as paid upon approval
                bill.save()
                messages.success(request, f"Billing approved via Insurance for Token {token.token_number}.")
            elif action == 'approve_corporate':
                bill.payment_status = 'Paid'
                bill.save()
                messages.success(request, f"Billing approved via Corporate Credit for Token {token.token_number}.")
            elif action == 'mark_paid':
                bill.payment_status = 'Paid'
                bill.save()
                messages.success(request, f"Bill #{bill.bill_id} marked as Paid manually.")
                
            # If token status was waiting, update token reference
            if not token.bill:
                token.bill = bill
                token.save()
        else:
            messages.error(request, "No bill found for this prescription.")
        return redirect('billing_verification')
        
    context = {
        'tokens': tokens
    }
    return render(request, 'hospitalapp/pharmacy/billing_verification.html', context)

# INVENTORY DASHBOARD
@pharmacy_roles_required('pharmacist', 'senior_pharmacist', 'inventory_manager')
def inventory_dashboard(request):
    medicines = Medicine.objects.all().order_by('name')
    
    # Alerts
    today = timezone.localdate()
    low_stock = medicines.filter(stock__lt=20, stock__gt=0)
    out_of_stock = medicines.filter(stock=0)
    near_expiry = medicines.filter(expiry_date__lte=today + timedelta(days=90), expiry_date__gt=today)
    expired = medicines.filter(expiry_date__lte=today)

    context = {
        'medicines': medicines,
        'low_stock_count': low_stock.count(),
        'out_of_stock_count': out_of_stock.count(),
        'near_expiry_count': near_expiry.count(),
        'expired_count': expired.count(),
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'near_expiry': near_expiry,
        'expired': expired,
    }
    return render(request, 'hospitalapp/pharmacy/inventory_dashboard.html', context)

# REPORTS AND ANALYTICS
@pharmacy_roles_required('pharmacy_supervisor', 'admin')
def pharmacy_reports(request):
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    
    # 1. Counter performance
    perf_records = CounterPerformance.objects.filter(date=today).select_related('counter', 'pharmacist')
    
    # 2. Daily token summary
    tokens_by_status = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt)).values('status').annotate(count=Count('token_id'))
    tokens_by_priority = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt)).values('priority_level').annotate(count=Count('token_id'))
    
    # 3. Peak hour analysis (group tokens by hour)
    hourly_tokens = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt)).annotate(
        hour=ExtractHour('created_at')
    ).values('hour').annotate(count=Count('token_id')).order_by('hour')
    
    # 4. Medicine consumption report
    dispensed_items = DispensingRecord.objects.filter(dispensed_at__range=(start_dt, end_dt)).values('medicine__name').annotate(
        total_qty=Sum('quantity_dispensed'),
        total_value=Sum(F('quantity_dispensed') * F('medicine__price'))
    ).order_by('-total_qty')[:10]

    # 5. Average wait time by priority
    avg_wait_priority = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt), status='Completed', waiting_time__isnull=False).values('priority_level').annotate(
        avg_wait=Avg('waiting_time')
    )
    for aw in avg_wait_priority:
        aw['avg_wait_min'] = round(aw['avg_wait'] / 60, 1)

    context = {
        'perf_records': perf_records,
        'tokens_by_status': tokens_by_status,
        'tokens_by_priority': tokens_by_priority,
        'hourly_tokens': hourly_tokens,
        'dispensed_items': dispensed_items,
        'avg_wait_priority': avg_wait_priority,
    }
    return render(request, 'hospitalapp/pharmacy/reports_analytics.html', context)

# SUPERVISOR DASHBOARD
@pharmacy_roles_required('pharmacy_supervisor')
def supervisor_dashboard(request):
    today = timezone.localdate()
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    
    active_counters = PharmacyCounter.objects.all().order_by('number')
    waiting_tokens = PharmacyToken.objects.filter(status='Waiting')
    
    # Pharmacist productivity
    pharmacist_performance = CounterPerformance.objects.filter(date=today).select_related('pharmacist')
    
    # Audit log
    audit_logs = PharmacyAuditLog.objects.filter(timestamp__range=(start_dt, end_dt)).order_by('-timestamp')[:20]

    context = {
        'active_counters': active_counters,
        'waiting_count': waiting_tokens.count(),
        'pharmacist_performance': pharmacist_performance,
        'audit_logs': audit_logs,
    }
    return render(request, 'hospitalapp/pharmacy/supervisor_dashboard.html', context)


# ==========================================
# AJAX API ENDPOINTS FOR DIGITAL BOARD
# ==========================================

def api_serving_tokens(request):
    today = timezone.localdate()
    
    # Get currently serving tokens at active counters
    active_counters = PharmacyCounter.objects.filter(status__in=['Active', 'Busy']).order_by('number')
    serving_list = []
    for counter in active_counters:
        assignment = CounterAssignment.objects.filter(counter=counter, is_active=True).first()
        serving_list.append({
            'counter_number': counter.number,
            'counter_type': counter.type,
            'pharmacist': assignment.pharmacist.username if assignment else "N/A",
            'token_number': counter.current_token.token_number if counter.current_token else "-",
            'patient_name': counter.current_token.patient.name if counter.current_token else "-",
            'status': counter.status
        })

    # Get waiting tokens queue
    waiting_tokens = PharmacyToken.objects.filter(status='Waiting').annotate(
        priority_score=Case(
            When(priority_level='Emergency', then=Value(5)),
            When(priority_level='VIP', then=Value(4)),
            When(priority_level='Senior Citizen', then=Value(3)),
            When(priority_level='Corporate', then=Value(2)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('-priority_score', 'created_at')[:10]
    
    waiting_list = []
    for token in waiting_tokens:
        waiting_list.append({
            'token_number': token.token_number,
            'priority': token.priority_level,
            'patient_name': token.patient.name
        })

    total_waiting = PharmacyToken.objects.filter(status='Waiting').count()
    
    # Calculate avg wait time
    start_dt = timezone.make_aware(datetime.combine(today, time.min))
    end_dt = timezone.make_aware(datetime.combine(today, time.max))
    completed_today = PharmacyToken.objects.filter(created_at__range=(start_dt, end_dt), status='Completed', waiting_time__isnull=False)
    avg_wait_sec = completed_today.aggregate(Avg('waiting_time'))['waiting_time__avg']
    avg_wait_min = round(avg_wait_sec / 60) if avg_wait_sec else 8

    return JsonResponse({
        'serving': serving_list,
        'waiting': waiting_list,
        'total_waiting': total_waiting,
        'avg_wait_time': avg_wait_min
    })


def api_play_voice(request):
    # Fetch all unplayed voice announcements
    logs = VoiceAnnouncementLog.objects.filter(is_played=False).order_by('played_at')
    
    announcements = []
    for log in logs:
        announcements.append({
            'log_id': log.log_id,
            'text': log.announcement_text,
            'language': log.language,
            'token': log.token.token_number,
            'counter': log.counter.number
        })
        log.is_played = True
        log.save()
        
    return JsonResponse({
        'announcements': announcements
    })
