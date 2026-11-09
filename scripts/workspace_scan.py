#!/usr/bin/env python3
"""Check whether a name, acronym or phrase already exists in this workspace.

Text files are searched directly. Office files (.docx, .pptx, .xlsx) are opened as
zips and their XML is searched, because grep cannot see inside them. That second
half is the point: a name absent from every markdown file here still turned up in
five decks the first time this was run by hand.

Every hit is shown with the text around it, because a raw count lies. A short
two-letter acronym matches inside base64 and inside minified HTML, which is how
the first version of this script reported 505 files for a term that appears in
prose in far fewer. Matches that land inside a long unbroken token are counted
separately as noise and not presented as evidence.

Usage:
    python3 workspace_scan.py "Dana Whitfield" "Project Harbor"
    python3 workspace_scan.py QA --max 12
    python3 workspace_scan.py "Ask Anything" --substring

Short all-caps terms match on word boundaries automatically. Pass --substring to
force loose matching, or --word to force strict.

The workspace root is found by walking up from the current directory looking for
a marker, by default `.git`. Override with --root or --marker.

Exit code is 0 whether or not anything is found. Read the output.
"""

import argparse
import os
import re
import sys
import zipfile

TEXT_EXT = (".md", ".txt", ".csv", ".json", ".html", ".htm", ".py", ".url")
OFFICE_EXT = (".docx", ".pptx", ".xlsx")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
MAX_OFFICE_BYTES = 80 * 1024 * 1024

# A match sitting inside a token longer than this is encoded data, not writing.
MAX_TOKEN = 40
CONTEXT = 70


def office_text(path):
    try:
        with zipfile.ZipFile(path) as z:
            blob = b"".join(z.read(n) for n in z.namelist() if n.endswith(".xml"))
        text = blob.decode("utf8", "ignore")
    except Exception:
        return ""
    # Office XML is one long line of tags. Turn tags into spaces so the token
    # test below sees words rather than markup.
    return re.sub(r"<[^>]+>", " ", text)


def token_around(text, pos):
    """The unbroken run of non-whitespace containing pos."""
    start = pos
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    end = pos
    while end < len(text) and not text[end].isspace():
        end += 1
    return end - start


def snippet(text, start, end):
    left = max(0, start - CONTEXT)
    right = min(len(text), end + CONTEXT)
    out = text[left:right].replace("\n", " ").replace("\r", " ")
    out = re.sub(r"\s+", " ", out).strip()
    return ("..." if left > 0 else "") + out + ("..." if right < len(text) else "")


def find_root(start, marker):
    """Walk up from start looking for the workspace marker, e.g. '.git'."""
    cur = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(cur, marker)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(start)
        cur = parent


def build_pattern(term, mode):
    escaped = re.escape(term)
    strict = mode == "word" or (
        mode == "auto" and len(term) <= 5 and term.isupper() and term.isalpha()
    )
    if strict:
        return re.compile(r"\b%s\b" % escaped), True
    return re.compile(escaped, re.IGNORECASE), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--root", default=None)
    ap.add_argument("--marker", default=".git",
                    help="filename that marks the workspace root (default: .git)")
    ap.add_argument("--max", type=int, default=8, help="files to print per term")
    ap.add_argument("--word", action="store_true", help="force word-boundary matching")
    ap.add_argument("--substring", action="store_true", help="force loose matching")
    args = ap.parse_args()

    if args.word and args.substring:
        sys.exit("pick one of --word or --substring")
    mode = "word" if args.word else "substring" if args.substring else "auto"

    root = args.root or find_root(os.getcwd(), args.marker)
    if not os.path.isdir(root):
        sys.exit("root not found: %s" % root)

    patterns = {}
    for t in args.terms:
        patterns[t] = build_pattern(t, mode)

    hits = {t: {"text": [], "office": []} for t in args.terms}
    noise = {t: 0 for t in args.terms}
    scanned = {"text": 0, "office": 0}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            low = fn.lower()
            if low.endswith(TEXT_EXT):
                kind = "text"
                try:
                    with open(path, "r", encoding="utf8", errors="ignore") as fh:
                        content = fh.read()
                except Exception:
                    continue
            elif low.endswith(OFFICE_EXT):
                kind = "office"
                try:
                    if os.path.getsize(path) > MAX_OFFICE_BYTES:
                        continue
                except OSError:
                    continue
                content = office_text(path)
                if not content:
                    continue
            else:
                continue

            scanned[kind] += 1
            for term, (pattern, _strict) in patterns.items():
                real = 0
                first = None
                for m in pattern.finditer(content):
                    if token_around(content, m.start()) > MAX_TOKEN:
                        noise[term] += 1
                        continue
                    real += 1
                    if first is None:
                        first = snippet(content, m.start(), m.end())
                if real:
                    hits[term][kind].append((rel, real, first))

    print("root: %s" % root)
    print("scanned %d text files and %d Office files\n"
          % (scanned["text"], scanned["office"]))

    for term in args.terms:
        pattern, strict = patterns[term]
        t_hits = sorted(hits[term]["text"], key=lambda x: -x[1])
        o_hits = sorted(hits[term]["office"], key=lambda x: -x[1])
        files = len(t_hits) + len(o_hits)
        occurrences = sum(h[1] for h in t_hits + o_hits)
        print("=== %s   [%s match]" % (term, "word-boundary" if strict else "substring"))
        if files == 0:
            print("    NOT FOUND in readable text anywhere in this workspace")
            if noise[term]:
                print("    (%d matches suppressed as encoded data, not writing)"
                      % noise[term])
            print("    Safe to write that it has no history here. Say what was scanned.\n")
            continue
        print("    %d files, %d occurrences (%d text files, %d Office files)"
              % (files, occurrences, len(t_hits), len(o_hits)))
        if noise[term]:
            print("    %d further matches suppressed as encoded data, not writing"
                  % noise[term])
        for label, group in (("text", t_hits), ("Office", o_hits)):
            for rel, count, sample in group[:args.max]:
                print("      [%s x%d] %s" % (label, count, rel))
                if sample:
                    print("               %s" % sample[:200])
            if len(group) > args.max:
                print("      [%s] ... and %d more files" % (label, len(group) - args.max))
        print()


if __name__ == "__main__":
    main()
