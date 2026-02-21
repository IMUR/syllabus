---
name: skills-validator
description: Comprehensive validation of AI agent skills against the 44-point
  cross-platform quality checklist. Use when (1) Building or editing a skill
  and need quality verification before deployment, (2) Reviewing community
  skills for compliance, (3) Running pre-commit or CI validation on skill
  changes, (4) Auditing local skills for cross-platform compatibility.
  Primary command is validate-skill with a path to a skill directory.
---

# Skills Validator

Validates AI agent skills against a 44-point cross-platform quality checklist covering structure, metadata, triggers, token efficiency, and portability.

## Quick Start

```bash
python3 scripts/validate_skill.py /path/to/skill
```

Example output:

```
Skills Validator: /path/to/my-skill
==========================================================
SKILL.md Core (7 checks)
  [PASS] C1.1  SKILL.md exists
  [PASS] C1.2  YAML frontmatter parses
  [WARN] C1.5  Description completeness (no numbered use cases)
...
==========================================================
Summary: 28 PASS | 2 WARN | 0 FAIL | 12 MANUAL | 1 SKIP
Result: WARN (exit code 2)
```

## Commands

### Primary: Validate a skill

```bash
# Validate a single skill directory
python3 scripts/validate_skill.py /path/to/skill

# JSON output for tooling
python3 scripts/validate_skill.py /path/to/skill --json

# Strict mode (WARNs become FAILs, for CI)
python3 scripts/validate_skill.py /path/to/skill --strict

# Single category only
python3 scripts/validate_skill.py /path/to/skill --category C1
```

### Natural Language (Cross-Platform)

- "Validate this skill"
- "Check skill quality"
- "Run the skills checklist"
- "Audit this skill for compliance"

### Batch Validation

```bash
# Validate all local skills
for d in ~/.agent/skills/local/*/; do
  python3 scripts/validate_skill.py "$d"
  echo "---"
done
```

## Check Categories

| Category | Checks | Focus |
|----------|--------|-------|
| C1 | 7 | SKILL.md core: existence, frontmatter, name, description, body |
| C2 | 7 | File structure: dirs, executability, paths, references depth |
| C3 | 6 | Frontmatter: properties, file references, trigger placement |
| C4 | 7 | Triggers: keywords, natural language, examples, dependencies, body sections |
| C5 | 8 | Token efficiency: budget, relevance (mostly manual review) |
| C6 | 9 | Portability: Markdown-only, platform deps (partially manual) |

## Result Statuses

| Status | Meaning | Affects Exit Code |
|--------|---------|-------------------|
| PASS | Check passed | No |
| WARN | Heuristic concern (may be false positive) | Exit 2 |
| FAIL | Hard requirement violated | Exit 1 |
| MANUAL | Requires human/AI judgment | No |
| SKIP | Not applicable or deduped | No |

## Exit Codes

- `0` — All automated checks pass
- `1` — At least one FAIL (or WARNs in `--strict` mode)
- `2` — No FAILs but at least one WARN

## Options

| Flag | Effect |
|------|--------|
| `--json` | Machine-readable JSON output |
| `--strict` | Promote all WARNs to FAILs |
| `--category C1,C2` | Run only specified categories |

## Scripts

Requires **Python 3.8+**. No external packages needed (PyYAML optional for YAML parsing; falls back to built-in parser).

- `scripts/validate_skill.py` — Main validator. Run against any skill directory.

## Reference Files

- `references/skills-checklist.md` — Read when you need the full 44-point checklist with rationale, platform compatibility matrix, or cross-platform testing guidance. Contains all check definitions and their sources.
