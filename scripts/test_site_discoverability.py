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
REF = ROOT / "reference"

PAYMENTS = {
    "instapay-is-not-ach",
    "us-and-philippine-payment-rails",
    "payments-glossary",
    "agent-rail-war-red-herring",
}
SNAPSHOT_SLUG = re.compile(r"-\d{8}$")
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def sitemap_locs(text: str) -> set[str]:
    return set(re.findall(r"<loc>([^<]+)</loc>", text))


def is_snapshot_slug(slug: str) -> bool:
    return bool(SNAPSHOT_SLUG.search(slug))


def parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    return datetime.fromisoformat(value)


def bucket_datetimes(html: str) -> dict[str, list[str]]:
    sections = re.findall(
        r'<section class="bucket" id="([^"]+)">(.*?)</section>',
        html,
        re.S,
    )
    return {
        bucket_id: re.findall(r'<time datetime="([^"]+)">', body)
        for bucket_id, body in sections
    }


class MetaDescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.descriptions = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attributes = dict(attrs)
        if tag == "meta" and attributes.get("name") == "description":
            self.descriptions.append(attributes.get("content"))


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
        datetimes = bucket_datetimes(html)
        self.assertEqual(list(datetimes), ["systems", "payments", "essays"])
        for bucket_id, dates in datetimes.items():
            self.assertEqual(dates, sorted(dates, reverse=True), bucket_id)
        systems = re.search(
            r'<section class="bucket" id="systems">.*?</section>', html, re.S
        ).group(0)
        employee = systems.find("/writing/the-employee-you-cant-stop-managing/")
        meat = systems.find("/writing/meat-proxy-problem/")
        source = systems.find("/writing/build-source-of-truth-before-index/")
        self.assertTrue(0 <= employee < meat < source)

    def test_homepage_pins_and_linters(self):
        html = HOME.read_text(encoding="utf-8")
        self.assertNotIn("40+", html)
        self.assertIn("8-check", html)
        self.assertIn('<section id="writing-pins">', html)
        self.assertEqual(html.count('class="hook"'), 3)
        self.assertNotIn("HOOK-", html)
        self.assertNotIn('class="writing-pins"', html)
        self.assertIn("/writing/meat-proxy-problem/", html)
        self.assertIn("/writing/instapay-is-not-ach/", html)
        self.assertIn("/writing/five-checks-against-motivated-reasoning/", html)
        self.assertNotIn("How that upgrade ran", html)
        more = re.search(r'<p class="writing-more">.*?</p>', html, re.S).group(0)
        self.assertIn("/writing/", more)
        self.assertIn("/eli5/", more)
        self.assertIn("/trees/", more)
        self.assertIn("/reference/", more)
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
        self.assertIn('<a href="https://rubyonrails.org/">Ruby on Rails</a>', html)
        next_step = re.search(r'<p class="next-step">.*?</p>', html, re.S).group(0)
        self.assertIn("I work from Manila, UTC+8, so US teams get overnight coverage.", next_step)
        my_work = html.split('<section id="my-work">', 1)[1].split(
            '<section id="personal">', 1
        )[0]
        self.assertNotIn("overnight coverage", my_work)
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
        self.assertIn("<h4>Ruby on Rails Modernization", html)
        self.assertIn("<h4>Payment System Integration", html)
        self.assertIn("<h4>Agents in the Work", html)
        header = re.search(r'<p class="header-links">.*?</p>', html, re.S).group(0)
        self.assertNotIn("gumroad.com", header)
        self.assertNotIn("/eli5/", header)
        self.assertNotIn("/trees/", header)
        self.assertNotIn("/reference/", header)
        self.assertIn("/writing/", header)
        css = (ROOT / "style.css").read_text(encoding="utf-8")
        self.assertIn(".card h3, .card h4", css)
        self.assertNotIn(".writing-pins {", css)
        self.assertIn("#writing-pins ul.pins", css)
        self.assertIn("#writing-pins .hook", css)
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
        items_by_url = {
            f"https://ngpestelos.com/writing/{item['slug']}/": item for item in items
        }
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
        feed_updated = parse_iso_datetime(root.findtext("atom:updated", namespaces=ATOM_NS))
        for entry in entries:
            entry_id = entry.findtext("atom:id", namespaces=ATOM_NS)
            self.assertIn(entry_id, items_by_url)
            item = items_by_url[entry_id]
            article = ROOT / "writing" / item["slug"] / "index.html"
            parser = MetaDescriptionParser()
            parser.feed(article.read_text(encoding="utf-8"))
            self.assertEqual(len(parser.descriptions), 1, article)
            summaries = entry.findall("atom:summary", ATOM_NS)
            self.assertEqual(len(summaries), 1, entry_id)
            self.assertEqual(summaries[0].text, parser.descriptions[0])
            entry_updated = parse_iso_datetime(
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


class ReferenceSeoTests(unittest.TestCase):
    def test_reference_titles_use_middot_not_emdash(self):
        for path in sorted(REF.rglob("index.html")):
            raw = path.read_bytes()
            m = re.search(rb"<title>(.*?)</title>", raw, re.I | re.S)
            self.assertIsNotNone(m, path)
            title = m.group(1).decode("utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("—", title)
                self.assertNotIn("&mdash;", title)

    def test_reference_entries_have_definedterm_jsonld(self):
        for path in sorted(REF.glob("*/index.html")):
            html = path.read_text(encoding="utf-8")
            with self.subTest(slug=path.parent.name):
                self.assertIn("application/ld+json", html)
                self.assertIn('"@type":"DefinedTerm"', html)

    def test_reference_index_has_jsonld(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", html)

    def test_intermediate_packets_is_registered(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/reference/intermediate-packets/"', html)
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        self.assertIn(
            "https://ngpestelos.com/reference/intermediate-packets/",
            locs,
        )

    def test_personal_knowledge_management_is_registered(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/reference/personal-knowledge-management/"', html)
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        self.assertIn(
            "https://ngpestelos.com/reference/personal-knowledge-management/",
            locs,
        )

    def test_adversarial_review_title_scopes_ai_agents(self):
        raw = (REF / "adversarial-agent-review" / "index.html").read_bytes()
        title = re.search(rb"<title>(.*?)</title>", raw, re.I | re.S).group(1).decode("utf-8")
        h1 = (REF / "adversarial-agent-review" / "index.html").read_text(encoding="utf-8")
        self.assertIn("AI Agents", title)
        self.assertIn("Adversarial Review (AI Agents)", h1)
        self.assertNotIn("—", title)

    def test_amdahls_title_targets_parallel_agents(self):
        raw = (REF / "amdahls-law" / "index.html").read_bytes()
        title = re.search(rb"<title>(.*?)</title>", raw, re.I | re.S).group(1).decode("utf-8")
        html = (REF / "amdahls-law" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Parallel AI Agents", title)
        self.assertIn("Amdahl's Law for Parallel AI Agents", html)
        self.assertNotIn("—", title)

    def test_llm_reference_expansion_is_registered(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        for slug in ("transformer-architecture", "llm-inference", "prompt-injection"):
            self.assertIn(f'href="/reference/{slug}/"', html, f"Missing from reference/index.html: {slug}")
            self.assertIn(
                f"https://ngpestelos.com/reference/{slug}/",
                locs,
                f"Missing from sitemap.xml: {slug}",
            )

    def test_large_language_models_cross_links(self):
        html = (REF / "large-language-models" / "index.html").read_text(encoding="utf-8")
        expected_links = [
            "/reference/transformer-architecture/",
            "/reference/llm-inference/",
            "/reference/prompt-injection/",
            "/reference/autoregressive/",
            "/reference/deep-neural-networks/",
            "/reference/softmax/",
            "/reference/tokens/",
            "/reference/embeddings/",
            "/reference/vector-search/",
            "/reference/context-engineering/",
            "/reference/context-window/",
            "/reference/prompt-engineering/",
            "/reference/llm-gateway/",
            "/reference/model-router/",
            "/reference/semantic-caching/",
            "/reference/prompt-caching/",
            "/reference/llm-evaluations/",
            "/reference/llm-mutation-testing/",
            "/reference/firewall-llm/",
            "/reference/plan-approve-execute/",
        ]
        for link in expected_links:
            self.assertIn(link, html, f"Missing cross-link in large-language-models: {link}")


    def test_learning_paradigms_reference_registered(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        for slug in ("supervised-learning", "unsupervised-learning"):
            self.assertIn(f'href="/reference/{slug}/"', html, f"Missing from reference/index.html: {slug}")
            self.assertIn(
                f"https://ngpestelos.com/reference/{slug}/",
                locs,
                f"Missing from sitemap.xml: {slug}",
            )
            entry_html = (REF / slug / "index.html").read_text(encoding="utf-8")
            self.assertIn("application/ld+json", entry_html)
            self.assertIn('"@type":"DefinedTerm"', entry_html)

        ml_html = (REF / "machine-learning" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/reference/supervised-learning/"', ml_html)
        self.assertIn('href="/reference/unsupervised-learning/"', ml_html)


    def test_vector_reference_registered(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        self.assertIn('href="/reference/vector/"', html, "Missing from reference/index.html: vector")
        self.assertIn("https://ngpestelos.com/reference/vector/", locs, "Missing from sitemap.xml: vector")
        entry_html = (REF / "vector" / "index.html").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", entry_html)
        self.assertIn('"@type":"DefinedTerm"', entry_html)
        vs_html = (REF / "vector-search" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/reference/vector/"', vs_html)


    def test_computer_vision_reference_registered(self):
        html = (REF / "index.html").read_text(encoding="utf-8")
        locs = sitemap_locs(SITEMAP.read_text(encoding="utf-8"))
        self.assertIn('href="/reference/computer-vision/"', html, "Missing from reference/index.html: computer-vision")
        self.assertIn("https://ngpestelos.com/reference/computer-vision/", locs, "Missing from sitemap.xml: computer-vision")
        entry_html = (REF / "computer-vision" / "index.html").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", entry_html)
        self.assertIn('"@type":"DefinedTerm"', entry_html)
        p_html = (REF / "perception" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/reference/computer-vision/"', p_html)


if __name__ == "__main__":
    unittest.main()



