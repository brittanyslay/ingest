# Workspace profile

Copy this file to `references/workspace-profile.md` and fill it in. That copy is gitignored, so
your folder names, file paths and colleagues' terminology never leave your machine.

The skill builds this by interviewing you on first use. You can also fill it in by hand. Any
slot you genuinely do not have gets `none`, and the steps that depend on it are skipped rather
than improvised.

---

## Where things go

**Transcripts and captured threads:** `none`
Example: `notes/captures/`, `docs/meetings/`, `records/`

**The ingest playbook, the running log plus lessons:** `none`
Example: `notes/INGEST_PLAYBOOK.md`

**The register of open questions:** `none`
A table of questions waiting on an answer, with a column naming the documents that will be wrong
once each is answered. If you do not have one, the skill will offer to start it.

**The folder map or routing document:** `none`
Whatever says where a given kind of file belongs. Could be a README, a CONTRIBUTING file, or a
folder map.

**The house style guide:** `none`

---

## Root detection

The scan script needs to know where the workspace starts.

**Marker file at the workspace root:** `.git`
Change this if your workspace is not a git repository. Any filename that exists at the root and
nowhere else will do.

---

## House style

The skill carries four writing rules of its own. These are yours.

**Spelling:** `none`
Example: `American. Not labelled, organise, colour, behaviour, recognise, analyse, centre.`

**Punctuation:** `none`
Example: `No em dashes. Commas, colons or periods.`

**Symbols and numerals:** `none`
Example: `Always the % symbol, never the word.`

**Dates:** `none`
Example: `Month Day, Year. Never day-month-year.`

**Emoji:** `none`
Example: `None anywhere, including in headers copied out of chat summaries.`

**Terminology, preferred forms and words to avoid:** `none`
Example: `Say "ACME" not "AcmeCorp". Avoid the words "friction" and "generic".`

**The style check to run before finishing:** `none`
A single shell command that greps the file you wrote for your own violations. Example:

```
grep -nE "—|labelled|organise|colour|behaviour|recognise|analyse|centre" <file>
```

---

## Generated files, never hand-edited

List any file that a script writes, and what regenerates it. Editing one of these by hand is
silently undone on the next run.

- `none`

---

## Sensitivity routing

Which locations in this workspace are team-visible, and which are not. The skill uses this to
decide where a record about people belongs.

**Team-visible, anyone can open:** `none`

**Not team-visible:** `none`

**Never goes in a team-visible location:** `none`
Example: `Anything characterizing a named colleague, personnel changes, credentials.`

---

## Pipelines that own their own sources

Any source type that an automated job already captures, which the skill should leave alone.

- `none`
