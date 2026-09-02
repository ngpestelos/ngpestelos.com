#!/usr/bin/env python3
"""Fill writing-layout.html from existing writing HTML. No markdown parse."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
LAYOUT_PATH = SCRIPTS / "writing-layout.html"

GOLD_CRUMB = (
    '<p class="back" id="top"><a href="/">Nestor G Pestelos Jr</a>'
    ' &middot; <a href="/writing/">Writing</a>'
    '<span class="print"> &middot; '
    '<a href="#print" onclick="window.print();return false">Print</a></span></p>'
)
ESSAY_TO_TOP = '<p class="to-top"><a href="#top">Back to top</a></p>'
PLACEHOLDERS = (
    "title",
    "description",
    "og_title",
    "og_description",
    "og_type",
    "canonical",
    "main_attrs",
    "crumb",
    "inner",
    "to_top",
    "footer",
    "extra_scripts",
)


def layout_text() -> str:
    return LAYOUT_PATH.read_text(encoding="utf-8")


def _attr(tag: str, name: str) -> str:
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag)
    return m.group(1) if m else ""


def _head_tag(html: str, pattern: str) -> str:
    m = re.search(pattern, html)
    return m.group(0) if m else ""


def _title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1) if m else ""


def _meta_name(html: str, name: str) -> str:
    m = re.search(
        rf'<meta\b[^>]*\bname="{re.escape(name)}"[^>]*>',
        html,
    )
    return _attr(m.group(0), "content") if m else ""


def _meta_prop(html: str, prop: str) -> str:
    m = re.search(
        rf'<meta\b[^>]*\bproperty="{re.escape(prop)}"[^>]*>',
        html,
    )
    return _attr(m.group(0), "content") if m else ""


def _block(text: str) -> str:
    if not text or not str(text).strip():
        return ""
    return str(text).strip("\n") + "\n"


def is_writing_index(page: dict) -> bool:
    inner = page.get("inner", "")
    if 'id="writing"' in inner:
        return True
    path = str(page.get("path") or "").replace("\\", "/")
    return path.endswith("writing/index.html")


def split(html: str) -> dict:
    main_m = re.search(r"<main([^>]*)>(.*?)</main>", html, re.S)
    if not main_m:
        raise ValueError("no <main> in html")
    main_attrs = main_m.group(1)
    inner = main_m.group(2)

    crumb = ""
    crumb_m = re.match(r'\s*(<p class="back"[^>]*>.*?</p>)', inner, re.S)
    if crumb_m:
        crumb = crumb_m.group(1)
        inner = inner[crumb_m.end() :]

    footer = ""
    foot_m = re.search(r'(\s*<footer class="meta">.*?</footer>)\s*$', inner, re.S)
    if foot_m:
        footer = foot_m.group(1).strip("\n") + "\n"
        inner = inner[: foot_m.start()]

    to_top_m = re.search(r'\s*<p class="to-top">.*?</p>\s*$', inner, re.S)
    if to_top_m:
        inner = inner[: to_top_m.start()]

    after = html.split("</main>", 1)[1] if "</main>" in html else ""
    after = re.sub(r"</body>\s*</html>\s*$", "", after, flags=re.I | re.S)
    after = re.sub(
        r'\s*<button\b[^>]*\bid="backToTop"[^>]*>.*?</button>',
        "",
        after,
        flags=re.S,
    )

    def _keep_script(match: re.Match) -> str:
        return "" if "backToTop" in match.group(0) else match.group(0)

    after = re.sub(r"\s*<script\b[^>]*>.*?</script>", _keep_script, after, flags=re.S)
    extra_scripts = after.strip("\n")
    if extra_scripts.strip():
        extra_scripts = extra_scripts + "\n"
    else:
        extra_scripts = ""

    canon_tag = _head_tag(html, r'<link\b[^>]*\brel="canonical"[^>]*>')
    canonical = _attr(canon_tag, "href")

    return {
        "title": _title(html),
        "description": _meta_name(html, "description"),
        "og_title": _meta_prop(html, "og:title"),
        "og_description": _meta_prop(html, "og:description"),
        "og_type": _meta_prop(html, "og:type"),
        "canonical": canonical,
        "main_attrs": main_attrs,
        "crumb": crumb,
        "inner": inner,
        "to_top": "",
        "footer": footer,
        "extra_scripts": extra_scripts,
    }


def render(page: dict) -> str:
    values = {
        "title": page.get("title", ""),
        "description": page.get("description", ""),
        "og_title": page.get("og_title", ""),
        "og_description": page.get("og_description", ""),
        "og_type": page.get("og_type", ""),
        "canonical": page.get("canonical", ""),
        "main_attrs": page.get("main_attrs", ""),
        "inner": page.get("inner", ""),
        "extra_scripts": page.get("extra_scripts", ""),
    }
    if is_writing_index(page):
        crumb = page.get("crumb") or ""
        values["crumb"] = _block("    " + crumb) if crumb.strip() else ""
        values["to_top"] = ""
        values["footer"] = ""
    else:
        values["crumb"] = _block("    " + GOLD_CRUMB)
        values["to_top"] = _block("    " + ESSAY_TO_TOP)
        values["footer"] = _block(page.get("footer") or "")

    html = layout_text()
    for key in PLACEHOLDERS:
        html = html.replace("{{" + key + "}}", values.get(key, ""))
    leftover = re.findall(r"\{\{[^}]+\}\}", html)
    if leftover:
        raise ValueError("leftover placeholders: " + ", ".join(leftover))
    return html


def rebuild(root: Path | None = None) -> list[Path]:
    base = root or ROOT
    writing = base / "writing"
    written: list[Path] = []
    for path in sorted(writing.rglob("index.html")):
        page = split(path.read_text(encoding="utf-8"))
        page["path"] = str(path.relative_to(base))
        path.write_text(render(page), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="rewrite writing/**/index.html from the layout template",
    )
    args = parser.parse_args(argv)
    if not args.rebuild:
        parser.print_help()
        return 2
    rebuild()
    return 0


if __name__ == "__main__":
    sys.exit(main())
