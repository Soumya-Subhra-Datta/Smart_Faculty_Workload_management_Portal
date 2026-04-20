# 🎓 Faculty Workload Scheduling & Substitution Portal

> AI-Powered workload management system for Sathyabama Institute of Science and Technology

## ⚡ Quick Start

### Prerequisites
- **Python 3.8+**
- **MySQL 8.0+** running locally
- **pip** (Python package manager)

### 1. Install Dependencies
```bash
cd faculty-workload-portal
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file with your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=faculty_workload_db
JWT_SECRET_KEY=change-this-in-production
FLASK_PORT=5000
```

### 3. Setup Database
```bash
python database_setup.py
```
This creates the database, tables, and populates sample data (37 faculty across 6 departments).

### 4. Start the Server
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

---

## 🔑 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Faculty (any) | `cse_priya` | `faculty123` |

All faculty accounts use password `faculty123`.

---

## 🏗️ Architecture

```
Backend:  Python Flask + MySQL + JWT Authentication
Frontend: Vanilla HTML/CSS/JS (Single Page Application)
AI:       Scoring-based substitution engine
Scheduler: APScheduler (auto-completes past duties)
```

### AI Substitution Scoring
| Factor | Score |
|--------|-------|
| Subject expertise match | +10 |
| Workload balancing | +0 to +5 (fewer subs = higher) |
| Same department | +3 |
| Available (fallback) | +1 |

---

## 📡 API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/me` | Get current user |

### Admin Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Dashboard stats |
| GET/POST | `/api/admin/faculty` | List/Add faculty |
| PUT/DELETE | `/api/admin/faculty/:id` | Update/Delete faculty |
| GET/POST | `/api/admin/duties` | List/Create duties |
| PUT | `/api/admin/duties/:id/cancel` | Cancel a duty |
| POST | `/api/admin/duties/upload-csv` | Bulk CSV upload |
| GET | `/api/admin/substitutions` | All substitutions |

### Faculty Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faculty/timetable` | My timetable |
| GET | `/api/faculty/duties` | My duties |
| GET | `/api/faculty/substitutions` | My substitutions |
| GET | `/api/faculty/notifications` | Notifications |
| PUT | `/api/faculty/notifications/:id/read` | Mark read |
| PUT | `/api/faculty/notifications/read-all` | Mark all read |
| DELETE | `/api/faculty/notifications/clear` | Clear history |

### CSV Format
```csv
event_name,description,date,start_time,end_time,venue,faculty_username
NAAC Inspection,Accreditation visit,2025-04-20,09:00,12:00,Main Auditorium,cse_priya
```

---

## 🔧 Project Structure

```
faculty-workload-portal/
├── app.py                 # Flask entry point
├── config.py              # Environment config
├── database_setup.py      # DB setup & sample data
├── models/                # Data access layer
│   ├── db.py             # Connection pool
│   ├── user.py           # User CRUD
│   ├── timetable.py      # Timetable queries
│   ├── event.py          # Duty/event CRUD
│   ├── substitution.py   # Substitution CRUD
│   └── notification.py   # Notification CRUD
├── routes/                # API routes
│   ├── auth.py           # Login/auth
│   ├── admin.py          # Admin endpoints
│   └── faculty.py        # Faculty endpoints
├── services/              # Business logic
│   ├── substitution_engine.py  # AI scoring engine
│   ├── scheduler.py            # Auto-completion
│   └── csv_handler.py          # CSV parsing
├── templates/
│   └── index.html        # SPA shell
└── static/
    ├── css/style.css      # Dark theme UI
    └── js/
        ├── app.js         # Router & utilities
        ├── auth.js        # Login handler
        ├── admin.js       # Admin views
        └── faculty.js     # Faculty views
```
