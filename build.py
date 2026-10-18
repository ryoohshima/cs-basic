from pathlib import Path
from html import escape
from html.parser import HTMLParser
import json
import re
import sys
BASE=Path(__file__).resolve().parent
from ingest import validate_lessons
L=json.loads((BASE/'lessons.json').read_text(encoding='utf-8'))
validate_lessons(L)
def check_html(html,count):
 class Parser(HTMLParser):
  def __init__(self):
   super().__init__();self.ids=[];self.links=[];self.articles=0
  def handle_starttag(self,tag,attrs):
   attrs=dict(attrs)
   if 'id' in attrs:self.ids.append(attrs['id'])
   if tag=='a' and attrs.get('href','').startswith('#'):self.links.append(attrs['href'][1:])
   if tag=='article':self.articles+=1
 p=Parser();p.feed(html)
 if len(p.ids)!=len(set(p.ids)):raise ValueError('idが重複しています')
 if any(link not in p.ids for link in p.links):raise ValueError('内部リンクの参照先がありません')
 if p.articles!=count:raise ValueError('講義数が一致しません')
def present_body(lesson):
 body, marker, supplement = lesson['body'].partition('<h4>補足解説</h4>')
 body = body.removeprefix('<h4>元スレッドの講義</h4>')
 # Remove code-pane labels, while retaining language names inside the teaching text and examples.
 body = re.sub(r'(?<=>)(?:プレーンテキスト|JavaScript|SQL|http)\s*(?=<pre\b)', '', body)
 body = re.sub(r'<h4>CS基礎 5分学習｜第[0-9]+回</h4>', '', body)
 body = re.sub(r'<h4>① 今日の(?:CS)?テーマ：(.*?)</h4>', r'<p class="lead">\1</p>', body, flags=re.S)
 def heading(match):
  text = match.group(1)
  if text.startswith('② 3分で'):
   return '<h3>仕組みを理解する</h3>'
  if text.startswith('③ フロントエンド実務'):
   return '<h3>実務との接続</h3>'
  if text.startswith('④ 理解確認'):
   return '<h3>理解確認</h3>'
  if text == '今日のまとめ':
   return '<h3>要点のおさらい</h3>'
  text = text.replace('元スレッドの追加回答：', '関連する疑問：').replace('元スレッドの復習：', '復習：').replace('元スレッドの総復習：', '総復習：')
  return '<h4>' + text + '</h4>'
 body = re.sub(r'<h4>(.*?)</h4>', heading, body, flags=re.S)
 body = re.sub(r'(<details><summary>解答を見る</summary>)(.*?)(</details>)', r'\1<div class="answer">\2</div>\3', body, flags=re.S)
 return body, supplement if marker else ''
css='''
:root{--ink:#202e35;--muted:#536771;--accent:#09685f;--paper:#fffefa;--line:#dce4de;--soft:#edf4ee}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:5rem}body{margin:0;background:#f3f1e9;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;line-height:1.95;overflow-wrap:anywhere}a{color:var(--accent);text-underline-offset:4px}a:hover{text-decoration-thickness:2px}a:focus-visible,summary:focus-visible,pre:focus-visible{outline:3px solid #a64d20;outline-offset:4px}.skip{position:absolute;top:-100px;left:1rem;z-index:5;background:white;padding:1rem}.skip:focus{top:1rem}.topbar{position:sticky;top:0;z-index:2;background:#fffefaee;border-bottom:1px solid var(--line);backdrop-filter:blur(10px)}.topbar div{max-width:1120px;margin:auto;padding:.6rem 1.3rem;display:flex;justify-content:space-between;gap:1rem;font-size:.85rem}.brand{font-weight:800;letter-spacing:.08em}.wrap{max-width:1120px;margin:auto;padding:0 1.3rem}.hero{padding:4rem 0 2.6rem;max-width:820px}.eyebrow{color:var(--accent);font-size:.78rem;font-weight:800;letter-spacing:.14em}.hero h1{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;font-size:clamp(2.2rem,6vw,3.8rem);letter-spacing:.03em;line-height:1.4;margin:.6rem 0 1rem}.hero p{max-width:660px;color:var(--muted)}.pill{display:inline-block;border:1px solid #baccc0;border-radius:30px;padding:.2rem .9rem;margin:.3rem .3rem .3rem 0;font-size:.8rem}.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:2.5rem;align-items:start}.toc{position:sticky;top:5rem;max-height:calc(100vh - 6rem);overflow:auto;padding:1rem 1rem 1rem 0}.toc h2{font-size:1rem;margin:0}.toc ol{padding:0;list-style:none}.toc a{display:flex;gap:.7rem;padding:.45rem .5rem;text-decoration:none;font-size:.86rem;border-radius:5px}.toc a:hover{background:#e0eae2}.num{font-variant-numeric:tabular-nums;color:#607b6d;min-width:1.4rem}.category{font-size:.76rem;font-weight:750;color:var(--muted);padding:.9rem .5rem .1rem;grid-column:1/-1}.toc small{color:var(--muted)}main{min-width:0}.intro,.lesson,.ending{background:var(--paper);border:1px solid var(--line);padding:clamp(1.2rem,3vw,2.4rem);margin-bottom:2rem;border-radius:12px}.intro h2{font-size:1.25rem;margin-top:0}.flow{border-left:3px solid var(--accent);padding-left:1rem;font-weight:600}.lesson{scroll-margin-top:5rem}.lesson header{padding-bottom:1.1rem;border-bottom:1px solid var(--line)}.lesson header p{font-size:.8rem;margin:0;color:var(--accent);font-weight:700;letter-spacing:.07em}.lesson h2{font-size:clamp(1.5rem,3vw,2rem);line-height:1.5;margin:.5rem 0}.goal{color:var(--muted);font-size:.92rem}.lesson h4{font-size:1rem;margin:1.8rem 0 .65rem}.lesson h3{font-size:1.1rem;margin:2rem 0 .7rem}.lesson p{margin:.9rem 0}strong{font-weight:750}code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.89em;background:#eaf0eb;padding:.1em .25em;border-radius:3px}table{display:block;overflow-x:auto;border-collapse:collapse;max-width:100%;margin:1rem 0}th,td{border:1px solid var(--line);padding:.5rem .7rem;text-align:left;min-width:7rem}th{background:var(--soft)}blockquote{border-left:3px solid var(--accent);margin:1rem 0;padding:.1rem 1rem}hr{border:0;border-top:1px solid var(--line);margin:1.5rem 0}pre{white-space:pre;overflow-x:auto;background:#1f3336;color:#e9f3e9;padding:1.1rem 1.25rem;border-radius:7px;font-size:.85rem;line-height:1.8;max-width:100%}pre code{background:none;padding:0;font-size:inherit;color:inherit}aside,.practice{background:var(--soft);border-radius:7px;padding:1rem 1.2rem;margin:1.3rem 0}.practice h3{margin:.1rem 0 .5rem}.ref{font-size:.8rem;color:var(--muted)}.quiz{padding-top:.2rem}.question{border-top:1px solid var(--line);padding:1rem 0}.question p{margin:.2rem 0 .7rem;font-weight:650}details{border:1px solid #c8d8cb;border-radius:6px;background:#f5f8f3}summary{cursor:pointer;padding:.6rem .85rem;color:var(--accent);font-weight:650;font-size:.9rem;min-height:44px}details .answer{padding:.2rem 1rem 1rem;font-size:.94rem}.pager{border-top:1px solid var(--line);padding-top:1.1rem;display:grid;grid-template-columns:1fr auto 1fr;gap:.7rem;align-items:center;font-size:.84rem}.pager a{padding:.45rem 0;min-height:44px}.pager a:last-child{text-align:right}dt{font-weight:750;margin-top:.7rem}dd{margin:.2rem 0 .6rem}footer{color:var(--muted);font-size:.8rem;padding:0 0 3rem}.ending h2{font-size:1.2rem}.note{font-size:.82rem;color:var(--muted)}@media(max-width:780px){.layout{display:block}.toc{position:static;max-height:none;padding:1.2rem;background:#e9eee5;border-radius:10px;margin-bottom:1.5rem}.toc ol{display:grid;grid-template-columns:1fr 1fr;gap:.3rem;margin-bottom:0}.toc a{padding:.5rem .3rem}.hero{padding-top:2.3rem}.wrap{padding:0 1rem}.lesson,.intro{margin-bottom:1.2rem}.topbar div{padding:.6rem 1rem}.pager{font-size:.8rem;gap:.5rem}}@media(max-width:430px){.toc ol{grid-template-columns:1fr}.lesson{padding:1.15rem}.hero h1{font-size:2.15rem}.pager{grid-template-columns:1fr 1fr}.pager a:nth-child(2){grid-column:1/-1;grid-row:2;text-align:center}.pager a:last-child{text-align:right}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{body{background:white;font-size:10pt}.topbar,.skip,.pager{display:none}.layout{display:block}.toc{position:static;max-height:none}.toc ol{columns:2}.hero{padding:0}.lesson{border:0;border-top:1px solid #aaa;border-radius:0;padding:1rem 0;break-before:page}pre{white-space:pre-wrap;color:black;background:#eee}details .answer{display:block}details::details-content{content-visibility:visible}.intro,.ending{border:0}.wrap{max-width:none}.ref a{color:black}}
'''
head='''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="CS基礎 第1回から。仕組み・フロントエンド実務・理解確認をつないだ復習ノート。"><title>CS基礎｜第1回からの 復習ノート</title><style>'''+css+'''</style></head><body><a class="skip" href="#main">本文へ移動</a><div class="topbar"><div><span class="brand">CS STUDY NOTES</span><a href="#contents">目次へ ↑</a></div></div><div class="wrap"><header class="hero"><div class="eyebrow">COMPUTER SCIENCE / LEARNING NOTE / FROM 01</div><h1>仕組みがつながる、<br>CS基礎の復習ノート。</h1><p>プログラムの実行から、データを速く探し、安全に更新するところまで。必要な回から読み直せる、収録済みの各回の学習ノートです。</p><span class="pill">オフラインで読める</span></header><div class="layout"><nav class="toc" id="contents" aria-label="各回の目次"><h2>学習の目次</h2><small>気になるテーマからどうぞ</small><ol>'''
parts=[head]
pages=[]
last_group=None
for n,l in enumerate(L,1):
 if l["group"] != last_group:
  parts.append(f'<li class="category">{escape(l["group"])}</li>')
  last_group=l["group"]
 parts.append(f'<li><a href="#lesson-{n}"><span class="num">{n:02}</span><span>{l["title"]}</span></a></li>')
parts.append('''</ol></nav><main id="main"><section class="intro"><h2>まず、全体のつながりをつかむ</h2><p class="flow">実行する → 同時処理を制御する → メモリを管理する → データの置き方を選ぶ → DBで速さと正しさを守る</p><p>各回は「仕組み → 実務との接続 → 理解確認」の順です。答えを開く前に、自分の言葉で一度説明してみてください。読了時間は人によるため、1回ずつ区切って進めましょう。</p><details><summary>元の会話と、このノートの編集方針</summary><div class="answer">元資料は会話「基本情報 5分学習」。元スレッドの個別講義を取得し、解説・コード・図解・確認問題・解答を省略せず収録しました。MapやReactの参照についての追加回答、総復習も関連回に収録しています。元の情報を保持しながら、見出しを整理してコード用の画面ラベルを除いています。関連する補足解説・実務例・追加問題は開閉できる欄にまとめています。見出し階層や表・コードの表示形式を整え、画面操作用のボタンは除いています。原文中の単純化した説明には補足解説を併せて確認してください。計算量の前提、JavaScriptの仕様と典型実装の違い、B-treeとB+tree系の区別、トランザクションの保証範囲を明確にしました。公式資料のリンクは該当回に記載しています。本文の閲覧に通信は不要ですが、外部の確認資料を開くときは通信が必要です。</div></details></section>''')
for n,l in enumerate(L,1):
 article_start=len(parts)
 body,supplement=present_body(l)
 parts.append(f'<article class="lesson" id="lesson-{n}" aria-labelledby="title-{n}"><header><p>LESSON {n:02} / {l["group"]}</p><h2 id="title-{n}">第{n}回 {l["title"]}</h2><div class="goal">この回のゴール：{l["goal"]}</div></header>{body}<details class="supplement"><summary>補足解説と追加の実務例・確認問題</summary><div class="answer"><h3>補足解説</h3>{supplement}<section class="practice"><h3>フロントエンド実務との接続</h3>{l["practice"]}</section><section class="quiz"><h3>追加の理解確認</h3>')
 for j,(q,a) in enumerate(l['questions'],1): parts.append(f'<div class="question"><p>Q{j}. {q}</p><details><summary>解答と解説を開く</summary><div class="answer">{a}</div></details></div>')
 prev=f'<a rel="prev" href="#lesson-{n-1}">← 第{n-1}回</a>' if n>1 else '<span>ここからスタート</span>'
 nxt=f'<a rel="next" href="#lesson-{n+1}">第{n+1}回 →</a>' if n<len(L) else '<a href="#finish">全体を振り返る →</a>'
 parts.append(f'</section></div></details><nav class="pager" aria-label="第{n}回の前後移動">{prev}<a href="#contents">目次に戻る</a>{nxt}</nav></article>')
 pages.append(''.join(parts[article_start:]))
parts.append('''<section class="ending" id="finish"><div class="eyebrow">CONNECT THE DOTS</div><h2>収録済みの各回を、ひとつの流れで振り返る</h2><p>CPUが命令を実行し、スタックやヒープで呼び出しとデータを管理する。クロージャは外側の環境を参照し、イベントループは非同期処理の実行機会を調整する。プロセスとスレッドで仕事を進めると、競合や待ちの問題が生まれる。データは仮想メモリで管理され、配置とキャッシュが処理速度に影響する。用途に応じたデータ構造を選び、DBではインデックスで探索を効率化し、トランザクションと競合制御で更新の正しさを守る。</p><p>「何という名前か」だけでなく、<strong>何を解決するか・どの条件で有効か・何までは保証しないか</strong>を説明できれば、理解がつながっています。</p><a href="#contents">目次から、もう一度復習する ↑</a></section></main></div><footer>CS基礎 復習ノート · 第1回からの<br>外部フォント・画像・ライブラリ不使用</footer></div></body></html>''')
out=Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'dist'
(out/'lessons').mkdir(parents=True,exist_ok=True)
html=''.join(parts)
check_html(html,len(L))
(out/'cs-basics.html').write_text(html,encoding='utf-8')
# The combined offline edition and individual pages share the same lesson markup.
catalog=[]
last_group=None
for n,lesson in enumerate(L,1):
 if lesson['group']!=last_group:
  catalog.append(f'<li class="category">{escape(lesson["group"])}</li>')
  last_group=lesson['group']
 catalog.append(f'<li><a href="lessons/{n:03}.html"><span class="num">{n:02}</span><span>{escape(lesson["title"])}</span></a></li>')
index=f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CS基礎｜学習目次</title><style>{css}.catalog{{max-width:800px;padding-top:2rem;padding-bottom:3rem}}.catalog .toc{{position:static;max-height:none;padding:1.3rem}}.catalog h1{{font-size:1.6rem}}.catalog .toc a{{font-size:1rem}}</style></head><body><main class="wrap catalog" id="main"><h1>CS基礎 学習目次</h1><nav class="toc" id="contents" aria-label="各回の目次"><ol>{"".join(catalog)}</ol></nav></main></body></html>'
(out/'index.html').write_text(index,encoding='utf-8')
for n,article in enumerate(pages,1):
 for target in range(1,len(L)+1):
  article=article.replace(f'href="#lesson-{target}"',f'href="{target:03}.html"')
 article=article.replace('href="#contents"','href="../index.html#contents"').replace('href="#finish"','href="../index.html"')
 page=f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第{n}回 {escape(L[n-1]["title"])}</title><style>{css}</style></head><body><div class="wrap"><header class="hero"><a href="../index.html">CS基礎の学習目次へ</a> · <a href="../cs-basics.html">全回をまとめて読む</a></header><main>{article}</main></div></body></html>'
 (out/'lessons'/f'{n:03}.html').write_text(page,encoding='utf-8')
print(f'{out}: {len(L)} lessons / {sum(len(x["questions"]) for x in L)} questions')
