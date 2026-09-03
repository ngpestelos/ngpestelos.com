#!/usr/bin/env python3
"""Tests for writing chrome split/render."""

import json
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
        page["path"] = "writing/index.html"
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

    def test_inner_placeholder_syntax_is_preserved(self):
        page = writing_layout.split(ESSAY.read_text(encoding="utf-8"))
        page["path"] = "writing/example/index.html"
        literal = "<p>Literal {{title}} {{to_top}} {{footer}} {{unknown}}</p>"
        page["inner"] = "    " + literal + "\n"
        rendered = writing_layout.render(page)
        self.assertIn(literal, rendered)
        self.assertEqual(rendered.count(writing_layout.ESSAY_TO_TOP), 1)

    def test_meta_attribute_quotes_are_escaped(self):
        page = writing_layout.split(ESSAY.read_text(encoding="utf-8"))
        page["path"] = "writing/example/index.html"
        page["description"] = 'Say "just validate it" now.'
        page["og_description"] = page["description"]
        rendered = writing_layout.render(page)
        escaped = 'content="Say &quot;just validate it&quot; now."'
        self.assertEqual(rendered.count(escaped), 2)

    def test_article_json_ld_uses_plain_text(self):
        page = {
            "path": "writing/example/index.html",
            "og_title": "Your Agent&#x27;s Plan",
            "description": "Read *[the guide](https://example.com)* with `care`.",
            "canonical": "https://ngpestelos.com/writing/example/",
        }
        script = writing_layout.article_json_ld(page, {})
        payload = re.search(r"\n(\{.*\})\n", script).group(1)
        data = json.loads(payload)
        self.assertEqual(data["headline"], "Your Agent's Plan")
        self.assertEqual(data["description"], "Read the guide with care.")

    def test_essay_with_writing_id_keeps_essay_chrome(self):
        page = writing_layout.split(ESSAY.read_text(encoding="utf-8"))
        page["path"] = "writing/example/index.html"
        page["inner"] = '    <section id="writing">Example</section>\n'
        rendered = writing_layout.render(page)
        self.assertIn(writing_layout.GOLD_CRUMB, rendered)
        self.assertIn(writing_layout.ESSAY_TO_TOP, rendered)
        self.assertIn('<footer class="meta">', rendered)

    def test_all_writing_metadata_survives_render(self):
        fields = ("description", "og_title", "og_description", "og_type", "canonical")
        for path in sorted((ROOT / "writing").rglob("index.html")):
            with self.subTest(path=path):
                page = writing_layout.split(path.read_text(encoding="utf-8"))
                page["path"] = str(path.relative_to(ROOT))
                rendered = writing_layout.render(page)
                rerendered = writing_layout.split(rendered)
                self.assertEqual(
                    tuple(page[field] for field in fields),
                    tuple(rerendered[field] for field in fields),
                )


if __name__ == "__main__":
    unittest.main()
