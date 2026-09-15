# Approved questionnaire answers

Answers previously approved by Security, Legal, or Product and sent to prospects. Reuse where the question matches. Each entry carries the approval date and approver. Older answers may no longer reflect current practice; check against the knowledge base.

| ID | Question (as asked) | Approved answer | Approved | Approver |
|---|---|---|---|---|
| AA-001 | Do you hold ISO 27001 certification? | Yes. Usercentrics is certified against ISO/IEC 27001:2022 by BSI. The certificate is available on request. | 2026-06-20 | Security |
| AA-002 | Do you have a SOC 2 report? | Yes. A SOC 2 Type II report covering Security and Availability is available under NDA. | 2026-07-15 | Security |
| AA-003 | Is data encrypted at rest? | Yes. All customer data at rest is encrypted with AES-256. | 2026-05-10 | Security |
| AA-004 | Is data encrypted in transit? | Yes. All external connections use TLS 1.2 or higher, with TLS 1.3 preferred. Older protocols are disabled. | 2026-05-10 | Security |
| AA-005 | Where is our data hosted? | In Google Cloud Platform in the EU (Belgium, with the Netherlands as secondary) by default. US hosting is available on Enterprise plans. | 2026-03-02 | Product |
| AA-006 | Do you offer on-premise deployment? | No. Usercentrics is delivered as a multi-tenant SaaS. | 2025-11-14 | Product |
| AA-007 | Is MFA enforced for your staff? | Yes. MFA is enforced for all employees and contractors, with hardware security keys required for production access. | 2026-04-22 | Security |
| AA-008 | How quickly do you revoke access when an employee leaves? | Access is revoked within 24 hours of termination, automated through our HR system and identity provider. | 2026-04-22 | Security |
| AA-009 | When was your last penetration test? | Our most recent independent penetration test was completed in September 2024 by an external testing firm, covering the customer-facing applications and APIs. No critical findings were open at report close. An executive summary is available under NDA. | 2024-10-08 | Security |
| AA-010 | Do you perform background checks on employees? | Yes, for employees in Germany and Denmark, to the extent permitted by local law, covering identity and employment history. | 2026-03-15 | Security |
| AA-011 | Within what timeframe do you notify us of a data breach? | Within 48 hours of confirming a personal data breach affecting your data, to your registered security contact. | 2026-06-12 | Legal |
| AA-012 | Have you had a data breach in the last 3 years? | No. Usercentrics has not had a reportable personal data breach in the last 36 months. | 2026-06-12 | Security |
| AA-013 | Who are your subprocessors? | Our current subprocessor list is published online and includes Google Cloud Platform, Cloudflare, Datadog, Zendesk, Salesforce, and HubSpot. | 2026-07-01 | Legal |
| AA-014 | How do you notify us of new subprocessors? | At least 30 days before the new subprocessor begins processing, via our subprocessor page and email to your registered privacy contact, with a right to object as set out in the DPA. | 2026-07-01 | Legal |
| AA-015 | Do you transfer data outside the EEA? | Only where a customer selects US hosting or where a subprocessor operates outside the EEA. Transfers rely on the EU Standard Contractual Clauses with a transfer impact assessment, and the EU-US Data Privacy Framework where applicable. | 2026-07-01 | Legal |
| AA-016 | Do you have a Data Protection Officer? | Yes. Usercentrics has appointed an external DPO, registered with the Bavarian data protection authority. | 2025-09-18 | Legal |
| AA-017 | Do you sign a DPA? | Yes. Our standard DPA is incorporated into all contracts and covers Article 28 GDPR requirements. | 2025-09-18 | Legal |
| AA-018 | What is your RTO and RPO? | RTO is 4 hours and RPO is 1 hour for the Admin Interface and APIs. The banner delivery path is served from the edge and remains available if the origin is unavailable. | 2026-02-01 | Product |
| AA-019 | How often do you test disaster recovery? | A full DR exercise is performed annually. The most recent was November 2025 and met RTO and RPO targets. Backup restores are tested quarterly. | 2026-02-01 | Product |
| AA-020 | Do you have a public status page? | Yes. Service status and incident history are published publicly and customers can subscribe to notifications. | 2026-02-01 | Product |
| AA-021 | What personal data does the CMP collect from end users? | A pseudonymous consent ID, timestamp, consent choices, banner version, and setting ID. No names or email addresses are collected by default. IP addresses are processed transiently for geolocation and not stored. | 2026-02-11 | Product |
| AA-022 | Do you store end-user IP addresses? | No. IP addresses are used transiently to determine region and are not stored. | 2026-02-11 | Product |
| AA-023 | Can we export our consent records? | Yes, at any time via the Admin Interface or the API. | 2026-02-11 | Product |
| AA-024 | What happens to our data when the contract ends? | All customer data is deleted from primary storage within 30 days of termination and from backups within a further 30 days. Written confirmation is available on request. | 2026-02-11 | Legal |
| AA-025 | Do you support SSO for our users? | Yes. SAML 2.0 and OIDC single sign-on are available on Enterprise plans. | 2026-04-22 | Product |
| AA-026 | Does your product support role based access control? | Yes. The Admin Interface provides Owner, Admin, Editor, and Viewer roles. | 2026-04-22 | Product |
| AA-027 | How do you manage vulnerabilities? | Vulnerabilities are triaged by CVSS 3.1 severity with remediation targets of 7 days for Critical, 30 days for High, 90 days for Medium. Dependency and container scanning run in CI and block builds with critical findings. | 2026-06-22 | Security |
| AA-028 | Do you have a secure development lifecycle? | Yes. All code is peer reviewed, and CI runs SAST, dependency scanning, and secret detection on every change. Production deployments are automated. | 2026-06-22 | Security |
| AA-029 | Are production and test environments separated? | Yes. Production, staging, and development are separate GCP projects. No production data is used outside production. | 2026-06-22 | Security |
| AA-030 | Do you have a vulnerability disclosure programme? | Yes. A public vulnerability disclosure policy with a safe-harbour statement is in place. | 2026-08-05 | Security |
| AA-031 | Are you PCI DSS compliant? | Not applicable. Usercentrics does not process, store, or transmit payment card data. | 2026-08-05 | Security |
| AA-032 | Do you provide security awareness training? | Yes. Training is mandatory at onboarding and annually, with completion tracked. Phishing simulations run quarterly. | 2026-03-15 | Security |
| AA-033 | Do you use customer data to train AI models? | No. Customer and end-user data is not used to train machine learning models. | 2026-01-20 | Legal |
| AA-034 | Is your platform TCF compliant? | Yes. Usercentrics is a registered IAB Europe TCF v2.2 CMP and passes annual compliance validation. | 2026-08-05 | Product |
| AA-035 | Do you support Google Consent Mode? | Yes. Google Consent Mode v2 is supported natively, and Usercentrics is a Google Certified CMP Partner. | 2026-06-22 | Product |
| AA-036 | How is privileged access to production logged? | All privileged actions are logged to a tamper-evident store with 12 months retention and reviewed by Security through alerting and weekly manual review. | 2026-04-22 | Security |
| AA-037 | Can we audit you? | Enterprise customers have contractual audit rights once per year on 30 days notice, satisfied in the first instance by our SOC 2 report and ISO certificate. | 2026-08-05 | Legal |
| AA-038 | Do you have cyber insurance? | Yes. Usercentrics maintains cyber liability and professional indemnity insurance. | 2025-09-18 | Legal |
| AA-039 | What is your uptime? | Measured availability of the banner delivery path over the last 12 months is 99.99 percent. Our standard terms set a 99.9 percent monthly availability target for the Admin Interface and APIs. | 2026-02-01 | Product |
| AA-040 | Do you have a business continuity plan? | Yes. A Business Continuity and Disaster Recovery Policy is in place, exercised annually, and available under NDA. | 2026-02-01 | Security |
| AA-041 | Do you support HIPAA? | No. Usercentrics does not process protected health information and does not offer a HIPAA Business Associate Agreement. | 2025-06-30 | Legal |
| AA-042 | Are your employees bound by confidentiality? | Yes. All employees and contractors sign confidentiality agreements before access is granted. | 2026-03-15 | Legal |
