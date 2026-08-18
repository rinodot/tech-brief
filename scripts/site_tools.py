#!/usr/bin/env python3
"""テックブリーフ静的サイト生成: briefs/ とmanifestからindexを再生成し、各号にナビを注入する（冪等）
使い方:
  python3 site_tools.py --site DIR rebuild   # briefs/全件からmanifestのtitles更新+ナビ注入+index再生成
  python3 site_tools.py --site DIR index     # manifest.jsonだけからindex.htmlを再生成
  python3 site_tools.py nav --file F --prev '{"date":...,"weekday":...,"file":...}' --next 'null'
"""
import json, re, os, sys

import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--site", default="/home/claude/site")
_ap.add_argument("--file")
_ap.add_argument("--prev", default="null")
_ap.add_argument("--next", default="null")
_ap.add_argument("cmd", nargs="?", default="rebuild", choices=["rebuild", "index", "nav"])
_ARGS = _ap.parse_args()
SITE = _ARGS.site
BRIEFS = os.path.join(SITE, "briefs")

WD = {"Mon":"月","Tue":"火","Wed":"水","Thu":"木","Fri":"金","Sat":"土","Sun":"日"}

NAV_CSS = """
  .bnav{background:var(--wash); border-bottom:1px solid var(--hair); font-size:12.5px;}
  .bnav .wrap{display:flex; justify-content:space-between; padding-top:10px; padding-bottom:10px;}
  .bnav a{color:var(--soft); text-decoration:none;}
  .bnav a:hover{text-decoration:underline;}
  .bnav .dis{color:var(--grey);}
"""

def jdate(d):
    y, m, dd = d.split("-")
    return f"{int(m)}/{int(dd)}"

def extract_titles(html):
    titles = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<h2>(.*?)</h2>", html, re.S)]
    sp = re.findall(r'<h3 class="sp">(.*?)</h3>', html, re.S)
    titles += [re.sub(r"<[^>]+>", "", m) for m in sp]
    return [t.strip() for t in titles]

def inject_nav(html, prev_e, next_e):
    html = re.sub(r"<!--BNAV START-->.*?<!--BNAV END-->\n?", "", html, flags=re.S)
    html = re.sub(r"<body>\n+", "<body>\n", html)
    if "/*BNAVCSS*/" not in html:
        html = html.replace("</style>", f"/*BNAVCSS*/{NAV_CSS}</style>", 1)
    left = f'<a href="{prev_e["file"]}">← {jdate(prev_e["date"])}（{prev_e["weekday"]}）</a>' if prev_e else '<span class="dis">←</span>'
    right = f'<a href="{next_e["file"]}">{jdate(next_e["date"])}（{next_e["weekday"]}）→</a>' if next_e else '<span class="dis">最新号</span>'
    nav = (f'<!--BNAV START--><nav class="bnav"><div class="wrap">{left}'
           f'<a href="../index.html">一覧</a>{right}</div></nav><!--BNAV END-->\n')
    return html.replace("<body>", "<body>\n" + nav, 1)

def build():
    entries = json.load(open(os.path.join(SITE, "manifest.json"), encoding="utf-8"))
    entries.sort(key=lambda e: e["date"])
    for i, e in enumerate(entries):
        p = os.path.join(BRIEFS, e["file"])
        html = open(p, encoding="utf-8").read()
        e["titles"] = extract_titles(html)
        prev_e = entries[i-1] if i > 0 else None
        next_e = entries[i+1] if i < len(entries)-1 else None
        open(p, "w", encoding="utf-8").write(inject_nav(html, prev_e, next_e))
    json.dump(entries, open(os.path.join(SITE, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    _write_index(entries)
    print(f"built: {len(entries)} issues")
    for e in entries:
        print(" ", e["date"], e["weekday"], "|", len(e["titles"]), "titles")

def _write_index(entries):
    latest = entries[-1]
    months = {}
    for e in reversed(entries):
        months.setdefault(e["date"][:7], []).append(e)
    rows = []
    for mon, es in months.items():
        y, m = mon.split("-")
        rows.append(f'<h2 class="mon">{y}年{int(m)}月</h2>')
        for e in es:
            t = " ／ ".join(e["titles"])
            rows.append(
                f'<a class="row" href="briefs/{e["file"]}"><span class="d">{jdate(e["date"])}（{e["weekday"]}）</span>'
                f'<span class="t">{t}</span></a>')
    lt = "".join(f'<li>{t}</li>' for t in latest["titles"])
    index = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>テックブリーフ</title>
<style>
  :root{{--bg:#FCFCFB; --wash:#F9F9F7; --ink:#2E2C27; --body:#514F47; --soft:#6B6A63; --grey:#B4B3A8; --hair:#E4E3DC; --clay:#C6613F;}}
  *{{box-sizing:border-box; margin:0; padding:0;}}
  body{{background:var(--bg); color:var(--body); font-family:-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif; font-size:15px; line-height:1.9;}}
  .wrap{{max-width:720px; margin:0 auto; padding:0 22px;}}
  header{{background:var(--wash); border-bottom:1px solid #E1E1DF; padding:38px 0 26px;}}
  h1{{font-family:"Hiragino Mincho ProN","Yu Mincho",YuMincho,"Noto Serif JP",serif; font-weight:600; font-size:32px; color:var(--ink); letter-spacing:.05em;}}
  .tag{{font-size:12.5px; color:var(--soft); margin-top:6px;}}
  main{{padding:10px 0 50px;}}
  .latest{{display:block; background:var(--wash); padding:18px 20px; margin:24px 0 10px; text-decoration:none; color:inherit;}}
  .latest:hover .lt{{text-decoration:underline;}}
  .latest .lab{{font-size:11.5px; color:var(--clay); letter-spacing:.08em;}}
  .latest .lt{{font-size:16px; font-weight:700; color:var(--ink); margin:4px 0 6px;}}
  .latest ul{{list-style:none;}}
  .latest li{{font-size:13px; color:var(--soft); padding-left:1em; text-indent:-1em;}}
  .latest li::before{{content:"· ";}}
  h2.mon{{font-size:13px; color:var(--grey); letter-spacing:.06em; margin:26px 0 4px; font-weight:600;}}
  .row{{display:block; padding:12px 2px; border-bottom:1px solid var(--hair); text-decoration:none; color:inherit;}}
  .row:hover .t{{text-decoration:underline;}}
  .row .d{{display:block; font-size:12.5px; color:var(--grey);}}
  .row .t{{display:block; font-size:14px; color:var(--ink); line-height:1.7;}}
  @media (max-width:640px){{.wrap{{padding:0 18px;}} h1{{font-size:26px;}}}}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>テックブリーフ</h1>
  <div class="tag">毎朝6:00配信 · AIエージェント／Flutter・Android／ローカルLLM</div>
</div></header>
<main><div class="wrap">
  <a class="latest" href="briefs/{latest['file']}">
    <div class="lab">最新号</div>
    <div class="lt">{jdate(latest['date'])}（{latest['weekday']}）のブリーフ</div>
    <ul>{lt}</ul>
  </a>
  {"".join(rows)}
</div></main>
</body>
</html>
"""
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(index)

def gen_index_only():
    entries = json.load(open(os.path.join(SITE, "manifest.json"), encoding="utf-8"))
    entries.sort(key=lambda e: e["date"])
    _write_index(entries)

def nav_one():
    e_prev = json.loads(_ARGS.prev)
    e_next = json.loads(_ARGS.next)
    html = open(_ARGS.file, encoding="utf-8").read()
    open(_ARGS.file, "w", encoding="utf-8").write(inject_nav(html, e_prev, e_next))

if __name__ == "__main__":
    if _ARGS.cmd == "index":
        gen_index_only()
    elif _ARGS.cmd == "nav":
        nav_one()
    else:
        build()
