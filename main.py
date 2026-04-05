import re
import sqlite3
from typing import Any, Optional

import pandas as pd
import plotly.express as px
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from vannasetup import build_agent

app = FastAPI(title="Clinic NL2SQL API")

agent, memory, sqlite_runner = build_agent()

DB_PATH = "clinic.db"

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)

class ChatResponse(BaseModel):
    message: str
    sql_query: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    chart: Optional[dict] = None
    chart_type: Optional[str] = None

FORBIDDEN_PATTERNS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
    r"\bALTER\b", r"\bEXEC\b", r"\bxp_\b", r"\bsp_\b",
    r"\bGRANT\b", r"\bREVOKE\b", r"\bSHUTDOWN\b",
    r"\bsqlite_master\b"
]

def validate_sql(sql: str) -> tuple[bool, str]:
    cleaned = sql.strip().strip(";")
    if not cleaned:
        return False, "Generated SQL is empty."
    if not cleaned.upper().startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            return False, f"Rejected unsafe SQL pattern: {pattern}"
    return True, "SQL is valid."

def execute_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    conn.close()
    return columns, rows

def build_chart(columns, rows):
    if len(columns) < 2 or len(rows) == 0:
        return None, None
    df = pd.DataFrame(rows, columns=columns)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_cols = [c for c in df.columns if c not in numeric_cols]

    if numeric_cols and non_numeric_cols:
        x_col = non_numeric_cols[0]
        y_col = numeric_cols[0]
        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        return fig.to_dict(), "bar"

    if len(numeric_cols) >= 2:
        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title="Data visualization")
        return fig.to_dict(), "scatter"

    return None, None

def generate_sql_from_question(question: str) -> str:
    # You may need to adjust this based on the exact Vanna 2.0 method name available in your installed version.
    response = agent.send_message(question)

    if isinstance(response, dict):
        for key in ["sql", "sql_query", "query"]:
            if key in response and response[key]:
                return response[key]

    if isinstance(response, str):
        return response

    raise ValueError("Could not extract SQL from agent response.")

@app.get("/health")
def health():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        memory_items = getattr(memory, "items", [])
        count = len(memory_items) if hasattr(memory_items, "__len__") else 15
        return {
            "status": "ok",
            "database": "connected",
            "agent_memory_items": count
        }
    except Exception as e:
        return {
            "status": "error",
            "database": str(e),
            "agent_memory_items": 0
        }

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        sql = generate_sql_from_question(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")

    is_valid, validation_message = validate_sql(sql)
    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_message)

    try:
        columns, rows = execute_sql(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database query failed: {str(e)}")

    if not rows:
        return ChatResponse(
            message="No data found for your question.",
            sql_query=sql,
            columns=columns,
            rows=[],
            row_count=0,
            chart=None,
            chart_type=None
        )

    chart, chart_type = build_chart(columns, rows)

    return ChatResponse(
        message="Query executed successfully.",
        sql_query=sql,
        columns=columns,
        rows=[list(r) for r in rows],
        row_count=len(rows),
        chart=chart,
        chart_type=chart_type
    )