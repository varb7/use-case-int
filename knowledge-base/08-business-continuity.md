# Business Continuity and Disaster Recovery

**Owner:** Platform Engineering. **Last reviewed:** 2026-01-28.

## Availability

The Consent Management Platform is designed for high availability. The script delivery path (the banner served to end users) is served from Cloudflare's global edge and is architected to remain available even if the origin is unavailable. The measured availability of the script delivery path over the last 12 months is 99.99 percent. The Admin Interface and APIs are deployed across multiple availability zones in the primary region.

## Availability commitment

Our standard terms of service set an availability target of 99.9 percent per calendar month for the Admin Interface and APIs. This is a target, not a contractual service level with credits. Custom service level agreements with defined credits are available on Enterprise contracts and are agreed by Legal on a case by case basis. Solutions Engineers should not confirm SLA terms; route to Legal.

## Recovery objectives

Recovery Time Objective (RTO): 4 hours for the Admin Interface and APIs. Recovery Point Objective (RPO): 1 hour, based on continuous database replication and hourly snapshots. The script delivery path has no meaningful RPO as configuration is cached at the edge.

## Backups

Databases are replicated synchronously to a secondary zone and snapshotted hourly. Snapshots are encrypted (see `02-encryption-and-key-management.md`) and retained for 30 days. Backup restoration is tested quarterly by restoring to an isolated environment and validating integrity.

## DR testing

A full disaster recovery exercise, failing the production environment to the secondary zone, is performed annually. The most recent exercise was in November 2025 and met the RTO and RPO targets.

## Status communication

Real-time service status and incident history are published at a public status page. Customers can subscribe to notifications.
