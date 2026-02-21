---
name: skill-deploy
description: Validate and deploy skills from dev/ into generated syllabus/ and .agent/skills/ artifacts. Use when a skill is ready for first deploy or update.
---

# skill-deploy: Skill Deployment Workflow

## When to Use This Skill

Use when:
- A skill in `dev/` is ready for first deployment
- A deployed skill in `dev/` was updated and needs redeploy
- You need a validation gate before publishing/deploying

---

## Assumed Context

This skill runs from the skills monorepo at `/mnt/ops/prj/skills/` (Linux) or `/Volumes/ops/prj/skills/` (macOS trtr).

---

## Architecture Overview

```
dev/                    → Source of truth (all edits happen here)
    ↓ skill-deploy
syllabus/               → Public semi-packed artifacts (generated)
    ↓
.agent/skills/          → Runtime deployment artifacts (generated)
    ↓ skills-sync push
~/.claude/skills/       → Platform paths
~/.gemini/skills/
~/.cursor/skills/
...
```

---

## Commands

### Deploy or Update a Skill

```bash
python3 dev/skill-deploy/scripts/skill_deploy.py dev/<skill-name>
```

Or via wrapper command:

```bash
skill-deploy dev/<skill-name>
```

### Deploy or Update All Skills

```bash
python3 dev/skill-deploy/scripts/skill_deploy.py --all
```

Batch mode behavior:
- Discovers all top-level `dev/*` directories with `SKILL.md`
- Validates all first (unless `--no-validate`)
- Aborts before packaging if any validation FAIL occurs
- Packages all skills to both `syllabus/` and `.agent/skills/`
- Runs `./skills-sync push` once at the end

### Validate Only (No Artifact Writes)

```bash
skill-deploy --validate-only dev/<skill-name>
skill-deploy --all --validate-only
```

### Deploy Without Validation (Dangerous)

```bash
skill-deploy --no-validate dev/<skill-name>
skill-deploy --all --no-validate
```

---

## Deployment Behavior

`skill-deploy` now performs one flow for both first deploy and updates:

1. Verifies source path is `dev/<skill-name>`
2. Validates with `dev/skills-validator/scripts/validate_skill.py`
3. Detects existing deployment (`syllabus/<skill>` and `.agent/skills/<skill>`)
4. Generates/updates `syllabus/<skill>` (public semi-packed profile)
5. Generates/updates `.agent/skills/<skill>` (runtime profile)
6. Runs `./skills-sync push`

No source directory move occurs. Source remains in `dev/`.

---

## Packaging Profiles

### Public Profile (`syllabus/<skill>/`)

Includes:
- `SKILL.md`
- `README.md` (if present)
- `CHANGELOG.md`, `CHANGELOG` (if present)
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (if present)
- `scripts/`, `references/`, `examples/`, `assets/`, `resources/`
- `LICENSE`, `LICENSE.txt`

### Runtime Profile (`.agent/skills/<skill>/`)

Includes:
- `SKILL.md`
- `scripts/`, `references/`, `examples/`, `assets/`, `resources/`
- `LICENSE`, `LICENSE.txt`

Excludes dev-only files like `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.git/`, `.protext/`, `.archive/`, `docs/`.

---

## Ignore Files

### `.skillignore`

Applies to both profiles.

### `.syllabusignore`

Applies only to `syllabus/` output.

Example:

```text
# .skillignore
notes.md
drafts/
*.tmp
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation failed |
| 2 | Packaging error |
| 3 | skills-sync failed |

---

## Workflow Examples

### Example 1: First Deploy

```bash
$ skill-deploy dev/my-new-skill

[skill-deploy] Validating /mnt/ops/prj/skills/dev/my-new-skill...
[skill-deploy] No existing deployment found, running first deploy flow.
✅ Validation passed.
[skill-deploy] Packaging public artifact to /mnt/ops/prj/skills/syllabus/my-new-skill...
  ✅ Created syllabus/my-new-skill/
[skill-deploy] Packaging runtime artifact to /mnt/ops/prj/skills/.agent/skills/my-new-skill...
  ✅ Created .agent/skills/my-new-skill/
[skill-deploy] Running skills-sync push...

✅ Deployed my-new-skill successfully (syllabus + runtime).
```

### Example 2: Update Existing Deployment

```bash
$ skill-deploy dev/protext

[skill-deploy] Validating /mnt/ops/prj/skills/dev/protext...
[skill-deploy] Existing deployment found, running update flow.
⚠️  Validation passed with warnings.
[skill-deploy] Packaging public artifact to /mnt/ops/prj/skills/syllabus/protext...
  ✅ Updated syllabus/protext/
[skill-deploy] Packaging runtime artifact to /mnt/ops/prj/skills/.agent/skills/protext...
  ✅ Updated .agent/skills/protext/
[skill-deploy] Running skills-sync push...

✅ Deployed protext successfully (syllabus + runtime).
```

---

## Troubleshooting

### "Skill source must be inside dev/"

Use:

```bash
skill-deploy dev/<skill-name>
```

### "Validator not found"

Ensure validator exists at:

```bash
dev/skills-validator/scripts/validate_skill.py
```

### "skills-sync not found"

Ensure you're running from repo root and script is executable:

```bash
cd /mnt/ops/prj/skills
chmod +x skills-sync
./skills-sync push
```

---

## Scripts

- `scripts/skill_deploy.py` — Main deployment script
