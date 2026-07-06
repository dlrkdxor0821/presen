#!/usr/bin/env python3
"""Fetch Jira (arte1) board sprints + issues -> jira_data.json.
Reads credentials from ../.jira.env (gitignored). Run before update_sprint_slides.py.
"""
import urllib.request, json, base64, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_env(p):
    env = {}
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

_envp = os.path.join(ROOT, ".jira.env")
if not os.path.exists(_envp):
    _envp = os.path.expanduser("~/.config/atlassian/.env")  # 전역 fallback
env = load_env(_envp)
BASE = f"https://{env['JIRA_SITE']}"
AUTH = base64.b64encode(f"{env['JIRA_EMAIL']}:{env['JIRA_TOKEN']}".encode()).decode()
BOARD = env.get("JIRA_BOARD", "2")

def get(path):
    req = urllib.request.Request(BASE + path,
        headers={"Authorization": f"Basic {AUTH}", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def sprint_issues(sid):
    out, start = [], 0
    while True:
        d = get(f"/rest/agile/1.0/sprint/{sid}/issue?startAt={start}&maxResults=50"
                "&fields=summary,status,assignee,priority,issuetype")
        for it in d.get("issues", []):
            f = it["fields"]
            out.append({
                "key": it["key"],
                "summary": f["summary"],
                "status": (f.get("status") or {}).get("name"),
                "assignee": ((f.get("assignee") or {}) or {}).get("displayName"),
                "type": ((f.get("issuetype") or {}) or {}).get("name"),
            })
        if start + d.get("maxResults", 50) >= d.get("total", 0):
            break
        start += d.get("maxResults", 50)
    out.sort(key=lambda x: int(x["key"].split("-")[1]))
    return out

sp = get(f"/rest/agile/1.0/board/{BOARD}/sprint?maxResults=50")
sprints = []
for s in sp.get("values", []):
    sprints.append({
        "id": s["id"], "name": s["name"], "state": s.get("state"),
        "start": (s.get("startDate") or "")[:10], "end": (s.get("endDate") or "")[:10],
        "issues": sprint_issues(s["id"]),
    })

out_path = os.path.join(ROOT, "jira_data.json")
json.dump({"sprints": sprints}, open(out_path, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"saved {out_path}: {len(sprints)} sprints")
for s in sprints:
    print(f"  [{s['state']:>8}] {s['name']} ({s['start']}~{s['end']}) {len(s['issues'])} issues")
