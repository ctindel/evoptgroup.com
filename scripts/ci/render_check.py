#!/usr/bin/env python3
"""Render-integrity check for the Hugo build output in public/.

Run after `hugo`. Fails (exit 1) if the site didn't build into something
servable: missing/empty homepage, internal links or asset references that
don't resolve to real files, or suspiciously few pages. Stdlib only.
"""
from __future__ import annotations
import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

PUBLIC = sys.argv[1] if len(sys.argv) > 1 else "public"
MIN_INDEX_BYTES = 2048
MIN_HTML_PAGES = 3
# Refs listed here (one per line, format "<page>: <ref>") are pre-existing
# breakage: reported as warnings, not failures. Shrink this file as the
# underlying bugs get fixed; never grow it to silence NEW breakage.
BASELINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", ".ci", "known-broken.txt")


def load_baseline() -> set[str]:
    try:
        return {ln.strip() for ln in open(BASELINE_FILE) if ln.strip()
                and not ln.strip().startswith("#")}
    except OSError:
        return set()


class RefExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.refs.append(value)


def is_internal(ref: str) -> bool:
    p = urlparse(ref)
    if p.scheme or p.netloc:
        return False
    if ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return False
    return True


def resolves(ref: str, base_dir: str) -> bool:
    path = unquote(urlparse(ref).path)
    if not path:
        return True  # pure fragment/query
    if path.startswith("/"):
        cand = os.path.join(PUBLIC, path.lstrip("/"))
    else:
        cand = os.path.join(base_dir, path)
    cand = os.path.normpath(cand)
    if os.path.isfile(cand):
        return True
    if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "index.html")):
        return True
    # Hugo pretty URLs: /foo/ may be written as /foo
    if os.path.isfile(cand + "/index.html") or os.path.isfile(cand + ".html"):
        return True
    return False


def main() -> int:
    errors: list[str] = []

    index = os.path.join(PUBLIC, "index.html")
    if not os.path.isfile(index):
        print(f"FAIL: {index} does not exist — build produced no homepage")
        return 1
    size = os.path.getsize(index)
    if size < MIN_INDEX_BYTES:
        errors.append(f"index.html is only {size} bytes (<{MIN_INDEX_BYTES}) — likely an empty/broken render")

    html_files = []
    for root, _dirs, files in os.walk(PUBLIC):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))
    if len(html_files) < MIN_HTML_PAGES:
        errors.append(f"only {len(html_files)} HTML pages rendered (<{MIN_HTML_PAGES})")

    baseline = load_baseline()
    warnings: list[str] = []
    broken = 0
    for hf in html_files:
        try:
            content = open(hf, encoding="utf-8", errors="replace").read()
        except OSError as e:
            errors.append(f"unreadable page {hf}: {e}")
            continue
        ex = RefExtractor()
        ex.feed(content)
        base_dir = os.path.dirname(hf)
        page = os.path.relpath(hf, PUBLIC)
        for ref in ex.refs:
            if is_internal(ref) and not resolves(ref, base_dir):
                key = f"{page}: {ref}"
                if key in baseline:
                    warnings.append(key)
                    continue
                broken += 1
                if broken <= 20:
                    errors.append(f"broken internal ref in {key}")
    if broken > 20:
        errors.append(f"...and {broken - 20} more broken internal refs")

    if warnings:
        print(f"WARN: {len(warnings)} known-broken ref(s) still present "
              f"(baselined in .ci/known-broken.txt — fix these eventually):")
        for w in sorted(set(warnings))[:10]:
            print(f"  ~ {w}")

    if errors:
        print(f"FAIL: {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(html_files)} pages rendered, index.html {size} bytes, "
          f"no NEW broken internal refs ({len(warnings)} baselined warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
