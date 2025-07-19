-- Fresh PostgreSQL Database Setup Script for Japanese Learning Website
-- Run this script as a PostgreSQL superuser (usually 'postgres')
-- This creates a completely new database and user from scratch

-- Drop existing database if it exists (to start fresh)
DROP DATABASE IF EXISTS japanese_learning_new;

-- Create or update user with the specified password
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        ALTER USER app_user WITH PASSWORD 'E8BnuCBpWKP';
    ELSE
        CREATE USER app_user WITH PASSWORD 'E8BnuCBpWKP';
    END IF;
END
$$;

-- Create new database
CREATE DATABASE japanese_learning_new OWNER app_user;

-- Connect to the new database to set up permissions
\c japanese_learning_new

-- Grant all necessary permissions to the user
GRANT ALL PRIVILEGES ON DATABASE japanese_learning_new TO app_user;
GRANT ALL ON SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Set default privileges for future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

SELECT 'Fresh PostgreSQL database setup completed successfully!' as status;
SELECT 'Database: japanese_learning_new' as database_name;
SELECT 'User: app_user' as username;
SELECT 'Password: E8BnuCBpWKP' as password;
