-- ==========================================
-- 1. COURSE PERFORMANCE REPORT
-- Requirement: Calculate average grade per course [cite: 132]
-- ==========================================
SELECT c.course_code,
    c.course_name,
    COUNT(g.grade_id) as total_assessments,
    ROUND(AVG(g.score), 2) as average_score,
    CASE
        WHEN AVG(g.score) >= 90 THEN 'Excellent'
        WHEN AVG(g.score) >= 75 THEN 'Good'
        WHEN AVG(g.score) >= 60 THEN 'Average'
        ELSE 'Needs Improvement'
    END as performance_category
FROM courses c
    JOIN enrollments e ON c.course_id = e.course_id
    JOIN grades g ON e.enrollment_id = g.enrollment_id
GROUP BY c.course_id,
    c.course_name
ORDER BY average_score DESC;
-- ==========================================
-- 2. AT-RISK STUDENTS (LOW ATTENDANCE)
-- Requirement: Find students with attendance below 75% [cite: 133]
-- Logic: (Present Days / Total Days) * 100
-- ==========================================
WITH AttendanceStats AS (
    SELECT e.student_id,
        e.course_id,
        COUNT(*) as total_classes,
        SUM(
            CASE
                WHEN a.status IN ('Present', 'Late') THEN 1
                ELSE 0
            END
        ) as classes_attended
    FROM attendance a
        JOIN enrollments e ON a.enrollment_id = e.enrollment_id
    GROUP BY e.student_id,
        e.course_id
)
SELECT s.first_name,
    s.last_name,
    c.course_code,
    stat.classes_attended,
    stat.total_classes,
    ROUND(
        (
            stat.classes_attended::decimal / stat.total_classes
        ) * 100,
        1
    ) as attendance_pct
FROM AttendanceStats stat
    JOIN students s ON stat.student_id = s.student_id
    JOIN courses c ON stat.course_id = c.course_id
WHERE (
        stat.classes_attended::decimal / stat.total_classes
    ) < 0.75
ORDER BY attendance_pct ASC;
-- ==========================================
-- 3. DEAN'S LIST (TOP 10 STUDENTS)
-- Requirement: List top 10 students by GPA [cite: 135]
-- Logic: Weighted average of all their grades across all courses
-- ==========================================
SELECT s.student_id,
    s.first_name,
    s.last_name,
    s.major,
    ROUND(AVG(g.score), 2) as overall_gpa
FROM students s
    JOIN enrollments e ON s.student_id = e.student_id
    JOIN grades g ON e.enrollment_id = g.enrollment_id
GROUP BY s.student_id
HAVING COUNT(g.score) > 2 -- Filter: Must have at least 3 graded items
ORDER BY overall_gpa DESC
LIMIT 10;
-- ==========================================
-- 4. POPULARITY CONTEST (ENROLLMENT STATS)
-- Requirement: Show course enrollment statistics [cite: 137]
-- ==========================================
SELECT c.course_name,
    COUNT(e.student_id) as total_students,
    e.semester
FROM courses c
    LEFT JOIN enrollments e ON c.course_id = e.course_id
GROUP BY c.course_name,
    e.semester
ORDER BY total_students DESC;