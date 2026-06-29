"""
Seed script: populates LabTest + LabTestParameter records
and RadiologyTest records for Asha Hospital HMS.

Run from the hospitalproject directory:
    python seed_lab_radiology.py
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospitalproject.settings')
django.setup()

from hospitalapp.models import LabTest, LabTestParameter, RadiologyTest

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def get_or_create_test(name, price, category='General', normal_range=''):
    test, created = LabTest.objects.get_or_create(
        name=name,
        defaults={'price': price, 'category': category, 'normal_range': normal_range}
    )
    if created:
        print(f'  [+] LabTest: {name}')
    else:
        print(f'  [=] LabTest exists: {name}')
    return test


def add_param(test, name, unit, ref, male_min=None, male_max=None,
              female_min=None, female_max=None, min_v=None, max_v=None,
              crit_min=None, crit_max=None):
    p, created = LabTestParameter.objects.get_or_create(
        test=test,
        name=name,
        defaults=dict(
            unit=unit,
            reference_range=ref,
            min_value=min_v,
            max_value=max_v,
            male_min=male_min,
            male_max=male_max,
            female_min=female_min,
            female_max=female_max,
            critical_min=crit_min,
            critical_max=crit_max,
        )
    )
    if created:
        print(f'      -> Param: {name}')


# ---------------------------------------------
# 1. Complete Blood Count (CBC)
# ---------------------------------------------
print('\n[CBC]')
cbc = get_or_create_test('Complete Blood Count (CBC)', 250, 'Full blood picture including WBC differential')
add_param(cbc, 'Hemoglobin (Hb)', 'g/dL', '13–17 (M), 12–15 (F)',
          male_min=13, male_max=17, female_min=12, female_max=15, crit_min=7, crit_max=20)
add_param(cbc, 'Total WBC Count', '/µL', '4000–11000',
          min_v=4000, max_v=11000, crit_min=2000, crit_max=30000)
add_param(cbc, 'Platelet Count', 'lakh/µL', '1.5–4.5',
          min_v=1.5, max_v=4.5, crit_min=0.5, crit_max=10)
add_param(cbc, 'RBC Count', 'million/µL', '4.5–5.9 (M), 3.8–5.2 (F)',
          male_min=4.5, male_max=5.9, female_min=3.8, female_max=5.2)
add_param(cbc, 'Hematocrit (PCV)', '%', '40–50 (M), 36–46 (F)',
          male_min=40, male_max=50, female_min=36, female_max=46)
add_param(cbc, 'MCV', 'fL', '80–100', min_v=80, max_v=100)
add_param(cbc, 'MCH', 'pg', '27–33', min_v=27, max_v=33)
add_param(cbc, 'MCHC', 'g/dL', '32–36', min_v=32, max_v=36)
add_param(cbc, 'Neutrophils', '%', '40–70', min_v=40, max_v=70)
add_param(cbc, 'Lymphocytes', '%', '20–40', min_v=20, max_v=40)
add_param(cbc, 'Monocytes', '%', '2–8', min_v=2, max_v=8)
add_param(cbc, 'Eosinophils', '%', '1–6', min_v=1, max_v=6)
add_param(cbc, 'Basophils', '%', '0–1', min_v=0, max_v=1)
add_param(cbc, 'ESR', 'mm/hr', '0–20 (M), 0–30 (F)',
          male_min=0, male_max=20, female_min=0, female_max=30)

# ─────────────────────────────────────────────
# 2. Lipid Profile
# ─────────────────────────────────────────────
print('\n[Lipid Profile]')
lip = get_or_create_test('Lipid Profile', 450, 'Comprehensive cardiovascular risk assessment')
add_param(lip, 'Total Cholesterol', 'mg/dL', '< 200', max_v=200, crit_max=400)
add_param(lip, 'Triglycerides (TG)', 'mg/dL', '< 150', max_v=150, crit_max=500)
add_param(lip, 'HDL Cholesterol', 'mg/dL', '> 40 (M), > 50 (F)',
          male_min=40, female_min=50)
add_param(lip, 'LDL Cholesterol', 'mg/dL', '< 100', max_v=100, crit_max=190)
add_param(lip, 'VLDL Cholesterol', 'mg/dL', '5–40', min_v=5, max_v=40)
add_param(lip, 'Cholesterol/HDL Ratio', '', '< 5', max_v=5)

# ─────────────────────────────────────────────
# 3. Thyroid Profile
# ─────────────────────────────────────────────
print('\n[Thyroid Profile]')
thy = get_or_create_test('Thyroid Profile (T3, T4, TSH)', 600, 'Complete thyroid function assessment')
add_param(thy, 'T3 (Triiodothyronine)', 'ng/mL', '0.8–2.0', min_v=0.8, max_v=2.0)
add_param(thy, 'T4 (Thyroxine)', 'µg/dL', '5.0–12.0', min_v=5.0, max_v=12.0)
add_param(thy, 'TSH (Thyroid Stimulating Hormone)', 'µIU/mL', '0.4–4.5',
          min_v=0.4, max_v=4.5, crit_min=0.01, crit_max=100)

# ─────────────────────────────────────────────
# 4. Liver Function Test (LFT)
# ─────────────────────────────────────────────
print('\n[LFT]')
lft = get_or_create_test('Liver Function Test (LFT)', 500, 'Assessment of liver enzymes and function')
add_param(lft, 'Total Bilirubin', 'mg/dL', '0.3–1.2', min_v=0.3, max_v=1.2, crit_max=15)
add_param(lft, 'Direct Bilirubin', 'mg/dL', '0.0–0.3', min_v=0, max_v=0.3)
add_param(lft, 'Indirect Bilirubin', 'mg/dL', '0.2–0.9', min_v=0.2, max_v=0.9)
add_param(lft, 'SGOT (AST)', 'U/L', '10–40', min_v=10, max_v=40, crit_max=1000)
add_param(lft, 'SGPT (ALT)', 'U/L', '7–56', min_v=7, max_v=56, crit_max=1000)
add_param(lft, 'Alkaline Phosphatase (ALP)', 'U/L', '44–147', min_v=44, max_v=147)
add_param(lft, 'Total Protein', 'g/dL', '6.0–8.3', min_v=6.0, max_v=8.3)
add_param(lft, 'Albumin', 'g/dL', '3.5–5.0', min_v=3.5, max_v=5.0, crit_min=2.0)
add_param(lft, 'Globulin', 'g/dL', '2.0–3.5', min_v=2.0, max_v=3.5)
add_param(lft, 'A/G Ratio', '', '1.0–2.2', min_v=1.0, max_v=2.2)

# ─────────────────────────────────────────────
# 5. Kidney Function Test (KFT)
# ─────────────────────────────────────────────
print('\n[KFT]')
kft = get_or_create_test('Kidney Function Test (KFT)', 500, 'Assessment of renal function')
add_param(kft, 'Blood Urea', 'mg/dL', '15–40', min_v=15, max_v=40, crit_max=200)
add_param(kft, 'Serum Creatinine', 'mg/dL', '0.6–1.3', min_v=0.6, max_v=1.3, crit_max=10)
add_param(kft, 'Uric Acid', 'mg/dL', '3.5–7.2', min_v=3.5, max_v=7.2)
add_param(kft, 'Sodium (Na+)', 'mEq/L', '135–145', min_v=135, max_v=145, crit_min=120, crit_max=160)
add_param(kft, 'Potassium (K+)', 'mEq/L', '3.5–5.0', min_v=3.5, max_v=5.0, crit_min=2.5, crit_max=6.5)
add_param(kft, 'Chloride (Cl-)', 'mEq/L', '98–107', min_v=98, max_v=107)
add_param(kft, 'Calcium', 'mg/dL', '8.5–10.5', min_v=8.5, max_v=10.5, crit_min=6.0, crit_max=13.0)
add_param(kft, 'eGFR', 'mL/min/1.73m²', '> 90', min_v=90)

# ─────────────────────────────────────────────
# 6. HbA1c
# ─────────────────────────────────────────────
print('\n[HbA1c]')
hba1c = get_or_create_test('HbA1c (Glycated Hemoglobin)', 400, 'Long-term blood sugar control indicator')
add_param(hba1c, 'HbA1c', '%', '< 5.7 (Normal), 5.7–6.4 (Pre-diabetic), ≥ 6.5 (Diabetic)',
          max_v=5.7, crit_max=10)

# ─────────────────────────────────────────────
# 7. Blood Sugar
# ─────────────────────────────────────────────
print('\n[Blood Sugar]')
bsg = get_or_create_test('Blood Sugar (FBS & PPBS)', 150, 'Fasting and post-prandial glucose levels')
add_param(bsg, 'Fasting Blood Sugar (FBS)', 'mg/dL', '70–99', min_v=70, max_v=99,
          crit_min=40, crit_max=500)
add_param(bsg, 'Post-Prandial Blood Sugar (PPBS)', 'mg/dL', '< 140', max_v=140, crit_max=500)

# ─────────────────────────────────────────────
# 8. CRP
# ─────────────────────────────────────────────
print('\n[CRP]')
crp = get_or_create_test('C-Reactive Protein (CRP)', 300, 'Inflammation marker')
add_param(crp, 'CRP (Quantitative)', 'mg/L', '< 10', max_v=10, crit_max=200)

# ─────────────────────────────────────────────
# 9. Dengue Profile
# ─────────────────────────────────────────────
print('\n[Dengue]')
dengue = get_or_create_test('Dengue Profile (NS1 + IgM + IgG)', 800, 'Dengue antigen and antibody screen')
add_param(dengue, 'NS1 Antigen', '', 'Negative', )
add_param(dengue, 'IgM Antibody', '', 'Negative')
add_param(dengue, 'IgG Antibody', '', 'Negative')

# ─────────────────────────────────────────────
# 10. Malaria Test
# ─────────────────────────────────────────────
print('\n[Malaria]')
malaria = get_or_create_test('Malaria Antigen Test (RDT)', 200, 'Rapid malaria antigen detection')
add_param(malaria, 'P. falciparum Antigen', '', 'Negative')
add_param(malaria, 'P. vivax Antigen', '', 'Negative')

# ─────────────────────────────────────────────
# 11. Urine Routine
# ─────────────────────────────────────────────
print('\n[Urine Routine]')
urine = get_or_create_test('Urine Routine Examination', 100, 'Complete urine analysis')
add_param(urine, 'Colour', '', 'Pale Yellow')
add_param(urine, 'Appearance', '', 'Clear')
add_param(urine, 'pH', '', '4.5–8.0', min_v=4.5, max_v=8.0)
add_param(urine, 'Specific Gravity', '', '1.005–1.030', min_v=1.005, max_v=1.030)
add_param(urine, 'Protein', 'mg/dL', 'Nil/Negative')
add_param(urine, 'Glucose', 'mg/dL', 'Nil/Negative')
add_param(urine, 'Pus Cells (WBC)', '/HPF', '0–5')
add_param(urine, 'RBC', '/HPF', 'Nil')
add_param(urine, 'Epithelial Cells', '/HPF', 'Few')
add_param(urine, 'Casts', '', 'Absent')
add_param(urine, 'Crystals', '', 'Absent')
add_param(urine, 'Bacteria', '', 'Absent')

# ─────────────────────────────────────────────
# 12. Blood Group & Rh Typing
# ─────────────────────────────────────────────
print('\n[Blood Group]')
bg = get_or_create_test('Blood Group & Rh Typing', 100, 'ABO and Rh blood group determination')
add_param(bg, 'Blood Group (ABO)', '', 'A / B / AB / O')
add_param(bg, 'Rh Factor', '', 'Positive / Negative')

# ─────────────────────────────────────────────
# 13. Coagulation Profile
# ─────────────────────────────────────────────
print('\n[Coagulation Profile]')
coag = get_or_create_test('Coagulation Profile (PT/INR/APTT)', 600, 'Clotting ability assessment')
add_param(coag, 'Prothrombin Time (PT)', 'seconds', '11–14', min_v=11, max_v=14, crit_max=30)
add_param(coag, 'INR', '', '0.9–1.2', min_v=0.9, max_v=1.2, crit_max=4)
add_param(coag, 'APTT', 'seconds', '26–40', min_v=26, max_v=40, crit_max=90)
add_param(coag, 'Thrombin Time (TT)', 'seconds', '12–18', min_v=12, max_v=18)
add_param(coag, 'Bleeding Time', 'minutes', '2–7', min_v=2, max_v=7)
add_param(coag, 'Clotting Time', 'minutes', '5–11', min_v=5, max_v=11)

# ─────────────────────────────────────────────
# 14. ESR (standalone)
# ─────────────────────────────────────────────
print('\n[ESR]')
esr = get_or_create_test('ESR (Erythrocyte Sedimentation Rate)', 80, 'Non-specific inflammation marker')
add_param(esr, 'ESR (Westergren)', 'mm/hr', '0–20 (M), 0–30 (F)',
          male_min=0, male_max=20, female_min=0, female_max=30)

# ─────────────────────────────────────────────
# RADIOLOGY TESTS
# ─────────────────────────────────────────────
print('\n\n=== RADIOLOGY TESTS ===')

radiology_tests = [
    ('X-Ray Chest (PA View)', 300, 'Posterior-anterior chest radiograph'),
    ('X-Ray Skull (AP & Lateral)', 350, 'Skull plain radiograph'),
    ('X-Ray Spine (Cervical/Lumbar)', 400, 'Spinal plain radiograph'),
    ('X-Ray Pelvis & Hip', 350, 'Pelvic radiograph'),
    ('X-Ray Extremities', 300, 'Limbs and joints radiograph'),
    ('Ultrasound Abdomen & Pelvis', 800, 'Soft tissue abdominal and pelvic evaluation'),
    ('Ultrasound Whole Abdomen', 1000, 'Complete abdominal ultrasound'),
    ('Ultrasound Obstetric (OB)', 900, 'Pregnancy dating and fetal wellbeing scan'),
    ('Ultrasound Neck & Thyroid', 700, 'Neck mass and thyroid nodule evaluation'),
    ('CT Scan Brain (Plain)', 2500, 'Brain CT without contrast'),
    ('CT Scan Brain (With Contrast)', 3500, 'Brain CT with IV contrast'),
    ('CT Scan Chest (HRCT)', 3000, 'High-resolution chest CT'),
    ('CT Scan Abdomen & Pelvis', 4000, 'Abdominal and pelvic CT with contrast'),
    ('MRI Brain (Plain)', 5000, 'Brain MRI without contrast'),
    ('MRI Brain (With Contrast)', 6500, 'Brain MRI with gadolinium contrast'),
    ('MRI Spine (Cervical/Lumbar)', 5500, 'Spinal cord and disc evaluation'),
    ('MRI Knee / Shoulder / Joints', 5000, 'Musculoskeletal MRI evaluation'),
    ('ECG (12-lead)', 150, '12-lead resting electrocardiogram'),
    ('2D ECHO (Echocardiography)', 2000, 'Cardiac structure and function assessment'),
    ('Doppler Study (Venous/Arterial)', 1500, 'Blood flow assessment using Doppler'),
    ('Mammography (Bilateral)', 1500, 'Bilateral breast screening'),
    ('OPG (Panoramic Dental X-Ray)', 500, 'Full dental panoramic radiograph'),
    ('Bone Densitometry (DEXA Scan)', 1800, 'Bone mineral density measurement'),
    ('PET-CT Scan', 18000, 'Combined metabolic and anatomic imaging'),
]

for name, price, desc in radiology_tests:
    obj, created = RadiologyTest.objects.get_or_create(
        name=name,
        defaults={'price': price, 'description': desc, 'active': True}
    )
    status = '[+]' if created else '[=]'
    print(f'  {status} RadiologyTest: {name}')

print('\n[+] Seeding complete!')
