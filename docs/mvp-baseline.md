# MESA Law MVP Baseline

Recorded on 2026-08-01 before MVP implementation, at commit
`f2eb643b7c740eccfd4de5f8edb62b14305e713c`.

## Environment

| Tool | Version |
| --- | --- |
| Project Python | 3.13.12 |
| System Python | 3.10.12 |
| Node.js | 24.14.0 |
| pnpm | 11.17.0 |
| Docker | 29.6.2 |
| Alembic head | `c150029e598e` (single head) |

The host has 16 GB RAM and no GPU. Local model weights, GPU stacks, large
datasets, and large new container images are outside the implementation
budget.

## Initial gates

| Gate | Result | Evidence |
| --- | --- | --- |
| `python -m compileall -q apps tests evaluation` | PASS | Exit code 0 |
| `ruff check apps tests` | FAIL | 99 violations |
| `ruff format --check apps tests` | FAIL | 101 files require formatting |
| `mypy apps` | FAIL | 65 errors in 24 files |
| Pytest | FAIL / BLOCKED | 180 tests collected; dependency probe returns 401 and an RLS test waits for unavailable PostgreSQL |
| Frontend lint | PASS WITH WARNING | One warning |
| Frontend typecheck | FAIL | `sonner` is imported but not installed |
| Frontend unit tests | FAIL | Timeline test renders no events |
| Frontend build | FAIL | `next/font/google` attempts a network font download |
| OpenAPI drift | FAIL | Checked-in schema differs from the live FastAPI schema; one duplicate operation ID exists |
| Local test runner | FAIL-CLOSED VIOLATION | Ruff, Bandit, and Alembic failures are swallowed before an unconditional success message |

These results establish **NO-GO**. A check that is skipped, times out, lacks a
required service, or exits non-zero is not reported as passed.

## External integration boundary

MESA Core v4 is referenced read-only from `/home/yasin/Desktop/MESA`, pinned to
commit `c5901881fc414dfd3475c386d2c59bb461e65cd2` (version `0.7.1`). This project
will not merge or modify that repository. If the only remaining release gate
requires starting, building, downloading, or live-testing that external Core,
the final status is `LAW-SIDE READY / OVERALL NO-GO`.
