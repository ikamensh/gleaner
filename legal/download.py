"""Download provider legal documents and convert to clean markdown.

One registry of all providers and their legal document URLs. Output lands in
legal/<provider>/<filename>. Uses curl + html2text for deterministic
HTML-to-markdown conversion — no AI involved, lossless text extraction.

Usage:
    python legal/download.py              # refresh every provider
    python legal/download.py claude xai   # refresh selected providers
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import html2text

LEGAL_DIR = Path(__file__).parent

# provider -> {output filename: url}
PROVIDERS: dict[str, dict[str, str]] = {
    "claude": {
        "consumer-terms.md": "https://www.anthropic.com/legal/consumer-terms",
        "commercial-terms.md": "https://www.anthropic.com/legal/commercial-terms",
        "acceptable-use-policy.md": "https://www.anthropic.com/legal/aup",
        "privacy-policy.md": "https://www.anthropic.com/legal/privacy",
        "claude-code-legal-and-compliance.md": "https://code.claude.com/docs/en/legal-and-compliance",
        "claude-code-data-usage.md": "https://code.claude.com/docs/en/data-usage",
    },
    "cursor": {
        "terms-of-service.md": "https://cursor.com/terms-of-service",
        "privacy-policy.md": "https://cursor.com/privacy",
        "data-use.md": "https://cursor.com/data-use",
        "security.md": "https://cursor.com/security",
        "terms-of-service-teams.md": "https://www.cursor.com/en/terms-of-service-teams",
        "msa.md": "https://cursor.com/terms/msa",
        "dpa.md": "https://cursor.com/terms/dpa",
    },
    "deepseek": {
        "terms-of-use.md": "https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html",
        "privacy-policy.md": "https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html",
        "open-platform-terms.md": "https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html",
        "model-training-disclosure.md": "https://cdn.deepseek.com/policies/en-US/model-algorithm-disclosure.html",
    },
    "google": {
        "gemini-api-terms.md": "https://ai.google.dev/gemini-api/terms",
        "generative-ai-use-policy.md": "https://policies.google.com/terms/generative-ai/use-policy",
        "google-privacy-policy.md": "https://policies.google.com/privacy",
        "api-data-logging.md": "https://ai.google.dev/gemini-api/docs/logs-policy",
        "google-apis-tos.md": "https://developers.google.com/terms",
        "vertex-ai-tos.md": "https://cloud.google.com/terms/",
        "vertex-ai-service-terms.md": "https://cloud.google.com/terms/service-terms",
    },
    "groq": {
        "services-agreement.md": "https://console.groq.com/docs/legal/services-agreement",
        "privacy-policy.md": "https://groq.com/privacy-policy",
        "ai-policy.md": "https://console.groq.com/docs/legal/ai-policy",
        "your-data.md": "https://console.groq.com/docs/your-data",
        "dpa.md": "https://console.groq.com/docs/legal/customer-data-processing-addendum",
        "feedback-policy.md": "https://console.groq.com/docs/feedback-policy",
    },
    "kimi": {
        "api-terms-of-service.md": "https://platform.moonshot.ai/docs/agreement/modeluse",
        "api-privacy-policy.md": "https://platform.moonshot.ai/docs/agreement/userprivacy",
    },
    "kiro": {
        "kiro-license.md": "https://kiro.dev/license/",
        "kiro-data-protection.md": "https://kiro.dev/docs/privacy-and-security/data-protection/",
        "kiro-security.md": "https://kiro.dev/docs/privacy-and-security/",
        "aws-customer-agreement.md": "https://aws.amazon.com/agreement/",
        "aws-responsible-ai-policy.md": "https://aws.amazon.com/ai/responsible-ai/policy/",
    },
    "mistral": {
        "commercial-terms.md": "https://legal.mistral.ai/terms/commercial-terms-of-service",
        "privacy-policy.md": "https://legal.mistral.ai/terms/privacy-policy",
        "usage-policy.md": "https://legal.mistral.ai/terms/usage-policy",
        "data-processing-addendum.md": "https://legal.mistral.ai/terms/data-processing-addendum",
        "additional-terms.md": "https://legal.mistral.ai/terms/additional-terms",
    },
    "openai": {
        "services-agreement.md": "https://openai.com/policies/services-agreement/",
        "business-terms.md": "https://openai.com/policies/business-terms",
        "service-terms.md": "https://openai.com/policies/service-terms/",
        "usage-policies.md": "https://openai.com/policies/usage-policies/",
        "privacy-policy.md": "https://openai.com/policies/privacy-policy/",
        "api-data-usage.md": "https://openai.com/policies/api-data-usage-policies/",
        "sharing-publication.md": "https://openai.com/policies/sharing-publication-policy/",
    },
    "openrouter": {
        "terms-of-service.md": "https://openrouter.ai/terms",
        "privacy-policy.md": "https://openrouter.ai/privacy",
    },
    "xai": {
        "terms-of-service.md": "https://x.ai/legal/terms-of-service",
        "terms-of-service-enterprise.md": "https://x.ai/legal/terms-of-service-enterprise",
        "privacy-policy.md": "https://x.ai/legal/privacy-policy",
        "acceptable-use-policy.md": "https://x.ai/legal/acceptable-use-policy",
        "data-processing-addendum.md": "https://x.ai/legal/data-processing-addendum",
    },
}

# Providers whose pages carry heavy nav/cookie chrome that survives html2text.
# The line filter is too aggressive for the rest (it would eat short legitimate
# lines like a "Cookies" heading in a privacy policy).
STRIP_BOILERPLATE = {"claude", "cursor"}

_BOILERPLATE_PATTERNS = [
    "cookie", "nav ", "skip to", "sign up", "log in",
    "toggle", "menu", "search", "×",
]


def fetch(url: str) -> str:
    return subprocess.run(
        ["curl", "-sL", url], capture_output=True, text=True, check=True
    ).stdout


def html_to_md(html: str) -> str:
    h = html2text.HTML2Text()
    h.body_width = 0  # no wrapping
    h.ignore_images = True
    h.ignore_links = False
    h.protect_links = True
    h.single_line_break = False
    return h.handle(html)


def strip_chrome(md: str, boilerplate: bool) -> str:
    """Remove navigation/footer boilerplate that isn't part of the legal text."""
    # Drop everything before the first H1
    match = re.search(r"^# .+", md, re.MULTILINE)
    if match:
        md = md[match.start():]
    if not boilerplate:
        return md
    cleaned = []
    for line in md.split("\n"):
        low = line.strip().lower()
        if any(p in low for p in _BOILERPLATE_PATTERNS) and len(line.strip()) < 100:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def download_provider(name: str):
    out_dir = LEGAL_DIR / name
    out_dir.mkdir(exist_ok=True)
    today = date.today().isoformat()

    for filename, url in PROVIDERS[name].items():
        print(f"Fetching {url} ...")
        md = strip_chrome(html_to_md(fetch(url)), boilerplate=name in STRIP_BOILERPLATE)
        header = (
            f"<!-- Source: {url} -->\n"
            f"<!-- Downloaded: {today} -->\n"
            f"<!-- Converted with html2text (deterministic, no AI) -->\n\n"
        )
        out_path = out_dir / filename
        out_path.write_text(header + md)
        print(f"  -> {name}/{out_path.name} ({len(md)} chars)")


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(PROVIDERS)
    unknown = [n for n in names if n not in PROVIDERS]
    if unknown:
        sys.exit(f"Unknown provider(s): {', '.join(unknown)}. Known: {', '.join(sorted(PROVIDERS))}")
    for name in names:
        download_provider(name)
    print("Done.")
