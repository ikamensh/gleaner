"""Download Anthropic legal documents and convert to clean markdown.

Uses curl for download + html2text for deterministic HTML-to-markdown conversion.
No AI involved — lossless text extraction.
"""

import subprocess
import re
from pathlib import Path

import html2text

DOCS = {
    "consumer-terms.md": "https://www.anthropic.com/legal/consumer-terms",
    "commercial-terms.md": "https://www.anthropic.com/legal/commercial-terms",
    "acceptable-use-policy.md": "https://www.anthropic.com/legal/aup",
    "privacy-policy.md": "https://www.anthropic.com/legal/privacy",
    "claude-code-legal-and-compliance.md": "https://code.claude.com/docs/en/legal-and-compliance",
    "claude-code-data-usage.md": "https://code.claude.com/docs/en/data-usage",
}

OUT_DIR = Path(__file__).parent


def fetch(url: str) -> str:
    result = subprocess.run(
        ["curl", "-sL", url], capture_output=True, text=True, check=True
    )
    return result.stdout


def html_to_md(html: str) -> str:
    h = html2text.HTML2Text()
    h.body_width = 0  # no wrapping
    h.ignore_images = True
    h.ignore_links = False
    h.protect_links = True
    h.single_line_break = False
    return h.handle(html)


def strip_chrome(md: str) -> str:
    """Remove navigation/footer boilerplate that isn't part of the legal text."""
    # Drop everything before the first H1
    match = re.search(r'^# .+', md, re.MULTILINE)
    if match:
        md = md[match.start():]
    # Drop cookie banners and nav lines commonly at the top
    lines = md.split('\n')
    cleaned = []
    skip_patterns = [
        'cookie', 'nav ', 'skip to', 'sign up', 'log in',
        'toggle', 'menu', 'search', '×',
    ]
    for line in lines:
        low = line.strip().lower()
        if any(p in low for p in skip_patterns) and len(line.strip()) < 100:
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


if __name__ == "__main__":
    from datetime import date
    today = date.today().isoformat()

    for filename, url in DOCS.items():
        print(f"Fetching {url} ...")
        html = fetch(url)
        md = html_to_md(html)
        md = strip_chrome(md)

        header = (
            f"<!-- Source: {url} -->\n"
            f"<!-- Downloaded: {today} -->\n"
            f"<!-- Converted with html2text (deterministic, no AI) -->\n\n"
        )

        out_path = OUT_DIR / filename
        out_path.write_text(header + md)
        print(f"  -> {out_path.name} ({len(md)} chars)")

    print("Done.")
