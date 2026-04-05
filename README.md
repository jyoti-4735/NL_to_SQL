# Clinic NL2SQL Chatbot

A Natural Language to SQL chatbot built with **FastAPI**, **SQLite**, and **Vanna 2.0**.  
It lets users ask clinic-related questions in plain English and returns SQL-backed results, row data, and optional chart output.

## Features

- Natural language to SQL query handling.
- SQLite database with realistic clinic data.
- FastAPI backend with `/health` and `/chat` endpoints.
- SQL safety checks to allow only safe `SELECT` queries.
- Pre-seeded memory with example question-SQL pairs.
- Support for chart-ready responses for analytics queries.
- Input validation and friendly error messages.

## Tech Stack

- Python 3.10+
- FastAPI
- SQLite
- Vanna 2.0
- Plotly
- pandas
- python-dotenv
- Google Gemini 

## Project Structure

```bash
project/
├── setupdatabase.py
├── seedmemory.py
├── vannasetup.py
├── main.py
├── requirements.txt
├── RESULTS.md
├── README.md
├── clinic.db
└── .env
```

## Setup Instructions

### 1. Create a virtual environment


- Command : python -m venv .venv


### 2. Activate the virtual environment

On Windows:

- Command :.venv\Scripts\activate


On macOS/Linux:


- Command : source .venv/bin/activate


### 3. Install dependencies


- Command : pip install -r requirements.txt


### 4. Add API key

Create a `.env` file in the project root.

Used Gemini Here:

GOOGLE_API_KEY=your_gemini_api_key_here


## Create the Database

Run the database setup script:


- Command :python setupdatabase.py


This creates `clinic.db` and inserts:
- 15 doctors
- 200 patients
- 500 appointments
- 350 treatments
- 300 invoices

## Seed the Agent Memory

Run:

- Command : python seedmemory.py

This preloads example question-SQL pairs into memory so the agent can answer common clinic questions better.

## Start the API Server

Run:


- Command :uvicorn main:app --reload --port 8000


Then open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## API Endpoints

### GET `/health`

Returns service status and database connectivity.

Example response:

```json
{
  "status": "ok",
  "database": "connected",
  "agent_memory_items": 15
}
```

### POST `/chat`

Request body:

```json
{
  "question": "How many patients do we have?"
}
```

Example response:

```json
{
  "message": "Query executed successfully.",
  "sql_query": "SELECT COUNT(*) AS total_patients FROM patients",
  "columns": ["total_patients"],
  "rows": [],
  "row_count": 1,
  "chart": null,
  "chart_type": null
}
```

## Sample Questions

You can test the API with questions like:

- 1	How many patients do we have?	Returns count
- 2	List all doctors and their specializations	Returns doctor list
- 3	Show me appointments for last month	Filters by date
- 4	Which doctor has the most appointments?	Aggregation + ordering
- 5	What is the total revenue?	SUM of invoice amounts
- 6	Show revenue by doctor	JOIN + GROUP BY
- 7	How many cancelled appointments last quarter?	Status filter + date
- 8	Top 5 patients by spending	JOIN + ORDER + LIMIT
- 9	Average treatment cost by specialization	Multi-table JOIN + AVG
- 10	Show monthly appointment count for the past 6 months	Date grouping
- 11	Which city has the most patients?	GROUP BY + COUNT
- 12	List patients who visited more than 3 times	HAVING clause
- 13	Show unpaid invoices	Status filter
- 14	What percentage of appointments are no-shows?	Percentage calculation
- 15	Show the busiest day of the week for appointments	Date function
- 16	Revenue trend by month	Time series
- 17	Average appointment duration by doctor	AVG + GROUP BY
- 18	List patients with overdue invoices	JOIN + filter
- 19	Compare revenue between departments	JOIN + GROUP BY
- 20	Show patient registration trend by month	Date grouping


## Architecture Overview

The system follows this flow:


User Question
→ FastAPI
→ SQL generation
→ SQL validation
→ SQLite execution
→ JSON response


For analytics queries, the API can also return chart-ready data.

## SQL Safety Rules

Before executing SQL, the application checks that:

- Only `SELECT` queries are allowed.
- Dangerous commands are blocked.
- System tables are not accessed.
- Invalid queries return a friendly error message.

## Results Summary

The `RESULTS.md` file contains:

- Each test question
- Generated SQL
- Whether it was correct
- A short result summary
- Final pass count out of 20
- Notes on any issues or failures
