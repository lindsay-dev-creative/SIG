#!/usr/bin/env python3
"""
Turn a meeting agenda page and its answers into one Markdown record.

    python3 meeting-record.py sig-meet-10052026.html
    python3 meeting-record.py sig-meet-10052026.html -o records/meet-10052026.md

The agenda comes from the page's JSON block. Answers come from the shared
project store (the STORE_URL written in the page): every point on the page
has Confirm: Yes and Confirm: No buttons, and a No opens a Notes box.

The record lists every section, item and point in agenda order:

    - [x] point   Confirm: Yes
    - [ ] point   Confirm: No, with its notes indented underneath
    - [ ] point   not answered

Images added to an item are listed under it with their title, description
and a Google Drive link.

A Yes means the point stands as written, so it can go into the copy as is.
A No means it doesn't, and the notes say what changes; use the notes, not
the point's wording, when updating copy. Notes typed under a point that was
later switched back to Yes are kept and shown too.

Answers are tied to a point's exact wording. If a point was reworded after
it was answered, its answer is listed at the end under "Answered points no
longer in the agenda", with the wording that was answered.
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


def by_whom(c):
    # Answering asks for no name, so one is recorded only when the browser had it.
    return " by " + c["by"] if c.get("by") else ""


def answer_of(c):
    # "yes", "no" or None. Records from the earlier single Confirmed button count as yes.
    if not c:
        return None
    if "answer" in c:
        return c["answer"]
    return "yes" if c.get("confirmed") else None


def answer_lines(text, c, prefix=""):
    answer = answer_of(c)
    notes = (c or {}).get("notes", "").strip()
    if answer == "yes":
        lines = ["- [x] %s%s  (Confirm: Yes%s, %s)" % (prefix, text, by_whom(c), when(c.get("at")))]
    elif answer == "no":
        lines = ["- [ ] %s%s  (Confirm: No%s, %s)" % (prefix, text, by_whom(c), when(c.get("at")))]
    else:
        lines = ["- [ ] %s%s" % (prefix, text)]
    if notes:
        lines.append("  Notes: " + notes.replace("\n", "\n  "))
    return lines


def image_lines(lst, with_item=False):
    out = []
    for i in lst:
        where = "%s / %s: " % (i.get("section", ""), i.get("itemTitle", "")) if with_item else ""
        line = "- %s%s" % (where, i.get("title") or "Untitled image")
        if i.get("description"):
            line += ": " + i["description"].replace("\n", " ")
        line += "  (https://drive.google.com/file/d/%s/view)" % i.get("driveId", "")
        out.append(line)
    return out


def points_of(details, info=False):
    """The confirmable points of an item, in order, as the page builds them.
    A reference item ("info") has no confirmable points: every line is context."""
    lines = details.split("\n")
    if info:
        return [("context", BULLET.match(l).group(1).strip() if BULLET.match(l) else l.strip())
                for l in lines if l.strip()]
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
    images = {}
    for r in records:
        if r["kind"] == "meetimage" and not r.get("deleted"):
            images.setdefault(r["payload"].get("item"), []).append(r["payload"])
    for lst in images.values():
        lst.sort(key=lambda i: i.get("at") or 0)
    shown_images = set()

    used = set()
    out = ["# %s · %s" % (agenda.get("title", "Meeting"), agenda.get("date", "")), ""]
    out.append("Record generated %s from the shared store. [x] is Confirm: Yes; Confirm: No points carry their notes." %
               datetime.datetime.now().strftime("%b %-d, %Y %-I:%M %p"))
    for sec in agenda.get("sections", []):
        out += ["", "## " + sec.get("title", "")]
        for item in sec.get("items", []):
            if not (item.get("text") or item.get("details")):
                continue
            out += ["", "### " + item.get("text", "")]
            if item.get("note"):
                out.append("_%s_" % item["note"])
            info = item.get("info")
            for kind, text in points_of(item.get("details", ""), info):
                if kind == "context":
                    out.append(("- " if info else "") + text)
                    if info:
                        # Reference points can't be answered, but can carry notes.
                        key = item["id"] + "~" + text_key(text)
                        used.add(key)
                        ref_notes = (confirms.get(key) or {}).get("notes", "").strip()
                        if ref_notes:
                            out.append("  Notes: " + ref_notes.replace("\n", "\n  "))
                    continue
                key = item["id"] + "~" + text_key(text)
                used.add(key)
                out += answer_lines(text, confirms.get(key))
            item_images = images.get(item["id"], [])
            if item_images:
                shown_images.add(item["id"])
                out += ["", "Images:"]
                out += image_lines(item_images)
            # Item-level notes from before the Confirm buttons, if any were left.
            item_notes = notes.get(item["id"], [])
            if item_notes:
                out += ["", "Notes:"]
                for n in item_notes:
                    body = n.get("text", "").replace("\n", "\n  ")
                    edited = " (edited)" if n.get("editedAt") else ""
                    out.append("- %s, %s%s: %s" % (n.get("name") or "Someone", when(n.get("at")), edited, body))

    orphans = [c for k, c in confirms.items() if k not in used and (answer_of(c) or (c.get("notes") or "").strip())]
    if orphans:
        out += ["", "## Answered points no longer in the agenda", "",
                "These were answered, then the wording on the page changed. This is the wording that was answered."]
        for c in orphans:
            out += answer_lines(c.get("text", ""), c, "%s / %s: " % (c.get("section", ""), c.get("itemTitle", "")))

    stray = [i for k, lst in images.items() if k not in shown_images for i in lst]
    if stray:
        out += ["", "## Images on items no longer in the agenda", ""]
        out += image_lines(stray, with_item=True)

    text = "\n".join(out) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
