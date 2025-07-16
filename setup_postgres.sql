-- PostgreSQL Setup Script for Japanese Learning Website Migration
-- Run this script as a PostgreSQL superuser (usually 'postgres')
-- Create the user with a password
-- Replace 'your_password_here' with your actual password
ALTER ROLE app_user WITH PASSWORD 'wL9D3nijM';

SELECT 'PASSWORD setup completed successfully!' as status;
