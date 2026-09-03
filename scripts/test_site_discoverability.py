#!/usr/bin/env python3
"""Discoverability tests for writing catalog, index, feed, and schema."""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CATALOG_PATH = SCRIPTS / "writing-catalog.json"
INDEX = ROOT / "writing" / "index.html"
HOME = ROOT / "index.html"
ESSAY = ROOT / "writing" / "debt-with-diff-attached" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
ATOM = ROOT / "writing" / "atom.xml"
PRIVACY = ROOT / "privacy.html"
DEEP_DIVE = ROOT / "writing" / "legacy-rails-upgrade-with-agents" / "index.html"
COMPARISON = ROOT / "writing" / "upgrade-or-rewrite" / "index.html"

PAYMENTS = {
    "instapay-is-not-ach",
    "us-and-philippine-payment-rails",
    "payments-glossary",
}
SNAPSHOT_SLUG = re.compile(r"-\d{8}$")
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def sitemap_locs(text: str) -> set[str]:
    return set(re.findall(r"<loc>([^<]+)</loc>", text))


def is_snapshot_slug(slug: str) -> bool:
    return bool(SNAPSHOT_SLUG.search(slug))


class SiteDiscoverabilityTests(unittest.TestCase):
    def test_catalog_buckets_and_pins(self):
        items = load_catalog()
        slugs = [item["slug"] for item in items]
        self.assertGreaterEqual(len(slugs), 58)
        self.assertEqual(len(slugs), len(set(slugs)))
        for item in items:
            self.assertIn(item["bucket"], {"systems", "payments", "essays"})
            self.assertFalse(is_snapshot_slug(item["slug"]), item["slug"])
        payments = {item["slug"] for item in items if item["bucket"] == "payments"}
        self.assertEqual(payments, PAYMENTS)
        systems_pins = {
            item["pin"]
            for item in items
            if item["bucket"] == "systems" and item.get("pin")
        }
        essays_pins = {
            item["pin"]
            for item in items
            if item["bucket"] == "essays" and item.get("pin")
        }
        self.assertEqual(systems_pins, {1, 2, 3, 4, 5})
        self.assertEqual(essays_pins, {1, 2, 3, 4, 5})

    def test_writing_index_grouped(self):
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("<h2>Production systems and agents</h2>", html)
        self.assertIn("<h2>Payments</h2>", html)
        self.assertIn("<h2>Essays</h2>", html)
        self.assertNotIn('<p class="tagline">', html)
        self.assertIn('class="next-step"', html)
        self.assertRegex(
            html,
            r'mailto:nestor@pestelos\.net\?subject=[^"\']*writing',
        )
        items = load_catalog()
        for item in items:
            self.assertRegex(
                html,
                rf'href="/writing/{re.escape(item["slug"])}/">[^<]*</a>\s*<time datetime="{item["date"]}"',
            )
        self.assertGreaterEqual(len(re.findall(r'<li class="pin">', html)), 13)

    def test_homepage_pins_and_linters(self):
        html = HOME.read_text(encoding="utf-8")
        self.assertNotIn("40+", html)
        self.assertIn("8-check", html)
        self.assertIn("/writing/meat-proxy-problem/", html)
        self.assertIn("/writing/instapay-is-not-ach/", html)
        self.assertIn("/writing/five-checks-against-motivated-reasoning/", html)
        self.assertIn('"@type":"Person"', html)
        self.assertRegex(
            html,
            r'mailto:nestor@pestelos\.net\?subject=[^"\']*homepage',
        )
        self.assertNotIn('id="proof"', html)
        self.assertNotIn("Track Record", html)
        self.assertEqual(html.count("91% test coverage"), 1)
        self.assertNotIn("25 years", html)
        self.assertEqual(html.count("gumroad.com"), 1)
        self.assertIn("written readiness read", html)
        self.assertIn("Software engineer since 2001. Manila, UTC+8.", html)
        next_step = re.search(r'<p class="next-step">.*?</p>', html, re.S).group(0)
        self.assertIn("UTC+8 provides overnight coverage for US teams", next_step)
        my_work = html.split('<section id="my-work">', 1)[1].split(
            '<section id="personal">', 1
        )[0]
        self.assertNotIn("UTC+8 provides overnight coverage for US teams", my_work)
        self.assertIn('<section id="my-work">', html)
        self.assertIn("<h2>My Work</h2>", html)
        self.assertIn("<h3>What I Do</h3>", html)
        self.assertIn('<h3 id="projects">Open Source</h3>', html)
        self.assertNotIn('<section id="work">', html)
        self.assertNotIn('<section id="projects">', html)
        self.assertIn('<section id="personal">', html)
        self.assertIn("Family &amp; Hobby", html)
        self.assertNotIn("3 MCP servers", html)
        self.assertNotIn("6+ providers", html)
        self.assertNotIn("BS Computer Science", html)
        self.assertIn("<h4>Rails Modernization", html)
        self.assertIn("<h4>Payment System Integration", html)
        self.assertIn("<h4>Agents in the Work", html)
        header = re.search(r'<p class="header-links">.*?</p>', html, re.S).group(0)
        self.assertNotIn("gumroad.com", header)
        self.assertIn("/eli5/", header)
        self.assertIn("/trees/", header)
        self.assertIn("/reference/", header)
        self.assertIn("/writing/", header)
        css = (ROOT / "style.css").read_text(encoding="utf-8")
        self.assertIn(".card h3, .card h4", css)
        self.assertRegex(css, r"\.writing-pins\s*\{[^}]*margin-top:\s*0\.85rem")
        HTMLParser().feed(html)

    def test_essay_schema_and_head(self):
        essay = ESSAY.read_text(encoding="utf-8")
        self.assertIn('rel="canonical"', essay)
        self.assertIn('property="og:url"', essay)
        self.assertIn('"@type":"Article"', essay)
        self.assertIn("AI-DDoS", essay)
        index = INDEX.read_text(encoding="utf-8")
        self.assertNotIn('"@type":"Article"', index)

    def test_live_essays_have_article_head(self):
        for path in sorted((ROOT / "writing").glob("*/index.html")):
            slug = path.parent.name
            if is_snapshot_slug(slug):
                continue
            html = path.read_text(encoding="utf-8")
            with self.subTest(slug=slug):
                self.assertRegex(html, r"<title>.+</title>")
                self.assertIn('name="description"', html)
                self.assertIn('rel="canonical"', html)
                self.assertIn('property="og:title"', html)
                self.assertIn('property="og:description"', html)
                self.assertIn('property="og:url"', html)
                self.assertIn("application/ld+json", html)
                self.assertIn('"@type":"Article"', html)

    def test_sitemap_and_atom(self):
        items = load_catalog()
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        self.assertIn("https://ngpestelos.com/", locs)
        self.assertIn("https://ngpestelos.com/writing/", locs)
        self.assertIn("https://ngpestelos.com/writing/atom.xml", locs)
        for item in items:
            self.assertIn(f"https://ngpestelos.com/writing/{item['slug']}/", locs)
        self.assertTrue(ATOM.is_file(), ATOM)
        root = ET.parse(ATOM).getroot()
        entries = root.findall("atom:entry", ATOM_NS)
        if not entries:
            entries = root.findall("entry")
        self.assertEqual(len(entries), len(items))
        feed_updated = datetime.fromisoformat(root.findtext("atom:updated", namespaces=ATOM_NS))
        for entry in entries:
            entry_updated = datetime.fromisoformat(
                entry.findtext("atom:updated", namespaces=ATOM_NS)
            )
            self.assertEqual(entry_updated.utcoffset(), timedelta(hours=8))
            self.assertLessEqual(entry_updated, feed_updated)

    def test_privacy_mentions_cloudflare(self):
        html = PRIVACY.read_text(encoding="utf-8")
        self.assertIn("Cloudflare Web Analytics", html)
        self.assertNotIn("beacon.min.js", html)

    def test_proof_pages(self):
        deep = DEEP_DIVE.read_text(encoding="utf-8")
        comparison = COMPARISON.read_text(encoding="utf-8")
        for html in (deep, comparison):
            self.assertNotRegex(html, r"(?i)chaos")
            self.assertNotIn("40+ linters", html)
            self.assertNotIn("3,797", html)
            self.assertNotIn("91%", html)
            self.assertNotIn("6.8M", html)
            self.assertNotIn("66%", html)
            self.assertNotIn('class="next-step"', html)
        self.assertIn("8-check", deep)
        self.assertIn("1,116,726", deep)
        self.assertNotIn("ROI", comparison)


if __name__ == "__main__":
    unittest.main()
