from vannasetup import build_agent

SEED_EXAMPLES = [
    ("How many patients do we have?",
     "SELECT COUNT(*) AS total_patients FROM patients"),
    ("List all doctors and their specializations",
     "SELECT name, specialization FROM doctors ORDER BY name"),
    ("Which city has the most patients?",
     "SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1"),
    ("Show female patients from Bengaluru",
     "SELECT first_name, last_name, city FROM patients WHERE gender = 'F' AND city = 'Bengaluru'"),
    ("Show male patients from Mumbai",
     "SELECT first_name, last_name, city FROM patients WHERE gender = 'M' AND city = 'Mumbai'"),
    ("Which doctor has the most appointments?",
     "SELECT d.name, COUNT(*) AS total_appointments FROM appointments a JOIN doctors d ON a.doctor_id = d.id GROUP BY d.name ORDER BY total_appointments DESC LIMIT 1"),
    ("Show appointments per doctor",
     "SELECT d.name, COUNT(*) AS total_appointments FROM appointments a JOIN doctors d ON a.doctor_id = d.id GROUP BY d.name ORDER BY total_appointments DESC"),
    ("Show completed appointments",
     "SELECT * FROM appointments WHERE status = 'Completed'"),
    ("Show cancelled appointments last quarter",
     "SELECT COUNT(*) AS cancelled_count FROM appointments WHERE status = 'Cancelled' AND appointment_date >= date('now', '-3 months')"),
    ("Show appointments for last month",
     "SELECT * FROM appointments WHERE appointment_date >= date('now', '-1 month') ORDER BY appointment_date DESC"),
    ("What is the total revenue?",
     "SELECT SUM(total_amount) AS total_revenue FROM invoices"),
    ("Show unpaid invoices",
     "SELECT * FROM invoices WHERE status IN ('Pending', 'Overdue')"),
    ("List patients with overdue invoices",
     "SELECT p.first_name, p.last_name, i.total_amount, i.paid_amount FROM invoices i JOIN patients p ON i.patient_id = p.id WHERE i.status = 'Overdue'"),
    ("Revenue trend by month",
     "SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total_amount) AS revenue FROM invoices GROUP BY month ORDER BY month"),
    ("Show revenue by doctor",
     "SELECT d.name, SUM(i.total_amount) AS total_revenue FROM invoices i JOIN appointments a ON i.patient_id = a.patient_id JOIN doctors d ON a.doctor_id = d.id GROUP BY d.name ORDER BY total_revenue DESC"),
    ("Average treatment cost by specialization",
     "SELECT d.specialization, AVG(t.cost) AS avg_treatment_cost FROM treatments t JOIN appointments a ON t.appointment_id = a.id JOIN doctors d ON a.doctor_id = d.id GROUP BY d.specialization ORDER BY avg_treatment_cost DESC"),
    ("Show monthly appointment count for the past 6 months",
     "SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS appointment_count FROM appointments WHERE appointment_date >= date('now', '-6 months') GROUP BY month ORDER BY month"),
]

def main():
    agent, memory, _ = build_agent()

    added = 0
    for question, sql in SEED_EXAMPLES:
        try:
            # Adjust this if your installed Vanna version uses a slightly different memory method.
            memory.save_correct_tool_use(
                question=question,
                tool_name="RunSqlTool",
                args={"sql": sql}
            )
            added += 1
        except Exception as e:
            print(f"Failed to seed: {question} -> {e}")

    print(f"Seeded {added} question-SQL pairs into memory.")

if __name__ == "__main__":
    main()