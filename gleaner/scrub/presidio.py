"""Presidio scrub backend: pattern recognizers + custom secret patterns.

Uses a blank spaCy model (tokenizer only) so the expensive NER pass is
skipped; detection relies on Presidio's built-in pattern recognizers
(credit cards, emails, phones, IPs, SSNs, ...) plus custom secret patterns.
"""

from gleaner.scrub.patterns import PII_REDACTED, REDACTED

_presidio_analyzer = None
_presidio_engine = None


def _get_presidio():
    """Lazy-init Presidio analyzer with pattern-only recognizers (no spaCy NER).

    SpacyRecognizer (PERSON, LOCATION, NRP) is the slow part (~15x overhead).
    We skip it and rely on the built-in pattern recognizers plus our custom
    secret patterns.
    """
    global _presidio_analyzer, _presidio_engine
    if _presidio_analyzer is not None:
        return _presidio_analyzer, _presidio_engine

    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    from presidio_anonymizer import AnonymizerEngine

    # Custom recognizers for secrets that Presidio doesn't cover
    secret_patterns = [
        PatternRecognizer(
            supported_entity="SECRET_KEY",
            name="assignment_secret",
            patterns=[Pattern(
                "assignment",
                # \\? handles JSON-escaped quotes (\" in JSONL)
                r"(?i)(?:api[_-]?key|secret|token|password|passwd|private[_-]?key|access[_-]?key)\s*[=:]\s*\\?[\"']?([^\"',\s}\\]{8,})",
                0.9,
            )],
        ),
        PatternRecognizer(
            supported_entity="PEM_KEY",
            name="pem_block",
            patterns=[Pattern(
                "pem",
                r"-----BEGIN [A-Z0-9 ]+(?:PRIVATE KEY|KEY BLOCK)-----[\s\S]*?-----END [A-Z0-9 ]+(?:PRIVATE KEY|KEY BLOCK)-----",
                1.0,
            )],
        ),
        PatternRecognizer(
            supported_entity="BEARER_TOKEN",
            name="bearer_auth",
            patterns=[Pattern(
                "bearer",
                r"(?i)(?:Authorization:\s*Bearer\s+|Bearer\s+)([A-Za-z0-9_\-\.]{20,})",
                0.85,
            )],
        ),
        PatternRecognizer(
            supported_entity="CONNECTION_STRING",
            name="connection_string",
            patterns=[Pattern(
                "connstr",
                r"(?:postgres|mysql|mongodb|redis|amqp)(?:ql)?://[^\s,\"'}{]+",
                0.9,
            )],
        ),
        PatternRecognizer(
            supported_entity="AWS_KEY",
            name="aws_access_key",
            patterns=[Pattern("aws", r"AKIA[0-9A-Z]{16}", 0.95)],
        ),
        PatternRecognizer(
            supported_entity="GITHUB_TOKEN",
            name="github_token",
            patterns=[Pattern(
                "ghp",
                r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}",
                0.95,
            )],
        ),
    ]

    # Use a blank spaCy model (tokenizer only, no NER/parser).
    # This avoids loading en_core_web_* and the expensive NER pass.
    import spacy
    blank_nlp = spacy.blank("en")
    blank_nlp.max_length = 10_000_000
    nlp_engine = SpacyNlpEngine(models=[{"lang_code": "en", "model_name": "en_core_web_sm"}])
    nlp_engine.nlp = {"en": blank_nlp}  # inject blank model, skip load()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

    # Remove SpacyRecognizer — requires NER which the blank model doesn't have.
    analyzer.registry.recognizers = [
        r for r in analyzer.registry.recognizers
        if type(r).__name__ != "SpacyRecognizer"
    ]

    for recognizer in secret_patterns:
        analyzer.registry.add_recognizer(recognizer)

    engine = AnonymizerEngine()

    _presidio_analyzer = analyzer
    _presidio_engine = engine
    return analyzer, engine


# Entity types worth redacting in code transcripts.
# Excludes DATE_TIME (timestamps are structural), URL (file paths get caught),
# NRP, US_DRIVER_LICENSE, and other low-signal types that cause false positives.
_PII_ENTITIES = [
    "CREDIT_CARD", "CRYPTO", "EMAIL_ADDRESS", "IBAN_CODE", "IP_ADDRESS",
    "PHONE_NUMBER", "US_SSN", "US_PASSPORT", "US_BANK_NUMBER", "US_ITIN",
]
_SECRET_ENTITIES = [
    "SECRET_KEY", "PEM_KEY", "BEARER_TOKEN", "CONNECTION_STRING",
    "AWS_KEY", "GITHUB_TOKEN",
]
_ENTITIES = _PII_ENTITIES + _SECRET_ENTITIES

_SCORE_THRESHOLD = 0.4

_CHUNK_SIZE = 900_000  # stay under spaCy's 1M char limit


def scrub(text: str) -> tuple[str, int]:
    """Scrub secrets and PII. Returns (scrubbed_text, redaction_count)."""
    from presidio_anonymizer.entities import OperatorConfig

    analyzer, engine = _get_presidio()

    operators = {
        "DEFAULT": OperatorConfig("replace", {"new_value": PII_REDACTED}),
        **{e: OperatorConfig("replace", {"new_value": REDACTED}) for e in _SECRET_ENTITIES},
    }

    # Split into chunks on newline boundaries to stay under spaCy's limit.
    if len(text) <= _CHUNK_SIZE:
        chunks = [text]
    else:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + _CHUNK_SIZE, len(text))
            if end < len(text):
                # Break at last newline within the chunk
                nl = text.rfind("\n", start, end)
                if nl > start:
                    end = nl + 1
            chunks.append(text[start:end])
            start = end

    total_redactions = 0
    scrubbed_parts = []
    for chunk in chunks:
        results = analyzer.analyze(
            text=chunk,
            language="en",
            entities=_ENTITIES,
            score_threshold=_SCORE_THRESHOLD,
        )
        if results:
            anonymized = engine.anonymize(
                text=chunk, analyzer_results=results, operators=operators,
            )
            scrubbed_parts.append(anonymized.text)
            total_redactions += len(results)
        else:
            scrubbed_parts.append(chunk)

    return "".join(scrubbed_parts), total_redactions
