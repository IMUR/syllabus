---
name: align-agentfiles
description: Orchestrates and synchronizes multiple root-level AI agent instruction
  files to prevent context duplication. Use this skill when you need to align agents,
  sync markdowns, manage agent context, or maintain separate instruction files like
  AGENTS.md, CLAUDE.md, and GEMINI.md.
---

# Align Agentfiles

## Use this skill when
- You are working in a repository with multiple root-level agent files (e.g., `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
- You need to update project-wide context, rules, or coding standards.
- You want to eliminate duplicated context and ensure all agents follow a single source of truth.

## Do not use this skill when
- The repository only has a single agent instruction file.
- You are modifying code logic rather than agent documentation.

## Dependencies
- Standard Unix utilities (grep, find) for auditing.
- No external packages required.

## Instructions

This skill enforces a modular structure where one file acts as the single source of truth and all other agent files are thin wrappers that point to it.

### 1. Identify the Single Source of Truth

Detect which file already serves as the central specification. Do NOT create a new file if one already exists.

**Detection order (use the first match):**

| File | Auto-read by | Notes |
|------|-------------|-------|
| `AGENTS.md` | Codex CLI, OpenCode | Preferred — widest native auto-read support |
| `CLAUDE.md` | Claude Code | If it's the only file, it is the source of truth |
| `SPEC.md` / `ARCHITECTURE.md` | None (manual reference) | Legacy pattern — migrate to AGENTS.md when possible |

**Decision logic:**

1. If `AGENTS.md` exists and is comprehensive (>50 lines with commands, conventions, guidelines), use it as the source of truth.
2. If `AGENTS.md` does not exist but `CLAUDE.md` is comprehensive, create `AGENTS.md` by extracting the shared content from `CLAUDE.md`, then slim `CLAUDE.md` to a wrapper.
3. If a `SPEC.md` or `ARCHITECTURE.md` exists, migrate its content into `AGENTS.md` and convert it to a wrapper or remove it.

**Why AGENTS.md:** It is auto-read by the most tools natively (Codex, OpenCode). Claude auto-reads `CLAUDE.md` and Gemini auto-reads `GEMINI.md`, but neither auto-reads the other's file. `AGENTS.md` is the only convention that multiple tools share.

### 2. Audit Existing Files

List all agent-related files in the repo root to assess duplication:

```bash
ls -1 AGENTS.md AGENT.md CLAUDE.md GEMINI.md CURSOR.md COPILOT.md SPEC.md ARCHITECTURE.md 2>/dev/null
```

For each file found, assess:
- **Line count** — A wrapper should be under ~30 lines. Anything longer likely contains duplicated content.
- **Overlap** — Does it repeat repo layout, commands, conventions, or rules already in the source of truth?
- **Unique content** — Does it contain provider-specific behavioral tuning that belongs only in this wrapper?

### 3. Refactor to Wrapper Pattern

Each agent wrapper should contain ONLY:
1. A directive to read the source of truth
2. A brief orientation (1-3 sentences)
3. Provider-specific behavioral notes
4. Provider-specific critical constraints (brief)

**Target:** Each wrapper should be under 30 lines. All shared content lives in `AGENTS.md`.

**Template for `CLAUDE.md` wrapper:**
```markdown
# CLAUDE.md — [Project Name]

This file provides guidance to Claude Code when working in this repository.

## Core Guidelines

For project architecture, coding standards, and all operational guidelines, you MUST read and adhere to `AGENTS.md` before beginning any task. That is the single source of truth.

## Quick Orientation

[1-3 sentences: what this repo is, what it contains, key constraint]

## Tooling Notes

[Claude-specific behavioral tuning — MCP tools, plugins, etc.]

## Critical Constraints

- [Constraint 1]
- [Constraint 2]
```

**Template for `GEMINI.md` wrapper:**
```markdown
# GEMINI.md — [Project Name]

## Core Guidelines

For project architecture, coding standards, and all operational guidelines, read `AGENTS.md` before beginning any task. That is the single source of truth.

## Quick Orientation

[1-3 sentences]

## Tooling Notes

[Gemini-specific — built-in tools, shell behavior, etc.]

## Critical Constraints

- [Constraint 1]
- [Constraint 2]
```

**Template for additional wrappers** (`CURSOR.md`, `COPILOT.md`, etc.):
Same structure — directive to read `AGENTS.md`, brief orientation, provider quirks only.

### 4. Provider-Specific Behavioral Notes

Use wrappers exclusively for things that differ between providers. Common examples:

| Provider | Typical quirks |
|----------|---------------|
| Claude Code | MCP tool availability, plugin config, permission modes, `alwaysThinkingEnabled` |
| Gemini CLI | Built-in `run_shell_command`, `httpUrl` for MCP (not `command`+`args`), session retention |
| Codex CLI | `config.toml` format, personality setting, project trust levels |
| OpenCode | XDG config paths, `opencode.json` format |
| Cursor | `.cursorrules` integration, editor-specific behavior |

### 5. Verify Alignment

After refactoring, verify:

```bash
# Check wrapper sizes (should be <30 lines each)
wc -l CLAUDE.md GEMINI.md CURSOR.md 2>/dev/null

# Check source of truth exists and is comprehensive
wc -l AGENTS.md

# Check wrappers reference the source of truth
grep -l "AGENTS.md" CLAUDE.md GEMINI.md CURSOR.md 2>/dev/null
```

### 6. Flag Missing Files

If the repo is used with multiple AI tools, flag gaps:

- **No `AGENTS.md`** — Codex and OpenCode get no context. Create one.
- **No `CLAUDE.md`** — Claude Code gets no context. Create a wrapper.
- **No `GEMINI.md`** — Gemini CLI gets no context. Create a wrapper if Gemini is used.
- **`AGENTS.md` exists but wrappers don't reference it** — Wrappers have stale/duplicated content.

## Architecture Summary

```
AGENTS.md              ← Single source of truth (comprehensive)
  ↑ reads                    ↑ reads
CLAUDE.md (<30 lines)      GEMINI.md (<30 lines)
  └ Claude-specific            └ Gemini-specific
    behavioral tuning            behavioral tuning
```

All shared content (repo layout, commands, conventions, coding standards, commit rules, security policy) lives in `AGENTS.md`. Wrappers contain only a read directive, brief orientation, and provider quirks.
