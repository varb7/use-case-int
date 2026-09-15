# Access Control

**Owner:** Security. **Last reviewed:** 2026-04-20.

## Principles

Access follows least privilege and need to know. All access to production systems is role based and tied to a named individual. Shared accounts are prohibited.

## Authentication

Single sign-on via the corporate identity provider (Okta) is mandatory for all internal systems. Multi-factor authentication is enforced for all employees and contractors with no exceptions. Hardware security keys (FIDO2) are required for production and cloud console access.

## Authorisation and reviews

Access to production is granted via IAM roles mapped to job function. Elevated access to production data requires a ticketed request approved by the Head of Security or the VP Engineering and is time-limited to 8 hours. Access reviews are performed quarterly for production systems and semi-annually for corporate systems. Access is revoked within 24 hours of termination, automated via the HR system to Okta deprovisioning.

## Customer access to the product

The Usercentrics Admin Interface supports role based access control with the roles Owner, Admin, Editor, and Viewer. Customers on Enterprise plans can enforce SSO via SAML 2.0 or OIDC. MFA is available to all customers and can be enforced at account level by an Owner.

## Privileged access logging

All privileged actions in production are logged to a central, tamper-evident log store with 12 months retention. Logs are reviewed by Security through automated alerting and a weekly manual review of high-risk actions.

## Remote access

There is no VPN into production. Access is via identity-aware proxy with device posture checks. Production database access from engineer workstations is not permitted; queries run through an audited bastion tool.
