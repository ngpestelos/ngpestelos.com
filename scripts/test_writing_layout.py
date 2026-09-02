#!/usr/bin/env python3
"""Tests for writing chrome split/render."""

import re
import unittest
from pathlib import Path

import writing_layout

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
ESSAY = ROOT / "writing" / "debt-with-diff-attached" / "index.html"
INDEX = ROOT / "writing" / "index.html"


class WritingLayoutTests(unittest.TestCase):
    def test_css_ver_comes_from_layout(self):
        layout = writing_layout.layout_text()
        tokens = re.findall(r"style\.css\?v=[^\"'\s>]+", layout)
        self.assertEqual(len(tokens), 1, layout)
        token = tokens[0]
        page = writing_layout.split(ESSAY.read_text(encoding="utf-8"))
        rendered = writing_layout.render(page)
        self.assertIn(token, rendered)
        self.assertEqual(rendered.count("style.css?v="), 1)

    def test_essay_roundtrip_preserves_body(self):
        page = writing_layout.split(ESSAY.read_text(encoding="utf-8"))
        rendered = writing_layout.render(page)
        self.assertIn("AI-DDoS", rendered)
        self.assertIn('<div class="tldr">', rendered)
        self.assertIn("main class=\"article\"", rendered)
        self.assertIn('id="top"', rendered)
        self.assertNotIn('class="next-step"', rendered)

    def test_index_keeps_list_and_knock(self):
        page = writing_layout.split(INDEX.read_text(encoding="utf-8"))
        rendered = writing_layout.render(page)
        self.assertIn('id="writing"', rendered)
        self.assertIn('class="next-step"', rendered)
        self.assertIn("js-paged", rendered)
        self.assertNotIn("main class=\"article\"", rendered)

    def test_essay_crumb_gold(self):
        page = writing_layout.split(ESSAY.read_text(encoding="utf-8"))
        rendered = writing_layout.render(page)
        self.assertIn(
            '<p class="back" id="top"><a href="/">Nestor G Pestelos Jr</a>',
            rendered,
        )
        self.assertIn('<a href="/writing/">Writing</a>', rendered)
        self.assertIn(
            '<span class="print"> &middot; <a href="#print" onclick="window.print();return false">Print</a></span>',
            rendered,
        )
        self.assertNotIn('<a class="back"', rendered)


if __name__ == "__main__":
    unittest.main()
