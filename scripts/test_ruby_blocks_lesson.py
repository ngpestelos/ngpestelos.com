"""Regression checks for the Ruby lesson's permanent redirect."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
PATH = '/lessons/ruby-blocks-closures/'
TARGET = 'https://rubyplayground.org/'
PAGE = ROOT / PATH.lstrip('/') / 'index.html'


class RedirectParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refresh = None
        self.canonical = None
        self.links = []
        self.editors = 0
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
            self.refresh = attrs.get('content')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')
        if tag == 'a':
            self.links.append(attrs.get('href'))
        self.editors += tag == 'textarea'
        self.scripts += tag == 'script'


class RubyLessonTests(unittest.TestCase):
    def test_permanent_redirect_covers_existing_url_forms(self):
        redirects = ROOT / '_redirects'
        self.assertTrue(redirects.is_file(), 'Pages redirect rules must exist')
        rules = [line.split() for line in redirects.read_text().splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        aliases = {PATH.rstrip('/'), PATH, PATH + 'index.html'}
        self.assertEqual({rule[0] for rule in rules}, aliases)
        for source, destination, status in rules:
            with self.subTest(source=source):
                self.assertEqual(destination, TARGET)
                self.assertEqual(status, '301')

    def test_fallback_redirect_has_canonical_and_readable_link(self):
        parser = RedirectParser()
        parser.feed(PAGE.read_text())
        self.assertIsNotNone(parser.refresh, 'fallback must redirect without JavaScript')
        delay, destination = parser.refresh.split(';', 1)
        self.assertEqual(delay.strip(), '0')
        key, value = destination.strip().split('=', 1)
        self.assertEqual(key.lower(), 'url')
        self.assertEqual(value, TARGET)
        self.assertEqual(parser.canonical, TARGET)
        self.assertIn(TARGET, parser.links)
        self.assertEqual(parser.editors, 0)
        self.assertEqual(parser.scripts, 0)

    def test_redirect_is_not_advertised_as_indexable_content(self):
        tree = ElementTree.parse(ROOT / 'sitemap.xml')
        locations = [node.text for node in tree.findall('.//{*}loc')]
        self.assertNotIn('https://ngpestelos.com' + PATH, locations)
        self.assertNotIn(TARGET, locations)
        self.assertIn('https://ngpestelos.com/', locations)
        self.assertIn(PATH, (ROOT / 'index.html').read_text())


if __name__ == '__main__':
    unittest.main()
