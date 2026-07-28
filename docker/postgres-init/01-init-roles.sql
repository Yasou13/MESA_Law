-- 01-init-roles.sql
-- Bootstraps the necessary roles for MESA Law with distinct privileges

-- Application Role (NOSUPERUSER, NOBYPASSRLS)
CREATE ROLE mesa_law_app WITH LOGIN PASSWORD 'app_pass' NOSUPERUSER NOBYPASSRLS;

-- Worker Role (NOSUPERUSER, NOBYPASSRLS)
CREATE ROLE mesa_law_worker WITH LOGIN PASSWORD 'worker_pass' NOSUPERUSER NOBYPASSRLS;

-- Migrator Role (Used by Alembic)
CREATE ROLE mesa_law_migrator WITH LOGIN PASSWORD 'migrator_pass' CREATEROLE CREATEDB;

-- Note: The database 'mesa_law' is created by the postgres docker image natively
-- due to POSTGRES_DB env var. Here we just grant privileges.

GRANT ALL PRIVILEGES ON DATABASE mesa_law TO mesa_law_migrator;
GRANT CONNECT ON DATABASE mesa_law TO mesa_law_app;
GRANT CONNECT ON DATABASE mesa_law TO mesa_law_worker;

-- Since public schema might be restricted, let migrator own it
\c mesa_law
GRANT ALL ON SCHEMA public TO mesa_law_migrator;
GRANT USAGE ON SCHEMA public TO mesa_law_app;
GRANT USAGE ON SCHEMA public TO mesa_law_worker;
