"""Regression checks for the Ruby lesson's readable and runnable contract."""
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'lessons' / 'ruby-blocks-closures' / 'index.html'

class LessonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.editors = 0
        self.reveals = 0
        self.labels = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'textarea' and attrs.get('aria-label'):
            self.editors += 1
        if tag == 'details':
            self.reveals += 1
        if attrs.get('aria-live'):
            self.labels += 1

class RubyLessonTests(unittest.TestCase):
    def test_examples_remain_readable_and_interactive(self):
        self.assertTrue(PAGE.exists(), "lesson page must exist")

        html = PAGE.read_text()
        parser = LessonParser()
        parser.feed(html)
        self.assertGreaterEqual(parser.editors, 4)
        self.assertGreaterEqual(parser.reveals, 3)
        self.assertGreaterEqual(parser.labels, 1)
        self.assertIn('make_counter_pair', html)
        self.assertIn('Hello, Ana!', html)
        self.assertIn('JavaScript', html)
    def test_site_links_to_lesson_and_sitemap(self):
        path = '/lessons/ruby-blocks-closures/'
        self.assertIn(path, (ROOT / 'index.html').read_text())
        self.assertIn('https://ngpestelos.com' + path, (ROOT / 'sitemap.xml').read_text())

if __name__ == '__main__':
    unittest.main()
