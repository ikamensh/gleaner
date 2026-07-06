"""Download xAI (Grok) legal documents and convert to clean markdown."""

import subprocess
import re
from pathlib import Path

import html2text

DOCS = {
    "terms-of-service.md": "https://x.ai/legal/terms-of-service",
    "terms-of-service-enterprise.md": "https://x.ai/legal/terms-of-service-enterprise",
    "privacy-policy.md": "https://x.ai/legal/privacy-policy",
    "acceptable-use-policy.md": "https://x.ai/legal/acceptable-use-policy",
    "data-processing-addendum.md": "https://x.ai/legal/data-processing-addendum",
}

OUT_DIR = Path(__file__).parent


def fetch(url: str) -> str:
    return subprocess.run(
        ["curl", "-sL", url], capture_output=True, text=True, check=True
    ).stdout


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
