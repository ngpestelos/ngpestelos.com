#!/usr/bin/env python3
"""Build /writing-from-first-principles/ from the vault Site/ markdown sources.

Reuses the stdlib markdown converter from the static-essay-publish skill
(md_to_essay.py). Stdlib only. Writes HTML; does not commit.

    python3 scripts/wffp_build.py --site . \
        --source "$HOME/src/PARA/0 Projects/2026 Writing from First Principles/Site" \
        --converter-dir "$HOME/.agents/skills/static-essay-publish/scripts"
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

SITE_HOST = "https://ngpestelos.com"
SECTION = "writing-from-first-principles"
SECTION_TITLE = "Writing from First Principles"
GA_ID = "G-TLBY8P4GG9"
DATE_PUBLISHED = "2026-09-06"
# (slug, nav label) in reading order; index first.
ORDER = [
    ("index", "Contents"),
    ("reader", "0. The Reader"),
    ("reading", "1. Reading Comprehension"),
    ("essay", "2. Essay Structure"),
    ("paragraph", "3. Paragraph Construction"),
    ("sentence", "4. Sentence Construction"),
    ("practice-card", "5. Practice Card"),
    ("glossary", "6. Glossary"),
]


def page_path(slug: str) -> str:
    return f"/{SECTION}/" if slug == "index" else f"/{SECTION}/{slug}/"


def strip_title_h1(body: str, title: str) -> str:
    """Drop a leading '# <title>' line; render() emits the page <h1> itself."""
    lines = body.lstrip("\n").split("\n", 1)
    if lines and lines[0].strip() == f"# {title}":
        return lines[1] if len(lines) > 1 else ""
    return body


def convert_with_quotes(md, body: str) -> tuple[str, str]:
    """convert_body has no blockquote support; render '>' runs here."""
    parts: list[str] = []
    buf: list[str] = []
    desc = ""

    def flush() -> None:
        nonlocal desc
        text = "\n".join(buf)
        buf.clear()
        if text.strip():
            _byline, _series, part_html, part_desc = md.convert_body(text)
            parts.append(part_html)
            if not desc:
                desc = part_desc

    lines = body.splitlines()
    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith(">"):
            flush()
            quote: list[str] = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip(">").strip())
                i += 1
            parts.append(f"<blockquote><p>{md.inline(' '.join(quote))}</p></blockquote>")
            continue
        buf.append(line)
        i += 1
    flush()
    return "\n\n".join(parts), desc


def render(slug: str, title: str, body_html: str, desc: str, css_ver: str,
           prev: tuple[str, str] | None, nxt: tuple[str, str] | None) -> str:
    url = SITE_HOST + page_path(slug)
    headline = SECTION_TITLE if slug == "index" else title
    tab_title = SECTION_TITLE if slug == "index" else f"{title} · {SECTION_TITLE}"
    crumb = '<a href="/">Nestor G Pestelos Jr</a>'
    if slug != "index":
        crumb += f' &middot; <a href="{page_path("index")}">{SECTION_TITLE}</a>'
    pager = []
    if prev:
        pager.append(f'<a href="{prev[0]}">&larr; {html.escape(prev[1])}</a>')
    pager.append('<a href="#top">Back to top</a>')
    if nxt:
        pager.append(f'<a href="{nxt[0]}">{html.escape(nxt[1])} &rarr;</a>')
    ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "datePublished": DATE_PUBLISHED,
            "dateModified": DATE_PUBLISHED,
            "author": {"@type": "Person", "name": "Nestor G Pestelos Jr", "url": f"{SITE_HOST}/"},
            "description": desc,
            "url": url,
            "isPartOf": {"@type": "CreativeWorkSeries", "name": SECTION_TITLE, "url": SITE_HOST + page_path("index")},
        },
        separators=(",", ":"),
        ensure_ascii=False,
    ).replace("</", "<\\/")  # never let a value close the script element
    desc_esc = html.escape(desc, quote=True)
    tab_esc = html.escape(tab_title)
    h1_esc = html.escape(headline)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{tab_esc} · Nestor G Pestelos Jr</title>
  <meta name="description" content="{desc_esc}">
  <meta property="og:title" content="{tab_esc}">
  <meta property="og:description" content="{desc_esc}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{url}">
  <link rel="canonical" href="{url}">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png?v=20260813f">
  <link rel="icon" href="/favicon-192.png?v=20260813f" type="image/png" sizes="192x192">
  <link rel="icon" href="/favicon-32.png?v=20260813f" type="image/png" sizes="32x32">
  <link rel="icon" href="/favicon.ico?v=20260813f" sizes="48x48 32x32 16x16">
  <link rel="icon" href="/favicon.svg?v=20260813f" type="image/svg+xml">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="stylesheet" href="/style.css?v={css_ver}">
  <script type="application/ld+json">{ld}</script>
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_ID}');
  </script>
</head>
<body>
  <main class="article">
    <p class="back" id="top">{crumb}<span class="print"> &middot; <a href="#print" onclick="window.print();return false">Print</a></span></p>
    <h1>{h1_esc}</h1>
{body_html}
    <p class="to-top">{" &middot; ".join(pager)}</p>
    <footer class="meta">
      <a href="/privacy.html">Privacy</a>
    </footer>
  </main>
  <button id="backToTop" class="back-to-top" aria-label="Back to top" title="Back to top">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M18 15l-6-6-6 6"/>
    </svg>
  </button>

  <script>
    const btt = document.getElementById('backToTop');
    window.addEventListener('scroll', () => {{
      if (window.scrollY > 250) {{
        btt.classList.add('visible');
      }} else {{
        btt.classList.remove('visible');
      }}
    }}, {{ passive: true }});
    btt.addEventListener('click', () => {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
  </script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", required=True, help="ngpestelos.com checkout")
    ap.add_argument("--source", required=True, help="vault Site/ folder with the markdown")
    ap.add_argument("--converter-dir", required=True, help="folder containing md_to_essay.py")
    args = ap.parse_args(argv)

    site = Path(args.site).expanduser().resolve()
    source = Path(args.source).expanduser().resolve()
    converter_dir = Path(args.converter_dir).expanduser().resolve()
    if not (site / "style.css").is_file():
        raise SystemExit(f"not a site checkout (no style.css): {site}")
    if not (converter_dir / "md_to_essay.py").is_file():
        raise SystemExit(f"md_to_essay.py not found in {converter_dir}")
    sys.path.insert(0, str(converter_dir))
    import md_to_essay as md  # noqa: E402

    css_ver = md.detect_css_ver(site)
    for pos, (slug, _label) in enumerate(ORDER):
        src = source / f"{slug}.md"
        if not src.is_file():
            raise SystemExit(f"missing source: {src}")
        meta, body = md.parse_frontmatter(src.read_text(encoding="utf-8"))
        if meta.get("permalink", "") != slug:
            raise SystemExit(f"{src.name}: permalink {meta.get('permalink')!r} != {slug!r}")
        title = meta.get("title", "").strip() or slug
        body_html, desc = convert_with_quotes(md, strip_title_h1(body, title))
        if not desc:
            desc = title
        prev = None
        nxt = None
        if pos > 0:
            p_slug, p_label = ORDER[pos - 1]
            prev = (page_path(p_slug), p_label)
        if pos + 1 < len(ORDER):
            n_slug, n_label = ORDER[pos + 1]
            nxt = (page_path(n_slug), n_label)
        dest_dir = site / SECTION if slug == "index" else site / SECTION / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "index.html"
        if dest.is_symlink():
            raise SystemExit(f"refusing to write through a symlink: {dest}")
        dest.write_text(render(slug, title, body_html, desc, css_ver, prev, nxt), encoding="utf-8")
        print(dest.relative_to(site))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
