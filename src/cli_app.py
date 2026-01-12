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

# ==========================================
# VALIDATION HELPERS
# ==========================================
def validate_score(score):
    return 0 <= score <= 100

def validate_date(date_str):
    # Simple check for YYYY-MM-DD format
    return re.match(r"\d{4}-\d{2}-\d{2}", date_str) is not None

# ==========================================
# REPORTING: PDF GENERATION (New Requirement)
# ==========================================
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
            # Row mapping: 4=Code, 5=Name, 8=Score, 9=Grade
            line = f"{row[4]} | {row[5]} | {row[8]} | {row[9]}"
            c.drawString(50, y_position, line)
            y_position -= 20
            
        c.save()
        print(f"PDF Report saved to {filename}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

# ==========================================
# CORE ACTIONS
# ==========================================
def add_new_student(cursor):
    print("\n--- ADD NEW STUDENT (CREATE) ---")
    first = input("First Name: ")
    last = input("Last Name: ")
    email = input("Email: ")
    
    dob = input("Date of Birth (YYYY-MM-DD): ")
    if not validate_date(dob):
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        return

    major = input("Major: ")
    
    try:
        cursor.execute("""
            INSERT INTO students (first_name, last_name, email, date_of_birth, major)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING student_id;
        """, (first, last, email, dob, major))
        print(f"SUCCESS: Student created with ID {cursor.fetchone()[0]}")
    except Exception as e:
        print(f"ERROR: {e}")

def delete_student(cursor):
    print("\n--- DELETE STUDENT (DELETE) ---")
    email = input("Enter Email of student to DELETE: ")
    confirm = input(f"Are you sure you want to delete {email} and ALL their records? (yes/no): ")
    
    if confirm.lower() == 'yes':
        try:
            # Assuming ON DELETE CASCADE was set in schema, this deletes enrollments/grades too
            cursor.execute("DELETE FROM students WHERE email = %s RETURNING student_id", (email,))
            if cursor.fetchone():
                print("SUCCESS: Student deleted.")
            else:
                print("Error: Student not found.")
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        print("Deletion cancelled.")

def enroll_student_ui(cursor):
    print("\n--- ENROLL STUDENT ---")
    email = input("Student Email: ")
    code = input("Course Code (e.g., DE101): ")
    semester = input("Semester (e.g., Fall 2024): ")
    
    try:
        cursor.execute("CALL register_student(%s, %s, %s)", (email, code, semester))
        print("SUCCESS: Student enrolled.")
    except Exception as e:
        print(f"ERROR: {e}")

def record_grade_ui(cursor):
    print("\n--- RECORD GRADE (UPDATE) ---")
    email = input("Student Email: ")
    code = input("Course Code: ")
    assess = input("Assessment (Midterm/Final): ")
    
    try:
        score = float(input("Score (0-100): "))
        if not validate_score(score):
            print("Error: Score must be between 0 and 100.")
            return
            
        weight = float(input("Weight (0.0-1.0): "))
        
        cursor.execute("CALL record_grade(%s, %s, %s, %s, %s)", (email, code, assess, score, weight))
        print("SUCCESS: Grade recorded.")
    except ValueError:
        print("Error: Invalid number format.")
    except Exception as e:
        print(f"ERROR: {e}")

def mark_attendance_ui(cursor):
    print("\n--- MARK ATTENDANCE ---")
    email = input("Student Email: ")
    code = input("Course Code: ")
    status = input("Status (Present/Absent/Late): ")
    
    if status not in ['Present', 'Absent', 'Late', 'Excused']:
        print("Error: Invalid status.")
        return

    try:
        cursor.execute("CALL mark_attendance(%s, %s, %s)", (email, code, status))
        print("SUCCESS: Attendance marked.")
    except Exception as e:
        print(f"ERROR: {e}")

def generate_reports(cursor):
    print("\n--- GENERATE REPORTS (READ) ---")
    email = input("Student Email: ")
    
    try:
        cursor.execute("SELECT * FROM student_transcripts_view WHERE email = %s", (email,))
        records = cursor.fetchall()
        
        if not records:
            print("No records found.")
            return

        print(f"\nLoaded {len(records)} records for {records[0][1]} {records[0][2]}.")
        
        print("1. Export to CSV")
        print("2. Generate PDF (ReportLab)")
        print("3. View on Screen")
        sub_choice = input("Choose format (1-3): ")
        
        student_name = f"{records[0][1]} {records[0][2]}"
        base_filename = f"transcript_{records[0][1]}_{records[0][2]}"

        if sub_choice == '1':
            filename = f"{base_filename}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Student ID', 'First', 'Last', 'Email', 'Code', 'Course', 'Credits', 'Semester', 'Avg Score', 'Grade'])
                writer.writerows(records)
            print(f"Saved CSV to {filename}")
            
        elif sub_choice == '2':
            filename = f"{base_filename}.pdf"
            generate_pdf_transcript(student_name, records, filename)
            
        elif sub_choice == '3':
            print(f"\nTRANSCRIPT: {student_name}")
            print("-" * 40)
            for row in records:
                print(f"{row[5]:<25} | {row[9]}")
                
    except Exception as e:
        print(f"ERROR: {e}")

# ==========================================
# MAIN MENU
# ==========================================
def main_menu():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()

    while True:
        print("\n=== STUDENT RECORDS SYSTEM (ADMIN CLI) ===")
        print("1. Add New Student")
        print("2. Enroll Student")
        print("3. Record Grade")
        print("4. Mark Attendance (New)")
        print("5. Generate Reports (CSV/PDF)")
        print("6. Delete Student (New)")
        print("7. Exit")
        
        choice = input("Select an option (1-7): ")
        
        if choice == '1': add_new_student(cursor)
        elif choice == '2': enroll_student_ui(cursor)
        elif choice == '3': record_grade_ui(cursor)
        elif choice == '4': mark_attendance_ui(cursor)
        elif choice == '5': generate_reports(cursor)
        elif choice == '6': delete_student(cursor)
        elif choice == '7': 
            print("Exiting System.")
            break
        else:
            print("Invalid selection.")

    conn.close()

if __name__ == "__main__":
    main_menu()