# Asha Hospital Management System (HMS)

Asha Hospital Management System (HMS) is a premium, feature-rich, and fully responsive Django web application designed to streamline healthcare workflows. It connects administrators, doctors, patients, receptionists, pharmacists, nurses, laboratory technicians, and radiologists in a unified collaborative portal.

---

## 🚀 Key Modules & Features

### 👤 1. Admin Portal
* **Dashboard Analytics:** Visual overview of total doctors, patients, appointments, and medicine inventory.
* **Staff Promotion & Management:** Manage profiles, delete staff, view all roles.
* **Master Configurations:** Configure Lab Test Parameters, Radiology Tests, Bed capacities, and Medicine lists.
* **Bill Audits:** Track all generated bills and mark them as paid/unpaid.

### 🩺 2. Doctor Workspace
* **My Appointments:** Manage approved and completed outpatient schedules.
* **Digital Prescriptions:** Generate diagnoses, clinical notes, and medicine orders with specific dosage and frequency.
* **Emergency/Casualty Evaluate:** Triage and admit critical cases, order emergency lab tests/radiology scans, and send critical alerts.
* **Collaborative Inpatient (IP) Care:** Access active inpatient lists, add clinical notes, suggest investigation paths, and assign nurses.
* **Referral Inbox:** Accept or reject patient referrals from other specialists.

### 👩‍⚕️ 3. Nurse & Superintendent Station
* **Head Nurse Console:** Track active shift rotations, assign nurses to patients, and monitor nursing task queues.
* **Vitals & ICU Tracker:** Log vitals (blood pressure, temperature, pulse rate, oxygen levels) and monitor live ICU patient vitals history.
* **Medication Administration:** Record medicine doses administered to inpatients.

### 🔬 4. Diagnostics (Laboratory & Radiology)
* **Lab Technician Board:** Manage collected blood/urine samples, process diagnostics in a stage-by-stage pipeline, input test results, and generate certified printable PDF reports.
* **Radiologist Workspace:** Schedule and queue scans (X-ray, MRI, CT), upload attachments, write radiology findings, and export reports.

### 💊 5. Outpatient (OP) Pharmacy
* **Multi-Counter Queuing:** Modern token queue management system (dispense tokens, call next, skip, recall, or transfer tokens).
* **Digital Queue Display:** Real-time dashboard showing current active tokens and counters.
* **Stock Control:** Edit stock, verify billing status, and dispense prescribed items.

### 📞 6. Receptionist Desk
* **Quick Registration:** Register patients, generate patient ID cards, download printable ID card PDFs (CR80 standard with barcodes).
* **Admissions & Bed Management:** Admit emergency/specialist referred patients and allocate hospital beds.
* **IP billing & Discharge:** Process final discharge summaries, apply discounts, and clear bills.
* **Ambulance & Services Log:** Track ambulance dispatch logs, visitor logs, laundry schedules, and cleaning entries.

### 🩹 7. Patient Portal
* **Outpatient Bookings:** Request doctor consultations and view history.
* **My Records:** Read prescriptions, view certified Lab Results, Radiology Results, and unpaid bills.

---

## 🛠️ Technology Stack
* **Core Backend:** Python, Django 6.0
* **Frontend UI:** HTML5, CSS3 (Vanilla), Bootstrap 5, Font Awesome Icons
* **Database:** MySQL (recommended for production) / SQLite3 (automatic local fallback)
* **API Integrations:** Razorpay Payment Gateway (SDK), n8n webhooks
* **Reporting:** ReportLab (PDF Generation)

---

## 🔒 Security & Environment Setup
All sensitive credentials, API keys, and database passwords are kept secure and out of version control. 

1. **`.env` file:** Handled locally for environment configuration (this file is ignored by git).
2. **`.env.example` file:** Provided as a template to fill in configuration variables for deployment.

---

## ⚙️ Installation & Running Locally

Follow these steps to set up and run the website on your local machine:

### 1. Clone the Project
```bash
git clone <your-repository-url>
cd hospitalproject
```

### 2. Set Up Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# (Make sure to install django, mysqlclient, razorpay, reportlab, and requests)
```

### 4. Configure Environment Variables
1. Copy the sample file:
   * **Windows (PowerShell):** `Copy-Item .env.example .env`
   * **Linux/macOS/Git Bash:** `cp .env.example .env`
2. Open `.env` and fill in your actual credentials (database, Razorpay keys, webhook URLs).

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

---

## 📂 Project Structure
```text
hospitalproject/
├── hospitalproject/        # Django main settings and project configuration
│   ├── settings.py         # Configured to load environment variables from .env
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── hospitalapp/            # Main application containing views, models, and forms
│   ├── templates/          # Responsive templates for all modules
│   ├── static/             # CSS, JavaScript, and asset library
│   ├── models.py           # Database schema designs for HMS
│   ├── views.py            # Main business logic
│   └── urls.py             # App-level routing
├── .env                    # Local environment secrets (IGNORED BY GIT)
├── .env.example            # Environment template for GitHub
├── .gitignore              # Files to ignore in Git repository
└── README.md               # Project documentation
```
