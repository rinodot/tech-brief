#!/usr/bin/env python3
"""テックブリーフ静的サイト生成: briefs/ とmanifestからindexを再生成し、各号にナビを注入する（冪等）"""
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
    # 各号にナビ注入
    for i, e in enumerate(entries):
        p = os.path.join(BRIEFS, e["file"])
        html = open(p, encoding="utf-8").read()
        e["titles"] = extract_titles(html)
        prev_e = entries[i-1] if i > 0 else None
        next_e = entries[i+1] if i < len(entries)-1 else None
        open(p, "w", encoding="utf-8").write(inject_nav(html, prev_e, next_e))
    with open(os.path.join(SITE, "manifest.json"), "w", encoding="utf-8") as _mf:
        json.dump(entries, _mf, ensure_ascii=False, indent=1)
        _mf.write("\n")
    _write_index(entries)
    print(f"built: {len(entries)} issues")
    for e in entries:
        print(" ", e["date"], e["weekday"], "|", len(e["titles"]), "titles")

INDEX_CSS = """  :root{--bg:#FCFCFB; --wash:#F9F9F7; --ink:#2E2C27; --body:#514F47; --soft:#6B6A63; --grey:#B4B3A8; --hair:#E4E3DC; --clay:#C6613F;}
  *{box-sizing:border-box; margin:0; padding:0;}
  html{-webkit-text-size-adjust:100%;}
  body{background:var(--bg); color:var(--body); font-family:-apple-system,"Segoe UI","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif; font-size:15px; line-height:1.8;}
  .wrap{max-width:720px; margin:0 auto; padding:0 22px;}
  header{background:var(--wash); border-bottom:1px solid #E1E1DF; padding:38px 0 26px;}
  h1{font-family:"Hiragino Mincho ProN","Yu Mincho",YuMincho,"Noto Serif JP",serif; font-weight:600; font-size:32px; color:var(--ink); letter-spacing:.05em;}
  .tag{font-size:12.5px; color:var(--soft); margin-top:6px;}
  main{padding:0 0 56px;}

  .latest{display:block; background:var(--wash); padding:20px 22px 18px; margin:26px 0 34px; text-decoration:none; color:inherit; border-left:2px solid var(--clay);}
  .latest .lab{font-size:11px; color:var(--clay); letter-spacing:.12em; font-weight:600;}
  .latest .lt{font-size:17px; font-weight:700; color:var(--ink); margin:5px 0 10px; letter-spacing:.02em;}
  .latest:hover .lt{text-decoration:underline;}

  h2.mon{display:flex; align-items:baseline; gap:10px; font-size:12px; color:var(--grey); letter-spacing:.1em; font-weight:600; margin:0 0 6px; padding-bottom:8px; border-bottom:1px solid var(--hair);}
  h2.mon .cnt{font-size:11px; color:var(--grey); font-weight:400; letter-spacing:.04em;}

  .issue{display:grid; grid-template-columns:78px 1fr; gap:0 16px; padding:16px 4px 16px 2px; border-bottom:1px solid var(--hair); text-decoration:none; color:inherit;}
  .issue:hover{background:var(--wash);}
  .issue:hover .tt{text-decoration:underline;}
  .date{display:flex; align-items:baseline; gap:5px; padding-top:1px;}
  .date .dd{font-family:"Hiragino Mincho ProN","Yu Mincho",YuMincho,"Noto Serif JP",serif; font-size:20px; font-weight:600; color:var(--ink); letter-spacing:.02em;}
  .date .wd{font-size:11.5px; color:var(--grey);}

  ol.tl, .latest ol{list-style:none;}
  ol.tl li, .latest li{display:flex; gap:9px; font-size:14px; line-height:1.65; padding:3px 0;}
  ol.tl .n, .latest .n{flex:none; width:1.1em; font-size:11px; color:var(--grey); padding-top:.35em; font-variant-numeric:tabular-nums;}
  ol.tl .tt{color:var(--ink);}
  .latest li{font-size:14px;}
  .latest .tt{color:var(--body);}

  @media (max-width:640px){
    .wrap{padding:0 18px;}
    h1{font-size:26px;}
    .issue{grid-template-columns:1fr; gap:6px; padding:15px 2px;}
    .date{gap:6px;}
    .date .dd{font-size:17px;}
    ol.tl li, .latest li{font-size:14px;}
  }
"""

INDEX_JS = r"""
(async function(){
  const wrap=document.getElementById('list');
  const jd=d=>{const [y,m,dd]=d.split('-');return `${+m}/${+dd}`;};
  const el=(t,c,txt)=>{const e=document.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e;};
  const ol=(titles,cls)=>{const o=el('ol',cls);titles.forEach((t,i)=>{const li=el('li');li.append(el('span','n',String(i+1)),el('span','tt',t));o.append(li);});return o;};
  let entries;
  try{
    const r=await fetch('manifest.json?t='+Date.now(),{cache:'no-store'});
    entries=await r.json();
  }catch(e){wrap.textContent='一覧を読み込めませんでした。再読み込みしてください。';return;}
  entries.sort((a,b)=>a.date<b.date?1:-1);
  const latest=entries[0];
  const a=el('a','latest');a.href='briefs/'+latest.file;
  a.append(el('div','lab','最新号'),el('div','lt',`${jd(latest.date)}（${latest.weekday}）のブリーフ`),ol(latest.titles));
  wrap.append(a);
  const months=new Map();
  entries.forEach(e=>{const k=e.date.slice(0,7);if(!months.has(k))months.set(k,[]);months.get(k).push(e);});
  for(const [mon,es] of months){
    const rest=es.filter(e=>e.date!==latest.date);
    if(!rest.length)continue;
    const [y,m]=mon.split('-');
    const h=el('h2','mon',`${y}年${+m}月`);h.append(el('span','cnt',`全${es.length}号`));
    wrap.append(h);
    rest.forEach(e=>{
      const r=el('a','issue');r.href='briefs/'+e.file;
      const d=el('div','date');d.append(el('span','dd',jd(e.date)),el('span','wd',e.weekday));
      r.append(d,ol(e.titles,'tl'));wrap.append(r);
    });
  }
})();
"""

def _write_index(entries):
    """index.html は静的シェル。一覧は manifest.json をブラウザ側で読んで描画する（日次で index.html を push しない）。"""
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    open(os.path.join(SITE, "assets", "index.css"), "w", encoding="utf-8").write(INDEX_CSS)
    index = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>テックブリーフ</title>
<link rel="stylesheet" href="assets/index.css">
</head>
<body>
<header><div class="wrap">
  <h1>テックブリーフ</h1>
  <div class="tag">毎朝6:00配信 · AIエージェント／Flutter・Android／ローカルLLM</div>
</div></header>
<main><div class="wrap" id="list">
  <noscript><p>一覧の表示にはJavaScriptが必要です。</p></noscript>
</div></main>
<script>{INDEX_JS}</script>
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
