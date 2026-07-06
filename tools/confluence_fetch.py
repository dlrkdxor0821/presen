#!/usr/bin/env python3
"""Fetch Confluence (arte1 wiki) pages -> confluence_data.json.
Reads credentials from ../.jira.env (gitignored) — same Atlassian token as Jira.

Usage:
  python3 tools/confluence_fetch.py                # list all spaces (discover keys)
  python3 tools/confluence_fetch.py --space KEY    # fetch every page in a space
  python3 tools/confluence_fetch.py --page ID      # fetch a single page by id
Default space = CONFLUENCE_SPACE in .jira.env, if set.
"""
import urllib.request, urllib.parse, json, base64, os, sys, re, html

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_env(p):
    env = {}
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

env = load_env(os.path.join(ROOT, ".jira.env"))
BASE = f"https://{env['JIRA_SITE']}/wiki"
AUTH = base64.b64encode(f"{env['JIRA_EMAIL']}:{env['JIRA_TOKEN']}".encode()).decode()

def get(path):
    req = urllib.request.Request(BASE + path,
        headers={"Authorization": f"Basic {AUTH}", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def paged(path):
    """Iterate Confluence v2 cursor-paginated results."""
    while True:
        d = get(path)
        for r in d.get("results", []):
            yield r
        nxt = (d.get("_links") or {}).get("next")
        if not nxt:
            break
        path = "/" + nxt.split("/wiki/", 1)[1] if "/wiki/" in nxt else nxt

def to_text(storage):
    """Rough Confluence storage (XHTML) -> plain text."""
    if not storage:
        return ""
    t = re.sub(r"<br\s*/?>", "\n", storage)
    t = re.sub(r"</(p|li|h[1-6]|tr|div|table)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def page_obj(p):
    body = (((p.get("body") or {}).get("storage") or {}).get("value")) or ""
    link = (p.get("_links") or {}).get("webui") or ""
    return {
        "id": p["id"],
        "title": p["title"],
        "url": BASE + link if link else "",
        "text": to_text(body),
    }

def list_spaces():
    rows = [{"id": s["id"], "key": s["key"], "name": s["name"], "type": s.get("type")}
            for s in paged("/api/v2/spaces?limit=100")]
    print(f"{len(rows)} spaces:")
    for s in sorted(rows, key=lambda x: x["key"]):
        print(f"  {s['key']:<12} {s['name']}  (id={s['id']}, {s['type']})")
    print("\nfetch one:  python3 tools/confluence_fetch.py --space <KEY>")

def space_id(key):
    d = get(f"/api/v2/spaces?keys={urllib.parse.quote(key)}")
    r = d.get("results", [])
    if not r:
        sys.exit(f"space not found: {key}")
    return r[0]["id"]

def fetch_space(key):
    sid = space_id(key)
    pages = [page_obj(p) for p in
             paged(f"/api/v2/spaces/{sid}/pages?limit=100&body-format=storage")]
    save({"space": key, "pages": pages})
    print(f"space {key}: {len(pages)} pages")
    for p in pages:
        print(f"  {p['title']}  ({len(p['text'])} chars)")

def fetch_page(pid):
    p = get(f"/api/v2/pages/{pid}?body-format=storage")
    obj = page_obj(p)
    save({"space": None, "pages": [obj]})
    print(f"page {pid}: {obj['title']}  ({len(obj['text'])} chars)")

def save(data):
    out_path = os.path.join(ROOT, "confluence_data.json")
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"saved {out_path}")

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--page" in a:
        fetch_page(a[a.index("--page") + 1])
    elif "--space" in a:
        fetch_space(a[a.index("--space") + 1])
    elif env.get("CONFLUENCE_SPACE"):
        fetch_space(env["CONFLUENCE_SPACE"])
    else:
        list_spaces()
