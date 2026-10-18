import copy
import hashlib
import re
import json
import subprocess
import sys
import tempfile
import unittest
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from ingest import BASE, append_lesson, validate_lesson


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.articles = 0
        self.answers = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                raise AssertionError('duplicate id')
            self.ids.add(attrs['id'])
        if tag == 'a':
            self.links.append(attrs['href'])
        if tag == 'article':
            self.articles += 1
        if tag == 'details':
            self.answers += 1


class NotesTest(unittest.TestCase):
    def setUp(self):
        self.lessons = json.loads((BASE / 'lessons.json').read_text())
        self.lesson = copy.deepcopy(self.lessons[-1])
        self.lesson['title'] = 'テスト講義'
        self.payload = {'number': len(self.lessons) + 1, 'lesson': self.lesson}

    def test_append_retry_conflict_and_gap(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'lessons.json'
            original = json.dumps(self.lessons, ensure_ascii=False)
            path.write_text(original)
            for number in [0, True, len(self.lessons) + 2]:
                with self.assertRaises(ValueError):
                    append_lesson(path, {**self.payload, 'number': number})
                self.assertEqual(path.read_text(), original)
            self.assertTrue(append_lesson(path, self.payload))
            saved = path.read_bytes()
            self.assertFalse(append_lesson(path, self.payload))
            self.assertEqual(path.read_bytes(), saved)
            self.payload['lesson']['title'] = '競合'
            with self.assertRaises(ValueError):
                append_lesson(path, self.payload)
            self.assertEqual(path.read_bytes(), saved)
            self.assertEqual(json.loads(saved)[:-1], self.lessons)

    def test_original_lessons_are_preserved(self):
        manifest = json.loads((BASE / 'source-manifest.json').read_text())
        self.assertEqual([item['number'] for item in manifest], list(range(1, 16)))
        for item in manifest:
            body = self.lessons[item['number'] - 1]['body']
            original = body.split('<h4>元スレッドの講義</h4>', 1)[1].split('<h4>補足解説</h4>', 1)[0]
            self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), item['sha256'])
            self.assertEqual(len(original), item['html_characters'])

    def test_next_lesson_builds_with_updated_navigation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for name in ['build.py', 'ingest.py', 'lessons.json']:
                (root / name).write_bytes((BASE / name).read_bytes())
            append_lesson(root / 'lessons.json', self.payload)
            subprocess.run([sys.executable, str(root / 'build.py')], check=True)
            number = self.payload['number']
            self.assertTrue((root / 'dist' / 'lessons' / f'{number:03}.html').exists())
            previous = (root / 'dist' / 'lessons' / f'{number-1:03}.html').read_text()
            self.assertIn(f'href="{number:03}.html"', previous)
            index = (root / 'dist' / 'index.html').read_text()
            self.assertIn(f'href="lessons/{number:03}.html"', index)

    def test_reject_unsafe_or_incomplete_input(self):
        for fragment in ['<script>alert(1)</script>', '<a href="javascript:alert(1)">x</a>',
                         '<p onclick="alert(1)">x</p>', '<p>閉じ忘れ', '<iframe></iframe>',
                         '<img src=x onerror=alert(1) ',
                         '<a href="https://example.com" onclick="alert(1)" ']:
            with self.subTest(fragment=fragment), self.assertRaises(ValueError):
                validate_lesson({**self.lesson, 'body': fragment})
        with self.assertRaises(ValueError):
            validate_lesson({**self.lesson, 'questions': []})

    def test_all_generated_pages_and_links(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder).resolve()
            subprocess.run([sys.executable, str(BASE / 'build.py'), str(output)], check=True)
            files = list(output.rglob('*.html'))
            self.assertEqual(len(files), len(self.lessons) + 2)
            index = (output / 'index.html').read_text()
            self.assertNotIn('<article', index)
            self.assertNotIn('<section', index)
            self.assertNotIn('<details', index)
            self.assertNotIn('まず、全体のつながり', index)
            self.assertNotIn('全回をまとめて読む', index)
            parsed = {}
            for path in files:
                parser = Links()
                parser.feed(path.read_text())
                parsed[path] = parser
            for path, parser in parsed.items():
                for href in parser.links:
                    url = urlsplit(href)
                    if url.scheme:
                        self.assertEqual(url.scheme, 'https')
                        continue
                    target = (path.parent / unquote(url.path)).resolve() if url.path else path
                    self.assertIn(target, parsed, (path, href))
                    if url.fragment:
                        self.assertIn(url.fragment, parsed[target].ids, (path, href))
            for i, lesson in enumerate(self.lessons, 1):
                page = output / 'lessons' / f'{i:03}.html'
                self.assertEqual(parsed[page].articles, 1)
                self.assertEqual(parsed[page].answers, len(lesson['questions']) + lesson['body'].count('<details>') + lesson['practice'].count('<details>') + 1)
                text = page.read_text()
                self.assertNotIn('&lt;details&gt;', text)
                self.assertNotIn('&lt;summary&gt;解答を見る', text)
                if 4 <= i <= 15:
                    self.assertIn('<details><summary>解答を見る</summary>', text)
                self.assertNotRegex(text, r'>(?:プレーンテキスト|JavaScript|SQL|http)\s*<pre')
                self.assertNotIn('<h4>元スレッドの講義</h4>', text)
                prose = re.sub(r'<(?:pre|code)\b[^>]*>.*?</(?:pre|code)>', '', text, flags=re.S)
                self.assertNotRegex(prose, r'\*\*[^*<>]+\*\*')
                self.assertIn('<details class="supplement">', text)
                original = lesson['body'].split('<h4>補足解説</h4>', 1)[0]
                for tag, block in re.findall(r'<(p|pre|li|td|th)(?:\s[^>]*)?>(.*?)</\1>', original, re.S):
                    if tag == 'pre':
                        self.assertIn(block, text, (i, tag, block[:60]))
                    else:
                        def plain(value):
                            return ' '.join(unescape(re.sub(r'<[^>]+>', '', value)).replace('**', '').split())
                        self.assertIn(plain(block), plain(text), (i, tag, block[:60]))
                if i > 1:
                    self.assertIn(f'href="{i-1:03}.html"', text)
                if i < len(self.lessons):
                    self.assertIn(f'href="{i+1:03}.html"', text)


if __name__ == '__main__':
    unittest.main()
