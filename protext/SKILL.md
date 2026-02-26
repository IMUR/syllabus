---
name: protext
description: Dynamic context management for AI agents. Invoke /protext at session
  start to load token-efficient project orientation. Use when (1) Starting a session
  and need quick orientation, (2) Handing off between sessions, (3) Managing context
  for multi-scope projects (dev/ops/security), (4) Linking related projects,
  (5) Reducing token usage while maintaining awareness. Primary command is /protext
  to load context. Other commands include protext init, status, scope, handoff,
  extract, link.
---

# Protext: Dynamic Context Management

Protext provides a three-layer context hierarchy for token-efficient AI agent orientation.

## Core Concept

```
AGENTS.md footer (Layer 0)  →  .protext/index.yaml (Layer 1)  →  Deep Context (Layer 2)
     ~500 tokens                     Signposts only                  Full docs/memory
     Always loaded                   On-demand hints                 Explicit extraction
```

Protext embeds project state as a **footer section inside `AGENTS.md`**. This keeps root-level files minimal and ensures every tool that reads `AGENTS.md` gets both behavioral instructions and project orientation in one read.

**Unified Architecture:**
- `AGENTS.md` = Agent behavior (stable, top) + Project context (dynamic, footer)
- `CLAUDE.md` / `GEMINI.md` = Thin wrappers that point to `AGENTS.md`
- `.protext/` = Scopes, extractions, handoff, config (hidden dir)

## File Structure

```
project-root/
├── AGENTS.md                   # Behavior + Protext footer (single source of truth)
├── CLAUDE.md                   # Wrapper → reads AGENTS.md (Claude Code)
├── GEMINI.md                   # Wrapper → reads AGENTS.md (optional)
└── .protext/
    ├── config.yaml             # Protext settings
    ├── index.yaml              # Layer 1: Extraction signposts
    ├── handoff.md              # Session continuity
    └── scopes/
        ├── ops.md              # Operations context
        ├── dev.md              # Development context
        └── security.md         # Security context
```

**Root-level files:** Only `AGENTS.md` + `CLAUDE.md` required. `GEMINI.md` optional. No standalone `PROTEXT.md`.

## Protext Footer Format

The protext section lives at the **end** of `AGENTS.md`, delimited by `<!-- protext:begin -->` and `<!-- protext:end -->`. Everything above is stable behavioral content; everything inside is dynamic project state managed exclusively by protext.

```markdown
# AGENTS.md

[... behavioral content: commands, conventions, rules ...]

---

<!-- protext:begin -->
<!-- This section is managed by /protext. Do not edit manually. Do not add content below this block. -->
## Project Context
> Updated: YYYY-MM-DD | Scope: [active-scope] | Tokens: ~XXX

### Identity
<!-- marker:identity -->
[1-2 sentences: What is this project/system?]
<!-- /marker:identity -->

### Current State
<!-- marker:state -->
Active: [current work] | Blocked: [blockers] | Recent: [last completed]
<!-- /marker:state -->

### Hot Context
<!-- marker:hot -->
- [Critical point 1]
- [Critical point 2]
- [Critical point 3]
<!-- /marker:hot -->

### Scope Signals
- `@ops` → .protext/scopes/ops.md
- `@security` → .protext/scopes/security.md
- `@deep:[name]` → Extract from index

### Child Projects
- `./child/` → **active** | [description] | Recent: [last activity]

### Links
<!-- marker:links -->
- `[path]` → [rel-type] | [note]
<!-- /marker:links -->

### Handoff
<!-- marker:handoff -->
Last: [summary] | Next: [suggested] | Caution: [warnings]
<!-- /marker:handoff -->
<!-- protext:end -->
```

**Footer rules:**
- `<!-- protext:begin/end -->` delimiters are required — they make the block machine-addressable
- The guard comment (`Do not edit manually. Do not add content below this block.`) keeps other agents from modifying or displacing the footer
- Only `/protext` commands should write to this block
- Use `## Project Context` (H2), `###` for subsections — peers with other AGENTS.md sections
- Preserve all `<!-- marker:* -->` tags — parent aggregation depends on them
- `### Child Projects` and `### Links` are optional (omit if unused)
- Keep the footer under ~500 tokens

## Commands

### `/protext` (Primary - Session Start)

**Load project orientation.** This is the main entry point - invoke at session start.

```text
/protext              # Load protext footer + active scope + handoff
/protext @security    # Load with security scope
/protext --full       # Include available extractions list
```

**What it does:**
1. Finds the protext block (see detection order below)
2. Reads and displays the project context
3. Shows handoff status (FRESH/AGING/STALE)
4. Loads active scope context
5. Lists available deep extractions (with `--full`)

**Detection order — find protext content using the first match:**
1. `AGENTS.md` contains `<!-- protext:begin -->` → read the footer block (current pattern)
2. Standalone `PROTEXT.md` exists → read it (legacy pattern — offer to migrate)
3. Neither found → offer to run `protext init`

**Cross-platform:** Works as slash command on Claude Code, or natural language on other platforms:
- "Load protext"
- "Show me the project context"
- "What's the current state?"

**If legacy `PROTEXT.md` detected:** Load it normally, but inform the user that protext now embeds in `AGENTS.md` and offer to migrate. Do not auto-migrate.

---

### `protext init`

Initialize protext in a project.

```text
# Standard mode
"Initialize protext for this project"
"Set up protext here"

# Parent mode (aggregates children)
"protext init --parent"
```

**Detection-based behavior — examine what exists and act accordingly:**

| State found | Action |
|-------------|--------|
| `AGENTS.md` with `<!-- protext:begin -->` | Already initialized — inform user, no action |
| `AGENTS.md` exists, no protext footer | Append the protext footer block to `AGENTS.md` |
| No `AGENTS.md`, standalone `PROTEXT.md` exists | Create `AGENTS.md` (extract shared content from `CLAUDE.md` if present), fold `PROTEXT.md` content into footer, delete `PROTEXT.md` after user confirms |
| No `AGENTS.md`, no `PROTEXT.md` | Create `AGENTS.md` with minimal behavior section + protext footer, create `.protext/` |
| `.protext/` dir missing | Create it with config.yaml, empty scopes/ |

When folding a standalone `PROTEXT.md` into the footer:
- `# Protext: [Name]` H1 becomes `## Project Context` H2
- All `## Section` H2 headings become `### Section` H3
- All `<!-- marker:* -->` tags are preserved
- The `<!-- protext:begin/end -->` delimiters and guard comment are added

**Parent mode:** Scans for child `AGENTS.md` files (falling back to child `PROTEXT.md` for unmigrated repos), aggregates their status into `### Child Projects`. One-level hierarchy only.

### `protext status`

Display current protext state.

```text
"Show protext status"
"What's the current context state?"
```

Shows: Tier, active scope, handoff age, token budget, available extractions.

### `protext scope [name]`

Switch active scope context.

```text
"Switch to ops scope"
"Focus on security context"
"@security"  # Shorthand
```

### `protext handoff`

Capture or display session handoff. **User-initiated only** — no auto-capture, no TTL enforcement.

```text
"Capture handoff: stopped mid-refactor, next step is testing"
"What was the last handoff?"
```

Handoff is an optional scratchpad. Only created when user explicitly captures.

### `protext extract [name]`

Pull deep context from index.

```text
"Extract network context"
"@deep:services"  # Shorthand
```

Agent receives extraction suggestion; confirm to load.

### `protext link [path]`

Add a cross-project link. Guided flow — agent asks for relationship type and note.

```text
"Link this project to ../skills-validator"
"protext link ../homelab"
"What projects are linked?"
```

Relationship types with spatial validation:
- `child` — Subdirectory (./name) — aggregates status
- `parent` — Ancestor (../) — no aggregation
- `sibling` — Adjacent (../name) — no aggregation
- `peer` — Any path (relative preferred) — no aggregation

**Path preference:** Use relative paths (`../sibling`, `./child`) wherever possible — they are portable across nodes and OS mount points. Absolute paths may break on machines with different prefixes (e.g., `/mnt/ops` on Linux vs `/Volumes/ops` on macOS).

Validates path patterns with regex enforcement (ERROR if spatial rules violated). Max 5 lateral links. See **Spatial Validation Rules** in `references/commands.md` for pattern specs, validation flow, and edge cases.

### `protext refresh --children`

Re-aggregate child status in parent protext. **User-initiated only** — no auto-refresh.

```text
"protext refresh --children"
"Update children status"
```

Scans child `AGENTS.md` files for `<!-- protext:begin -->` blocks, extracts status from markers. Falls back to standalone `PROTEXT.md` for unmigrated children. Updates parent `### Child Projects` subsection.

## Parent Protext

Meta-projects that aggregate multiple child protexts. Created with `protext init --parent`.

**Key features:**
- `### Child Projects` subsection lists all children with status (active/idle/stale)
- Child status based on `.protext/config.yaml` modification time (< 7 days = active, ≥ 7 = idle, ≥ 30 = stale)
- No extraction index (children have their own)
- `protext refresh --children` re-aggregates (explicit user command only)
- One-level hierarchy: parent → children only

**Marker extraction:** Parent reads `<!-- marker:identity -->`, `<!-- marker:state -->` from child `AGENTS.md` protext footers. Falls back to standalone `PROTEXT.md` if no footer found (backward compatible with unmigrated repos).

**Zero auto-execution:** Parent never auto-refreshes on load. Always explicit.

## Extraction Modes

Configure in `.protext/config.yaml`:

```yaml
extraction_mode: suggest  # suggest | auto | confirm
token_budget: 2000        # Max extraction tokens per session
```

- **suggest** (default): Agent sees "context available: X" but doesn't auto-load
- **auto**: Keyword triggers load (opt-in, risky for token budget)
- **confirm**: Agent proposes extraction, user must approve

## Index Schema

`.protext/index.yaml`:

```yaml
extractions:
  network:
    source: docs/NETWORK.md
    triggers: [dns, ip, tailscale, mesh, routing]
    summary: "IPs, DNS config, mesh nodes"
    tokens: ~600

  services:
    source: docs/SERVICES.md
    triggers: [docker, container, service, port]
    summary: "Docker services, ports, domains"
    tokens: ~800

  secrets:
    source: docs/SECRETS.md
    triggers: [secret, credential, infisical, auth]
    summary: "Secrets management, auth patterns"
    tokens: ~400
```

**Limits:** Max 20 extractions per project.

## Scopes

Scopes provide domain-specific orientation. Max 5 per project.

Default scopes:
- `ops` — Infrastructure, deployment, monitoring
- `dev` — Development workflow, code patterns
- `security` — Auth, secrets, vulnerabilities
- `project` — Project-specific context (custom)

Scope file format (`.protext/scopes/ops.md`):

```markdown
# Scope: Operations

## Focus
Infrastructure management, service health, deployment.

## Key Resources
- [Service config paths]
- [Key infrastructure locations]

## Current Priorities
1. [Priority 1]
2. [Priority 2]

## Cautions
- [Ops-specific warnings]
```

## Handoff Protocol

**User-initiated only** — handoff is an optional scratchpad for session continuity.

`.protext/handoff.md` format:

```markdown
# Session Handoff
> Updated: YYYY-MM-DDTHH:MM

## Last Session
**Completed:**
- [Task 1]
- [Task 2]

**In Progress:**
- [Task] (stopped at: [point])

**Deferred:**
- [Task] (blocked by: [reason])

## Cautions
- [Warning 1]
- [Warning 2]

## Agent Notes
[Observations that might help next session]
```

Behavior:
- No auto-capture at session end
- No TTL warnings based on age
- Created only when user runs `protext handoff capture`
- Agents do not automatically update handoff

## Progressive Tiers

### Beginner
- AGENTS.md with protext footer only
- No scopes, extractions, or handoff
- Direct editing of footer

### Intermediate
- AGENTS.md footer + handoff.md
- Session continuity
- No extraction index

### Advanced (Default)
- Full feature set
- Scopes, extractions, token budgets
- Config-driven behavior

## Constraints

| Limit | Value | Rationale |
|-------|-------|-----------|
| Max scopes | 5 | Prevent fragmentation |
| Max lateral links | 5 | Keep peer/sibling/reference list concise |
| Max child links | Unlimited | Structure dictates count |
| Max extractions | 20 | Index stays scannable |
| Token budget | 2000 | Default per-session limit |
| Protext footer size | ~500 tokens | Quick orientation |
| Hierarchy depth | 1 level | Parent → children only |

## Integration with Agent Files

Protext embeds in `AGENTS.md`, which is the single source of truth per the `align-agentfiles` pattern:

```
AGENTS.md              ← Behavior (stable) + Protext footer (dynamic)
  ↑ reads                    ↑ reads
CLAUDE.md (<30 lines)      GEMINI.md (<30 lines)
  └ Claude-specific            └ Gemini-specific
```

- **Codex/OpenCode** auto-read `AGENTS.md` → get both behavior and protext
- **Claude** reads `CLAUDE.md` which directs it to `AGENTS.md` → gets both
- **Gemini** reads `GEMINI.md` which directs it to `AGENTS.md` → gets both

### With Memory Systems

Protext complements but doesn't replace:
- **memory/** — Long-term learnings, patterns
- **Protext footer** — Current session orientation

## Scripts

Requires **Python 3.8+**. No external packages needed (yaml parsed with fallback).

- `scripts/init_protext.py` — Bootstrap protext in a project
- `scripts/protext_status.py` — Display current state

## Reference Files

Consult these only when deeper detail is needed:

- `references/formats.md` — Read when creating or editing protext footers, index.yaml, handoff.md, or scope files. Contains complete templates and field guidelines.
- `references/commands.md` — Read when implementing command handling or troubleshooting. Contains full syntax, flags, error messages, and natural language alternatives.
