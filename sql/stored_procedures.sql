-- ==========================================
-- 1. PROCEDURE: REGISTER_STUDENT
-- Purpose: Safely enroll a student in a course using email & course code
-- Logic: Looks up IDs automatically; fails gracefully if not found.
-- ==========================================
CREATE OR REPLACE PROCEDURE register_student(
        p_email VARCHAR,
        p_course_code VARCHAR,
        p_semester VARCHAR
    ) LANGUAGE plpgsql AS $$
DECLARE v_student_id INT;
v_course_id INT;
BEGIN -- 1. Get Student ID
SELECT student_id INTO v_student_id
FROM students
WHERE email = p_email;
IF v_student_id IS NULL THEN RAISE EXCEPTION 'Student % not found',
p_email;
END IF;
-- 2. Get Course ID
SELECT course_id INTO v_course_id
FROM courses
WHERE course_code = p_course_code;
IF v_course_id IS NULL THEN RAISE EXCEPTION 'Course % not found',
p_course_code;
END IF;
-- 3. Insert Enrollment (Ignore if already exists)
INSERT INTO enrollments (student_id, course_id, semester, enrollment_date)
VALUES (
        v_student_id,
        v_course_id,
        p_semester,
        CURRENT_DATE
    ) ON CONFLICT (student_id, course_id, semester) DO NOTHING;
RAISE NOTICE 'Student % enrolled in % successfully.',
p_email,
p_course_code;
END;
$$;
-- ==========================================
-- 2. PROCEDURE: RECORD_GRADE
-- Purpose: Add a grade OR update it if it already exists (Upsert)
-- ==========================================
CREATE OR REPLACE PROCEDURE record_grade(
        p_email VARCHAR,
        p_course_code VARCHAR,
        p_assessment VARCHAR,
        p_score DECIMAL,
        p_weight DECIMAL
    ) LANGUAGE plpgsql AS $$
DECLARE v_enrollment_id INT;
BEGIN -- 1. Find the specific enrollment ID
SELECT e.enrollment_id INTO v_enrollment_id
FROM enrollments e
    JOIN students s ON e.student_id = s.student_id
    JOIN courses c ON e.course_id = c.course_id
WHERE s.email = p_email
    AND c.course_code = p_course_code;
IF v_enrollment_id IS NULL THEN RAISE EXCEPTION 'Enrollment not found for % in %',
p_email,
p_course_code;
END IF;
-- 2. Update if exists, Insert if new (Upsert logic)
-- Note: We check if a grade exists for this enrollment + assessment type
IF EXISTS (
    SELECT 1
    FROM grades
    WHERE enrollment_id = v_enrollment_id
        AND assessment_type = p_assessment
) THEN
UPDATE grades
SET score = p_score,
    weight = p_weight
WHERE enrollment_id = v_enrollment_id
    AND assessment_type = p_assessment;
RAISE NOTICE 'Updated existing grade for %.',
p_email;
ELSE
INSERT INTO grades (enrollment_id, assessment_type, score, weight)
VALUES (v_enrollment_id, p_assessment, p_score, p_weight);
RAISE NOTICE 'Added new grade for %.',
p_email;
END IF;
END;
$$;
-- ==========================================
-- 3. PROCEDURE: MARK_ATTENDANCE
-- Purpose: Quickly mark a student present/absent
-- ==========================================
CREATE OR REPLACE PROCEDURE mark_attendance(
        p_email VARCHAR,
        p_course_code VARCHAR,
        p_status VARCHAR,
        p_date DATE DEFAULT CURRENT_DATE
    ) LANGUAGE plpgsql AS $$
DECLARE v_enrollment_id INT;
BEGIN -- 1. Find Enrollment
SELECT e.enrollment_id INTO v_enrollment_id
FROM enrollments e
    JOIN students s ON e.student_id = s.student_id
    JOIN courses c ON e.course_id = c.course_id
WHERE s.email = p_email
    AND c.course_code = p_course_code;
IF v_enrollment_id IS NULL THEN RAISE EXCEPTION 'Enrollment not found.';
END IF;
-- 2. Insert Attendance
INSERT INTO attendance (enrollment_id, attendance_date, status)
VALUES (v_enrollment_id, p_date, p_status);
RAISE NOTICE 'Attendance marked for %: %',
p_email,
p_status;
END;
$$;