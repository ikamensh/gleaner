"""Download DeepSeek legal documents and convert to clean markdown.

Uses curl for download + html2text for deterministic HTML-to-markdown conversion.
No AI involved — lossless text extraction.
"""

import subprocess
import re
from pathlib import Path

import html2text

DOCS = {
    "terms-of-use.md": "https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html",
    "privacy-policy.md": "https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html",
    "open-platform-terms.md": "https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html",
    "model-training-disclosure.md": "https://cdn.deepseek.com/policies/en-US/model-algorithm-disclosure.html",
}

OUT_DIR = Path(__file__).parent


def fetch(url: str) -> str:
    result = subprocess.run(
        ["curl", "-sL", url], capture_output=True, text=True, check=True
    )
    return result.stdout


def html_to_md(html: str) -> str:
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_images = True
    h.ignore_links = False
    h.protect_links = True
    h.single_line_break = False
    return h.handle(html)


def strip_chrome(md: str) -> str:
    match = re.search(r'^# .+', md, re.MULTILINE)
    if match:
        md = md[match.start():]
    return md


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
