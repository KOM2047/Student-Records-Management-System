import unittest
import psycopg2
import sys
import os

# Add src to path so we can import db connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from cli_app import DB_PARAMS

class TestStudentRecords(unittest.TestCase):
    
    def setUp(self):
        """Runs before EACH test. Connects to DB."""
        self.conn = psycopg2.connect(**DB_PARAMS)
        self.cursor = self.conn.cursor()
        self.conn.autocommit = False # Use transactions we can rollback

    def tearDown(self):
        """Runs after EACH test. Rolls back changes so we don't mess up real data."""
        self.conn.rollback()
        self.conn.close()

    # ==========================================
    # TEST CASE 1: DATA INSERTION & VALIDATION
    # Criteria: Validate Grade Ranges (0-100)
    # ==========================================
    def test_grade_range_constraint(self):
        print("\nTesting: Database should reject grades > 100...")
        
        # 1. Create a dummy enrollment
        self.cursor.execute("SELECT enrollment_id FROM enrollments LIMIT 1")
        enrollment_id = self.cursor.fetchone()[0]

        # 2. Try to insert an invalid grade (150)
        try:
            self.cursor.execute("""
                INSERT INTO grades (enrollment_id, assessment_type, score, weight)
                VALUES (%s, 'TestFail', 150.00, 0.5)
            """, (enrollment_id,))
            self.fail("Database did NOT reject invalid score of 150!") 
        except psycopg2.DatabaseError as e:
            print(" -> Success: Database rejected invalid grade as expected.")
            pass # We expect this error!

    # ==========================================
    # TEST CASE 2: ETL PIPELINE ACCURACY
    # Criteria: Verify Row Counts
    # ==========================================
    def test_etl_row_counts(self):
        print("\nTesting: ETL Pipeline Data Volume...")
        
        # Check Students (Should be > 300 based on our generation)
        self.cursor.execute("SELECT COUNT(*) FROM students")
        student_count = self.cursor.fetchone()[0]
        self.assertGreater(student_count, 100, "ETL Failure: Too few students found.")
        print(f" -> Success: Found {student_count} students (Threshold: >100).")

        # Check Courses (Should be exactly 29 based on generation + excel)
        self.cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = self.cursor.fetchone()[0]
        self.assertTrue(20 <= course_count <= 40, f"ETL Failure: Course count {course_count} out of range.")
        print(f" -> Success: Found {course_count} courses.")

    # ==========================================
    # TEST CASE 3: QUERY ACCURACY
    # Criteria: Verify GPA Calculation
    # ==========================================
    def test_gpa_calculation(self):
        print("\nTesting: GPA Calculation Accuracy...")
        
        # 1. Create a fake student with known grades
        # We use a transaction so this data vanishes after the test
        self.cursor.execute("""
            INSERT INTO students (first_name, last_name, email, major) 
            VALUES ('Test', 'GPA', 'test.gpa@test.com', 'Testing') 
            RETURNING student_id
        """)
        s_id = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT course_id FROM courses LIMIT 1")
        c_id = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            INSERT INTO enrollments (student_id, course_id, semester)
            VALUES (%s, %s, 'TestSem') RETURNING enrollment_id
        """, (s_id, c_id))
        e_id = self.cursor.fetchone()[0]
        
        # Insert two grades: 80 and 90. Average should be 85.
        self.cursor.execute("INSERT INTO grades (enrollment_id, assessment_type, score) VALUES (%s, 'T1', 80)", (e_id,))
        self.cursor.execute("INSERT INTO grades (enrollment_id, assessment_type, score) VALUES (%s, 'T2', 90)", (e_id,))
        
        # 2. Run the View logic
        self.cursor.execute("""
            SELECT final_score, letter_grade 
            FROM student_transcripts_view 
            WHERE student_id = %s
        """, (s_id,))
        result = self.cursor.fetchone()
        
        # 3. Assertions
        self.assertEqual(float(result[0]), 85.0, "Math Error: Average of 80 and 90 should be 85.")
        self.assertEqual(result[1], 'B', "Logic Error: 85 should be a 'B'.")
        print(f" -> Success: Calculated GPA 85.0 correctly as 'B'.")

if __name__ == '__main__':
    unittest.main()