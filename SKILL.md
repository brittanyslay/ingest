---
name: ingest
description: Turn raw material pasted or dropped into a workspace, an email thread, a meeting transcript or recap, a deck, a spreadsheet, into a durable document, and update every existing doc it touches. Use whenever the user says "ingest," pastes a thread or transcript, or points at a file and asks for it captured, written up, or absorbed into the workspace.
---

# Ingest

A procedure to run, not a document to summarize. The user pastes raw material and says
"ingest." The job is to write it into the workspace in the right place and shape, add nothing
the source does not support, and update whatever existing document the new material touches.

**Scope discipline.** This is capture, not consulting. Do the ingest, update what it touches,
log it, report. Do not add recommendations, plans or adjacent work unless asked. An observation
that belongs in the file goes in the file, not in the reply as advice.

---

## 0. First run: build the profile

This skill is written against a workspace it does not know yet. Everything workspace-specific
lives in one file, `references/workspace-profile.md`, which is gitignored.

**If that file does not exist, create it before doing anything else.** Copy
`references/workspace-profile.example.md` and fill it in by asking the user, one question at a
time, skipping anything you can answer by looking:

1. Where do captured transcripts and threads go?
2. Where does the running ingest log live?
3. Is there a register of open questions? Where?
4. Is there a folder map, routing document or README that governs where files go?
5. Is there a house style guide? Name it.
6. Any terminology rules, preferred spellings, or words to avoid?
7. Any generated files that must never be hand-edited?

A workspace with no answer to a question gets `none` in that slot, and the steps below that
depend on it are skipped rather than improvised.

**Then read the playbook named in the profile.** It holds the running log of everything ingested
and a lessons section that grows. This skill is the procedure; the playbook is the memory. Both
get updated at the end of every run. If the playbook does not exist yet, create it with a log
table and an empty lessons section.

---

## 1. Is this new, or does it already exist here?

Before writing anything, check whether the same source or the same event is already captured.
Search the transcripts folder and the destination folder for the topic, the date and the names.

```
ls "<transcripts folder>" | grep -i "<topic-or-name>"
python3 scripts/workspace_scan.py "<a distinctive phrase from the source>"
```

A distinctive phrase works better than a topic word. A verbatim line from the middle of a
transcript will find the earlier capture of the same call even when the filename does not match.

If it exists, **rebuild that file from all sources**. Do not write a second file, and do not
patch the first. A source often arrives more than once, each pass fuller than the last: 50
seconds of a call, then 4 more minutes, then the recap covering the middle. Each pass changes
what the file should say. The header names which sources it was built from and which one covers
which timespan.

**A different source covering the same event is not a duplicate.** Two accounts of one meeting,
written by different people from different vantage points, are two sources for one record. Write
the record, name the other capture inside it, and leave any pending draft alone.

## 2. Check the source for damage before reading it for content

This step exists because a fragment reads exactly like a complete record.

- **Timestamps.** Walk them for continuity. A gap in the middle leaves both ends looking whole.
  Note the exact span that is missing and how long it is.
- **Images and attachments.** A pasted email drops them silently. If the text refers to a
  schedule, a chart or a screenshot that is not there, that is a hole in the record.
- **Truncation.** Check whether the first message is really the first and the last is really the
  last.
- **Source type.** AI transcription, AI recap and human notes are three different grades of
  evidence. A recap is a machine summary of speech nobody has read. Never blend recap content
  into verbatim content; keep it in its own labeled section and say so.
- **Evidence grade inside the source.** A photograph of someone else's slide, a figure with no
  denominator, a number quoted without a source: these are weaker than the prose around them and
  do not look weaker. Say which is which.

If the source is damaged, that warning goes at the **top of the file**, above the content. Not
in a footnote.

## 3. Route it and name it

| Source | Destination | Filename |
| --- | --- | --- |
| Email thread | the transcripts folder | `<topic>_thread_<YYYY-MM-DD>.md` |
| Meeting transcript, recap or notes | the transcripts folder | `<topic>_<YYYY-MM-DD>.md` |
| Deck, spreadsheet, CSV, PDF | beside the original file, wherever it already lives | `<Original_Filename>_NOTES.md` |
| Material about one named account or client | that account's folder | that folder's own rules apply |
| Anything an automated pipeline already handles | leave it to the pipeline, do not write it by hand | |

The date is the source's date, not the ingest date. If the source carries no date, use the
ingest date and say in the file that it is assumed.

The folder map named in the profile governs anything not in this table. Do not invent a folder.
Nothing goes at the repository root.

**Route on sensitivity, not only on type.** A record about people, their roles, their departures
or their performance, belongs wherever the workspace keeps material that is not team-visible,
even when the announcement it came from was public. The record carries more than the source did:
your cross-references, your corrections, your open questions about people. Say in the file why
it sits where it sits.

## 4. Verify what is cheap to verify

Do this before writing, not after.

- **The date. Run `date` first.** Every line describing your own action, when it was ingested,
  when a URL was checked, when a sweep ran, uses today's real date. A date read out of the source
  belongs only in statements about what the source said. On one run an entire session's output
  was stamped with the date on the emails being read, six days earlier than the truth, and it was
  self-consistent across a dozen files, so nothing caught it until `date` was run.

- **URLs.** `curl -sS -o /dev/null -w "%{http_code}\n" -L "<url>"` before citing anything live.

- **Names, acronyms and product terms.** Run the bundled scan:

  ```
  python3 scripts/workspace_scan.py "Dana Whitfield" "Project Harbor"
  ```

  It searches text files and opens `.docx`, `.pptx` and `.xlsx` as zips, because grep cannot see
  inside them. It prints the text around every hit, and suppresses matches that land inside
  encoded blobs. Short all-caps terms match on word boundaries automatically; use `--substring`
  or `--word` to override.

  Never call a name new on a grep of markdown alone. The first hand-run of this check found a
  name in five Office files after finding nothing in any text file.

  When you cite a term, prefer the document that defines it over a count of documents that
  mention it.

- **A person's name against the directory.** A name on a slide is a reading, not a fact. The
  corporate directory, their task-tracker record and their own email signature outrank it. One
  announcement slide misspelled a surname that the directory, the task tracker and the person's
  own signature all spelled another way, and the scan then found the same misspelling travelling
  through an older deck.

- **Dates and figures** that appear in more than one source. Record both readings, do not pick.

## 5. Write the file

Not a rigid template, but every ingest carries these, roughly in this order:

1. **Title**, plain, naming the thing and its type.
2. **Header block**: ingest date, source date or span, length, who produced it, who is in it,
   and for AI material, the fact that it is AI-generated. List every source it was built from.
3. **The damage warning**, if there is one, above the content.
4. **The substance**, organized by what a reader would come looking for, not by the order the
   source happened to say it. Attribute and date everything: "Dana said X on 12 August" survives
   a personnel change, "X is the plan" does not.
5. **What ties to documents already in this workspace**, stated as matches, not conclusions.
6. **Uncertain, and why.** Probable mis-transcriptions, conflicting statements, unresolved
   dates, names with no surname. Name the conflict, do not arbitrate it.
7. **What did not come through.** Images, attachments, the timespan with no coverage.
8. **What this invalidates.** Name the file and name the claim. Not "cross-referenced" but
   "the agenda lists the attendee list as unknown; this answers it." If a document in this
   workspace asserts something this source changes, say which document and which sentence. This
   is the part that stops an answered question sitting in a file nobody re-reads.
9. **The raw source, last, complete, unedited.** Mark gaps inside it explicitly. When there are
   two sources, both go in, labeled.

**When the source is an image**, transcribe every text element in reading order and say so, keep
the image file beside the record, and measure anything you assert about the image rather than
judging it by eye.

## 6. Update what the ingest touches

The ingest is not finished when the new file is written. Find the existing documents the new
material dates, contradicts or completes, and update them in the same pass, each with a dated
line saying where the update came from. A hub document still carrying the old date is worse than
no hub document.

**Search the templates and generators too, not just the notes.** A stale name in a notes file is
stale. A stale name baked into a template, a slide master or a generator script gets rendered in
front of an audience the next time anyone runs it. Fix the rendering ones first.

**Then work the register**, if the profile names one. It holds every question waiting on an
answer and, in its last column, the documents that will be wrong once it is answered.

- If this ingest **raises** a question nobody can answer, add a row.
- If it **answers** one, move the row to Answered, date it, and open every document in its
  Depends on column and fix it now. Do it in the same session. A closed question with a stale
  dependent document is worse than an open one, because it looks handled.
- If it **orphans** one, because the person who owned the question has gone, say the owner is
  open. An unowned question that still reads as assigned is the worst of the three.

This is not optional tidying. On one run a meeting agenda went out listing three questions as
unanswered, hours after an ingested email had answered all three.

Do not hand-edit generated files. The profile lists which files in this workspace are generated
and what regenerates them.

## 7. Log it, and record anything learned

In the playbook named in the profile:

- Add a row to the running log: ingest date, source, where it was written.
- If this ingest taught something, append a lesson. What happened, and what to do differently.
  Append, never rewrite.

A lesson earns its place by being specific about the failure. "Be careful with dates" teaches
nothing. "An entire session was stamped with the source's date and was self-consistent, so only
running `date` caught it" teaches the check.

## 8. Before anything is handed over, check what moved

This runs the other way round from step 6, and it is the half that is usually missing. Ingestion
is fast and documents are slow: sixteen ingests landing in two days means anything written on the
first day is stale by lunchtime on the second.

Before an agenda, a brief, a deck or a copy document goes to anybody:

- Read the register. Has anything it depends on been answered since it was drafted?
- Check the ingest log for anything captured since the source material was written, on the same
  subject.
- If the document has already gone out, say what changed at the top of it, move the removed copy
  to a clearly marked section at the end with the reason it was pulled, and tell the person who
  builds from it. A document nobody re-opens is not a notification.

## 9. Report

Short. What was written, what was updated, what is uncertain, what is still missing. State
plainly if most of the source was unusable.

---

## The rule that outranks the rest

Only write what the source backs up. It bites harder on ingests than anywhere else, because an
ingest looks like a record and gets quoted like one.

- **Never fill a gap.** A missing eighteen minutes stays missing and gets labeled as missing. Do
  not infer it from the parts either side.
- **Never resolve a conflict silently.** Two dates from two sources means both are recorded with
  attribution and marked unresolved.
- **Never promote an inference to a fact.** If two documents probably describe the same meeting,
  write that it cannot be established from the sources.
- **Never clean up a quote.** Inside verbatim material the source stands as written, including
  spellings and stumbles that break the house style. The surrounding prose follows house style;
  the quote does not. If you alter one character inside verbatim material, say so in place.
- **A number can be arithmetically correct and still unsupported.** A label that claims a
  population it does not count, a comparison the sources cannot make, a ranking built from a
  sample. Those are inventions wearing a number.

## Writing rules that survive any house style

The profile carries this workspace's own spelling, punctuation and terminology rules. These four
are the skill's own, and they hold everywhere:

- **Never label your own sentence's epistemic status.** Not "a dated fact, not a projection," not
  "recorded as a count, not a judgment," not "stated as a lead, not a conclusion." Say what is
  uncertain and why, or say the thing. The label adds nothing the sentence did not already carry.
- **No ad-copy cadence.** Never "No X, no Y. Just Z," no triple negations, no one-word fragments
  for emphasis, no rule-of-three build to a punchline. Say the thing directly.
- **Attribute and date, or do not write it.** A sentence with no owner and no date is a claim the
  workspace cannot check in six months.
- **Describe the limit, do not name the blame.** When something is missing because a team or a
  person did not supply it, write what the record cannot show and why. A shared document is not
  the place to record someone's failure.

Before finishing, run the style check from the profile against the file you wrote.
