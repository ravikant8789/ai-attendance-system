# 🏢 AI Biometric Attendance System

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![OpenCV / Dlib](https://img.shields.io/badge/Biometrics-Dlib%20%7C%20Resemblyzer-informational?style=for-the-badge)](https://github.com/davisking/dlib)

An enterprise-grade, contactless **AI-Powered Biometric Attendance & Workplace Management System** built with **Python**, **Streamlit**, and **Supabase (PostgreSQL)**. Features real-time facial recognition, voice biometric check-ins, multi-employee reception kiosk scanning, and automated HR timesheet reporting.

---

## 🌟 Key Features

### 👤 1. Employee Portal
- **Facial Recognition Punch**: Clock In using device camera powered by high-dimensional deep face embeddings (`dlib` 128D representation).
- **Voice Biometric Punch**: Alternative voice verification powered by `Resemblyzer` speaker embeddings.
- **Daily Clock-In / Clock-Out**: Accurate tracking with live punch status (`🟢 Clocked In: HH:MM` | `🔴 Clocked Out: HH:MM`).
- **Personal Timesheets**: Visual breakdown of attendance rates, total logged days, and department memberships.
- **Biometric Registration**: Seamless single-click onboarding to register face and voice profiles.

### 💼 2. HR & Admin Portal
- **Reception Entrance Kiosk**: Scan multi-person entrance photos to automatically identify and mark attendance for multiple staff members in one shot.
- **Department & Shift Management**: Create departments, assign shifts/teams, generate department codes, and manage staff rosters.
- **Employee Roster & Search**: Search employees by name or ID, review attendance percentages, and manage team allocation.
- **Live Timesheet & Records**:
  - Detailed daily check-in and checkout timestamps.
  - Live duty status indicator (`⏳ On Duty` vs `Clocked Out`).
  - One-click CSV export (`employee_timesheet_<date>.csv`) for payroll processing.

### 🛡️ 3. Robust Data & Architecture
- **Idempotent Punching**: Prevents duplicate attendance logging within the same calendar day.
- **PostgreSQL Database on Supabase**: Relational integrity with cascading foreign keys and secure connection retries.
- **Password Security**: Strong `bcrypt` password hashing for HR management accounts.

---

## 🛠️ Tech Stack & Libraries

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend & UI** | Streamlit | Modern reactive single-page web app |
| **Backend & Pipeline** | Python 3.11 | Core business logic & biometric inference |
| **Face Biometrics** | `dlib`, `face_recognition_models` | 68-landmark face detection & 128D embeddings |
| **Voice Biometrics** | `resemblyzer`, `librosa` | Deep voice embeddings & cosine similarity |
| **Database** | Supabase (PostgreSQL) | Cloud relational database & secure storage |
| **Security** | `bcrypt` | Salted password hashing for HR accounts |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or 3.11 installed
- A free account on [Supabase](https://supabase.com)
- Webcam and microphone enabled for biometric capture

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/ai-attendance-project-app.git
cd ai-attendance-project-app
```

### 2. Set Up a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip setuptools<70.0.0
pip install -r requirements.txt
```

> **Note for Windows Users**: `dlib-bin` in `requirements.txt` provides pre-compiled Windows wheels without requiring Visual Studio C++ build tools.

### 4. Configure Supabase Database
1. Go to your [Supabase Dashboard](https://supabase.com/dashboard) and create a new project.
2. Open the **SQL Editor** in your Supabase dashboard.
3. Paste and run the contents of [`supabase_schema.sql`](file:///c:/Users/devik/Documents/project/ai-attendance-project-app-main/supabase_schema.sql).
4. Copy your **Project URL** and **Anon API Key** from **Project Settings -> API**.

### 5. Add Secrets Configuration
Create `.streamlit/secrets.toml` from the provided example:
```bash
# Copy example template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your credentials:
```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-supabase-anon-or-service-key"
```

---

## 💻 Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```
Open your browser and navigate to:
```
http://localhost:8501
```

---

## 📁 Project Structure

```text
ai-attendance-project-app/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example         # Template for Supabase credentials
├── src/
│   ├── assets/                      # Logos, mascots, branding
│   ├── components/                  # Reusable UI components & dialogs
│   │   ├── department_card.py
│   │   ├── dialog_add_photo.py
│   │   ├── dialog_attendance_results.py
│   │   ├── dialog_create_department.py
│   │   ├── dialog_view_department_staff.py
│   │   ├── dialog_voice_attendance.py
│   │   ├── header.py
│   │   └── footer.py
│   ├── database/                    # Database connections & operations
│   │   ├── config.py                # Supabase client setup
│   │   └── db.py                    # CRUD queries, retries & cascades
│   ├── pipelines/                   # Biometric inference pipelines
│   │   ├── face_pipeline.py         # Face embeddings & matching
│   │   └── voice_pipeline.py        # Voice embeddings & comparison
│   ├── screens/                     # Main user views
│   │   ├── home_screen.py           # Landing & role selection
│   │   ├── hr_screen.py             # HR Kiosk & Department Dashboard
│   │   └── employee_screen.py       # Employee Clock In / Out & Timesheets
│   └── ui/
│       └── base_layout.py           # CSS styles & theme injection
├── app.py                           # App entry point
├── requirements.txt                 # Python dependencies
├── supabase_schema.sql              # Supabase database schema setup
├── .gitignore                       # Git exclusions (credentials, venv, caches)
└── README.md                        # Documentation
```

---

## 👨‍💻 Author

Created with ❤️ by **Ravikant Kumar**

---

## 📄 License
This project is licensed under the MIT License.
