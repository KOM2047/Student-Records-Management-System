import pandas as pd
import psycopg2
import json
import os

# Database Connection (Use your specific password)
DB_PARAMS = {
    "host": "localhost",
    "database": "student_records_db",
    "user": "postgres",
    "password": "password"
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_PARAMS)
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

# ==========================================
# 1. EXTRACT & TRANSFORM: STUDENTS (CSV)
# ==========================================
def process_students(cursor):
    print("\n--- Processing Students (CSV) ---")
    file_path = 'raw_data/csv_source/new_students.csv'
    
    if not os.path.exists(file_path):
        print(f"Skipping: {file_path} not found.")
        return

    # Extract
    df = pd.read_csv(file_path)
    print(f"Extracted {len(df)} raw records.")

    # Transform: Remove rows with missing emails (Data Cleaning)
    df_clean = df.dropna(subset=['email'])
    print(f"Transformed: {len(df_clean)} records remain after cleaning null emails.")

    # Load
    count = 0
    for _, row in df_clean.iterrows():
        try:
            cursor.execute("""
                INSERT INTO students (first_name, last_name, email, date_of_birth, major)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING;
            """, (row['first_name'], row['last_name'], row['email'], row['dob'], row['major']))
            count += 1
        except Exception as e:
            print(f"Error loading student {row['email']}: {e}")
    print(f"Loaded: Processed {count} rows.")

# ==========================================
# 2. EXTRACT & TRANSFORM: COURSES (Excel)
# ==========================================
def process_courses(cursor):
    print("\n--- Processing Courses (Excel) ---")
    file_path = 'raw_data/excel_source/future_courses.xlsx'
    
    # Extract
    # Note: engine='openpyxl' is required for .xlsx files
    df = pd.read_excel(file_path, engine='openpyxl')
    
    # Load
    count = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO courses (course_name, course_code, credits)
            VALUES (%s, %s, %s)
            ON CONFLICT (course_code) DO NOTHING;
        """, (row['Course Name'], row['Code'], row['Credits']))
        count += 1
    print(f"Loaded: Processed {count} courses.")

# ==========================================
# 3. EXTRACT & TRANSFORM: GRADES (JSON)
# Complex Logic: Must link Grade -> Enrollment -> Student/Course
# ==========================================
def process_grades(cursor):
    print("\n--- Processing Grades (JSON) ---")
    file_path = 'raw_data/json_source/legacy_grades.json'
    
    # Extract
    with open(file_path, 'r') as f:
        grades_data = json.load(f)
    
    count = 0
    for item in grades_data:
        student_id = item['student_ref_id']
        course_code = item['course_code_ref']
        
        # 1. Find the course_id for 'DE101'
        cursor.execute("SELECT course_id FROM courses WHERE course_code = %s", (course_code,))
        course_res = cursor.fetchone()
        
        if not course_res:
            print(f"Skipping grade: Course {course_code} not found.")
            continue
        course_id = course_res[0]

        # 2. Find or Create Enrollment (Idempotent)
        # We need an enrollment_id to insert a grade.
        cursor.execute("""
            SELECT enrollment_id FROM enrollments 
            WHERE student_id = %s AND course_id = %s;
        """, (student_id, course_id))
        enrollment_res = cursor.fetchone()

        if enrollment_res:
            enrollment_id = enrollment_res[0]
        else:
            # Create a new enrollment if one doesn't exist
            cursor.execute("""
                INSERT INTO enrollments (student_id, course_id, semester, enrollment_date)
                VALUES (%s, %s, 'External Transfer', CURRENT_DATE)
                RETURNING enrollment_id;
            """, (student_id, course_id))
            enrollment_id = cursor.fetchone()[0]

        # 3. Load Grade
        cursor.execute("""
            INSERT INTO grades (enrollment_id, assessment_type, score, weight)
            VALUES (%s, %s, %s, %s);
        """, (enrollment_id, item['assessment'], item['score'], item['weight']))
        count += 1

    print(f"Loaded: {count} grade records (linked to valid enrollments).")

# ==========================================
# MAIN PIPELINE CONTROLLER
# ==========================================
def main():
    conn = get_db_connection()
    if not conn:
        return
    
    conn.autocommit = False
    cursor = conn.cursor()
    
    try:
        process_students(cursor)
        process_courses(cursor)
        process_grades(cursor)
        
        conn.commit()
        print("\nSUCCESS: ETL Pipeline Finished Successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"\nCRITICAL ERROR: Pipeline Failed. Rolled back changes. {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()