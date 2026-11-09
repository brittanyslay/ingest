#!/usr/bin/env python3
"""Check the written record against the source, before calling the ingest done.

The verbatim rule is the one that fails silently. A record's raw-source section
is supposed to be the source, complete and unedited, and nothing in a read-through
reveals that one character moved. It has been broken by an emoji quietly dropped
under a house no-emoji rule, and by a British spelling quietly Americanized inside
a reproduced table. Both were caught by conscience, late, which is why this is a
diff instead of a reminder.

Checks:
  1. VERBATIM     the raw-source blocks in the record against the source file
  2. DATES        anything claiming to be today that is not, and any future date
  3. SECTIONS     the parts of a record that carry the honesty, present or absent
  4. STYLE        the house patterns from your profile

Usage:
    python3 postflight.py <record.md> --source <raw-source-file>
    python3 postflight.py <record.md> --source <src> --style "—|labelled|organise"
    python3 postflight.py <record.md>            # skips the verbatim diff

Exit code 1 if any BLOCKER fired, 0 otherwise.
"""

import argparse
import datetime
import difflib
import re
import sys

FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
DATE_ISO = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
DATE_US = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),\s+(20\d\d)\b")
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# The sections that carry a record's honesty. Missing one is not fatal, but it
# is almost always an omission rather than a decision.
WANTED = [
    ("ingest date", r"\*\*Ingested:?\*\*|^\*\*Ingest(ed)? date"),
    ("source identified", r"\*\*Source:?\*\*|\*\*Built from"),
    ("uncertainty section", r"[Uu]ncertain"),
    ("what did not come through", r"did not come through|[Nn]ot captured|[Mm]issing from"),
    ("raw source", r"[Rr]aw source"),
]

blockers = []
warnings = []
notes = []


def norm(s):
    """Normalize only what a markdown round-trip legitimately changes."""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    return s.strip("\n")


def check_verbatim(record, source_text):
    blocks = [norm(b) for b in FENCE.findall(record)]
    if not blocks:
        warnings.append("No fenced block found in the record. The raw source is "
                        "supposed to be in one, complete and unedited.")
        return
    src = norm(source_text)
    # The source may be one block, or split across several labeled blocks.
    candidates = blocks + (["\n".join(blocks)] if len(blocks) > 1 else [])

    # Exact, first. A source pasted whole into one block is the common case.
    for b in candidates:
        if b == src:
            notes.append("VERBATIM: exact match against the source, %d chars." % len(src))
            return
    # Contained, next. The user often hands over an excerpt of a longer block.
    for b in candidates:
        if src and src in b:
            notes.append("VERBATIM: the source appears in the record exactly, as a "
                         "%d-char excerpt of a %d-char block." % (len(src), len(b)))
            return

    # ratio(), not quick_ratio(): quick_ratio ignores ordering and will happily
    # pick a block that shares a vocabulary with the source and nothing else.
    best, best_ratio = None, -1.0
    for b in candidates:
        r = difflib.SequenceMatcher(None, src, b).ratio()
        if r > best_ratio:
            best, best_ratio = b, r

    if best_ratio < 0.5:
        warnings.append(
            "VERBATIM: no fenced block resembles the source (best similarity %.0f%% "
            "across %d block(s)). Either the raw source is not in the record, or this "
            "is not the file it was built from. Checked nothing."
            % (best_ratio * 100, len(blocks)))
        return

    sm = difflib.SequenceMatcher(None, src, best)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    if not ops:
        notes.append("VERBATIM: matches the source.")
        return

    shown = 0
    detail = []
    for tag, i1, i2, j1, j2 in ops:
        a, b = src[i1:i2], best[j1:j2]
        if not a.strip() and not b.strip():
            continue           # pure whitespace, not a content change
        shown += 1
        if shown > 12:
            detail.append("   ... and %d more differences" % (len(ops) - 12))
            break
        ctx = src[max(0, i1 - 40):i1].replace("\n", " ")[-40:]
        detail.append("   %-7s source=%-28r record=%-28r  after: ...%s"
                      % (tag, a[:28], b[:28], ctx))
    if shown:
        blockers.append(
            "VERBATIM: the raw-source block differs from the source file in %d place(s).\n"
            "%s\n   If a change was deliberate, say so in place inside the record."
            % (shown, "\n".join(detail)))
    else:
        notes.append("VERBATIM: whitespace-only differences, content matches.")


def check_dates(record, today):
    seen = set()
    for m in DATE_ISO.finditer(record):
        try:
            d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        seen.add(d)
    for m in DATE_US.finditer(record):
        d = datetime.date(int(m.group(3)), MONTHS.index(m.group(1)) + 1, int(m.group(2)))
        seen.add(d)

    future = sorted(d for d in seen if d > today)
    if future:
        blockers.append("DATES: %d date(s) in the future: %s"
                        % (len(future), ", ".join(str(d) for d in future[:6])))

    # The line that says when this was ingested must say today.
    for line in record.split("\n"):
        if re.search(r"\*\*Ingested:?\*\*|^\*\*Ingest(ed)? date", line):
            on_line = set()
            for m in DATE_ISO.finditer(line):
                on_line.add("%s-%s-%s" % m.groups())
            for m in DATE_US.finditer(line):
                on_line.add("%04d-%02d-%02d" % (int(m.group(3)),
                                                MONTHS.index(m.group(1)) + 1,
                                                int(m.group(2))))
            if on_line and str(today) not in on_line:
                blockers.append(
                    "DATES: the ingest line says %s but today is %s. An ingest date is "
                    "today's date, never a date read out of the source.\n   %s"
                    % (", ".join(sorted(on_line)), today, line.strip()[:100]))
            elif not on_line:
                warnings.append("DATES: the ingest line carries no date: %s"
                                % line.strip()[:80])
    if seen:
        notes.append("DATES: %d distinct date(s), none in the future."
                     % len(seen) if not future else "")


def check_sections(record):
    missing = [label for label, pat in WANTED
               if not re.search(pat, record, re.M)]
    if missing:
        warnings.append("SECTIONS: not found: %s. Each is a place a record "
                        "usually hides what it does not know." % ", ".join(missing))
    else:
        notes.append("SECTIONS: all present.")


def check_style(record, pattern):
    if not pattern:
        return
    # Style applies to your own prose, not to quoted material.
    outside = FENCE.sub("\n", record)
    hits = []
    for i, line in enumerate(outside.split("\n"), 1):
        for m in re.finditer(pattern, line):
            hits.append((i, m.group(0), line.strip()[:80]))
    if hits:
        warnings.append("STYLE: %d hit(s) outside quoted material:\n%s"
                        % (len(hits), "\n".join("   line %d: %r in %r" % h for h in hits[:10])))
    else:
        notes.append("STYLE: clean outside quoted material.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("record", help="the record you just wrote")
    ap.add_argument("--source", default=None, help="the raw source file it was built from")
    ap.add_argument("--style", default=None,
                    help="regex of house-style violations, from your profile")
    ap.add_argument("--date", default=None, help="override today, for testing")
    args = ap.parse_args()

    try:
        record = open(args.record, encoding="utf-8", errors="replace").read()
    except OSError as e:
        sys.exit("cannot read record: %s" % e)

    today = (datetime.date.fromisoformat(args.date) if args.date
             else datetime.date.today())

    if args.source:
        try:
            check_verbatim(record, open(args.source, encoding="utf-8",
                                        errors="replace").read())
        except OSError as e:
            warnings.append("VERBATIM: cannot read source (%s), diff skipped." % e)
    else:
        warnings.append("VERBATIM: no --source given, so the one check that cannot "
                        "be done by reading was not done.")

    check_dates(record, today)
    check_sections(record)
    check_style(record, args.style)

    print("postflight: %s" % args.record)
    print("today: %s" % today)
    print()
    for n in notes:
        if n:
            print("  ok       %s" % n)
    for w in warnings:
        print("  WARNING  %s" % w)
    for b in blockers:
        print("  BLOCKER  %s" % b)
    print()
    print("%d blocker(s), %d warning(s)" % (len(blockers), len(warnings)))
    sys.exit(1 if blockers else 0)


if __name__ == "__main__":
    main()
