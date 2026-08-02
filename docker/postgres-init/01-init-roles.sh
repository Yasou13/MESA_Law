#!/usr/bin/env bash
set -Eeuo pipefail

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${MESA_LAW_APP_DB_PASSWORD:?MESA_LAW_APP_DB_PASSWORD is required}"
: "${MESA_LAW_WORKER_DB_PASSWORD:?MESA_LAW_WORKER_DB_PASSWORD is required}"
: "${MESA_LAW_MIGRATOR_DB_PASSWORD:?MESA_LAW_MIGRATOR_DB_PASSWORD is required}"
: "${KEYCLOAK_DB:?KEYCLOAK_DB is required}"

psql --set=ON_ERROR_STOP=1 \
  --username "${POSTGRES_USER}" \
  --dbname "${POSTGRES_DB}" \
  --set=app_password="${MESA_LAW_APP_DB_PASSWORD}" \
  --set=worker_password="${MESA_LAW_WORKER_DB_PASSWORD}" \
  --set=migrator_password="${MESA_LAW_MIGRATOR_DB_PASSWORD}" \
  --set=law_db="${POSTGRES_DB}" \
  --set=keycloak_db="${KEYCLOAK_DB}" <<'SQL'
SELECT format(
  'CREATE ROLE mesa_law_app LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS',
  :'app_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mesa_law_app') \gexec

SELECT format(
  'ALTER ROLE mesa_law_app LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS',
  :'app_password'
) \gexec

SELECT format(
  'CREATE ROLE mesa_law_worker LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS',
  :'worker_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mesa_law_worker') \gexec

SELECT format(
  'ALTER ROLE mesa_law_worker LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS',
  :'worker_password'
) \gexec

SELECT format(
  'CREATE ROLE mesa_law_migrator LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS',
  :'migrator_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mesa_law_migrator') \gexec

SELECT format(
  'ALTER ROLE mesa_law_migrator LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS',
  :'migrator_password'
) \gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'keycloak_db', current_user)
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'keycloak_db') \gexec

GRANT ALL PRIVILEGES ON DATABASE :"law_db" TO mesa_law_migrator;
GRANT CONNECT ON DATABASE :"law_db" TO mesa_law_app;
GRANT CONNECT ON DATABASE :"law_db" TO mesa_law_worker;
GRANT ALL ON SCHEMA public TO mesa_law_migrator;
GRANT USAGE ON SCHEMA public TO mesa_law_app;
GRANT USAGE ON SCHEMA public TO mesa_law_worker;

ALTER DEFAULT PRIVILEGES FOR ROLE mesa_law_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mesa_law_app;
ALTER DEFAULT PRIVILEGES FOR ROLE mesa_law_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mesa_law_worker;
ALTER DEFAULT PRIVILEGES FOR ROLE mesa_law_migrator IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO mesa_law_app;
ALTER DEFAULT PRIVILEGES FOR ROLE mesa_law_migrator IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO mesa_law_worker;
SQL
