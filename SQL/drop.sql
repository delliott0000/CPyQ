-- Drop all tables and types from the PostgreSQL database.
-- Run this using `psql`.
-- This is a tool to aid in development. Do not run this in production!

DROP TYPE IF EXISTS permission_scope CASCADE;
DROP TYPE IF EXISTS permission_type CASCADE;
DROP TYPE IF EXISTS task_sort CASCADE;

DROP TABLE IF EXISTS ids CASCADE;

DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP TABLE IF EXISTS assignments CASCADE;

DROP TABLE IF EXISTS permissions CASCADE;

DROP TABLE IF EXISTS tasks CASCADE;

DROP TABLE IF EXISTS quotes CASCADE;