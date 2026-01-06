# Student-Records-Management-System

erDiagram
    STUDENTS ||--o{ ENROLLMENTS : "registers for"
    COURSES ||--o{ ENROLLMENTS : "has"
    ENROLLMENTS ||--o{ GRADES : "receives"
    ENROLLMENTS ||--o{ ATTENDANCE : "records"

    STUDENTS {
        int student_id PK
        string first_name
        string last_name
        string email
    }
    COURSES {
        int course_id PK
        string course_name
        string course_code
    }
    ENROLLMENTS {
        int enrollment_id PK
        int student_id FK
        int course_id FK
        date enrollment_date
    }
    GRADES {
        int grade_id PK
        int enrollment_id FK
        string assessment_type
        float score
    }