import pandas as pd
import json
import random
import os
from faker import Faker

# Use GB locale to match your DB
fake = Faker('en_GB') 

# Ensure directories exist
os.makedirs('raw_data/csv_source', exist_ok=True)
os.makedirs('raw_data/excel_source', exist_ok=True)
os.makedirs('raw_data/json_source', exist_ok=True)

def generate_csv_students(count=50):
    """Generates a CSV with student info (some with bad emails)."""
    data = []
    print(f"--- Creating 'new_students.csv' with {count} records ---")
    for _ in range(count):
        first = fake.first_name()
        last = fake.last_name()
        # Intentional dirty data: 10% chance of missing email
        if random.random() < 0.1:
            email = None 
        else:
            email = f"{first}.{last}@externalsource.com".lower()
            
        data.append({
            "first_name": first,
            "last_name": last,
            "email": email,
            "dob": fake.date_of_birth(minimum_age=18, maximum_age=40),
            "major": "External Transfer"
        })
    
    df = pd.DataFrame(data)
    df.to_csv('raw_data/csv_source/new_students.csv', index=False)
    print(" -> Saved raw_data/csv_source/new_students.csv")

def generate_excel_courses():
    """Generates an Excel file with new courses."""
    print("--- Creating 'future_courses.xlsx' ---")
    courses = [
        {"Course Name": "Blockchain Fundamentals", "Code": "BC101", "Credits": 3},
        {"Course Name": "Quantum Computing Intro", "Code": "QC101", "Credits": 4},
        {"Course Name": "Ethical AI", "Code": "AI305", "Credits": 2},
        {"Course Name": "Robotics Process Automation", "Code": "RPA101", "Credits": 3}
    ]
    
    df = pd.DataFrame(courses)
    # Requires 'openpyxl' library
    df.to_excel('raw_data/excel_source/future_courses.xlsx', index=False)
    print(" -> Saved raw_data/excel_source/future_courses.xlsx")

def generate_json_grades():
    """Generates a JSON file with unnormalized grade data."""
    print("--- Creating 'legacy_grades.json' ---")
    grades = []
    # Generate random grades for existing students (IDs 1-50)
    for student_id in range(1, 51):
        grades.append({
            "student_ref_id": student_id,
            "course_code_ref": "DE101", # Assuming this course exists
            "assessment": "Final Project",
            "score": round(random.uniform(60, 100), 2),
            "weight": 0.40
        })
        
    with open('raw_data/json_source/legacy_grades.json', 'w') as f:
        json.dump(grades, f, indent=4)
    print(" -> Saved raw_data/json_source/legacy_grades.json")

if __name__ == "__main__":
    # You might need to install pandas and openpyxl first
    # pip install pandas openpyxl
    try:
        generate_csv_students()
        generate_excel_courses()
        generate_json_grades()
        print("\nSUCCESS: Raw source files created.")
    except ImportError as e:
        print(f"\nERROR: Missing library. {e}")
        print("Run: pip install pandas openpyxl")