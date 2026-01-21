import asyncio
import psycopg2
import csv
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

# Validation helpers
def validate_score(score):
    return 0 <= score <= 100

def validate_date(date_str):
    return re.match(r"\d{4}-\d{2}-\d{2}", date_str) is not None

# PDF generator
def generate_pdf_transcript(student_name, records, filename):
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, f"Official Transcript: {student_name}")
        c.setFont("Helvetica", 12)
        y_position = 700
        c.drawString(50, y_position, "Course Code | Course Name | Score | Grade")
        c.line(50, y_position - 5, 500, y_position - 5)
        y_position -= 25
        for row in records:
            line = f"{row[4]} | {row[5]} | {row[8]} | {row[9]}"
            c.drawString(50, y_position, line)
            y_position -= 20
        c.save()
        print(f"PDF Report saved to {filename}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

# Blocking DB helpers (run in threads)
def _add_student_blocking(first, last, email, dob, major):
    conn = get_db_connection()
    if not conn: return "DB connection failed"
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO students (first_name, last_name, email, date_of_birth, major)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING student_id;
        """, (first, last, email, dob, major))
        sid = cur.fetchone()[0]
        cur.close(); conn.close()
        return f"SUCCESS: Student created with ID {sid}"
    except Exception as e:
        cur.close(); conn.close()
        return f"ERROR: {e}"

def _call_register_student(email, code, semester):
    conn = get_db_connection()
    if not conn: return f"DB connection failed"
    cur = conn.cursor()
    try:
        cur.execute("CALL register_student(%s, %s, %s)", (email, code, semester))
        cur.close(); conn.close()
        return "SUCCESS: Student enrolled."
    except Exception as e:
        cur.close(); conn.close()
        return f"ERROR: {e}"

def _call_record_grade(email, code, assess, score, weight):
    conn = get_db_connection()
    if not conn: return "DB connection failed"
    cur = conn.cursor()
    try:
        cur.execute("CALL record_grade(%s, %s, %s, %s, %s)", (email, code, assess, score, weight))
        cur.close(); conn.close()
        return "SUCCESS: Grade recorded."
    except Exception as e:
        cur.close(); conn.close()
        return f"ERROR: {e}"

def _call_mark_attendance(email, code, status):
    conn = get_db_connection()
    if not conn: return "DB connection failed"
    cur = conn.cursor()
    try:
        cur.execute("CALL mark_attendance(%s, %s, %s)", (email, code, status))
        cur.close(); conn.close()
        return "SUCCESS: Attendance marked."
    except Exception as e:
        cur.close(); conn.close()
        return f"ERROR: {e}"

def _generate_reports_blocking(email, export_type):
    conn = get_db_connection()
    if not conn: return "DB connection failed"
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM student_transcripts_view WHERE email = %s", (email,))
        records = cur.fetchall()
        if not records:
            cur.close(); conn.close()
            return "No records found."
        student_name = f"{records[0][1]} {records[0][2]}"
        base_filename = f"transcript_{records[0][1]}_{records[0][2]}"
        if export_type == 'csv':
            filename = f"{base_filename}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Student ID', 'First', 'Last', 'Email', 'Code', 'Course', 'Credits', 'Semester', 'Avg Score', 'Grade'])
                writer.writerows(records)
            cur.close(); conn.close()
            return f"Saved CSV to {filename}"
        elif export_type == 'pdf':
            filename = f"{base_filename}.pdf"
            generate_pdf_transcript(student_name, records, filename)
            cur.close(); conn.close()
            return f"Saved PDF to {filename}"
        else:
            cur.close(); conn.close()
            return f"Found {len(records)} records for {student_name}"
    except Exception as e:
        cur.close(); conn.close()
        return f"ERROR: {e}"

def _delete_student_blocking(email):
    conn = get_db_connection()
    if not conn: return "DB connection failed"
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM students WHERE email = %s RETURNING student_id", (email,))
        res = cur.fetchone()
        cur.close(); conn.close()
        if res:
            return "SUCCESS: Student deleted."
        else:
            return "Error: Student not found."
    except Exception as e:
        cur.close(); conn.close()
        return f"ERROR: {e}"

# Textual TUI
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Header, Footer, Static

class StatusMessage(Static):
    def set_text(self, text: str):
        self.update(text)

class StudentApp(App):
    CSS_PATH = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="menu"):
                yield Static("Student Records System", id="title")
                yield Button("Add New Student", id="add")
                yield Button("Enroll Student", id="enroll")
                yield Button("Record Grade", id="grade")
                yield Button("Mark Attendance", id="attendance")
                yield Button("Generate Reports", id="reports")
                yield Button("Delete Student", id="delete")
                yield Button("Exit", id="exit", variant="error")
            with Vertical(id="main"):
                yield Static("Select an action from the left menu.", id="info")
                yield StatusMessage("", id="status")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        status: StatusMessage = self.query_one("#status")
        if btn_id == "add":
            first = await asyncio.to_thread(input, "First Name: ")
            last = await asyncio.to_thread(input, "Last Name: ")
            email = await asyncio.to_thread(input, "Email: ")
            dob = await asyncio.to_thread(input, "Date of Birth (YYYY-MM-DD): ")
            if not validate_date(dob):
                status.set_text("Error: Invalid date format.")
                return
            major = await asyncio.to_thread(input, "Major: ")
            status.set_text("Adding student...")
            res = await asyncio.to_thread(_add_student_blocking, first, last, email, dob, major)
            status.set_text(res)

        elif btn_id == "enroll":
            email = await asyncio.to_thread(input, "Student Email: ")
            code = await asyncio.to_thread(input, "Course Code: ")
            semester = await asyncio.to_thread(input, "Semester: ")
            status.set_text("Enrolling...")
            res = await asyncio.to_thread(_call_register_student, email, code, semester)
            status.set_text(res)

        elif btn_id == "grade":
            email = await asyncio.to_thread(input, "Student Email: ")
            code = await asyncio.to_thread(input, "Course Code: ")
            assess = await asyncio.to_thread(input, "Assessment (Midterm/Final): ")
            try:
                score = float(await asyncio.to_thread(input, "Score (0-100): "))
                if not validate_score(score):
                    status.set_text("Error: Score must be between 0 and 100.")
                    return
                weight = float(await asyncio.to_thread(input, "Weight (0.0-1.0): "))
            except ValueError:
                status.set_text("Error: Invalid number format.")
                return
            status.set_text("Recording grade...")
            res = await asyncio.to_thread(_call_record_grade, email, code, assess, score, weight)
            status.set_text(res)

        elif btn_id == "attendance":
            email = await asyncio.to_thread(input, "Student Email: ")
            code = await asyncio.to_thread(input, "Course Code: ")
            status_input = await asyncio.to_thread(input, "Status (Present/Absent/Late/Excused): ")
            if status_input not in ['Present', 'Absent', 'Late', 'Excused']:
                status.set_text("Error: Invalid status.")
                return
            status.set_text("Marking attendance...")
            res = await asyncio.to_thread(_call_mark_attendance, email, code, status_input)
            status.set_text(res)

        elif btn_id == "reports":
            email = await asyncio.to_thread(input, "Student Email: ")
            print("1. Export to CSV\n2. Generate PDF\n3. View on Screen")
            choice = await asyncio.to_thread(input, "Choose (1-3): ")
            export = 'screen'
            if choice == '1': export = 'csv'
            elif choice == '2': export = 'pdf'
            status.set_text("Generating report...")
            res = await asyncio.to_thread(_generate_reports_blocking, email, export)
            status.set_text(res)

        elif btn_id == "delete":
            email = await asyncio.to_thread(input, "Enter Email of student to DELETE: ")
            confirm = await asyncio.to_thread(input, f"Are you sure you want to delete {email}? (yes/no): ")
            if confirm.lower() != 'yes':
                status.set_text("Deletion cancelled.")
                return
            status.set_text("Deleting student...")
            res = await asyncio.to_thread(_delete_student_blocking, email)
            status.set_text(res)

        elif btn_id == "exit":
            await self.action_quit()

if __name__ == "__main__":
    StudentApp().run()