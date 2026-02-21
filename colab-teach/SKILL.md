---
name: colab-teach
description: Create new AI agent skills for the Co-lab cluster. Scaffolds in dev/,
  validates with skills-validator, and offers to deploy. Use when creating new skills
  from any directory with automatic context extraction.
---

# colab-teach: Co-lab Skill Creator

## When to Use This Skill

Use when:
- Creating a new skill for the Co-lab cluster
- Extracting a skill from current project context
- Scaffolding a skill with cluster-aware templates

---

## Assumed Context

This skill knows about the Co-lab skills monorepo at `/mnt/ops/prj/skills/` and creates skills in `dev/` by default. It can be invoked from any directory.

---

## Commands

### Create New Skill

```bash
colab-teach <skill-name>
```

**What it does:**
1. Creates `dev/<skill-name>/SKILL.md` with proper frontmatter
2. Creates `scripts/` and `references/` directories
3. Prompts for skill type to select appropriate template
4. Validates with skills-validator
5. Offers to deploy with skill-deploy

### Create from Context

```bash
colab-teach <skill-name> --from-context
```

Extracts skill content from the current project:
- Reads `CLAUDE.md`, `AGENTS.md`, or `README.md`
- Identifies patterns, commands, and workflows
- Suggests triggers based on domain
- Generates SKILL.md with extracted knowledge

### Create with Template

```bash
colab-teach <skill-name> --template <type>
```

**Template types:**

| Type | Use Case | Includes |
|------|----------|----------|
| `ops` | Operations/infrastructure | Node detection, SSH patterns, service commands |
| `dev` | Development workflow | Code patterns, testing, linting |
| `reference` | Documentation lookup | Deep docs, examples, API references |
| `meta` | Skill management tools | Integration with skill-deploy/colab-learn |

### Create and Deploy

```bash
colab-teach <skill-name> --deploy
```

Create, validate, and deploy in one shot:
1. Scaffold skill
2. Run skills-validator
3. If pass, run skill-deploy
4. Optionally run colab-learn

---

## Templates

### ops Template

For infrastructure/operations skills. Assumes crtr as hub.

```markdown
---
name: <skill-name>
description: <what it does>. Use when <triggers>.
---

# <skill-name>: <Title>

## When to Use

Use when:
- <trigger 1>
- <trigger 2>

---

## Assumed Context

This skill runs from crtr (cooperator) by default. Commands are shown for crtr;
remote nodes are accessed via SSH.

---

## Cluster Topology

| Node | Role | Access |
|------|------|--------|
| crtr | Hub, services | local |
| drtr | Compute | `ssh drtr` |
| trtr | Desktop | `ssh trtr` |
| prtr | Compute | `ssh prtr` |

---

## Commands

<!-- Commands here -->

---

## Scripts

- `scripts/<script>.sh` — Description
```

### dev Template

For development workflow skills.

```markdown
---
name: <skill-name>
description: <what it does>. Use when <triggers>.
---

# <skill-name>: <Title>

## When to Use

Use when:
- <trigger 1>
- <trigger 2>

---

## Quick Start

```bash
# Primary command
<command>
```

---

## Workflow

<!-- Development workflow here -->

---

## Examples

<!-- Code examples here -->
```

### reference Template

For documentation/lookup skills.

```markdown
---
name: <skill-name>
description: <what it does>. Use when looking up <topic>.
---

# <skill-name>: <Title>

## When to Use

Use when:
- Looking up <topic>
- Need reference for <domain>
- Debugging <related issues>

---

## Quick Reference

<!-- Cheat sheet here -->

---

## Deep Dive

See `references/` for detailed documentation.

---

## References

- `references/<topic>.md` — Detailed guide
```

### meta Template

For skill management tools.

```markdown
---
name: <skill-name>
description: <what it does>. Use when <triggers>.
---

# <skill-name>: <Title>

## When to Use

Use when:
- Managing skill source and artifacts
- Deploying or syncing skills

---

## Architecture

```
dev/                    → Skills source of truth
    ↓ skill-deploy
syllabus/               → Public semi-packed artifacts
    ↓ skill-deploy
.agent/skills/          → Runtime packaged skills
    ↓ colab-learn
~/.claude/skills/       → Platform paths
```

---

## Commands

<!-- Commands here -->

---

## Integration

Works with:
- `skill-deploy` — Package and deploy
- `colab-learn` — Cluster-wide sync
- `skills-validator` — Quality checks

---

## Scripts

- `scripts/<script>.py` — Main script
```

---

## Context Extraction

When using `--from-context`, colab-teach:

1. **Discovers project type:**
   - Python (requirements.txt, pyproject.toml)
   - Node.js (package.json)
   - Ruby (Gemfile)
   - Rust (Cargo.toml)
   - Generic (README.md only)

2. **Extracts patterns:**
   - Commands from README/CLAUDE.md
   - File paths mentioned
   - Key concepts and terminology

3. **Suggests triggers:**
   - Domain-specific keywords
   - Error messages mentioned
   - Tool names

4. **Generates SKILL.md:**
   - Populates frontmatter
   - Creates structure based on template
   - Includes extracted examples

---

## Workflow

```
┌─────────────────┐
│ colab-teach     │
│ <skill-name>    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select template │
│ (ops/dev/ref/   │
│  meta)          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create dev/     │
│ <skill-name>/   │
│ SKILL.md        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run             │
│ skills-validator│
└────────┬────────┘
         │
    ┌────┴────┐
    │ Pass?   │
    └────┬────┘
         │
    ┌────┴────┐
    │ Yes     │ No
    ▼         ▼
┌───────┐  ┌───────┐
│ Offer │  │ Show  │
│ deploy│  │ errors│
└───┬───┘  └───────┘
    │
    ▼
┌─────────────────┐
│ skill-deploy?   │
│ colab-learn?    │
└─────────────────┘
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Skill created successfully |
| 1 | Validation failed |
| 2 | Skill already exists |
| 3 | Template not found |

---

## Scripts

- `scripts/colab_teach.py` — Main skill creator script
