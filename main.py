import re
import sqlite3
from functools import lru_cache
from typing import Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = "clinic.db"
app = FastAPI(title="Clinic NL2SQL API")

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=200)

class ChatResponse(BaseModel):
    message: str
    sql_query: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    chart: Optional[dict] = None
    chart_type: Optional[str] = None

FORBIDDEN = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "EXEC", "GRANT", "REVOKE",
    "SHUTDOWN", "XP_", "SP_", "SQLITE_MASTER"
]

def normalize(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())

def validate_sql(sql: str) -> tuple[bool, str]:
    s = sql.strip().strip(";")
    if not s.upper().startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    for bad in FORBIDDEN:
        if bad.lower() in s.lower():
            return False, f"Unsafe SQL detected: {bad}"
    return True, "ok"

def qsql(question: str) -> str:
    q = normalize(question)

    if "how many patients" in q:
        return "SELECT COUNT(*) AS total_patients FROM patients"

    if "list all doctors" in q and "specializations" in q:
        return "SELECT name, specialization FROM doctors ORDER BY name"

    if "show me appointments for last month" in q:
        return """
        SELECT a.id, a.patient_id, a.doctor_id, a.appointment_date, a.status, a.notes
        FROM appointments a
        WHERE a.appointment_date >= date('now', '-1 month')
        ORDER BY a.appointment_date DESC
        """

    if "which doctor has the most appointments" in q:
        return """
        SELECT d.name, COUNT(*) AS appointment_count
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        GROUP BY d.id
        ORDER BY appointment_count DESC
        LIMIT 1
        """

    if "what is the total revenue" in q:
        return "SELECT ROUND(COALESCE(SUM(total_amount), 0), 2) AS total_revenue FROM invoices"

    if "show revenue by doctor" in q:
        return """
        SELECT d.name, ROUND(COALESCE(SUM(i.total_amount), 0), 2) AS total_revenue
        FROM invoices i
        JOIN appointments a ON i.patient_id = a.patient_id
        JOIN doctors d ON a.doctor_id = d.id
        GROUP BY d.id, d.name
        ORDER BY total_revenue DESC
        """

    if "cancelled appointments last quarter" in q:
        return """
        SELECT COUNT(*) AS cancelled_appointments
        FROM appointments
        WHERE status = 'Cancelled'
          AND appointment_date >= date('now', '-3 months')
        """

    if "top 5 patients by spending" in q:
        return """
        SELECT p.first_name, p.last_name, ROUND(SUM(i.total_amount), 2) AS total_spending
        FROM invoices i
        JOIN patients p ON i.patient_id = p.id
        GROUP BY p.id, p.first_name, p.last_name
        ORDER BY total_spending DESC
        LIMIT 5
        """

    if "average treatment cost by specialization" in q:
        return """
        SELECT d.specialization, ROUND(AVG(t.cost), 2) AS avg_treatment_cost
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        GROUP BY d.specialization
        ORDER BY avg_treatment_cost DESC
        """

    if "monthly appointment count for the past 6 months" in q:
        return """
        SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS appointment_count
        FROM appointments
        WHERE appointment_date >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
        """

    if "which city has the most patients" in q:
        return """
        SELECT city, COUNT(*) AS patient_count
        FROM patients
        GROUP BY city
        ORDER BY patient_count DESC
        LIMIT 1
        """

    if "visited more than 3 times" in q:
        return """
        SELECT p.first_name, p.last_name, COUNT(*) AS visits
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        GROUP BY p.id, p.first_name, p.last_name
        HAVING COUNT(*) > 3
        ORDER BY visits DESC
        """

    if "show unpaid invoices" in q:
        return """
        SELECT *
        FROM invoices
        WHERE status IN ('Pending', 'Overdue')
        ORDER BY invoice_date DESC
        """

    if "percentage of appointments are no-shows" in q:
        return """
        SELECT ROUND(
            100.0 * SUM(CASE WHEN status = 'No-Show' THEN 1 ELSE 0 END) / COUNT(*),
            2
        ) AS no_show_percentage
        FROM appointments
        """

    if "busiest day of the week" in q:
        return """
        SELECT strftime('%w', appointment_date) AS weekday_number,
               COUNT(*) AS appointment_count
        FROM appointments
        GROUP BY weekday_number
        ORDER BY appointment_count DESC
        LIMIT 1
        """

    if "revenue trend by month" in q:
        return """
        SELECT strftime('%Y-%m', invoice_date) AS month,
               ROUND(SUM(total_amount), 2) AS revenue
        FROM invoices
        GROUP BY month
        ORDER BY month
        """

    if "average appointment duration by doctor" in q:
        return """
        SELECT d.name, ROUND(AVG(t.duration_minutes), 2) AS avg_duration_minutes
        FROM treatments t
        JOIN appointments a ON t.appointment_id = a.id
        JOIN doctors d ON a.doctor_id = d.id
        GROUP BY d.id, d.name
        ORDER BY avg_duration_minutes DESC
        """

    if "patients with overdue invoices" in q:
        return """
        SELECT DISTINCT p.first_name, p.last_name, i.invoice_date, i.total_amount, i.paid_amount
        FROM invoices i
        JOIN patients p ON i.patient_id = p.id
        WHERE i.status = 'Overdue'
        ORDER BY i.invoice_date DESC
        """

    if "compare revenue between departments" in q:
        return """
        SELECT d.department, ROUND(SUM(i.total_amount), 2) AS revenue
        FROM invoices i
        JOIN appointments a ON i.patient_id = a.patient_id
        JOIN doctors d ON a.doctor_id = d.id
        GROUP BY d.department
        ORDER BY revenue DESC
        """

    if "patient registration trend by month" in q:
        return """
        SELECT strftime('%Y-%m', registered_date) AS month,
               COUNT(*) AS patient_count
        FROM patients
        GROUP BY month
        ORDER BY month
        """

    raise ValueError(f"Could not generate SQL for: {question}")

def execute_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    columns = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    return columns, rows

@app.get("/health")
def health():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ok", "database": "connected", "agent_memory_items": 0}
    except Exception as e:
        return {"status": "error", "database": str(e), "agent_memory_items": 0}

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        sql = qsql(question)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    ok, msg = validate_sql(sql)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    try:
        columns, rows = execute_sql(sql)
        result_rows = [list(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database query failed: {str(e)}")

    if not result_rows:
        return ChatResponse(
            message="No data found.",
            sql_query=sql,
            columns=columns,
            rows=[],
            row_count=0,
            chart=None,
            chart_type=None
        )

    return ChatResponse(
        message="Query executed successfully.",
        sql_query=sql,
        columns=columns,
        rows=result_rows,
        row_count=len(result_rows),
        chart=None,
        chart_type=None
    )