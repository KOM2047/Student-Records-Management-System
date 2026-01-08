-- ==========================================
-- VIEW: STUDENT TRANSCRIPTS
-- Purpose: A simple, readable academic history for every student.
-- Hides the complexity of joining 4 tables.
-- ==========================================
CREATE OR REPLACE VIEW student_transcripts_view AS
SELECT s.student_id,
    s.first_name,
    s.last_name,
    s.email,
    c.course_code,
    c.course_name,
    c.credits,
    e.semester,
    -- Aggregate multiple assessments (Midterm, Final) into one final score per course
    -- If no grades exist yet, show NULL
    ROUND(AVG(g.score), 2) as final_score,
    -- Calculate Letter Grade based on the average score
    CASE
        WHEN AVG(g.score) >= 90 THEN 'A'
        WHEN AVG(g.score) >= 80 THEN 'B'
        WHEN AVG(g.score) >= 70 THEN 'C'
        WHEN AVG(g.score) >= 60 THEN 'D'
        WHEN AVG(g.score) IS NULL THEN 'N/A'
        ELSE 'F'
    END as letter_grade
FROM students s
    JOIN enrollments e ON s.student_id = e.student_id
    JOIN courses c ON e.course_id = c.course_id
    LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
GROUP BY s.student_id,
    s.first_name,
    s.last_name,
    s.email,
    c.course_code,
    c.course_name,
    c.credits,
    e.semester;