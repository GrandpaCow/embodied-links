from pathlib import Path
from html import escape
import json, re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '_site'
data = json.loads((ROOT/'data.json').read_text(encoding='utf-8-sig'))

# Stop an invalid update before publishing; never silently discard entries.
category_ids = [c['id'] for c in data['categories']]
if len(category_ids) != len(set(category_ids)) or not category_ids:
    raise ValueError('Category IDs must be unique and nonempty')
for category in data['categories']:
    if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', category['id']) or not category['title'].strip():
        raise ValueError('Invalid category ID or title')
seen = set()
for entry in data['entries']:
    item_id = str(entry['id'])
    if item_id in seen or not re.fullmatch(r'[a-zA-Z0-9_-]+', item_id):
        raise ValueError('Invalid or duplicate entry ID: ' + item_id)
    seen.add(item_id)
    if entry['category'] not in category_ids:
        raise ValueError('Unknown category for entry ' + item_id)
    for key in ('title', 'url', 'summary'):
        if not isinstance(entry[key], str) or not entry[key].strip():
            raise ValueError('Missing ' + key + ' for entry ' + item_id)
    url = urlsplit(entry['url'])
    if url.scheme not in ('http', 'https') or not url.netloc:
        raise ValueError('Invalid URL for entry ' + item_id)
supplement = data.get('supplement')
if supplement and (supplement['category'] not in category_ids or
                   not supplement['title'].strip() or not supplement['summary'].strip()):
    raise ValueError('Invalid supplement')
OUT.mkdir(parents=True, exist_ok=True)
e = escape
parts = ['''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>具身大创群分享资料汇总</title>
<style>
:root{color-scheme:light;--ink:#153650;--link:#17658a;--body:#303b45;--line:#dce5e9}
*{box-sizing:border-box}
html{scroll-padding-top:24px}
body{margin:0;background:#f5f7f8;color:var(--body);font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.85;-webkit-text-size-adjust:100%}
main{max-width:900px;margin:36px auto;padding:44px 54px 64px;background:#fff;border-radius:12px}
h1{font-size:30px;line-height:1.4;letter-spacing:.01em;margin:0 0 30px;color:var(--ink);padding-bottom:22px;border-bottom:3px solid #288f8b}
h2{font-size:22px;line-height:1.55;color:var(--ink);margin:0 0 18px}
nav{margin-bottom:48px}
nav ol{padding:0;margin:0;list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:6px 24px}
nav a{display:flex;align-items:baseline;gap:10px;min-height:48px;padding:10px 0;border-bottom:1px solid var(--line);font-size:15px;color:var(--ink);text-decoration:none}
.num{color:#758490;font-variant-numeric:tabular-nums;flex-shrink:0}
section{margin-top:40px;padding-top:24px;border-top:1px solid var(--line)}
article{margin:0 0 23px}
h3{font-size:17px;line-height:1.65;margin:0 0 4px;font-weight:650;overflow-wrap:anywhere}
h3 a{display:block;color:var(--link);text-decoration:none;padding:7px 0;min-height:44px}
h3 .num{margin-right:8px;font-weight:600}
p{font-size:16px;margin:0;overflow-wrap:anywhere}
a:hover{text-decoration:underline;text-underline-offset:4px}
a:focus-visible{outline:3px solid #288f8b;outline-offset:4px;border-radius:2px}
@media(max-width:640px){body{background:#fff}main{margin:0;padding:28px 21px 42px;border-radius:0}h1{font-size:25px;margin-bottom:25px;padding-bottom:18px}nav ol{grid-template-columns:1fr;gap:0}nav{margin-bottom:32px}nav a{font-size:16px;padding:11px 0}h2{font-size:21px}section{margin-top:30px;padding-top:24px}article{margin-bottom:24px}h3{font-size:17px}p{font-size:16px;line-height:1.9}}
@media print{body{background:white}main{max-width:none;margin:0;padding:0}nav a,h3 a{color:var(--ink)}article{break-inside:avoid}}
</style></head><body><main>
<h1>具身大创群分享资料汇总</h1>
<nav aria-label="目录" id="contents"><h2>目录</h2><ol>''']
for i, cat in enumerate(data['categories'], 1):
    parts.append(f'<li><a href="#{e(cat["id"])}"><span class="num">{i:02}</span><span>{e(cat["title"])}</span></a></li>')
parts.append('</ol></nav>')
ordinal = 0
for i, cat in enumerate(data['categories'], 1):
    parts.append(f'<section id="{e(cat["id"])}" aria-labelledby="heading-{e(cat["id"])}"><h2 id="heading-{e(cat["id"])}">{i:02} {e(cat["title"])}</h2>')
    for entry in data['entries']:
        if entry['category'] != cat['id']:
            continue
        ordinal += 1
        title = entry['title']
        parts.append(f'<article id="entry-{entry["id"]}"><h3><a href="{e(entry["url"],quote=True)}"><span class="num">{ordinal:02}</span>{e(title)}</a></h3><p>{e(entry["summary"])}</p></article>')
    s = data.get('supplement')
    if s and s['category'] == cat['id']:
        parts.append(f'<article class="supplement"><h3>补充记录 · {e(s["title"])}</h3><p>{e(s["summary"])}</p></article>')
    parts.append('</section>')
parts.append('</main></body></html>')
if ordinal != len(data['entries']):
    raise ValueError('Some entries were not rendered')
(OUT/'index.html').write_text('\n'.join(parts), encoding='utf-8')
(OUT/'.nojekyll').touch()
print(f"Built {ordinal} links in {len(data['categories'])} categories: _site/index.html")
