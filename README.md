# ingest

A Claude Code skill that turns raw material, an email thread, a meeting transcript, an AI recap,
a deck, a spreadsheet, a screenshot, into a durable record in your workspace, and updates every
existing document that record contradicts.

It is a procedure, not a summarizer. The difference shows up months later, when someone quotes
the file.

## What it does differently

**It checks the source for damage before reading it for content.** A fragment reads exactly like
a complete record. Transcripts arrive with gaps in the middle and both ends look whole. Pasted
emails drop their attachments silently. The skill walks the timestamps, notes the exact span
that is missing, and puts that warning at the top of the file rather than in a footnote.

**It will not fill a gap.** A missing eighteen minutes stays missing and gets labeled as missing.
Two sources that disagree on a date produce both dates with attribution, not a decision.

**It separates grades of evidence.** AI transcription, AI recap and human notes are three
different things. A recap is a machine summary of speech nobody has read, and it never gets
blended into verbatim content.

**It updates what it touches.** The ingest is not finished when the new file is written. The
skill finds the documents the new material dates or contradicts and fixes them in the same pass.
This exists because of a specific failure: a meeting agenda went out listing three questions as
unanswered, hours after an ingested email had answered all three. Nothing connected the answer
to the document that depended on it.

**It gets better at this.** Every run appends to a playbook: a log row, and a lesson if the run
taught one. The skill is the procedure, the playbook is the memory.

## Install

```bash
git clone https://github.com/brittanyslay/ingest.git ~/.claude/skills/ingest
```

Or drop it in a project at `.claude/skills/ingest/`.

Then say `ingest` and paste something, or `/ingest` with a file.

## First run

The skill does not know your workspace, so it builds a profile by asking you: where captures go,
where the log lives, whether you keep a register of open questions, what your house style is.
That lands in `references/workspace-profile.md`, which is gitignored. Your folder names, file
paths and internal terminology stay on your machine.

Copy `references/workspace-profile.example.md` to start it by hand instead.

## What is in here

```
SKILL.md                                 the procedure
scripts/preflight.py                     run before writing: date, names, URLs
scripts/postflight.py                    run after writing: verbatim diff, dates, style
scripts/workspace_scan.py                search text and Office files for a term
references/workspace-profile.example.md  the profile template
```

**The two scripts are the point.** A procedure in prose gets skimmed. In the workspace this
skill grew up in, the identity check and the date check were written into step one on day one,
and 55 logged lessons later they were both still being broken. So the checkable parts are
commands now.

`preflight.py` prints today's real date, pulls the proper nouns, acronyms, emails and URLs out
of the source, scans the workspace for each one, checks the URLs, and hands back a header block.

`postflight.py` diffs the record's raw-source block against the source file character by
character, fails the record if its ingest line does not say today, and checks the sections that
carry a record's honesty are present. The verbatim diff is the only check here that cannot be
done by reading: a raw-source section is supposed to be the source, and nothing in a read-through
reveals that one character moved.

```bash
python3 scripts/preflight.py source.txt
# write the record
python3 scripts/postflight.py record.md --source source.txt
```

`workspace_scan.py` searches `.docx`, `.pptx` and `.xlsx` by opening them as zips, because grep
cannot see inside them. The first hand-run of that check found a name in five Office files after
finding nothing in any text file. It also shows the text around every hit and suppresses matches
that land inside base64 and minified HTML, because a raw count lies: an early version reported
505 files for a two-letter term that appears in prose in far fewer.

```bash
python3 scripts/workspace_scan.py "Dana Whitfield" "Project Harbor"
```

## The rule that outranks the rest

Only write what the source backs up. An ingest looks like a record and gets quoted like one, so
a plausible-looking sentence in one of these files has a long life.

A number can be arithmetically correct and still unsupported: a label claiming a population it
does not count, a comparison the sources cannot make, a ranking built from a sample. Those are
inventions wearing a number.

## License

CC BY-NC 4.0. Use it inside your company, change it, share it. Do not sell it or bundle it into
something you sell. See [LICENSE](LICENSE).
