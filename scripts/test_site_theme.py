#!/usr/bin/env python3
"""Landing tokens must own writing, ELI5, and reference chrome."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CSS = ROOT / "style.css"
CSS_VER = "style.css?v=20260903e"
IOWAN = '"Iowan Old Style"'
LANDING_BG = "#f4efe6"
LANDING_INK = "#1c1915"
LANDING_ACCENT = "#9a3412"


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class SiteThemeTests(unittest.TestCase):
    def test_root_tokens(self):
        css = text("style.css")
        root = css.split(":root", 1)[1].split("}", 1)[0]
        self.assertIn(LANDING_BG, root)
        self.assertIn(LANDING_INK, root)
        self.assertIn(LANDING_ACCENT, root)
        self.assertIn(IOWAN, css.split("body {", 1)[1].split("}", 1)[0])
        self.assertIn('"Segoe UI"', css)

    def test_writing_override_is_not_old_paper(self):
        css = text("style.css")
        self.assertNotIn("#faf8f4", css)
        self.assertNotIn('font-family: Georgia, "Iowan Old Style"', css)
        block = css[css.find("body:has(main.article)") :]
        self.assertNotIn('font-family: Georgia', block.split("@media print")[0])

    def test_writing_pages_use_busted_css(self):
        layout = text("scripts/writing-layout.html")
        self.assertIn(CSS_VER, layout)
        self.assertEqual(layout.count("style.css?v="), 1)
        self.assertIn(CSS_VER, text("writing/index.html"))
        self.assertIn(CSS_VER, text("writing/meat-proxy-problem/index.html"))
        self.assertIn(CSS_VER, text("index.html"))
        self.assertIn(CSS_VER, text("privacy.html"))
        self.assertIn(CSS_VER, text("404.html"))

    def test_eli5_uses_landing_tokens(self):
        for rel in ("eli5/index.html", "eli5/agents/index.html"):
            html = text(rel)
            self.assertIn(CSS_VER, html)
            self.assertRegex(html, r"<body[^>]*class=\"[^\"]*\beli5\b")
            self.assertNotIn("#f4eee4", html)
            self.assertNotIn("#1c1612", html)
            style = "".join(re.findall(r"<style>(.*?)</style>", html, re.S))
            self.assertNotRegex(style, r"body\s*\{[^}]*font-family:\s*\"Segoe UI\"")

    def test_reference_uses_landing_tokens(self):
        css = text("style.css")
        self.assertNotRegex(css, r"body\.eli5,\s*body\.reference\s*\{")
        self.assertRegex(
            css,
            r"body\.eli5,\s*body\.reference:not\(:has\(#reference\)\)\s*\{\s*padding:\s*0;",
        )

        index_html = text("reference/index.html")
        index_style = "".join(re.findall(r"<style>(.*?)</style>", index_html, re.S))
        self.assertNotRegex(index_style, r"font-family\s*:")
        for selector in ("body", "main", "h1", ".next-step"):
            with self.subTest(selector=selector):
                self.assertNotRegex(
                    index_style,
                    rf"(?m)^\s*{re.escape(selector)}\s*\{{",
                )

        for rel in ("reference/index.html", "reference/agents/index.html"):
            html = text(rel)
            self.assertIn(CSS_VER, html)
            self.assertRegex(html, r"<body[^>]*class=\"[^\"]*\breference\b")
            self.assertNotIn("#0645ad", html)
            self.assertNotIn("#795cb2", html)
            style = "".join(re.findall(r"<style>(.*?)</style>", html, re.S))
            self.assertNotRegex(style, r"--bg:\s*#fff")
            self.assertNotRegex(style, r"font-family:\s*Georgia")

    def test_ninthgreen_and_trees_untouched(self):
        sample = text("samples/ninthgreen/index.html")
        self.assertNotIn("style.css", sample)
        trees = text("trees/index.html")
        self.assertNotIn("style.css", trees)
        self.assertNotIn('class="eli5"', trees)
        self.assertNotIn('class="reference"', trees)


if __name__ == "__main__":
    unittest.main()
