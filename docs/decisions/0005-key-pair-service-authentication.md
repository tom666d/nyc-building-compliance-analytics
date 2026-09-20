# ADR 0005: Use key-pair authentication for the local pipeline

## Status

Accepted

## Context

Python ingestion and dbt must authenticate to Snowflake without embedding the portfolio owner's human password in source code or requiring an interactive second factor during every automated run. Snowflake distinguishes human users from non-interactive service users and is deprecating single-factor password authentication for automated workloads.

## Decision

Create a dedicated `TYPE = SERVICE` identity named `NYC_DOB_PIPELINE`. Register its public key in Snowflake and keep the matching encrypted PKCS#8 private key plus passphrase outside Git. Grant the service identity the existing loader, transformer, and reader roles, but activate only the workload-specific primary role for each connection.

The local Python connector and dbt profile accept private-key settings through environment variables. Password authentication remains available as a compatibility fallback for tests and future environments, but the configuration rejects simultaneous password and private-key settings.

## Consequences

- A leaked repository does not reveal an authentication secret.
- Scheduled local runs do not need the developer's human password or interactive authentication.
- Query history identifies automated activity through a dedicated service identity.
- The private key and passphrase must be protected and rotated together.
- Granting several workload roles to one development identity is convenient but is weaker isolation than separate production service identities. Production deployment should use one identity per workload or an equivalent centrally managed workload identity.
