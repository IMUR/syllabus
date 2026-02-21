---
name: record-keeping
description: Create operational records for the Co-lab cluster. Use when a
  session produced decisions, deployments, discoveries, or lessons worth
  preserving. Also use when a notable insight emerges mid-session and should
  be captured immediately. Triggers on create a record, record this, write a
  record, jot this down, save a record, document what happened, capture this
  decision, /record. Writes to node-specific paths with light front matter
  for future machine consumption. Two modes — full record (session-level)
  and quick capture (single insight).
---

# record-keeping: Co-lab Cluster Records

Create records that capture what happened, what was decided, and what was
rejected — written by agents, for agents.

## Use this skill when

- End of session — preserving decisions, deployments, lessons
- Mid-session — a single valuable insight or discovery worth capturing
- User says "create a record", "record this", "write a record", "/record"

## Do not use this skill for

- Searching or organizing existing records (future companion skill)
- Routine status checks with no decisions or discoveries
- Duplicating information already in CLAUDE.md or service docs

---

## Quick Start

When invoked, detect the current node and draft a record from session context.
Do not interrogate the user. You already have the context — use it.

---

## Modes

### Full Record

Default. Used at end of session or after significant work.

Draft a complete record from the session, then present it to the user for
review before writing. The record should include:

- **What was done** — concrete actions, not vague summaries
- **What was decided and why** — the reasoning, not just the outcome
- **What was rejected and why** — the most commonly lost, most valuable signal
- **What's still open** — unresolved items, known gaps, next steps
- **Key takeaway** — one sentence a future agent needs if it reads nothing else

### Quick Capture

Used for a single insight mid-session. Invoked with `/record quick` or when
the user asks to "jot this down" or capture a single finding.

Write 3-8 lines. Same front matter. Same path. No sections needed — just the
insight and enough context to make it useful in isolation.

---

## Record Structure

Records are Markdown files with YAML front matter. The front matter provides
machine-parseable metadata. The body is freeform.

### Front Matter (suggested, not enforced)

```yaml
---
date: 2026-02-20
node: crtr
type: session | deployment | decision | incident | insight
nodes_touched: [crtr, drtr, prtr]
topics: [termix, docker, headscale]
---
```

**Fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `date` | Yes | ISO date |
| `node` | Yes | Authoring node (detected automatically) |
| `type` | Suggested | Agent's best judgment. Not a rigid taxonomy — pick whatever fits |
| `nodes_touched` | Suggested | Which nodes were involved in the work |
| `topics` | Suggested | Freeform tags for future search/filtering |

The agent should always include `date` and `node`. The rest should be included
when they add signal, omitted when they don't.

### Body

Freeform Markdown. No mandatory sections. The agent writes what matters.

For full records, these sections tend to be valuable (but are not required):

- What was done
- Decisions and reasoning
- Alternatives rejected
- Open items
- Key takeaway

For quick captures, just write the insight.

---

## Paths and Naming

### Node Detection and Path Resolution

Detect the current node via `hostname`. The NFS share is mounted at different
paths depending on the OS. Resolve the base path first, then append the
node-specific records directory.

**Base path by OS:**

| OS | Mount Point |
|----|-------------|
| Linux (crtr, drtr, prtr) | `/mnt/ops` |
| macOS (trtr) | `/Volumes/ops` |

**Detection:** If `uname -s` returns `Darwin`, use `/Volumes/ops`. Otherwise
use `/mnt/ops`.

**Full path:** `{base}/records/{node}-records/`

| Hostname | Node | Linux Path | macOS Path |
|----------|------|-----------|------------|
| cooperator | crtr | `/mnt/ops/records/crtr-records/` | — |
| director | drtr | `/mnt/ops/records/drtr-records/` | — |
| projector | prtr | `/mnt/ops/records/prtr-records/` | — |
| terminator | trtr | — | `/Volumes/ops/records/trtr-records/` |

All four paths point to the same NFS share — the files are identical regardless
of which node writes them.

### Filename

```
YYYY-MM-DD-descriptive-slug.md
```

- Date prefix for chronological sorting
- Slug: lowercase, hyphenated, concise (3-6 words)
- Examples: `2026-02-20-termix-deployment.md`, `2026-02-20-bun-native-module-incompatibility.md`

---

## Authoring Guidelines

### Do

- **Draft from session context** — you have it, use it
- **Capture what was rejected** — this is the highest-value signal
- **Be dense** — future agents parse this, not casual readers
- **Include concrete details** — IPs, ports, file paths, command outputs
- **State the key takeaway** — one line, top of mind for a future agent

### Don't

- **Don't interrogate the user** — draft first, ask for review
- **Don't pad with boilerplate** — no "In this session we..." preamble
- **Don't duplicate CLAUDE.md content** — records capture what happened, not how things work
- **Don't create records for trivial work** — if nothing was decided or discovered, don't record

### On Consistency vs Freedom

The front matter is the consistency layer. The body is the freedom layer.
Future skills will parse front matter for search and organization.
The body should say whatever the authoring agent believes is worth preserving.

---

## Workflow

```text
1. User invokes /record (or /record quick)
2. Detect current node via hostname and OS
3. Resolve records path ({base}/records/{node}-records/)
4. Check: was a record already written in this session?
   → If yes: scope context to only what happened AFTER the last record
   → If no: scope context to the full session
5. Draft record from scoped context
6. Present draft to user
7. On approval, write to path with correct filename
```

The user may edit, approve, or reject the draft. Never write without showing
the draft first.

### Multi-Record Sessions

When invoked more than once in the same session, the agent must detect that
a prior record was already written and decide: **update the existing record**
or **create a new one**.

**Default heuristic — favor new records.** New records are safer (no risk of
overwriting good content) and simpler. Create a new record unless the prior
one would be incomplete or misleading without the new information.

**Update the existing record when:**
- The new work directly completes the prior record (deployment then bugfix,
  decision then immediate correction)
- The prior record would be misleading if read without the new context
- Same core topic, and merging produces a cleaner single artifact

**Create a new record when:**
- The session pivoted to a different topic or set of concerns
- The prior record already stands alone as a complete unit
- Different nodes, different decisions, independently valuable

**Do not ask the user which to do.** Make the judgment, show the draft. The
user reviews before anything is written — if the agent guessed wrong, the
user redirects. This keeps invocation frictionless.

**Scoping:** Whether updating or creating new, only draw from conversation
context that follows the prior record's creation. The agent wrote it — it
knows what was already covered.

**Standalone by default.** New records should not reference the prior one.
No "see previous record", no linking, no handoff language. If a small amount
of context from earlier work is needed for the new record to stand alone,
include it naturally — not as a cross-reference.

---

## Reference Files

- `references/record-examples.md` — Annotated examples of strong and weak records from the existing corpus
