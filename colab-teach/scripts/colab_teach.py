#!/usr/bin/env python3
"""
colab_teach.py - Create new AI agent skills for the Co-lab cluster

Usage:
    colab_teach.py <skill-name>
    colab_teach.py <skill-name> --from-context
    colab_teach.py <skill-name> --template <ops|dev|reference|meta>
    colab_teach.py <skill-name> --deploy

Creates skills in dev/ with proper structure, validates, and optionally deploys.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Detect monorepo root
if os.path.isdir("/Volumes/ops/prj/skills"):
    REPO_ROOT = Path("/Volumes/ops/prj/skills")
else:
    REPO_ROOT = Path("/mnt/ops/prj/skills")

DEV_DIR = REPO_ROOT / "dev"
VALIDATOR = DEV_DIR / "skills-validator" / "scripts" / "validate_skill.py"
SKILL_DEPLOY = DEV_DIR / "skill-deploy" / "scripts" / "skill_deploy.py"
COLAB_LEARN = DEV_DIR / "colab-learn" / "scripts" / "colab_learn.sh"

TEMPLATES = {
    "ops": """---
name: {name}
description: {description}. Use when {triggers}.
---

# {name}: {title}

## When to Use

Use when:
- {trigger_1}
- {trigger_2}

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

<!-- Add commands here -->

---

## Troubleshooting

<!-- Add troubleshooting here -->

---

## Scripts

- `scripts/<script>.sh` — Description
""",

    "dev": """---
name: {name}
description: {description}. Use when {triggers}.
---

# {name}: {title}

## When to Use

Use when:
- {trigger_1}
- {trigger_2}

---

## Quick Start

```bash
# Primary command
<command>
```

---

## Workflow

1. **Step 1** — Description
2. **Step 2** — Description
3. **Step 3** — Description

---

## Examples

```bash
# Example 1
<command>

# Example 2
<command>
```

---

## Troubleshooting

<!-- Add troubleshooting here -->

---

## Scripts

- `scripts/<script>.py` — Description
""",

    "reference": """---
name: {name}
description: {description}. Use when looking up {topic}.
---

# {name}: {title}

## When to Use

Use when:
- Looking up {topic}
- Need reference for {domain}
- Debugging {related} issues

---

## Quick Reference

<!-- Cheat sheet here -->

| Concept | Description |
|---------|-------------|
| Item 1 | Description 1 |
| Item 2 | Description 2 |

---

## Deep Dive

See `references/` for detailed documentation.

---

## References

- `references/<topic>.md` — Detailed guide
""",

    "meta": """---
name: {name}
description: {description}. Use when {triggers}.
---

# {name}: {title}

## When to Use

Use when:
- {trigger_1}
- {trigger_2}

---

## Architecture

```
dev/                    → Skills in development
    ↓ skill-deploy
syllabus/               → Public semi-packed artifacts
    ↓ skill-deploy
.agent/skills/          → Packaged skills
    ↓ colab-learn
~/.claude/skills/       → Platform paths
```

---

## Commands

### Primary Command

```bash
{name}
```

**What it does:**
1. Step 1
2. Step 2
3. Step 3

---

## Integration

Works with:
- `skill-deploy` — Package and deploy
- `colab-learn` — Cluster-wide sync
- `skills-validator` — Quality checks

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Failure |

---

## Scripts

- `scripts/<script>.py` — Main script
"""
}


def extract_project_context(project_dir: Path) -> dict:
    """Extract context from current project for skill generation."""
    context = {
        "name": project_dir.name,
        "description": "",
        "triggers": [],
        "commands": [],
        "paths": [],
        "domain": "general",
    }

    # Check for project files
    readme = project_dir / "README.md"
    claude_md = project_dir / "CLAUDE.md"
    agents_md = project_dir / "AGENTS.md"

    # Read available docs
    for doc in [claude_md, agents_md, readme]:
        if doc.exists():
            content = doc.read_text()

            # Extract title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match and context["name"] == project_dir.name:
                context["name"] = title_match.group(1).strip()

            # Extract description from first paragraph
            para_match = re.search(r'\n\n(.+?)(?:\n\n|\Z)', content, re.DOTALL)
            if para_match and not context["description"]:
                context["description"] = para_match.group(1).strip()[:200]

            # Extract commands (code blocks with bash/sh)
            cmd_matches = re.findall(r'```(?:bash|sh)\n(.+?)```', content, re.DOTALL)
            context["commands"].extend(cmd_matches[:5])

            # Extract paths
            path_matches = re.findall(r'`(/[^`]+)`', content)
            context["paths"].extend(list(set(path_matches))[:10])

            # Detect domain keywords
            keywords = {
                "docker": "containerization",
                "kubernetes": "orchestration",
                "terraform": "infrastructure",
                "ansible": "automation",
                "python": "python",
                "node": "javascript",
                "rust": "rust",
                "ruby": "ruby",
                "go ": "golang",
            }
            for kw, domain in keywords.items():
                if kw.lower() in content.lower():
                    context["domain"] = domain
                    break

    # Generate triggers from domain
    trigger_map = {
        "containerization": ["docker", "container", "image", "volume"],
        "orchestration": ["kubernetes", "k8s", "pod", "deployment"],
        "infrastructure": ["terraform", "infra", "resource", "plan"],
        "automation": ["ansible", "playbook", "inventory", "role"],
        "python": ["python", "pip", "venv", "pytest"],
        "javascript": ["node", "npm", "yarn", "javascript"],
        "rust": ["rust", "cargo", "rustc", "crate"],
        "ruby": ["ruby", "gem", "bundle", "rails"],
        "golang": ["go", "golang", "module", "package"],
    }
    context["triggers"] = trigger_map.get(context["domain"], ["project", "setup", "run"])

    return context


def create_skill(name: str, template: str = "dev", context: dict = None) -> Path:
    """Create a new skill directory with template."""
    skill_dir = DEV_DIR / name

    if skill_dir.exists():
        print(f"❌ Skill already exists: {skill_dir}")
        sys.exit(2)

    # Create directory structure
    skill_dir.mkdir(parents=True)
    (skill_dir / "scripts").mkdir()
    (skill_dir / "references").mkdir(exist_ok=True)

    # Prepare template variables
    if context:
        description = context.get("description", f"Skill for {name}")
        triggers = ", ".join(context.get("triggers", ["trigger"])[:3])
    else:
        description = f"Skill for {name}"
        triggers = "trigger 1, trigger 2"

    # Format title from name
    title = name.replace("-", " ").title()

    template_vars = {
        "name": name,
        "title": title,
        "description": description,
        "triggers": triggers,
        "trigger_1": context.get("triggers", ["trigger 1"])[0] if context else "trigger 1",
        "trigger_2": context.get("triggers", ["trigger 1", "trigger 2"])[1] if context and len(context.get("triggers", [])) > 1 else "trigger 2",
        "topic": name,
        "domain": context.get("domain", "general") if context else "general",
        "related": "related",
    }

    # Apply template
    template_content = TEMPLATES.get(template, TEMPLATES["dev"])
    skill_md_content = template_content.format(**template_vars)

    # Write SKILL.md
    (skill_dir / "SKILL.md").write_text(skill_md_content)

    return skill_dir


def run_validator(skill_path: Path) -> int:
    """Run skills-validator on a skill."""
    if not VALIDATOR.exists():
        print(f"⚠️  Validator not found at {VALIDATOR}")
        return 0  # Don't block if validator missing

    result = subprocess.run(
        ["python3", str(VALIDATOR), str(skill_path)],
        cwd=REPO_ROOT,
    )
    return result.returncode


def run_skill_deploy(skill_path: Path) -> bool:
    """Deploy skill using skill-deploy."""
    if not SKILL_DEPLOY.exists():
        print(f"⚠️  skill-deploy not found at {SKILL_DEPLOY}")
        return False

    result = subprocess.run(
        ["python3", str(SKILL_DEPLOY), str(skill_path)],
        cwd=REPO_ROOT,
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Create new skills for Co-lab cluster")
    parser.add_argument("name", help="Skill name (kebab-case)")
    parser.add_argument("--from-context", action="store_true", help="Extract skill from current directory")
    parser.add_argument("--template", choices=["ops", "dev", "reference", "meta"], default="dev", help="Skill template")
    parser.add_argument("--deploy", action="store_true", help="Deploy after creation")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    args = parser.parse_args()

    # Validate name format
    if not re.match(r'^[a-z][a-z0-9-]*$', args.name):
        print(f"❌ Invalid skill name: {args.name}")
        print("   Use lowercase letters, numbers, and hyphens only.")
        sys.exit(1)

    print(f"[colab-teach] Creating skill: {args.name}")
    print(f"[colab-teach] Template: {args.template}")

    # Extract context if requested
    context = None
    if args.from_context:
        current_dir = Path.cwd()
        print(f"[colab-teach] Extracting context from: {current_dir}")
        context = extract_project_context(current_dir)
        print(f"[colab-teach] Detected domain: {context['domain']}")

    # Create skill
    skill_dir = create_skill(args.name, args.template, context)
    print(f"[colab-teach] Created: {skill_dir}")
    print(f"  ├── SKILL.md")
    print(f"  ├── scripts/")
    print(f"  └── references/")

    # Validate
    if not args.no_validate:
        print(f"\n[colab-teach] Validating...")
        exit_code = run_validator(skill_dir)

        if exit_code == 1:
            print("❌ Validation failed. Fix issues before deploying.")
            sys.exit(1)
        elif exit_code == 2:
            print("⚠️  Validation passed with warnings.")
        else:
            print("✅ Validation passed.")

    # Deploy if requested
    if args.deploy:
        print(f"\n[colab-teach] Deploying...")
        if run_skill_deploy(skill_dir):
            print("✅ Skill deployed successfully!")
        else:
            print("❌ Deployment failed.")
            sys.exit(1)
    else:
        print(f"\n[colab-teach] Skill ready in dev/{args.name}/")
        print("   Next steps:")
        print(f"   1. Edit dev/{args.name}/SKILL.md")
        print(f"   2. Run: python3 dev/skill-deploy/scripts/skill_deploy.py dev/{args.name}")

    sys.exit(0)


if __name__ == "__main__":
    main()
