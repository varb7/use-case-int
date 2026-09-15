# Product Architecture Overview

**Owner:** Product. **Last reviewed:** 2026-06-22.

## Components

The Consent Management Platform has three parts:

1. **Script and banner.** A JavaScript library embedded on the customer's website or app SDK (iOS, Android, Flutter, React Native). It renders the consent banner, records choices, and signals consent state to tags and vendors via the TCF API, Google Consent Mode, and a custom event API.
2. **Admin Interface.** A web application where the customer configures banners, services, legal texts, and users, and views analytics.
3. **Backend APIs.** Configuration delivery, consent record ingestion, analytics aggregation, and a public REST API for customers.

## Hosting

All components run on Google Cloud Platform in the EU by default (see `06-data-residency-and-retention.md`). The script and configuration are cached at Cloudflare's edge. Usercentrics operates as a multi-tenant SaaS. Single-tenant or on-premise deployment is not offered.

## Secure development

Code is peer reviewed before merge. CI runs static analysis (SAST), dependency vulnerability scanning, and secret detection on every pull request. Container images are scanned before deployment. Dependencies with critical vulnerabilities block the build. Production deployments are automated via CI/CD with no manual access to production required.

## Vulnerability management

Vulnerabilities are triaged by severity using CVSS 3.1. Remediation targets: Critical 7 days, High 30 days, Medium 90 days, Low next planned release.

## Logging and monitoring

Application and infrastructure logs are centralised. Personal data is excluded from application logs by design and verified by automated scanning. Uptime and performance are monitored continuously with alerting to the on-call Platform Engineer.

## Environments

Production, staging, and development environments are fully separated at the project level in GCP. No production data is used in non-production environments.

## Change management

All changes to production go through version control, peer review, automated tests, and staged rollout. Emergency changes follow the same path with an expedited review and a retrospective ticket.
