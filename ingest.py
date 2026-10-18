"""Validate a delivered lesson and append it once, without modifying earlier lessons."""
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent
FIELDS = {'title', 'group', 'goal', 'body', 'practice', 'questions'}


class Fragment(HTMLParser):
    TAGS = {'p', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'dl',
            'dt', 'dd', 'a', 'aside', 'br', 'hr', 'h4',
            'table', 'thead', 'tbody', 'tr', 'th', 'td', 'blockquote'}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.TAGS:
            raise ValueError(f'許可されていないHTML: {tag}')
        for key, value in attrs:
            if key == 'href' and tag == 'a':
                url = urlsplit(value or '')
                if url.scheme != 'https' or not url.netloc or any(c.isspace() for c in value):
                    raise ValueError('リンクはHTTPS URLのみ使用できます')
            elif (key, value) not in {('class', 'ref'), ('tabindex', '0')}:
                raise ValueError(f'許可されていない属性: {key}')
        if tag not in {'br', 'hr'}:
            self.stack.append(tag)

    def handle_data(self, data):
        if "<" in data:
            raise ValueError("未完了のHTMLタグまたはエスケープされていない < があります")

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError(f'HTMLの閉じタグが一致しません: {tag}')

    def handle_comment(self, data):
        raise ValueError('HTMLコメントは使用できません')

    def handle_decl(self, decl):
        raise ValueError('HTML宣言は使用できません')


def validate_lesson(lesson):
    if not isinstance(lesson, dict) or set(lesson) != FIELDS:
        raise ValueError('講義のフィールドが一致しません')
    for field in FIELDS - {'questions'}:
        value = lesson[field]
        if not isinstance(value, str) or not value.strip() or len(value) > 100000:
            raise ValueError(f'必須文字列が不正です: {field}')
        if field in {'title', 'group', 'goal'}:
            if '<' in value or '>' in value:
                raise ValueError('見出しはプレーンテキストにしてください')
        else:
            validate_fragment(value)
    questions = lesson['questions']
    if not isinstance(questions, list) or not 1 <= len(questions) <= 20:
        raise ValueError('確認問題は1〜20問必要です')
    for pair in questions:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('確認問題は[質問, 解答]です')
        for value in pair:
            if not isinstance(value, str) or not value.strip() or len(value) > 10000:
                raise ValueError('質問と解答は空でない文字列が必要です')
            validate_fragment(value)


def validate_fragment(value):
    # Reject incomplete tokens before HTMLParser, whose recovery differs by Python version.
    tokens_removed = re.sub(r"""<(?:[^<>"']|"[^"]*"|'[^']*')*>""", '', value)
    if '<' in tokens_removed:
        raise ValueError('HTMLタグが未完了です。文字の < は &lt; にしてください')
    parser = Fragment()
    parser.feed(value)
    parser.close()
    if parser.stack or parser.rawdata:
        raise ValueError('HTMLの閉じタグが不足しています')


def validate_lessons(lessons):
    if not isinstance(lessons, list) or not lessons:
        raise ValueError('講義の配列が必要です')
    for lesson in lessons:
        validate_lesson(lesson)


def append_lesson(path, payload):
    if not isinstance(payload, dict) or set(payload) != {'number', 'lesson'}:
        raise ValueError('numberとlessonが必要です')
    number, lesson = payload['number'], payload['lesson']
    if type(number) is not int or number < 1:
        raise ValueError('回番号は正の整数が必要です')
    validate_lesson(lesson)
    lessons = json.loads(path.read_text(encoding='utf-8'))
    validate_lessons(lessons)
    if number <= len(lessons):
        if lessons[number - 1] == lesson:
            return False
        raise ValueError('登録済みの回と内容が異なります。自動上書きしません')
    if number != len(lessons) + 1:
        raise ValueError('欠番があります。次の回から順に追加してください')
    lessons.append(lesson)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(lessons, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)
    return True


if __name__ == '__main__':
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    if os.environ['GITHUB_EVENT_NAME'] == 'repository_dispatch':
        payload = event['client_payload']
    elif os.environ['GITHUB_EVENT_NAME'] == 'workflow_dispatch':
        payload = json.loads(event['inputs']['lesson_json'])
    else:
        raise ValueError('対応していないイベントです')
    changed = append_lesson(BASE / 'lessons.json', payload)
    print('講義を追加しました' if changed else '同一講義は登録済みです（変更なし）')
