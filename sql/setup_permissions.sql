-- ==========================================
-- SCRIPT: USER & PERMISSIONS SETUP
-- Purpose: Create a secured 'app_user' for the Python application
-- ==========================================
-- 1. Safely create the user (Role) if it doesn't exist
DO $do$ BEGIN IF NOT EXISTS (
    SELECT
    FROM pg_catalog.pg_roles -- Check system catalog
    WHERE rolname = 'app_user'
) THEN CREATE USER app_user WITH PASSWORD 'secure_pass_123';
END IF;
END $do$;
-- 2. Grant permission to connect to the specific database
GRANT CONNECT ON DATABASE student_records_db TO app_user;
-- 3. Grant usage on the schema (required to see tables)
GRANT USAGE ON SCHEMA public TO app_user;
-- 4. Grant Data Access: Allow Reading and Writing data
-- We explicitly list permissions rather than granting ALL PRIVILEGES (Least Privilege Principle)
GRANT SELECT,
    INSERT,
    UPDATE,
    DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- 5. CRITICAL: Grant permission to use "Sequences" (Auto-increment IDs)
-- Without this, 'app_user' cannot insert new rows because it cannot 
-- increment the student_id or course_id counters.
GRANT USAGE,
    SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- 6. Future-proofing: Ensure new tables created in the future also grant rights to this user automatically
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT,
    INSERT,
    UPDATE,
    DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE,
    SELECT ON SEQUENCES TO app_user;