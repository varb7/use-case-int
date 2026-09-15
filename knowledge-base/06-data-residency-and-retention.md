# Data Residency and Retention

**Owner:** Product (residency), Legal (retention). **Last reviewed:** 2026-02-11.

## Hosting regions

Customer data is hosted in Google Cloud Platform. The default and primary region is the EU (europe-west1, Belgium, with europe-west4, Netherlands, as the secondary zone). Customers on Enterprise plans may select US hosting (us-central1) at account creation. Region cannot be changed after account creation without a migration project.

## What data is stored

The Consent Management Platform stores:

- Consent records: a pseudonymous consent ID, timestamp, consent choices, banner version, and the customer's setting ID. No end-user names or email addresses are collected by the CMP by default.
- Customer configuration: banner settings, service and vendor lists, legal texts.
- Customer account data: names and email addresses of the customer's own admin users.

IP addresses of end users are processed transiently to determine geolocation for banner selection and are not stored.

## Retention

Consent records are retained for 12 months from the date of the consent event, after which they are deleted from primary storage. Backups containing consent records are retained for a further 30 days and then expire. Customers can export consent records at any time via the Admin Interface or API.

Customer configuration data is retained for the duration of the contract and deleted within 30 days of contract termination unless the customer requests earlier deletion.

## Deletion on termination

On termination, all customer data is deleted from primary storage within 30 days and from backups within a further 30 days. A deletion confirmation is provided in writing on request.
