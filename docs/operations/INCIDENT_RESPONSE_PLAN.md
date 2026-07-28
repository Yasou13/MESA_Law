# MESA Law Incident Response Plan

## 1. Severity Levels
- **SEV-1 (Critical)**: Total system outage, cross-tenant data leak, or complete database corruption.
- **SEV-2 (High)**: Core feature degraded (Parser offline, LLM offline, Login issues).
- **SEV-3 (Medium)**: Single user/matter issue, UI bug affecting workflow.

## 2. Immediate Action Plan (SEV-1 Data Leak)
1. Trigger **Kill Switch**: Disallow all logins via Keycloak (Set Realm to offline).
2. Evict active sessions using `kc.sh admin sessions delete`.
3. Inform all Pilot Champions within 30 minutes of discovery.
4. Preserve system state for forensic analysis. DO NOT purge logs.
5. Identify the vulnerability (e.g., RLS bypass, Prompt Injection).
6. Deploy hotfix -> Validate -> Restore Service.

## 3. Communication Protocol
- Dedicated Slack Channel: `#mesa-pilot-ops`
- PagerDuty integrated with OpenTelemetry Alerts for `HTTP 5xx > 5%` and `Latency P95 > 5s`.
