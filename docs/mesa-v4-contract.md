# MESA Core v4 Integration Contract

MESA Law is pinned to the read-only Core source at commit
`c5901881fc414dfd3475c386d2c59bb461e65cd2`, package version `0.7.1`.

The HTTP boundary uses `X-API-Key` and only the `/v4/catalog/*`,
`/v4/sessions/*`, `/v4/memory/*`, `/v4/mutations/*`, and `/v4/capability`
surfaces. A `202` memory response is durable admission, not publication.
Publication is complete only after mutation state `COMMITTED`.

`REJECTED`, `DEAD_LETTER`, `ROLLED_BACK`, and `BLOCKED` are also terminal
states and must never be presented as successful publication. Rebuild is a
documented `501` capability and remains disabled in MESA Law.

## Authorization onboarding

Law does not manufacture Core roles. Before a binding can become ready, an
operator must use the pinned Core repository's `mesa-v4-admin` commands to:

1. issue the API key for the Law principal;
2. grant tenant/workspace ownership needed for catalog onboarding;
3. grant dataset writer/reader roles;
4. grant the configured agent `SESSION_CREATE` and dataset permissions.

Law's preflight reads capability, visible workspaces, and visible datasets.
Missing grants produce a degraded binding with an actionable error; they do
not trigger an implicit role grant or fallback to a mock adapter.

## Runtime boundary

The external repository is never imported through a filesystem path and is
not merged into this repository. Contract tests use local HTTP fixtures. Live
Core startup and integration remain a separate release gate.
