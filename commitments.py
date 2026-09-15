"""Application-owned commitment policy; never populated by model output.

These are conservative English rules, not a complete natural-language classifier.
The registry describes supplied documents, not approval of a customer's contract.
"""
import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().replace("’", "'")
    text = text.replace("we'll", "we will").replace("we're", "we are")
    return " ".join(text.split())


# Hashes are pinned to reviewed SECTION text, not recomputed approvals on load.
AUTHORITY = {
    "KB:07-certifications-audits.md#customer-audit-rights": (
        "4eb10224ad616cd72c0e4eb15904d890472b34280f8b6ca24aa6a936d5ccfe12",
        "existing_standard_term",
        "Our Enterprise customers have contractual audit rights under the DPA, exercisable once per year on 30 days notice, at the customer's cost, and satisfied in the first instance by provision of the SOC 2 report and ISO certificate.",
        "Customers on Enterprise plans have contractual audit rights as set out in the DPA, exercisable once per year on 30 days notice, at the customer's cost, and satisfied in the first instance by provision of the SOC 2 report and ISO certificate.",
    ),
    "KB:09-privacy-and-dpa-terms.md#liability": (
        "f56fa8d106ce672de1d59dd88ffe833dad311fc7d8cd79d237c5f3df18c05fa9",
        "existing_standard_term",
        "Our standard terms cap our aggregate liability at the fees paid in the 12 months preceding the claim.",
        "The standard terms cap Usercentrics' aggregate liability at the fees paid in the 12 months preceding the claim.",
    ),
    "KB:08-business-continuity.md#availability-commitment": (
        "a2451a9d27f657ff5c80bbcb73e2d25c396975c51b30796af0c23b88bdfaec05",
        "negotiation_only", "", "",
    ),
    "KB:09-privacy-and-dpa-terms.md#insurance": (
        "16db1f51d1180d276f98a5442e8498cdb163aa0e51f5af0d302c6a0cb377ef15",
        "negotiation_only", "", "",
    ),
    "KB:09-privacy-and-dpa-terms.md#data-processing-agreement": (
        "ac74621f69d8b3c70759eb0225e21cdb8d389e66f3ec71153ede4d60ec22468e",
        "negotiation_only", "", "",
    ),
}


def authority_for(ref_id: str, content_hash: str) -> str:
    entry = AUTHORITY.get(ref_id)
    return entry[1] if entry and entry[0] == content_hash else "factual_policy"


def commitment_owner(text: str) -> str:
    text = normalize(text)
    if re.search(r"\b(liability|indemn\w*|dpa|baa|contract\w*)\b", text):
        return "Legal"
    return "Sales" if re.search(r"\b(discount|pricing|price|prices|price-lock)\b", text) else "Legal"


def commitment_request(question: str) -> tuple[str, str] | None:
    text = normalize(question)
    # Deliberately do not match bare "will you": notification-policy questions
    # in the supplied standard questionnaire use that wording.
    asks = re.search(
        r"\b(?:(?:will|would|can|could|do|does)\s+(?:you|your company)\s+"
        r"(?:be (?:willing|prepared) to\s+)?"
        r"(?:agree|accept|sign|commit|guarantee|undertake|indemnify|waive|promise)\b"
        r"|(?:please\s+)?(?:agree|commit|guarantee|undertake|indemnify|waive|promise)\b"
        r"|(?:please|must|required to)\s+(?:accept|sign)\b)", text)
    if asks:
        return "C1-new-commitment", commitment_owner(text)
    if re.search(r"\b(?:we|customer|customers)\b.*\bright to audit\b.*\b(?:on.site|facilities)\b", text):
        return "C1-nonstandard-audit", "Legal"
    return None


def has_promise(answer: str) -> bool:
    text = normalize(answer)
    return bool(re.search(
        r"\bwe\s+(?:(?:hereby|also|unconditionally)\s+)?"
        r"(?:will|shall|agree|accept|sign|commit|guarantee|undertake|promise|indemnify|waive)\b"
        r"(?!\s+(?:not|never)\s+(?:agree|accept|sign|commit|guarantee|indemnify|waive)\b)"
        r"|\bwe (?:can|could|would|may) (?:agree|accept|commit|guarantee|indemnify|sign)\b"
        r"|\bwe are (?:committed|required|obligated|bound)\b"
        r"|\bour\s+(?:\w+\s+){0,3}(?:liability|sla)\s+(?:is|will|covers|guarantees|provides)\b(?!\s+not\b)"
        r"|\bour standard terms cap\b"
        r"|\bour (?:enterprise )?customers have contractual audit rights\b"
        r"|\bwe (?:provide|offer|give)\s+(?:\w+\s+){0,4}(?:service credits|unlimited liability|indemnities)\b",
        text))


def unsupported_promise(draft, evidence_by_id, today) -> bool:
    # Only remove a complete, fixed standard-term sentence supported by a
    # current pinned source and its exact excerpt. Metadata alone grants nothing.
    remaining = draft.answer
    for use in draft.evidence_uses:
        source = evidence_by_id.get(use.ref_id)
        entry = AUTHORITY.get(use.ref_id)
        if not source or not entry or entry[1] != "existing_standard_term":
            continue
        if (source.content_hash != entry[0] or not source.source_date
                or not 0 <= (today - source.source_date).days <= 365
                or use.quote not in source.text or entry[3] not in use.quote):
            continue
        # Match whole sentences only: appended qualifiers must not extend a term.
        sentences = re.split(r"(?<=[.!?])\s+", remaining.strip())
        # Keep everything EXCEPT the authorized sentence for the risk scan.
        remaining = " ".join(s for s in sentences if s != entry[2])
    return has_promise(remaining)
