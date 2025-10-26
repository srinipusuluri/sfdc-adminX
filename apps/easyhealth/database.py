import sqlite3
import pandas as pd
from datetime import datetime, date
import streamlit as st

class Database:
    def __init__(self, db_name="hospital_portal.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                medical_history TEXT,
                allergies TEXT,
                blood_type TEXT,
                emergency_contact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                availability_schedule TEXT,
                rating REAL DEFAULT 5.0,
                experience_years INTEGER DEFAULT 0
            )
        ''')

        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                doctor_id INTEGER,
                appointment_type TEXT NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                status TEXT DEFAULT 'scheduled', -- scheduled, confirmed, completed, cancelled
                symptoms TEXT,
                notes TEXT,
                patient_type TEXT DEFAULT 'regular', -- regular, walkin, emergency
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')

        # Lab services table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2),
                estimated_duration INTEGER, -- in minutes
                preparation_instructions TEXT
            )
        ''')

        # Lab appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_id INTEGER,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                status TEXT DEFAULT 'scheduled',
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (service_id) REFERENCES lab_services (id)
            )
        ''')

        # Pharmacy orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pharmacy_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                prescription_id TEXT,
                medications TEXT NOT NULL, -- JSON string of medications
                status TEXT DEFAULT 'ordered', -- ordered, ready, picked_up, delivered
                total_amount DECIMAL(10,2),
                payment_status TEXT DEFAULT 'pending',
                delivery_option TEXT DEFAULT 'pickup', -- pickup, delivery
                delivery_address TEXT,
                delivery_time DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Diagnostic services table (X-ray, CT, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostic_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                category TEXT NOT NULL, -- xray, ct, mri, ultrasound, etc.
                description TEXT,
                price DECIMAL(10,2),
                estimated_duration INTEGER
            )
        ''')

        # Diagnostic appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostic_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service_id INTEGER,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                status TEXT DEFAULT 'scheduled',
                results TEXT,
                urgency TEXT DEFAULT 'routine', -- routine, urgent, emergency
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (service_id) REFERENCES diagnostic_services (id)
            )
        ''')

        # Physiotherapy sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physiotherapy_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                therapist_id INTEGER,
                session_date DATE NOT NULL,
                session_time TIME NOT NULL,
                duration INTEGER DEFAULT 45, -- in minutes
                session_type TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Health monitoring data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date_recorded DATE NOT NULL,
                weight_kg REAL,
                height_cm REAL,
                blood_pressure_systolic INTEGER,
                blood_pressure_diastolic INTEGER,
                heart_rate INTEGER,
                temperature REAL,
                blood_glucose REAL,
                oxygen_saturation REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Medication reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medication_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                medication_name TEXT NOT NULL,
                dosage TEXT NOT NULL,
                frequency TEXT NOT NULL, -- e.g., "twice daily", "every 8 hours"
                start_date DATE NOT NULL,
                end_date DATE,
                notes TEXT,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Insert sample data
        self.insert_sample_data(cursor)

        conn.commit()
        conn.close()

    def insert_sample_data(self, cursor):
        # Sample doctors
        doctors_data = [
            ("Dr. Sarah Johnson", "Cardiology", "+1-555-0101", "sarah.johnson@hospital.com", "Mon-Fri 9AM-5PM", 4.8, 12),
            ("Dr. Michael Chen", "Neurology", "+1-555-0102", "michael.chen@hospital.com", "Tue-Sat 8AM-4PM", 4.9, 15),
            ("Dr. Emily Rodriguez", "Dermatology", "+1-555-0103", "emily.rodriguez@hospital.com", "Mon-Thu 10AM-6PM", 4.7, 8),
            ("Dr. James Wilson", "Orthopedics", "+1-555-0104", "james.wilson@hospital.com", "Wed-Sun 9AM-5PM", 4.6, 20),
            ("Dr. Lisa Park", "Pediatrics", "+1-555-0105", "lisa.park@hospital.com", "Mon-Fri 8AM-4PM", 4.9, 10),
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO doctors (name, specialization, phone, email, availability_schedule, rating, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', doctors_data)

        # Sample lab services
        lab_services_data = [
            ("Complete Blood Count (CBC)", "Comprehensive blood analysis", 75.00, 30, "Fasting required, avoid alcohol 24hrs before"),
            ("Lipid Profile", "Cholesterol and triglyceride analysis", 85.00, 20, "Fasting required for 12 hours"),
            ("Thyroid Function Test", "TSH, T3, T4 levels", 95.00, 25, "No special preparation needed"),
            ("Diabetes Screening", "Blood glucose and HbA1c", 65.00, 15, "Fasting preferred but not required"),
            ("Liver Function Test", "Liver enzyme analysis", 90.00, 30, "Avoid alcohol 24hrs before"),
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO lab_services (service_name, description, price, estimated_duration, preparation_instructions)
            VALUES (?, ?, ?, ?, ?)
        ''', lab_services_data)

        # Sample diagnostic services
        diagnostic_data = [
            ("Chest X-Ray", "xray", "Standard chest imaging", 120.00, 15),
            ("CT Scan - Head", "ct", "Computed tomography of head", 450.00, 30),
            ("MRI - Knee", "mri", "Magnetic resonance imaging of knee", 380.00, 45),
            ("Ultrasound - Abdomen", "ultrasound", "Abdominal ultrasound", 150.00, 20),
            ("DEXA Scan", "other", "Bone density measurement", 85.00, 25),
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO diagnostic_services (service_name, category, description, price, estimated_duration)
            VALUES (?, ?, ?, ?, ?)
        ''', diagnostic_data)

    def get_user_by_email(self, email):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return user

    def create_user(self, email, password, full_name, phone=None, date_of_birth=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (email, password, full_name, phone, date_of_birth)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, password, full_name, phone, date_of_birth))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def get_available_doctors(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors")
        doctors = cursor.fetchall()
        conn.close()
        return doctors

    def create_appointment(self, user_id, doctor_id, appointment_type, appointment_date, appointment_time, symptoms="", notes=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, doctor_id, appointment_type, appointment_date, appointment_time, symptoms, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, doctor_id, appointment_type, appointment_date, appointment_time, symptoms, notes))
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return appointment_id

    def get_user_appointments(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, d.name as doctor_name, d.specialization
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.user_id = ?
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''', (user_id,))
        appointments = cursor.fetchall()
        conn.close()
        return appointments

    def get_lab_services(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lab_services")
        services = cursor.fetchall()
        conn.close()
        return services

    def create_lab_appointment(self, user_id, service_id, appointment_date, appointment_time):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO lab_appointments (user_id, service_id, appointment_date, appointment_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, service_id, appointment_date, appointment_time))
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return appointment_id

    def get_user_lab_appointments(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT la.*, ls.service_name, ls.description, ls.price
            FROM lab_appointments la
            JOIN lab_services ls ON la.service_id = ls.id
            WHERE la.user_id = ?
            ORDER BY la.appointment_date DESC, la.appointment_time DESC
        ''', (user_id,))
        appointments = cursor.fetchall()
        conn.close()
        return appointments

    def get_diagnostic_services(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM diagnostic_services")
        services = cursor.fetchall()
        conn.close()
        return services

    def create_diagnostic_appointment(self, user_id, service_id, appointment_date, appointment_time, urgency="routine"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO diagnostic_appointments (user_id, service_id, appointment_date, appointment_time, urgency)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, service_id, appointment_date, appointment_time, urgency))
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return appointment_id

    def create_pharmacy_order(self, user_id, medications, total_amount, delivery_option="pickup", delivery_address=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pharmacy_orders (user_id, medications, total_amount, delivery_option, delivery_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, medications, total_amount, delivery_option, delivery_address))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def get_user_pharmacy_orders(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM pharmacy_orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        orders = cursor.fetchall()
        conn.close()
        return orders

# Initialize database
db = Database()</content>
