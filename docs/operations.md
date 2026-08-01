# Bounded Operations and Release Gates

MESA Law is designed to run on the target 16 GB, CPU-only development host
without local model weights, GPU packages, large datasets, or a locally built
MESA Core image.

## Runtime profiles

- `docker compose --profile core up` starts only the Law application and its
  required PostgreSQL, Redis, MinIO, Keycloak, and ClamAV dependencies.
- `--profile observability` is opt-in and adds the OTel/Grafana stack. Set
  `MESA_LAW_OBSERVABILITY_ENABLED=true` only when the collector profile is
  running.
- `--profile edge` is opt-in and adds Caddy.
- `docker-compose.lite.yml` is development/test-only. It explicitly disables
  ClamAV readiness and cannot start in production because production config
  requires malware scanning.

PostgreSQL, Redis, MinIO, Keycloak, ClamAV, the API, worker, and web services
have memory limits. Worker concurrency is fixed to `1` in every supplied Law
profile. Keycloak persists to the separate `keycloak` database rather than the
Law canonical database. The PostgreSQL bootstrap consumes secrets from the
environment and grants the migrator no superuser, role-creation, database-
creation, or RLS-bypass privilege.

The checked-in Keycloak realm contains no user password and resolves its
client secret from an environment placeholder, as supported by the
[Keycloak realm import contract](https://www.keycloak.org/server/importExport#_using_environment_variables_within_the_realm_configuration_files).

## Health and telemetry

- `/health/live` reports process liveness only.
- `/health/ready` performs bounded async checks. PostgreSQL, Redis, MinIO,
  Keycloak, and required ClamAV failures produce HTTP 503. Missing MESA Core is
  reported as degraded so citation QA can abstain or use verified local lexical
  evidence.
- Request, trace, job, matter, and MESA mutation correlation values are added
  to logs. Authorization values, API keys, passwords, tokens, database
  credentials, document text, evidence, questions, answers, bodies, and bytes
  are redacted by the central logging boundary.
- OTel instruments record queue-depth snapshots, stale lease recovery,
  document-pipeline failures, job duration, MESA request latency, mutation
  terminal states, and citation verification failures. The authenticated
  `/api/v1/operations/metrics` endpoint supplies tenant- and matter-scoped
  database snapshots for queue depth, stale leases, pipeline failures, review
  backlog, and terminal mutation states.

## Fail-closed Law-side gate

Run `make release-gate` from a clean checkout with locked dependencies already
installed. It runs all checks sequentially and stops on the first non-zero
exit. Before browser acceptance it requires at least 3 GiB available memory
and low Linux memory pressure. It validates Compose files without starting or
pulling any image.

The final success message explicitly excludes live external MESA Core
integration. A skipped, timed-out, unavailable-service, or external-Core test
is never counted as passed.
