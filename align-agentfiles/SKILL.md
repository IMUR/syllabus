---
name: align-agentfiles
description: Orchestrates and synchronizes multiple root-level AI agent instruction files to prevent context duplication. Use this skill when you need to align agents, sync markdowns, manage agent context, or maintain separate instruction files like AGENT.md, CLAUDE.md, and GEMINI.md.
---

# Align Agentfiles

## Use this skill when
- You are working in a repository with multiple root-level agent files (e.g., `AGENT.md`, `CLAUDE.md`, `GEMINI.md`).
- You need to update project-wide context, rules, or coding standards.
- You want to eliminate duplicated context and ensure all agents follow a single source of truth.

## Do not use this skill when
- The repository only has a single agent instruction file.
- You are modifying code logic rather than agent documentation.

## Dependencies
- Standard Unix utilities (grep, find) for auditing.
- No external packages required.

## Instructions

This skill enforces a modular structure where a central specification file acts as the single source of truth, and agent wrappers load that context.

### 1. The "Single Source of Truth" Architecture

Enforce the following architectural pattern:

- **Central Specification (`SPEC.md` or `ARCHITECTURE.md`):** This file contains all shared context, including project architecture, coding standards, naming conventions, and general constraints.
- **Agent Wrappers (`CLAUDE.md`, `GEMINI.md`, etc.):** These files must explicitly reference or include the central specification file to load the shared context.

### 2. Auditing Existing Files (The "Align" Task)
First, audit the root of the repository for existing agent files to identify duplicated content.

```bash
# Example command to list common agent markdowns
ls -1 AGENT.md CLAUDE.md GEMINI.md CURSOR.md 2>/dev/null
```

### 3. Synchronizing and Refactoring
Refactor the agent-specific wrappers to remove the duplicated content. Replace the removed content with a clear directive to read the central specification. 

Example block to insert into `CLAUDE.md`:
```markdown
## Core Guidelines
For project architecture, coding standards, and general guidelines, you MUST read and adhere to `SPEC.md` before beginning any task.
```

### 4. Managing Provider Quirks
Use the agent wrappers exclusively for behavioral tuning. 

Example `GEMINI.md` quirk:
```markdown
## Tooling Notes
Gemini CLI has built-in tools like `run_shell_command`. Use them silently where possible.
```

Example `CLAUDE.md` quirk:
```markdown
## Tooling Notes
Claude relies on MCP tools for execution. Always check the available tools before attempting to run commands.
```
