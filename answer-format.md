# Presales questionnaire answer format

Every answered question carries these fields. Return them as columns appended to the prospect's CSV, keeping the prospect's original columns and row order intact so the file can be sent back in their format.

| Field | Allowed values | Notes |
|---|---|---|
| `status` | Yes, No, Partial, Not applicable, Cannot answer | Cannot answer is a valid and expected outcome. It is not a failure. |
| `answer` | Free text, 1 to 4 sentences | Written in first person plural, as Usercentrics speaking to the prospect. Plain language, no internal jargon. |
| `evidence` | File name plus section heading, or approved answer ID | Mandatory when status is Yes, No, Partial, or Not applicable. Empty when status is Cannot answer. |
| `owner` | Security, Legal, Product, Sales, or empty | Mandatory when status is Cannot answer. Who needs to supply or approve the answer. |
| `confidence` | High, Medium, Low | High: single current source states it directly. Medium: inferred from one or more sources, or source older than 12 months. Low: weak or indirect support, reviewer must check before send. |
| `reviewer_note` | Free text, optional | Anything the Solutions Engineer should know before sending. Conflicting sources, stale material, assumptions made. |

Rules Presales works to:

1. We never state a contractual commitment (SLA, liability, indemnity, penalty, exclusivity, custom terms) unless the knowledge base records it as an existing standard commitment. Requests for commitments go to Legal or Sales.
2. We never claim a certification, attestation, or audit we do not hold. If the knowledge base does not list it, the answer is No or Cannot answer, never Yes.
3. Dates matter. "Most recent" means current. A source older than 12 months is flagged in `reviewer_note` and the confidence is Medium at best.
4. When two sources disagree, we do not pick one. Status becomes Cannot answer, owner is whoever owns the topic, and the reviewer_note names both sources.
