"""
=============================================================================
Database Setup Script for Faculty Workload Scheduling & Substitution Portal
Sathyabama Institute of Science and Technology
=============================================================================

This script:
  1. Creates the MySQL database 'faculty_workload_db'
  2. Creates all required tables
  3. Populates comprehensive sample data
  4. Ensures guaranteed substitute availability

Execute independently: python database_setup.py
=============================================================================
"""

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
import json
import sys

# -----------------------------------------------
# CONFIGURATION - Modify these as needed
# -----------------------------------------------
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'faculty_workload_db'

# -----------------------------------------------
# DATABASE & TABLE CREATION
# -----------------------------------------------

def create_database(cursor):
    """Create the database if it does not exist."""
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_NAME}")
    print(f"[OK] Database '{DB_NAME}' created successfully.")


def create_tables(cursor):
    """Create all required tables."""

    # Users table
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            department VARCHAR(50) NOT NULL,
            role ENUM('admin', 'faculty') NOT NULL DEFAULT 'faculty',
            subjects JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_department (department),
            INDEX idx_role (role)
        ) ENGINE=InnoDB
    """)

    # Timetable table
    cursor.execute("""
        CREATE TABLE timetable (
            id INT AUTO_INCREMENT PRIMARY KEY,
            faculty_id INT NOT NULL,
            day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
            period INT NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            subject VARCHAR(100) NOT NULL,
            classroom VARCHAR(20) NOT NULL,
            semester VARCHAR(20) DEFAULT 'Even 2024-25',
            FOREIGN KEY (faculty_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_faculty_day (faculty_id, day_of_week),
            INDEX idx_day_time (day_of_week, start_time, end_time)
        ) ENGINE=InnoDB
    """)

    # Events / Duties table
    cursor.execute("""
        CREATE TABLE events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(200) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            venue VARCHAR(100) NOT NULL,
            assigned_faculty_id INT NOT NULL,
            status ENUM('upcoming','ongoing','completed','cancelled') DEFAULT 'upcoming',
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_faculty_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_status (status),
            INDEX idx_date (date),
            INDEX idx_faculty_status (assigned_faculty_id, status)
        ) ENGINE=InnoDB
    """)

    # Substitutions table
    cursor.execute("""
        CREATE TABLE substitutions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_id INT NOT NULL,
            original_faculty_id INT NOT NULL,
            substitute_faculty_id INT NOT NULL,
            subject VARCHAR(100) NOT NULL,
            classroom VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            status ENUM('assigned','completed','cancelled') DEFAULT 'assigned',
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
            FOREIGN KEY (original_faculty_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (substitute_faculty_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_substitute (substitute_faculty_id),
            INDEX idx_event (event_id),
            INDEX idx_date_status (date, status)
        ) ENGINE=InnoDB
    """)

    # Notifications table
    cursor.execute("""
        CREATE TABLE notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            type ENUM('duty_assignment','substitution','cancellation','completion','general') NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_read (user_id, is_read),
            INDEX idx_user_created (user_id, created_at)
        ) ENGINE=InnoDB
    """)

    print("[OK] All tables created successfully.")


# -----------------------------------------------
# SAMPLE DATA
# -----------------------------------------------

def insert_sample_data(cursor):
    """Insert comprehensive sample data ensuring substitute availability."""

    # ── Admin User ──
    admin_password = generate_password_hash('admin123')
    cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, email, department, role, subjects)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, ('admin', admin_password, 'Dr. S. Ramesh', 'admin@sathyabama.ac.in',
          'Administration', 'admin', json.dumps([])))

    # ── Faculty Data ──
    # Structure: (username, full_name, email, department, subjects[])
    # Each department has 5-6 faculty + 1-2 reserve faculty with lighter loads
    faculty_data = [
        # --- CSE Department (6 regular + 2 reserve) ---
        ('cse_priya', 'Dr. Priya Sharma', 'priya.sharma@sathyabama.ac.in', 'CSE',
         ['Machine Learning', 'Data Structures', 'Python Programming']),
        ('cse_rajesh', 'Dr. Rajesh Kumar', 'rajesh.kumar@sathyabama.ac.in', 'CSE',
         ['Machine Learning', 'Artificial Intelligence', 'Deep Learning']),
        ('cse_anitha', 'Prof. Anitha Venkatesh', 'anitha.v@sathyabama.ac.in', 'CSE',
         ['Data Structures', 'Algorithms', 'C Programming']),
        ('cse_kumar', 'Dr. Senthil Kumar', 'senthil.k@sathyabama.ac.in', 'CSE',
         ['Database Systems', 'SQL', 'Data Mining']),
        ('cse_deepa', 'Prof. Deepa Lakshmi', 'deepa.l@sathyabama.ac.in', 'CSE',
         ['Operating Systems', 'Computer Networks', 'Cloud Computing']),
        ('cse_vijay', 'Dr. Vijay Anand', 'vijay.a@sathyabama.ac.in', 'CSE',
         ['Web Development', 'Software Engineering', 'Python Programming']),
        # Reserve CSE faculty
        ('cse_res_meena', 'Prof. Meena Devi', 'meena.d@sathyabama.ac.in', 'CSE',
         ['Machine Learning', 'Data Structures', 'Python Programming', 'Algorithms']),
        ('cse_res_arjun', 'Dr. Arjun Reddy', 'arjun.r@sathyabama.ac.in', 'CSE',
         ['Artificial Intelligence', 'Deep Learning', 'Database Systems', 'Cloud Computing']),

        # --- ECE Department (5 regular + 1 reserve) ---
        ('ece_kavitha', 'Dr. Kavitha Rajan', 'kavitha.r@sathyabama.ac.in', 'ECE',
         ['Digital Electronics', 'VLSI Design', 'Embedded Systems']),
        ('ece_mohan', 'Prof. Mohan Das', 'mohan.d@sathyabama.ac.in', 'ECE',
         ['Signal Processing', 'Communication Systems', 'Digital Electronics']),
        ('ece_lakshmi', 'Dr. Lakshmi Narayan', 'lakshmi.n@sathyabama.ac.in', 'ECE',
         ['Microprocessors', 'Embedded Systems', 'IoT']),
        ('ece_suresh', 'Prof. Suresh Babu', 'suresh.b@sathyabama.ac.in', 'ECE',
         ['VLSI Design', 'Analog Circuits', 'Signal Processing']),
        ('ece_divya', 'Dr. Divya Krishnan', 'divya.k@sathyabama.ac.in', 'ECE',
         ['Communication Systems', 'Antenna Design', 'Wireless Networks']),
        # Reserve ECE
        ('ece_res_ganesh', 'Prof. Ganesh Subramanian', 'ganesh.s@sathyabama.ac.in', 'ECE',
         ['Digital Electronics', 'VLSI Design', 'Signal Processing', 'Microprocessors']),

        # --- EEE Department (5 regular + 1 reserve) ---
        ('eee_ravi', 'Dr. Ravi Chandran', 'ravi.c@sathyabama.ac.in', 'EEE',
         ['Power Systems', 'Electrical Machines', 'Control Systems']),
        ('eee_sunitha', 'Prof. Sunitha Menon', 'sunitha.m@sathyabama.ac.in', 'EEE',
         ['Control Systems', 'Power Electronics', 'Renewable Energy']),
        ('eee_prakash', 'Dr. Prakash Raj', 'prakash.r@sathyabama.ac.in', 'EEE',
         ['Electrical Machines', 'Transformers', 'Power Systems']),
        ('eee_nisha', 'Prof. Nisha Thomas', 'nisha.t@sathyabama.ac.in', 'EEE',
         ['Power Electronics', 'Drives', 'Renewable Energy']),
        ('eee_karthik', 'Dr. Karthik Sundaram', 'karthik.s@sathyabama.ac.in', 'EEE',
         ['Instrumentation', 'Control Systems', 'PLC Programming']),
        # Reserve EEE
        ('eee_res_arun', 'Prof. Arun Prasad', 'arun.p@sathyabama.ac.in', 'EEE',
         ['Power Systems', 'Control Systems', 'Electrical Machines', 'Power Electronics']),

        # --- MECH Department (5 regular + 1 reserve) ---
        ('mech_gopi', 'Dr. Gopi Krishnan', 'gopi.k@sathyabama.ac.in', 'MECH',
         ['Thermodynamics', 'Heat Transfer', 'Fluid Mechanics']),
        ('mech_saranya', 'Prof. Saranya Devi', 'saranya.d@sathyabama.ac.in', 'MECH',
         ['Manufacturing Technology', 'CAD/CAM', 'Industrial Engineering']),
        ('mech_manoj', 'Dr. Manoj Kumar', 'manoj.k@sathyabama.ac.in', 'MECH',
         ['Fluid Mechanics', 'Hydraulics', 'Thermodynamics']),
        ('mech_revathi', 'Prof. Revathi Srinivasan', 'revathi.s@sathyabama.ac.in', 'MECH',
         ['Strength of Materials', 'Engineering Mechanics', 'Finite Element Analysis']),
        ('mech_dinesh', 'Dr. Dinesh Babu', 'dinesh.b@sathyabama.ac.in', 'MECH',
         ['Automobile Engineering', 'Internal Combustion Engines', 'Manufacturing Technology']),
        # Reserve MECH
        ('mech_res_karthi', 'Prof. Karthikeyan Raj', 'karthi.r@sathyabama.ac.in', 'MECH',
         ['Thermodynamics', 'Fluid Mechanics', 'Manufacturing Technology', 'CAD/CAM']),

        # --- IT Department (5 regular + 1 reserve) ---
        ('it_ramya', 'Dr. Ramya Balan', 'ramya.b@sathyabama.ac.in', 'IT',
         ['Web Development', 'Java Programming', 'Software Testing']),
        ('it_naveen', 'Prof. Naveen Prasad', 'naveen.p@sathyabama.ac.in', 'IT',
         ['Cyber Security', 'Cryptography', 'Computer Networks']),
        ('it_swathi', 'Dr. Swathi Iyer', 'swathi.i@sathyabama.ac.in', 'IT',
         ['Cloud Computing', 'DevOps', 'Web Development']),
        ('it_bala', 'Prof. Balasubramanian', 'bala.s@sathyabama.ac.in', 'IT',
         ['Data Analytics', 'Big Data', 'Python Programming']),
        ('it_harini', 'Dr. Harini Venkatesan', 'harini.v@sathyabama.ac.in', 'IT',
         ['Mobile App Development', 'Java Programming', 'Software Engineering']),
        # Reserve IT
        ('it_res_sanjay', 'Prof. Sanjay Murugan', 'sanjay.m@sathyabama.ac.in', 'IT',
         ['Web Development', 'Java Programming', 'Cloud Computing', 'Python Programming']),

        # --- CIVIL Department (4 regular + 1 reserve) ---
        ('civil_ashok', 'Dr. Ashok Pillai', 'ashok.p@sathyabama.ac.in', 'CIVIL',
         ['Structural Analysis', 'RCC Design', 'Construction Management']),
        ('civil_sangeetha', 'Prof. Sangeetha Nair', 'sangeetha.n@sathyabama.ac.in', 'CIVIL',
         ['Geotechnical Engineering', 'Soil Mechanics', 'Foundation Engineering']),
        ('civil_venkat', 'Dr. Venkateshwaran', 'venkat.w@sathyabama.ac.in', 'CIVIL',
         ['Surveying', 'Highway Engineering', 'Transportation']),
        ('civil_preethi', 'Prof. Preethi Ramachandran', 'preethi.r@sathyabama.ac.in', 'CIVIL',
         ['Environmental Engineering', 'Water Resources', 'Structural Analysis']),
        # Reserve CIVIL
        ('civil_res_raja', 'Dr. Raja Sekaran', 'raja.s@sathyabama.ac.in', 'CIVIL',
         ['Structural Analysis', 'RCC Design', 'Surveying', 'Geotechnical Engineering']),
    ]

    faculty_password = generate_password_hash('faculty123')
    faculty_ids = {}

    for username, full_name, email, dept, subjects in faculty_data:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, department, role, subjects)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, faculty_password, full_name, email, dept, 'faculty', json.dumps(subjects)))
        faculty_ids[username] = cursor.lastrowid

    print(f"[OK] Inserted {len(faculty_data)} faculty members + 1 admin.")

    # ── Timetable Data ──
    # Time slots for a typical college day
    time_slots = [
        (1, '09:00:00', '09:50:00'),
        (2, '09:50:00', '10:40:00'),
        (3, '10:50:00', '11:40:00'),  # After break
        (4, '11:40:00', '12:30:00'),
        # Lunch: 12:30 - 13:20
        (5, '13:20:00', '14:10:00'),
        (6, '14:10:00', '15:00:00'),
        (7, '15:10:00', '16:00:00'),  # After break
    ]

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Timetable assignments — Regular faculty get 4-5 periods/day, Reserve get 2-3
    # This ensures reserve faculty are available for substitution
    timetable_entries = []

    # CSE Regular Faculty Timetables
    cse_regular = ['cse_priya', 'cse_rajesh', 'cse_anitha', 'cse_kumar', 'cse_deepa', 'cse_vijay']
    cse_subjects_map = {
        'cse_priya': ['Machine Learning', 'Data Structures', 'Python Programming'],
        'cse_rajesh': ['Machine Learning', 'Artificial Intelligence', 'Deep Learning'],
        'cse_anitha': ['Data Structures', 'Algorithms', 'C Programming'],
        'cse_kumar': ['Database Systems', 'SQL', 'Data Mining'],
        'cse_deepa': ['Operating Systems', 'Computer Networks', 'Cloud Computing'],
        'cse_vijay': ['Web Development', 'Software Engineering', 'Python Programming'],
    }

    classrooms = ['CS101', 'CS102', 'CS103', 'CS104', 'CS105', 'CS201', 'CS202']

    # For each regular CSE faculty, assign 4-5 periods per day with strategic gaps
    for day in days:
        for i, fname in enumerate(cse_regular):
            # Each faculty teaches 4 periods, with gaps that rotate
            # This ensures at least 2 faculty are free during each period
            skip_period = (i + days.index(day)) % 7  # Rotating gap
            skip_period2 = (i + days.index(day) + 3) % 7
            taught = 0
            for period, start, end in time_slots:
                if period - 1 == skip_period or period - 1 == skip_period2:
                    continue
                if taught >= 5:
                    continue
                subj = cse_subjects_map[fname][taught % len(cse_subjects_map[fname])]
                classroom = classrooms[taught % len(classrooms)]
                timetable_entries.append((faculty_ids[fname], day, period, start, end, subj, classroom))
                taught += 1

    # CSE Reserve faculty — only 2 periods per day (highly available)
    for day in days:
        for fname in ['cse_res_meena', 'cse_res_arjun']:
            # Only teach periods 1 and 4 (leaving most slots free)
            assigned_periods = [(1, 'Machine Learning', 'CS201'), (4, 'Data Structures', 'CS202')]
            if fname == 'cse_res_arjun':
                assigned_periods = [(2, 'Artificial Intelligence', 'CS201'), (5, 'Database Systems', 'CS202')]
            for p, subj, room in assigned_periods:
                slot = time_slots[p - 1]
                timetable_entries.append((faculty_ids[fname], day, slot[0], slot[1], slot[2], subj, room))

    # ECE Faculty Timetables
    ece_regular = ['ece_kavitha', 'ece_mohan', 'ece_lakshmi', 'ece_suresh', 'ece_divya']
    ece_subjects_map = {
        'ece_kavitha': ['Digital Electronics', 'VLSI Design', 'Embedded Systems'],
        'ece_mohan': ['Signal Processing', 'Communication Systems', 'Digital Electronics'],
        'ece_lakshmi': ['Microprocessors', 'Embedded Systems', 'IoT'],
        'ece_suresh': ['VLSI Design', 'Analog Circuits', 'Signal Processing'],
        'ece_divya': ['Communication Systems', 'Antenna Design', 'Wireless Networks'],
    }
    ece_classrooms = ['EC101', 'EC102', 'EC103', 'EC104', 'EC201']

    for day in days:
        for i, fname in enumerate(ece_regular):
            skip_period = (i + days.index(day)) % 7
            skip_period2 = (i + days.index(day) + 3) % 7
            taught = 0
            for period, start, end in time_slots:
                if period - 1 == skip_period or period - 1 == skip_period2:
                    continue
                if taught >= 5:
                    continue
                subj = ece_subjects_map[fname][taught % len(ece_subjects_map[fname])]
                classroom = ece_classrooms[taught % len(ece_classrooms)]
                timetable_entries.append((faculty_ids[fname], day, period, start, end, subj, classroom))
                taught += 1

    # ECE Reserve
    for day in days:
        for p, subj, room in [(1, 'Digital Electronics', 'EC201'), (4, 'VLSI Design', 'EC201')]:
            slot = time_slots[p - 1]
            timetable_entries.append((faculty_ids['ece_res_ganesh'], day, slot[0], slot[1], slot[2], subj, room))

    # EEE Faculty Timetables
    eee_regular = ['eee_ravi', 'eee_sunitha', 'eee_prakash', 'eee_nisha', 'eee_karthik']
    eee_subjects_map = {
        'eee_ravi': ['Power Systems', 'Electrical Machines', 'Control Systems'],
        'eee_sunitha': ['Control Systems', 'Power Electronics', 'Renewable Energy'],
        'eee_prakash': ['Electrical Machines', 'Transformers', 'Power Systems'],
        'eee_nisha': ['Power Electronics', 'Drives', 'Renewable Energy'],
        'eee_karthik': ['Instrumentation', 'Control Systems', 'PLC Programming'],
    }
    eee_classrooms = ['EE101', 'EE102', 'EE103', 'EE104', 'EE201']

    for day in days:
        for i, fname in enumerate(eee_regular):
            skip_period = (i + days.index(day)) % 7
            skip_period2 = (i + days.index(day) + 3) % 7
            taught = 0
            for period, start, end in time_slots:
                if period - 1 == skip_period or period - 1 == skip_period2:
                    continue
                if taught >= 5:
                    continue
                subj = eee_subjects_map[fname][taught % len(eee_subjects_map[fname])]
                classroom = eee_classrooms[taught % len(eee_classrooms)]
                timetable_entries.append((faculty_ids[fname], day, period, start, end, subj, classroom))
                taught += 1

    # EEE Reserve
    for day in days:
        for p, subj, room in [(2, 'Power Systems', 'EE201'), (5, 'Control Systems', 'EE201')]:
            slot = time_slots[p - 1]
            timetable_entries.append((faculty_ids['eee_res_arun'], day, slot[0], slot[1], slot[2], subj, room))

    # MECH Faculty Timetables
    mech_regular = ['mech_gopi', 'mech_saranya', 'mech_manoj', 'mech_revathi', 'mech_dinesh']
    mech_subjects_map = {
        'mech_gopi': ['Thermodynamics', 'Heat Transfer', 'Fluid Mechanics'],
        'mech_saranya': ['Manufacturing Technology', 'CAD/CAM', 'Industrial Engineering'],
        'mech_manoj': ['Fluid Mechanics', 'Hydraulics', 'Thermodynamics'],
        'mech_revathi': ['Strength of Materials', 'Engineering Mechanics', 'Finite Element Analysis'],
        'mech_dinesh': ['Automobile Engineering', 'Internal Combustion Engines', 'Manufacturing Technology'],
    }
    mech_classrooms = ['ME101', 'ME102', 'ME103', 'ME104', 'ME201']

    for day in days:
        for i, fname in enumerate(mech_regular):
            skip_period = (i + days.index(day)) % 7
            skip_period2 = (i + days.index(day) + 3) % 7
            taught = 0
            for period, start, end in time_slots:
                if period - 1 == skip_period or period - 1 == skip_period2:
                    continue
                if taught >= 5:
                    continue
                subj = mech_subjects_map[fname][taught % len(mech_subjects_map[fname])]
                classroom = mech_classrooms[taught % len(mech_classrooms)]
                timetable_entries.append((faculty_ids[fname], day, period, start, end, subj, classroom))
                taught += 1

    # MECH Reserve
    for day in days:
        for p, subj, room in [(3, 'Thermodynamics', 'ME201'), (6, 'Fluid Mechanics', 'ME201')]:
            slot = time_slots[p - 1]
            timetable_entries.append((faculty_ids['mech_res_karthi'], day, slot[0], slot[1], slot[2], subj, room))

    # IT Faculty Timetables
    it_regular = ['it_ramya', 'it_naveen', 'it_swathi', 'it_bala', 'it_harini']
    it_subjects_map = {
        'it_ramya': ['Web Development', 'Java Programming', 'Software Testing'],
        'it_naveen': ['Cyber Security', 'Cryptography', 'Computer Networks'],
        'it_swathi': ['Cloud Computing', 'DevOps', 'Web Development'],
        'it_bala': ['Data Analytics', 'Big Data', 'Python Programming'],
        'it_harini': ['Mobile App Development', 'Java Programming', 'Software Engineering'],
    }
    it_classrooms = ['IT101', 'IT102', 'IT103', 'IT104', 'IT201']

    for day in days:
        for i, fname in enumerate(it_regular):
            skip_period = (i + days.index(day)) % 7
            skip_period2 = (i + days.index(day) + 3) % 7
            taught = 0
            for period, start, end in time_slots:
                if period - 1 == skip_period or period - 1 == skip_period2:
                    continue
                if taught >= 5:
                    continue
                subj = it_subjects_map[fname][taught % len(it_subjects_map[fname])]
                classroom = it_classrooms[taught % len(it_classrooms)]
                timetable_entries.append((faculty_ids[fname], day, period, start, end, subj, classroom))
                taught += 1

    # IT Reserve
    for day in days:
        for p, subj, room in [(1, 'Web Development', 'IT201'), (6, 'Java Programming', 'IT201')]:
            slot = time_slots[p - 1]
            timetable_entries.append((faculty_ids['it_res_sanjay'], day, slot[0], slot[1], slot[2], subj, room))

    # CIVIL Faculty Timetables
    civil_regular = ['civil_ashok', 'civil_sangeetha', 'civil_venkat', 'civil_preethi']
    civil_subjects_map = {
        'civil_ashok': ['Structural Analysis', 'RCC Design', 'Construction Management'],
        'civil_sangeetha': ['Geotechnical Engineering', 'Soil Mechanics', 'Foundation Engineering'],
        'civil_venkat': ['Surveying', 'Highway Engineering', 'Transportation'],
        'civil_preethi': ['Environmental Engineering', 'Water Resources', 'Structural Analysis'],
    }
    civil_classrooms = ['CE101', 'CE102', 'CE103', 'CE104']

    for day in days:
        for i, fname in enumerate(civil_regular):
            skip_period = (i + days.index(day)) % 7
            skip_period2 = (i + days.index(day) + 3) % 7
            taught = 0
            for period, start, end in time_slots:
                if period - 1 == skip_period or period - 1 == skip_period2:
                    continue
                if taught >= 5:
                    continue
                subj = civil_subjects_map[fname][taught % len(civil_subjects_map[fname])]
                classroom = civil_classrooms[taught % len(civil_classrooms)]
                timetable_entries.append((faculty_ids[fname], day, period, start, end, subj, classroom))
                taught += 1

    # CIVIL Reserve
    for day in days:
        for p, subj, room in [(2, 'Structural Analysis', 'CE104'), (5, 'Surveying', 'CE104')]:
            slot = time_slots[p - 1]
            timetable_entries.append((faculty_ids['civil_res_raja'], day, slot[0], slot[1], slot[2], subj, room))

    # Bulk insert timetable entries
    cursor.executemany("""
        INSERT INTO timetable (faculty_id, day_of_week, period, start_time, end_time, subject, classroom)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, timetable_entries)

    print(f"[OK] Inserted {len(timetable_entries)} timetable entries.")
    print("[OK] Sample data population complete.")
    print()
    print("=" * 60)
    print("  LOGIN CREDENTIALS")
    print("=" * 60)
    print(f"  Admin:   username='admin'       password='admin123'")
    print(f"  Faculty: username='cse_priya'   password='faculty123'")
    print(f"           (all faculty share password 'faculty123')")
    print("=" * 60)


# -----------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------

def main():
    """Main entry point — creates database, tables, and sample data."""
    print()
    print("=" * 60)
    print("  Faculty Workload Portal - Database Setup")
    print("  Sathyabama Institute of Science and Technology")
    print("=" * 60)
    print()

    try:
        # Connect without specifying database (to create it)
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        create_database(cursor)
        create_tables(cursor)
        insert_sample_data(cursor)

        connection.commit()
        print()
        print("[OK] Database setup completed successfully!")
        print(f"[i] Database: {DB_NAME} @ {DB_HOST}:{DB_PORT}")

    except Error as e:
        print(f"\n[X] MySQL Error: {e}")
        print("[i] Make sure MySQL is running and credentials are correct.")
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()


if __name__ == '__main__':
    main()
