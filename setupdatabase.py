import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "clinic.db"

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krish",
    "Ananya", "Diya", "Aadhya", "Myra", "Ishita", "Sara", "Kiara", "Riya",
    "John", "Jane", "Michael", "Emily", "David", "Sophia", "Daniel", "Olivia"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Singh", "Gupta",
    "Das", "Kulkarni", "Smith", "Johnson", "Brown", "Miller", "Davis"
]

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Mysuru"]
SPECIALIZATIONS = ["Dermatology", "Cardiology", "Orthopedics", "General", "Pediatrics"]
DEPARTMENTS = {
    "Dermatology": "Skin Care",
    "Cardiology": "Heart Care",
    "Orthopedics": "Bone & Joint",
    "General": "General Medicine",
    "Pediatrics": "Child Care"
}
APPOINTMENT_STATUSES = ["Scheduled", "Completed", "Cancelled", "No-Show"]
INVOICE_STATUSES = ["Paid", "Pending", "Overdue"]
TREATMENTS = [
    "Consultation", "Skin Therapy", "ECG", "X-Ray", "Physiotherapy",
    "Vaccination", "Blood Test", "Minor Procedure", "Follow-up", "Health Checkup"
]

def random_date_within_last_year():
    now = datetime.now()
    days_back = random.randint(0, 365)
    dt = now - timedelta(days=days_back, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return dt

def maybe_null(value, chance=0.15):
    return None if random.random() < chance else value

def create_schema(conn):
    cursor = conn.cursor()
    cursor.executescript("""
    DROP TABLE IF EXISTS treatments;
    DROP TABLE IF EXISTS appointments;
    DROP TABLE IF EXISTS invoices;
    DROP TABLE IF EXISTS doctors;
    DROP TABLE IF EXISTS patients;

    CREATE TABLE patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT,
        city TEXT,
        registered_date DATE
    );

    CREATE TABLE doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        phone TEXT
    );

    CREATE TABLE appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATETIME,
        status TEXT,
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    );

    CREATE TABLE treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        treatment_name TEXT,
        cost REAL,
        duration_minutes INTEGER,
        FOREIGN KEY(appointment_id) REFERENCES appointments(id)
    );

    CREATE TABLE invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        invoice_date DATE,
        total_amount REAL,
        paid_amount REAL,
        status TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    );
    """)
    conn.commit()

def insert_doctors(conn):
    cursor = conn.cursor()
    doctors = []
    for i in range(15):
        specialization = SPECIALIZATIONS[i % len(SPECIALIZATIONS)]
        name = f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone = maybe_null(f"+91-9{random.randint(100000000, 999999999)}", 0.1)
        doctors.append((name, specialization, DEPARTMENTS[specialization], phone))
    cursor.executemany("""
        INSERT INTO doctors (name, specialization, department, phone)
        VALUES (?, ?, ?, ?)
    """, doctors)
    conn.commit()

def insert_patients(conn):
    cursor = conn.cursor()
    patients = []
    for _ in range(200):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = maybe_null(f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@mail.com", 0.2)
        phone = maybe_null(f"+91-8{random.randint(100000000, 999999999)}", 0.15)
        dob = (datetime.now() - timedelta(days=random.randint(18*365, 75*365))).date().isoformat()
        gender = random.choice(["M", "F"])
        city = random.choice(CITIES)
        registered_date = random_date_within_last_year().date().isoformat()
        patients.append((first_name, last_name, email, phone, dob, gender, city, registered_date))
    cursor.executemany("""
        INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ? ,?)
    """, patients)
    conn.commit()

def insert_appointments(conn):
    cursor = conn.cursor()
    patient_ids = [row[0] for row in cursor.execute("SELECT id FROM patients").fetchall()]
    doctor_ids = [row[0] for row in cursor.execute("SELECT id FROM doctors").fetchall()]

    weighted_patients = patient_ids + random.choices(patient_ids, k=150)
    weighted_doctors = doctor_ids + random.choices(doctor_ids[:5], k=120)

    appointments = []
    for _ in range(500):
        patient_id = random.choice(weighted_patients)
        doctor_id = random.choice(weighted_doctors)
        appointment_date = random_date_within_last_year().strftime("%Y-%m-%d %H:%M:%S")
        status = random.choices(APPOINTMENT_STATUSES, weights=[20, 55, 15, 10])[0]
        notes = maybe_null(random.choice([
            "Routine checkup", "Follow-up visit", "Patient reported pain",
            "Skin irritation observed", "Requires further tests", "Stable condition"
        ]), 0.25)
        appointments.append((patient_id, doctor_id, appointment_date, status, notes))

    cursor.executemany("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
    """, appointments)
    conn.commit()

def insert_treatments(conn):
    cursor = conn.cursor()
    completed_appointments = [row[0] for row in cursor.execute(
        "SELECT id FROM appointments WHERE status = 'Completed'"
    ).fetchall()]
    selected = random.sample(completed_appointments, min(350, len(completed_appointments)))

    treatments = []
    for appointment_id in selected:
        treatment_name = random.choice(TREATMENTS)
        cost = round(random.uniform(50, 5000), 2)
        duration = random.randint(15, 120)
        treatments.append((appointment_id, treatment_name, cost, duration))

    cursor.executemany("""
        INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
        VALUES (?, ?, ?, ?)
    """, treatments)
    conn.commit()

def insert_invoices(conn):
    cursor = conn.cursor()
    patient_ids = [row[0] for row in cursor.execute("SELECT id FROM patients").fetchall()]
    weighted_patients = patient_ids + random.choices(patient_ids, k=100)

    invoices = []
    for _ in range(300):
        patient_id = random.choice(weighted_patients)
        total_amount = round(random.uniform(100, 10000), 2)
        status = random.choices(INVOICE_STATUSES, weights=[55, 25, 20])[0]
        if status == "Paid":
            paid_amount = total_amount
        elif status == "Pending":
            paid_amount = round(total_amount * random.uniform(0, 0.7), 2)
        else:
            paid_amount = round(total_amount * random.uniform(0, 0.4), 2)

        invoice_date = random_date_within_last_year().date().isoformat()
        invoices.append((patient_id, invoice_date, total_amount, paid_amount, status))

    cursor.executemany("""
        INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
        VALUES (?, ?, ?, ?, ?)
    """, invoices)
    conn.commit()

def main():
    conn = sqlite3.connect(DB_NAME)
    create_schema(conn)
    insert_doctors(conn)
    insert_patients(conn)
    insert_appointments(conn)
    insert_treatments(conn)
    insert_invoices(conn)

    cursor = conn.cursor()
    patients = cursor.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    doctors = cursor.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    appointments = cursor.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    treatments = cursor.execute("SELECT COUNT(*) FROM treatments").fetchone()[0]
    invoices = cursor.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]

    print(f"Created {patients} patients, {doctors} doctors, {appointments} appointments, {treatments} treatments, {invoices} invoices.")
    conn.close()

if __name__ == "__main__":
    main()