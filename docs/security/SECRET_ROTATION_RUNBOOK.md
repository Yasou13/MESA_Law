# MESA Law Secret Rotation Runbook

## 1. Overview
All secrets in MESA Law (Database passwords, Keycloak client secrets, API keys, JWT signing keys) must be rotated periodically and immediately upon suspected compromise.
**No secrets are stored in plain-text `.env` files in production.** We use HashiCorp Vault (or External Secrets Operator in Kubernetes) to inject secrets as tmpfs mounts or environment variables at runtime.

## 2. JWT Signing Key Rotation (Keycloak)
1. Login to Keycloak Admin Console.
2. Navigate to `Realm Settings -> Keys`.
3. Generate a new `RS256` key pair. Set `Priority` higher than the current active key.
4. Set the old key to `Passive` (clients can still verify existing tokens until they expire, but new tokens will use the new key).
5. After 24 hours, safely delete the passive key.

## 3. Database Password Rotation
1. Update the password in Vault/Secret Manager:
   ```bash
   vault kv put secret/mesa-law/prod/db_password value="new_secure_password"
   ```
2. Update the actual PostgreSQL password:
   ```sql
   ALTER USER mesa_admin WITH PASSWORD 'new_secure_password';
   ```
3. Restart the FastAPI and Worker deployments to pick up the new secret from Vault.
   ```bash
   kubectl rollout restart deployment/mesa-api
   kubectl rollout restart deployment/mesa-worker
   ```

## 4. Third-Party API Keys (LLM Providers)
1. Generate a new key from the provider (e.g., Anthropic, OpenAI).
2. Store the new key in Vault (`secret/mesa-law/prod/llm_api_key`).
3. Restart deployments.
4. Monitor logs for 15 minutes to ensure no `401 Unauthorized` errors occur.
5. Revoke the old key from the provider console.
