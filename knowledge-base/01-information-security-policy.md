# Information Security Policy (summary)

**Owner:** Security. **Last reviewed:** 2026-03-15. **Version:** 4.2.

## Scope and governance

The Information Security Management System (ISMS) covers all Usercentrics production systems, corporate IT, and personnel. It is certified against ISO/IEC 27001:2022 (see `07-certifications-audits.md`). The ISMS is owned by the Head of Security, who reports to the CTO. Policies are reviewed at least annually and on material change.

## Policy set

The following policies are in force and available to customers under NDA on request:

- Information Security Policy
- Access Control Policy
- Cryptography Policy
- Incident Response Policy
- Business Continuity and Disaster Recovery Policy
- Secure Development Lifecycle Policy
- Supplier Security Policy
- Acceptable Use Policy
- Data Classification and Handling Policy

## Risk management

Risk assessments are performed annually and on significant change, using a 5x5 likelihood and impact matrix. The risk register is reviewed quarterly by the Security Steering Committee (CTO, Head of Security, Head of Legal, VP Engineering).

## Personnel security

All employees and contractors sign confidentiality agreements before access is granted. Background checks are performed for all employees in Germany and Denmark to the extent permitted by local law, covering identity and employment history. Security awareness training is mandatory at onboarding and annually thereafter, with completion tracked. Phishing simulations run quarterly.

## Asset management

All production assets are inventoried in the configuration management database and tagged with an owner and data classification. Laptops are managed via MDM with full disk encryption, screen lock, and remote wipe enforced.

## Security team

Security is a dedicated function of 4 people: Head of Security, 2 Security Engineers, 1 GRC Engineer. A 24/7 on-call rotation covers security incidents (see `04-incident-response.md`).
