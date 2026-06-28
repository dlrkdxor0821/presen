#!/usr/bin/env python3
"""Rewrite the 진행사항(slide 9) and 이번주 계획(slide 10) sections of index.html
from jira_data.json. 진행 = most-recent CLOSED sprint, 계획 = ACTIVE sprint.
Run after jira_fetch.py. Idempotent (re-run to refresh)."""
import json, os, re
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data = json.load(open(os.path.join(ROOT, "jira_data.json"), encoding="utf-8"))
sprints = data["sprints"]
active = next((s for s in sprints if s["state"] == "active"), None)
closed = [s for s in sprints if s["state"] == "closed"]
prog = closed[-1] if closed else sprints[0]
plan = active or sprints[-1]

STMAP = {"Done": ("done", "완료"), "In Progress": ("prog", "진행"), "To Do": ("todo", "예정")}
CNTCOL = {"done": "#1E8C80", "prog": "#2456A6", "todo": "#A9AEB8"}

def esc(t): return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def fmt(d): return d.replace("-", ".") if d else ""
def endshort(e): return e[5:].replace("-", ".") if e else ""

def rows(issues):
    r = []
    for i in issues:
        cls, lbl = STMAP.get(i["status"], ("todo", esc(i["status"])))
        r.append(f'<div class="jrow"><span class="jk">{i["key"]}</span>'
                 f'<span class="js">{esc(i["summary"])}</span>'
                 f'<span class="ja">{esc(i["assignee"] or "미배정")}</span>'
                 f'<span class="jb {cls}">{lbl}</span></div>')
    return "\n        ".join(r)

def counts(issues):
    c = Counter(i["status"] for i in issues)
    out = []
    for st, (cls, lbl) in STMAP.items():
        if c.get(st):
            out.append(f'<span class="cnt"><i style="background:{CNTCOL[cls]}"></i>{lbl} {c[st]}</span>')
    return "".join(out)

def section(marker, kn, kicker, title, foot, sp):
    meta = (f'<span class="sp">{esc(sp["name"])}</span> · {fmt(sp["start"])} – {endshort(sp["end"])} · '
            f'{counts(sp["issues"])} · 총 {len(sp["issues"])}건'
            f'<span class="src"><span class="lv"></span>Jira · arte1 · 실시간</span>')
    return f'''  <!-- ===== {marker} ===== -->
  <section class="slide">
    <header class="shead">
      <div class="kicker anim" style="--d:0"><span class="kn">{kn}</span> {kicker} <span class="kof">/ 11</span></div>
      <h2 class="stitle anim" style="--d:1">{title}</h2>
    </header>
    <div class="sbody"><div class="jira">
      <div class="jira-meta anim" style="--d:2">{meta}</div>
      <div class="jira-cols anim" style="--d:2">
        {rows(sp["issues"])}
      </div>
    </div></div>
    <footer class="sfoot"><span class="bd"><span class="dotg"></span>ABA · Libi <b>{foot}</b></span><span class="pg"></span></footer>
  </section>
'''

def section_img(marker, kn, kicker, title, foot, sp, img):
    meta = (f'<span class="sp">{esc(sp["name"])}</span> · {fmt(sp["start"])} – {endshort(sp["end"])} · '
            f'{counts(sp["issues"])} · 총 {len(sp["issues"])}건'
            f'<span class="src"><span class="lv"></span>Jira · arte1 · 실시간</span>')
    return f'''  <!-- ===== {marker} ===== -->
  <section class="slide">
    <header class="shead">
      <div class="kicker anim" style="--d:0"><span class="kn">{kn}</span> {kicker} <span class="kof">/ 11</span></div>
      <h2 class="stitle anim" style="--d:1">{title}</h2>
    </header>
    <div class="sbody"><div class="jira-shot">
      <div class="jira-meta anim" style="--d:2">{meta}</div>
      <div class="shot-wrap anim" style="--d:2"><img src="{img}" alt="Sprint Jira 보드"></div>
    </div></div>
    <footer class="sfoot"><span class="bd"><span class="dotg"></span>ABA · Libi <b>{foot}</b></span><span class="pg"></span></footer>
  </section>
'''

pno = prog["name"].split(".", 1)[0].strip()
ano = plan["name"].split(".", 1)[0].strip()
ash = plan["name"].split(".", 1)[-1].strip()

prog_sec = section_img("9 · 진행 사항 (Jira)", "07", f"Progress · {pno}",
    f'지난 주 진행 사항 <span class="hl">{esc(pno)}</span> <span class="sm">{fmt(prog["start"])} – {endshort(prog["end"])}</span>',
    f"Progress · {pno}", prog, "img/jira_sprint2.png")
plan_sec = section_img("10 · 이번 주 계획 (Jira)", "08", f"Next Sprint · {ano}",
    f'이번 주 계획 <span class="hl">{esc(ano)}</span> <span class="sm">{fmt(plan["start"])} – {endshort(plan["end"])}</span>',
    f"Next Sprint · {ano}", plan, "img/jira_sprint3.png")

idx = os.path.join(ROOT, "index.html")
html = open(idx, encoding="utf-8").read()
html = re.sub(r"  <!-- ===== 9 ·.*?</section>\n", lambda m: prog_sec, html, count=1, flags=re.S)
html = re.sub(r"  <!-- ===== 10 ·.*?</section>\n", lambda m: plan_sec, html, count=1, flags=re.S)
open(idx, "w", encoding="utf-8").write(html)
print("updated index.html")
print(f"  진행 = {prog['name']} ({len(prog['issues'])} issues)")
print(f"  계획 = {plan['name']} ({len(plan['issues'])} issues)")
