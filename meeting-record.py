#!/usr/bin/env python3
"""
Turn a meeting agenda page and its shared notes into one Markdown record.

    python3 meeting-record.py sig-meet-10052026.html
    python3 meeting-record.py sig-meet-10052026.html -o records/meet-10052026.md

The agenda comes from the page's JSON block. Notes and confirmations come
from the shared project store (the STORE_URL written in the page), where
anyone on the page adds notes and Lindsay marks points Confirmed.

The record lists every section, item and point in agenda order. Each point
says whether it was confirmed, by whom and when, and each item carries the
notes left under it. Those notes are where the answers are, so read a
confirmed point together with its item's notes before changing any copy.

Confirmations are tied to a point's exact wording. If a point was reworded
after it was confirmed, its confirmation is listed at the end under
"Confirmed points no longer in the agenda", with the wording it confirmed.
"""

import argparse
import datetime
import json
import re
import sys
import urllib.request

BULLET = re.compile(r"^\s*[-–•]\s+(.*)$")


def text_key(text):
    # Same hash as textKey() in the page, so keys line up.
    # Walk UTF-16 code units, as JavaScript's charCodeAt does.
    data = text.encode("utf-16-le")
    h = 5381
    for i in range(0, len(data), 2):
        unit = data[i] | (data[i + 1] << 8)
        h = ((h << 5) + h + unit) & 0xFFFFFFFF
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        h, r = divmod(h, 36)
        out = digits[r] + out
        if not h:
            return out


def when(ms):
    if not ms:
        return ""
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%b %-d, %Y %-I:%M %p")


def points_of(details):
    """The confirmable points of an item, in order, as the page builds them."""
    lines = details.split("\n")
    has_bullets = any(BULLET.match(line) for line in lines)
    out = []
    for line in lines:
        m = BULLET.match(line)
        if m:
            out.append(("point", m.group(1).strip()))
        elif line.strip():
            out.append(("point" if not has_bullets else "context", line.strip()))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("page", help="the meeting page, e.g. sig-meet-10052026.html")
    ap.add_argument("-o", "--out", help="write here instead of printing")
    args = ap.parse_args()

    html = open(args.page, encoding="utf-8").read()
    agenda = json.loads(re.search(r'<script type="application/json" id="page-data">(.*?)</script>', html, re.S).group(1))
    store = re.search(r'var STORE_URL = "([^"]*)"', html).group(1)
    meeting = re.search(r'var MEETING = "([^"]*)"', html).group(1)
    if not store:
        sys.exit("This page has no STORE_URL, so there are no notes or confirmations to read.")

    with urllib.request.urlopen(store + "?action=pull&since=0") as res:
        pulled = json.load(res)
    records = [r for r in pulled.get("records", []) if (r.get("payload") or {}).get("meeting") == meeting]

    notes = {}
    for r in records:
        if r["kind"] == "meetnote" and not r.get("deleted"):
            p = r["payload"]
            notes.setdefault(p.get("item"), []).append(p)
    for lst in notes.values():
        lst.sort(key=lambda n: n.get("at") or 0)
    confirms = {r["id"]: r["payload"] for r in records if r["kind"] == "meetconfirm"}

    used = set()
    out = ["# %s · %s" % (agenda.get("title", "Meeting"), agenda.get("date", "")), ""]
    out.append("Record generated %s from the shared notes store. [x] marks a point Lindsay confirmed." %
               datetime.datetime.now().strftime("%b %-d, %Y %-I:%M %p"))
    for sec in agenda.get("sections", []):
        out += ["", "## " + sec.get("title", "")]
        for item in sec.get("items", []):
            if not (item.get("text") or item.get("details")):
                continue
            out += ["", "### " + item.get("text", "")]
            if item.get("note"):
                out.append("_%s_" % item["note"])
            for kind, text in points_of(item.get("details", "")):
                if kind == "context":
                    out.append(text)
                    continue
                key = item["id"] + "~" + text_key(text)
                c = confirms.get(key)
                used.add(key)
                if c and c.get("confirmed"):
                    out.append("- [x] %s  (confirmed by %s, %s)" % (text, c.get("by", "Lindsay"), when(c.get("at"))))
                else:
                    out.append("- [ ] " + text)
            item_notes = notes.get(item["id"], [])
            if item_notes:
                out += ["", "Notes:"]
                for n in item_notes:
                    body = n.get("text", "").replace("\n", "\n  ")
                    edited = " (edited)" if n.get("editedAt") else ""
                    out.append("- %s, %s%s: %s" % (n.get("name") or "Someone", when(n.get("at")), edited, body))

    orphans = [c for k, c in confirms.items() if k not in used and c.get("confirmed")]
    if orphans:
        out += ["", "## Confirmed points no longer in the agenda", "",
                "These were confirmed, then the wording on the page changed. This is the wording that was confirmed."]
        for c in orphans:
            out.append("- [x] %s / %s: %s  (confirmed by %s, %s)" % (
                c.get("section", ""), c.get("itemTitle", ""), c.get("text", ""), c.get("by", "Lindsay"), when(c.get("at"))))

    text = "\n".join(out) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
