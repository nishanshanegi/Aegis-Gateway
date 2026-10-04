# app/services/pii_shield.py
import re

# Standard RegEx patterns for common PII
PII_PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "PHONE": r'\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d[ -]*?){13,16}\b',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b'
}

def redact_pii(text: str) -> tuple[str, list[str]]:
    """
    Scans input text for sensitive PII and masks it with placeholders.
    Returns the redacted text and a list of types that were redacted.
    """
    redacted_types = []
    sanitized_text = text

    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, sanitized_text):
            sanitized_text = re.sub(pattern, f"[{pii_type}_REDACTED]", sanitized_text)
            redacted_types.append(pii_type)

    return sanitized_text, redacted_types