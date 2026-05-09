"""Scrape Warren Buffett's annual letters (1977-2024) from berkshirehathaway.com."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests

INDEX_URL = "https://www.berkshirehathaway.com/letters/letters.html"
OUT_DIR = Path(__file__).parent / "letters"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    # Avoid brotli — requests cannot decode it without an extra dep.
    "Accept-Encoding": "gzip, deflate",
}
YEAR_FILE_RE = re.compile(r'href="((?:19|20)\d{2}(?:ltr)?\.(?:html|pdf))"', re.IGNORECASE)
LANDING_HREF_RE = re.compile(r'href="([^"]+\.(?:pdf|html?))"', re.IGNORECASE)


def fetch_index() -> str:
    resp = requests.get(INDEX_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    # The index is served as windows-1252 per the meta tag.
    resp.encoding = "windows-1252"
    return resp.text


def parse_letter_links(html: str) -> list[tuple[int, str]]:
    """Return a sorted list of (year, absolute_url) pairs for years 1977-2024."""
    pairs: dict[int, str] = {}
    for match in YEAR_FILE_RE.finditer(html):
        filename = match.group(1)
        year = int(filename[:4])
        if 1977 <= year <= 2024:
            pairs[year] = urljoin(INDEX_URL, filename)
    return sorted(pairs.items())


def download(url: str, dest: Path) -> int:
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return len(resp.content)


def is_landing_page(content: bytes) -> bool:
    """1998-2003 index entries link to a stub HTML page that points to the real letter."""
    if len(content) > 8192:
        return False
    text = content.decode("windows-1252", errors="ignore").lower()
    return "important note" in text and "chairman" in text and ".pdf" in text


def resolve_landing(landing_html: bytes, landing_url: str) -> str | None:
    """Pick the best real-letter URL from a stub page (prefer the PDF version)."""
    text = landing_html.decode("windows-1252", errors="ignore")
    candidates = [m.group(1) for m in LANDING_HREF_RE.finditer(text)]
    candidates = [c for c in candidates if "adobe.com" not in c.lower()]
    pdfs = [c for c in candidates if c.lower().endswith(".pdf")]
    htmls = [c for c in candidates if c.lower().endswith((".html", ".htm"))]
    chosen = (pdfs or htmls or [None])[0]
    return urljoin(landing_url, chosen) if chosen else None


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    print(f"Fetching index: {INDEX_URL}")
    html = fetch_index()

    links = parse_letter_links(html)
    print(f"Discovered {len(links)} letter links (years {links[0][0]}-{links[-1][0]}).")

    expected_years = set(range(1977, 2025))
    found_years = {y for y, _ in links}
    missing = expected_years - found_years
    if missing:
        print(f"WARNING: missing years from index: {sorted(missing)}", file=sys.stderr)

    failures: list[tuple[int, str, str]] = []
    for year, url in links:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            content = resp.content
            final_url = url

            if is_landing_page(content):
                real = resolve_landing(content, url)
                if real:
                    print(f"  [follow] {year}: landing page -> {real}")
                    time.sleep(0.3)
                    resp = requests.get(real, headers=HEADERS, timeout=60)
                    resp.raise_for_status()
                    content = resp.content
                    final_url = real
                else:
                    print(f"  [warn]  {year}: landing page had no inner link", file=sys.stderr)

            suffix = Path(final_url).suffix.lower()
            if suffix not in {".html", ".htm", ".pdf"}:
                suffix = ".html"
            dest = OUT_DIR / f"{year}{suffix}"
            dest.write_bytes(content)
            print(f"  [ok]    {year}: {dest.name} ({len(content)} B) <- {final_url}")
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL]  {year}: {url} -> {exc}", file=sys.stderr)
            failures.append((year, url, str(exc)))
        time.sleep(0.3)  # polite throttle

    print()
    print(f"Downloaded files in: {OUT_DIR}")
    files = sorted(OUT_DIR.iterdir())
    print(f"Total files on disk: {len(files)}")
    if failures:
        print(f"Failures: {len(failures)}")
        for year, url, err in failures:
            print(f"  {year} {url}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
