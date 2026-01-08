-- ==========================================
-- SCRIPT: CREATE PERFORMANCE INDEXES
-- Purpose: Optimize lookup speeds for frequent queries
-- ==========================================
-- 1. Index for searching students by name (e.g., in the CLI or UI)
CREATE INDEX IF NOT EXISTS idx_students_lastname ON students(last_name);
-- 2. Index for finding all enrollments for a specific student 
-- (Speeds up joins between Students and Enrollments)
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
-- 3. Index for finding all students in a specific course 
-- (Speeds up joins between Courses and Enrollments)
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
-- 4. Index for attendance reports filtered by date range
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
-- Note: We do not index 'email' or 'course_code' manually because 
-- the UNIQUE constraint on those columns already created an index for us.