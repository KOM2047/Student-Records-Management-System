-- ==========================================
-- SECTION 1: TABLES (Creation Safety)
-- Uses "IF NOT EXISTS" to prevent errors on re-runs
-- ==========================================
-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE,
    major VARCHAR(50)
);
-- 2. Courses Table
CREATE TABLE IF NOT EXISTS courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    credits INT CHECK (credits > 0)
);
-- 3. Enrollments Table
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(student_id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    semester VARCHAR(20),
    -- Unique constraint ensures we don't accidentally double-enroll a student
    CONSTRAINT unique_enrollment UNIQUE (student_id, course_id, semester)
);
-- 4. Grades Table
CREATE TABLE IF NOT EXISTS grades (
    grade_id SERIAL PRIMARY KEY,
    enrollment_id INT REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    assessment_type VARCHAR(50) NOT NULL,
    score DECIMAL(5, 2) CHECK (
        score >= 0
        AND score <= 100
    ),
    weight DECIMAL(3, 2)
);
-- 5. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id SERIAL PRIMARY KEY,
    enrollment_id INT REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    attendance_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) CHECK (
        status IN ('Present', 'Absent', 'Late', 'Excused')
    )
);
-- ==========================================
-- SECTION 2: UPDATES (Schema Evolution)
-- This handles your "Render Updates" requirement.
-- If you need to add a column later, you add a block here.
-- ==========================================
-- Example: Let's say you decide later to add "phone_number" to students.
-- Running this line is safe even if the column already exists.
ALTER TABLE students
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(15);
-- Example: Adding "department" to courses
ALTER TABLE courses
ADD COLUMN IF NOT EXISTS department VARCHAR(50);
-- ==========================================
-- SECTION 3: SEED DATA (Content Check)
-- Checks if content exists. If yes, it skips (DO NOTHING).
-- ==========================================
-- Insert a test student safely
INSERT INTO students (first_name, last_name, email, major)
VALUES (
        'John',
        'Doe',
        'john.doe@example.com',
        'Computer Science'
    ) ON CONFLICT (email) DO NOTHING;
-- ^ This is the magic line. If 'john.doe@example.com' exists, it stops silently.
-- Insert a test course safely
INSERT INTO courses (course_name, course_code, credits)
VALUES ('Intro to Data Engineering', 'DE101', 3) ON CONFLICT (course_code) DO NOTHING;