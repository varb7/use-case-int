# Encryption and Key Management

**Owner:** Security. **Last reviewed:** 2026-05-02.

## Data in transit

All external traffic is served over TLS 1.2 or higher. TLS 1.0 and 1.1 are disabled. TLS 1.3 is preferred where the client supports it. HSTS is enforced on all customer-facing domains with a max-age of one year. Internal service-to-service traffic inside the production VPC is encrypted with mutual TLS via the service mesh.

## Data at rest

All customer data at rest is encrypted with AES-256. This covers primary databases, object storage, backups, and snapshots. Encryption is enabled at the storage layer by the cloud provider (Google Cloud Platform) using provider-managed keys by default.

## Key management

Encryption keys are managed in Google Cloud KMS. Keys are rotated automatically every 90 days. Access to KMS is restricted to the platform team via IAM roles and is logged. Customer-managed encryption keys (CMEK) are not offered in the standard product.

## Secrets

Application secrets are stored in Google Secret Manager. No secrets are stored in source code. Static analysis in CI blocks commits containing credential patterns.

## Hashing and passwords

User passwords for the Usercentrics Admin Interface are hashed with bcrypt (cost factor 12). Single sign-on via SAML 2.0 and OIDC is available on Enterprise plans, in which case Usercentrics does not store passwords.

## Cryptographic standards

Only algorithms approved under the Cryptography Policy are permitted: AES-256, RSA 2048 or higher, ECDSA P-256 or higher, SHA-256 or higher. MD5 and SHA-1 are prohibited for security purposes.
