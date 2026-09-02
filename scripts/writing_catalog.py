#!/usr/bin/env python3
"""Render writing index inner HTML, Atom feed, and sitemap writing URLs."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CATALOG_PATH = SCRIPTS / "writing-catalog.json"
SITE = "https://ngpestelos.com"
ATOM_URL = f"{SITE}/writing/atom.xml"
WRITING_INDEX_URL = f"{SITE}/writing/"
HOME_URL = f"{SITE}/"

BUCKETS = (
    ("systems", "Production systems and agents"),
    ("payments", "Payments"),
    ("essays", "Essays"),
)
PROOF_SLUGS = (
    "legacy-rails-upgrade-with-agents",
    "upgrade-or-rewrite",
)


def load_catalog(path: Path | None = None) -> list[dict]:
    catalog_path = Path(path) if path else CATALOG_PATH
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def catalog_by_slug(items: list[dict] | None = None) -> dict[str, dict]:
    return {item["slug"]: item for item in (items if items is not None else load_catalog())}


def permalink(slug: str) -> str:
    return f"{SITE}/writing/{slug}/"


def display_date(iso_date: str) -> str:
    return date.fromisoformat(iso_date).strftime("%-d %b %Y")


def _ordered_bucket(items: list[dict], bucket: str) -> list[dict]:
    bucket_items = [item for item in items if item.get("bucket") == bucket]
    pins = sorted(
        [item for item in bucket_items if item.get("pin")],
        key=lambda item: item["pin"],
    )
    rest = [item for item in bucket_items if not item.get("pin")]
    rest.sort(key=lambda item: item["date"], reverse=True)
    return pins + rest


def index_inner_html(items: list[dict]) -> str:
    sections = []
    for bucket_id, heading in BUCKETS:
        lines = [
            f'      <section class="bucket" id="{bucket_id}">',
            f"        <h2>{heading}</h2>",
            "        <ul>",
        ]
        for item in _ordered_bucket(items, bucket_id):
            cls = ' class="pin"' if item.get("pin") else ""
            title = html.escape(item["title"], quote=True)
            lines.append(
                f"          <li{cls}><a href=\"/writing/{item['slug']}/\">{title}</a>"
                f' <time datetime="{item["date"]}">{display_date(item["date"])}</time></li>'
            )
        lines.append("        </ul>")
        lines.append("      </section>")
        sections.append("\n".join(lines))
    return "\n".join(sections) + "\n"


def replace_writing_inner(html_text: str, inner: str) -> str:
    open_tag = '<section id="writing">'
    start = html_text.find(open_tag)
    if start < 0:
        raise ValueError("missing #writing")
    i = start + len(open_tag)
    depth = 1
    lower = html_text.lower()
    end = None
    while i < len(html_text) and depth:
        next_open = lower.find("<section", i)
        next_close = lower.find("</section>", i)
        if next_close < 0:
            raise ValueError("unclosed #writing")
        if next_open != -1 and next_open < next_close:
            depth += 1
            i = next_open + 8
            continue
        depth -= 1
        if depth == 0:
            end = next_close
            break
        i = next_close + 10
    if end is None:
        raise ValueError("unclosed #writing")
    return html_text[: start + len(open_tag)] + "\n" + inner + "    " + html_text[end:]


def apply_index_inner(root: Path | None = None, items: list[dict] | None = None) -> Path:
    base = root or ROOT
    path = base / "writing" / "index.html"
    catalog = items if items is not None else load_catalog()
    path.write_text(
        replace_writing_inner(path.read_text(encoding="utf-8"), index_inner_html(catalog)),
        encoding="utf-8",
    )
    return path


def atom_xml(items: list[dict], now_iso: str | None = None) -> str:
    updated = now_iso or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ordered = sorted(items, key=lambda item: item["date"], reverse=True)
    entries = []
    for item in ordered:
        url = permalink(item["slug"])
        entries.append(
            "  <entry>\n"
            f"    <id>{xml_escape(url)}</id>\n"
            f"    <title>{xml_escape(item['title'])}</title>\n"
            f"    <updated>{item['date']}T00:00:00Z</updated>\n"
            f'    <link href="{xml_escape(url)}"/>\n'
            "  </entry>"
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        "  <title>Writing — Nestor G Pestelos Jr</title>\n"
        f'  <link rel="self" href="{ATOM_URL}"/>\n'
        f'  <link href="{WRITING_INDEX_URL}"/>\n'
        f"  <id>{WRITING_INDEX_URL}</id>\n"
        f"  <updated>{xml_escape(updated)}</updated>\n"
        "  <author>\n"
        "    <name>Nestor G Pestelos Jr</name>\n"
        "  </author>\n"
        + "\n".join(entries)
        + "\n</feed>\n"
    )


def sitemap_locs(items: list[dict], extra_locs: list[str]) -> list[str]:
    seen: set[str] = set()
    locs: list[str] = []
    for loc in extra_locs:
        if loc not in seen:
            seen.add(loc)
            locs.append(loc)
    for item in items:
        loc = permalink(item["slug"])
        if loc not in seen:
            seen.add(loc)
            locs.append(loc)
    if ATOM_URL not in seen:
        locs.append(ATOM_URL)
    return locs


def existing_non_writing_locs(sitemap_text: str) -> list[str]:
    locs = []
    seen = set()
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap_text):
        if loc.rstrip("/") == f"{SITE}/writing":
            loc = WRITING_INDEX_URL
        elif "/writing/" in loc:
            continue
        if loc not in seen:
            seen.add(loc)
            locs.append(loc)
    return locs


def proof_locs(root: Path | None = None) -> list[str]:
    base = root or ROOT
    locs = []
    for slug in PROOF_SLUGS:
        if (base / "writing" / slug / "index.html").is_file():
            locs.append(permalink(slug))
    return locs


def _url_meta(loc: str) -> tuple[str, str]:
    if loc.rstrip("/") == SITE:
        return "daily", "1.0"
    if loc == WRITING_INDEX_URL:
        return "daily", "0.8"
    if loc.endswith("/privacy.html"):
        return "monthly", "0.1"
    if loc in (f"{SITE}/eli5/", f"{SITE}/reference/"):
        return "weekly", "0.5"
    if loc == f"{SITE}/trees/":
        return "weekly", "0.6"
    if loc == ATOM_URL:
        return "daily", "0.5"
    if "/writing/" in loc:
        return "monthly", "0.6"
    return "monthly", "0.5"


def sitemap_xml(items: list[dict], extra_locs: list[str]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in sitemap_locs(items, extra_locs):
        changefreq, priority = _url_meta(loc)
        lines.extend(
            [
                "  <url>",
                f"    <loc>{xml_escape(loc)}</loc>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_feeds(root: Path | None = None, now_iso: str | None = None) -> None:
    base = root or ROOT
    items = load_catalog()
    extra = existing_non_writing_locs((base / "sitemap.xml").read_text(encoding="utf-8"))
    if HOME_URL not in extra:
        extra.insert(0, HOME_URL)
    if WRITING_INDEX_URL not in extra:
        extra.append(WRITING_INDEX_URL)
    extra.extend(proof_locs(base))
    extra.append(ATOM_URL)
    (base / "sitemap.xml").write_text(sitemap_xml(items, extra), encoding="utf-8")
    (base / "writing" / "atom.xml").write_text(
        atom_xml(items, now_iso=now_iso), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-feeds",
        action="store_true",
        help="write writing/atom.xml and merge catalog URLs into sitemap.xml",
    )
    args = parser.parse_args(argv)
    if not args.build_feeds:
        parser.print_help()
        return 2
    build_feeds()
    return 0


if __name__ == "__main__":
    sys.exit(main())
