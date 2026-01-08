-- ==========================================
-- TEST SCRIPT FOR: hannah.morgan165@capaciti.co.za
-- ==========================================
-- 1. Enroll Hannah in 'Machine Learning Basics' (AI201)
CALL register_student(
    'hannah.morgan165@capaciti.co.za',
    'AI201',
    'Fall 2024'
);
-- 2. Give Hannah a strong Midterm score (88.5%)
CALL record_grade(
    'hannah.morgan165@capaciti.co.za',
    'AI201',
    'Midterm',
    88.5,
    0.30
);
-- 3. Mark Hannah as Present for today's class
CALL mark_attendance(
    'hannah.morgan165@capaciti.co.za',
    'AI201',
    'Present'
);
-- ==========================================
-- VERIFICATION QUERY
-- ==========================================
SELECT s.first_name,
    s.last_name,
    c.course_code,
    g.assessment_type,
    g.score,
    a.status,
    a.attendance_date
FROM students s
    JOIN enrollments e ON s.student_id = e.student_id
    JOIN courses c ON e.course_id = c.course_id
    LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
    LEFT JOIN attendance a ON e.enrollment_id = a.enrollment_id
WHERE s.email = 'hannah.morgan165@capaciti.co.za'
    AND c.course_code = 'AI201';