#!/usr/bin/env python3
"""Run the checks that get skipped, before a word of the record is written.

This exists because writing a rule down does not execute it. Across 234 logged
lessons the two most-repeated failures were both already steps in the procedure:
stamping the record with the source's date instead of today's, and calling a name
or term new without scanning for it. Both were still recurring months after the
rule was written. Prose gets skimmed. A command that has not been run cannot be.

What it does:
  1. Prints today's real date. Every "ingested on" line uses this, never a date
     read out of the source.
  2. Pulls the candidate proper nouns, acronyms, emails and URLs out of the
     source and scans the workspace for each one, so "new here" is a measured
     claim rather than an impression.
  3. Checks every URL in the source.
  4. Emits a header block to paste into the record.

Usage:
    python3 preflight.py <source-file>
    python3 preflight.py <source-file> --root .. --marker .git
    python3 preflight.py <source-file> --no-urls

Exit code is 0 unless the source file cannot be read. Read the output.
"""

import argparse
import datetime
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import workspace_scan
except ImportError:
    workspace_scan = None

# Words that start sentences and look like names if you only check the capital.
STOP = {
    "The", "This", "That", "These", "Those", "There", "Then", "They", "We", "You",
    "He", "She", "It", "Its", "His", "Her", "Our", "Your", "Their", "My", "Me",
    "A", "An", "And", "But", "Or", "If", "So", "As", "At", "By", "For", "From",
    "In", "Of", "On", "To", "With", "Not", "No", "Yes", "All", "Any", "Some",
    "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "First", "Second", "Third", "Next", "Last", "New", "Old", "Good", "Best",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
    "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
    "Hi", "Hello", "Hey", "Thanks", "Thank", "Dear", "Regards", "Best",
    "Subject", "From", "Sent", "Date", "Cc", "Bcc", "Re", "Fwd", "Fw",
    "Please", "Let", "Here", "Just", "Also", "Will", "Can", "Should", "Would",
    "Could", "Have", "Has", "Had", "Do", "Does", "Did", "Is", "Are", "Was", "Were",
    "AM", "PM", "UTC", "GMT", "EST", "CST", "PST", "EDT", "CDT", "PDT",
    "I", "OK", "TBD", "FYI", "PS",
}

# [ \t]+ and not \s+: a name does not run across a line break. With \s+ the two
# halves of a slide card join into "Dana Whitfield Senior Manager", which is not a
# term anyone can scan for.
NAME = re.compile(r"\b[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){0,3}\b")
ACRONYM = re.compile(r"\b[A-Z]{2,6}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
URL = re.compile(r"https?://[^\s<>\"'\)\]]+")


def candidates(text):
    """Proper nouns, acronyms, emails and URLs worth scanning for."""
    names, acros = set(), set()

    for m in NAME.finditer(text):
        phrase = m.group(0)
        words = phrase.split()
        # Drop leading sentence-starters, keep what is left if anything is.
        while words and words[0] in STOP:
            words.pop(0)
        while words and words[-1] in STOP:
            words.pop()
        if not words:
            continue
        phrase = " ".join(words)
        # A lone common word is noise; two capitalized words rarely are.
        if len(words) == 1 and len(phrase) < 5:
            continue
        names.add(phrase)

    for m in ACRONYM.finditer(text):
        a = m.group(0)
        if a not in STOP:
            acros.add(a)

    return (sorted(names, key=lambda s: (-len(s.split()), s)),
            sorted(acros),
            sorted(set(EMAIL.findall(text))),
            sorted(set(URL.findall(text))))


def scan_terms(terms, root, maxfiles=3):
    """Run the workspace scan and return {term: (files, occurrences, sample)}."""
    if workspace_scan is None or not terms:
        return {}
    pats = {t: workspace_scan.build_pattern(t, "auto") for t in terms}
    found = {t: [0, 0, None] for t in terms}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in workspace_scan.SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            low = fn.lower()
            if low.endswith(workspace_scan.TEXT_EXT):
                try:
                    with open(path, "r", encoding="utf8", errors="ignore") as fh:
                        content = fh.read()
                except Exception:
                    continue
            elif low.endswith(workspace_scan.OFFICE_EXT):
                try:
                    if os.path.getsize(path) > workspace_scan.MAX_OFFICE_BYTES:
                        continue
                except OSError:
                    continue
                content = workspace_scan.office_text(path)
                if not content:
                    continue
            else:
                continue
            rel = os.path.relpath(path, root)
            for t, (pattern, _s) in pats.items():
                n = 0
                for m in pattern.finditer(content):
                    if workspace_scan.token_around(content, m.start()) <= workspace_scan.MAX_TOKEN:
                        n += 1
                if n:
                    found[t][0] += 1
                    found[t][1] += n
                    if found[t][2] is None:
                        found[t][2] = rel
    return found


def check_urls(urls, timeout=8):
    out = []
    for u in urls:
        try:
            req = urllib.request.Request(u, method="HEAD",
                                         headers={"User-Agent": "preflight/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out.append((u, str(r.status)))
        except Exception as e:
            code = getattr(e, "code", None)
            out.append((u, str(code) if code else type(e).__name__))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="file holding the raw pasted source")
    ap.add_argument("--root", default=None, help="workspace root (default: found via --marker)")
    ap.add_argument("--marker", default=".git", help="filename marking the workspace root")
    ap.add_argument("--max-terms", type=int, default=40)
    ap.add_argument("--no-urls", action="store_true", help="skip the URL checks")
    args = ap.parse_args()

    try:
        text = open(args.source, encoding="utf-8", errors="replace").read()
    except OSError as e:
        sys.exit("cannot read source: %s" % e)

    root = args.root
    if root is None:
        root = (workspace_scan.find_root(os.getcwd(), args.marker)
                if workspace_scan else os.getcwd())

    today = datetime.date.today()

    print("=" * 72)
    print("TODAY IS %s" % today.strftime("%A, %B %d, %Y"))
    print("Every line describing your own action uses this date.")
    print("A date read out of the source belongs only in statements about the source.")
    print("=" * 72)
    print()

    names, acros, emails, urls = candidates(text)
    terms = (names + acros)[:args.max_terms]

    print("SOURCE: %s  (%d chars, %d lines)" % (args.source, len(text), text.count("\n") + 1))
    print("ROOT:   %s" % root)
    print()

    if emails:
        print("EMAIL ADDRESSES IN SOURCE (check spelling against the directory, not the source):")
        for e in emails:
            print("   %s" % e)
        print()

    if workspace_scan is None:
        print("workspace_scan.py not importable, skipping the scan. Run it by hand.")
    else:
        print("SCANNING %d TERMS AGAINST THE WORKSPACE" % len(terms))
        print("Anything under NEW has no history here. Say what was scanned before")
        print("calling it new, and check a person's name against the directory as well.")
        print()
        found = scan_terms(terms, root)
        new = [t for t in terms if found.get(t, [0])[0] == 0]
        known = [(t, found[t][0], found[t][1], found[t][2])
                 for t in terms if found.get(t, [0])[0] > 0]
        print("--- NEW HERE (%d) ---" % len(new))
        for t in new:
            print("   %s" % t)
        if not new:
            print("   (none)")
        print()
        print("--- ALREADY IN THE WORKSPACE (%d) ---" % len(known))
        for t, f, o, sample in sorted(known, key=lambda x: -x[2])[:25]:
            print("   %-34s %3d files, %4d hits   e.g. %s" % (t[:34], f, o, sample))
        print()

    if urls and not args.no_urls:
        print("--- URLS (%d) ---" % len(urls))
        for u, status in check_urls(urls):
            flag = "ok " if status.startswith("2") or status.startswith("3") else "!! "
            print("   %s%-6s %s" % (flag, status, u[:90]))
        print()
    elif urls:
        print("--- URLS (%d, not checked) ---" % len(urls))
        for u in urls:
            print("   %s" % u[:90])
        print()

    print("=" * 72)
    print("HEADER BLOCK, paste into the record and fill the blanks:")
    print("=" * 72)
    print("""
**Ingested:** {today}
**Source:** {src}
**Source date or span:** <from the source, or "not stated">
**Produced by:** <who wrote it; for AI material say so>
**Who is in it:** <names, spelled as the directory spells them>
**Built from:** <every source this record was built from>
""".strip().format(today=today.strftime("%B %d, %Y"), src=os.path.basename(args.source)))
    print()
    print("Still yours to do, because no script can:")
    print("  - walk the timestamps for a gap in the middle")
    print("  - check whether the first message is really the first")
    print("  - separate verbatim from recap from human notes")
    print("  - name what did not come through")


if __name__ == "__main__":
    main()
