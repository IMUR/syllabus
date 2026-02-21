#!/usr/bin/env python3
"""
skill_deploy.py - Validate and deploy skills from dev/

Usage:
    skill_deploy.py dev/<skill-name>     # Deploy/update from dev/
    skill_deploy.py --all                # Deploy/update all skills in dev/
    skill_deploy.py --validate-only <path>
    skill_deploy.py --no-validate <path>

Exit codes:
    0 = success
    1 = validation failed
    2 = artifact packaging error
    3 = skills-sync failed
"""

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Set

# Detect monorepo root
if os.path.isdir("/Volumes/ops/prj/skills"):
    REPO_ROOT = Path("/Volumes/ops/prj/skills")
else:
    REPO_ROOT = Path("/mnt/ops/prj/skills")

DEV_DIR = REPO_ROOT / "dev"
SYLLABUS_DIR = REPO_ROOT / "syllabus"
AGENT_SKILLS = REPO_ROOT / ".agent" / "skills"
VALIDATOR = DEV_DIR / "skills-validator" / "scripts" / "validate_skill.py"
SKILLS_SYNC = REPO_ROOT / "skills-sync"

# Files to include in runtime deployment artifact (.agent/skills/)
RUNTIME_INCLUDE = {
    "SKILL.md",
    "scripts",
    "references",
    "examples",
    "assets",
    "resources",
    "LICENSE",
    "LICENSE.txt",
}

# Files to include in public publish artifact (syllabus/)
SYLLABUS_INCLUDE = set(RUNTIME_INCLUDE) | {
    "README.md",
    "CHANGELOG.md",
    "CHANGELOG",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
}

# Files to always exclude (even if listed in include profile)
COMMON_EXCLUDE = {
    "CLAUDE.md",
    "GEMINI.md",
    "AGENTS.md",
    ".git",
    ".gitignore",
    ".skillignore",
    ".archive",
    "docs",
    ".protext",
}


def run_validator(skill_path: Path) -> int:
    """Run skills-validator on a skill. Returns exit code."""
    if not VALIDATOR.exists():
        print(f"❌ Validator not found at {VALIDATOR}")
        return 1

    result = subprocess.run(
        ["python3", str(VALIDATOR), str(skill_path)],
        cwd=REPO_ROOT,
    )
    return result.returncode


def parse_ignore_file(skill_path: Path, filename: str) -> Set[str]:
    """Parse ignore file if it exists."""
    ignore_file = skill_path / filename
    if not ignore_file.exists():
        return set()

    patterns = set()  # type: Set[str]
    for line in ignore_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.add(line)
    return patterns


def is_ignored(name: str, ignore_patterns: Iterable[str]) -> bool:
    """Check if an item name matches any ignore pattern."""
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def package_skill(source: Path, target: Path, include: Set[str], extra_ignore: Set[str]) -> List[str]:
    """
    Package selected files from source to target.
    Returns list of copied top-level entries.
    """
    skillignore = parse_ignore_file(source, ".skillignore") | extra_ignore

    # Remove existing target to ensure clean sync
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    copied = []  # type: List[str]
    for item in source.iterdir():
        name = item.name

        if name in COMMON_EXCLUDE:
            continue

        # SKILL.md is mandatory and always copied if present.
        if name != "SKILL.md" and is_ignored(name, skillignore):
            continue

        if name in include:
            if item.is_dir():
                shutil.copytree(item, target / name)
            else:
                shutil.copy2(item, target / name)
            copied.append(name)

    return copied


def resolve_skill_path(raw_path: str) -> Path:
    """Resolve a skill path relative to repo root, preserving absolute paths."""
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def validate_source_path(skill_path: Path) -> Path:
    """Validate skill path and return its path relative to dev/."""
    if not skill_path.exists():
        print(f"❌ Skill not found: {skill_path}")
        sys.exit(1)

    if not skill_path.is_dir():
        print(f"❌ Not a directory: {skill_path}")
        sys.exit(1)

    if not (skill_path / "SKILL.md").exists():
        print(f"❌ No SKILL.md found in {skill_path}")
        sys.exit(1)

    try:
        relative = skill_path.relative_to(DEV_DIR.resolve())
    except ValueError:
        print(f"❌ Skill source must be inside dev/, got: {skill_path}")
        sys.exit(1)

    if len(relative.parts) != 1:
        print(f"❌ Skill path must be dev/<skill-name>, got: {skill_path}")
        sys.exit(1)

    return relative


def list_dev_skills() -> List[Path]:
    """List all top-level skill directories in dev/ that contain SKILL.md."""
    if not DEV_DIR.exists():
        return []

    skills = []  # type: List[Path]
    for item in sorted(DEV_DIR.iterdir(), key=lambda p: p.name):
        if item.is_dir() and (item / "SKILL.md").exists():
            skills.append(item.resolve())
    return skills


def package_artifacts(skill_path: Path) -> int:
    """Package syllabus and runtime artifacts for one skill. Returns exit-code style status."""
    relative_path = validate_source_path(skill_path)
    skill_name = relative_path.parts[0]
    syllabus_target = SYLLABUS_DIR / skill_name
    runtime_target = AGENT_SKILLS / skill_name

    runtime_exists = (runtime_target / "SKILL.md").exists()
    syllabus_exists = (syllabus_target / "SKILL.md").exists()
    existing_deployment = runtime_exists or syllabus_exists

    if existing_deployment:
        print("[skill-deploy] Existing deployment found, running update flow.")
    else:
        print("[skill-deploy] No existing deployment found, running first deploy flow.")

    print(f"[skill-deploy] Packaging public artifact to {syllabus_target}...")
    syllabus_ignore = parse_ignore_file(skill_path, ".syllabusignore")
    syllabus_copied = package_skill(
        skill_path,
        syllabus_target,
        include=SYLLABUS_INCLUDE,
        extra_ignore=syllabus_ignore,
    )
    if "SKILL.md" not in syllabus_copied:
        print("❌ Syllabus packaging failed - SKILL.md was not copied")
        return 2
    syllabus_action = "Updated" if syllabus_exists else "Created"
    print(f"  ✅ {syllabus_action} syllabus/{skill_name}/")

    print(f"[skill-deploy] Packaging runtime artifact to {runtime_target}...")
    runtime_copied = package_skill(
        skill_path,
        runtime_target,
        include=RUNTIME_INCLUDE,
        extra_ignore=set(),
    )
    if "SKILL.md" not in runtime_copied:
        print("❌ Runtime packaging failed - SKILL.md was not copied")
        return 2
    runtime_action = "Updated" if runtime_exists else "Created"
    print(f"  ✅ {runtime_action} .agent/skills/{skill_name}/")
    return 0


def run_skills_sync_push() -> int:
    """Run skills-sync push and return exit-code style status."""
    print("[skill-deploy] Running skills-sync push...")
    if not SKILLS_SYNC.exists():
        print("❌ skills-sync not found")
        return 3

    result = subprocess.run([str(SKILLS_SYNC), "push"], cwd=REPO_ROOT)
    if result.returncode != 0:
        print("❌ skills-sync failed")
        return 3
    return 0


def main():
    parser = argparse.ArgumentParser(description="Deploy skill artifacts from dev/")
    parser.add_argument("skill_path", nargs="?", help="Path to skill source (dev/<skill-name>)")
    parser.add_argument("--all", action="store_true", help="Deploy/update all skills in dev/")
    parser.add_argument("--validate-only", action="store_true", help="Validate without deploying")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation (dangerous)")
    args = parser.parse_args()

    if args.all and args.skill_path:
        parser.error("Provide either skill_path or --all, not both.")
    if not args.all and not args.skill_path:
        parser.error("skill_path is required unless --all is set.")

    SYLLABUS_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_SKILLS.mkdir(parents=True, exist_ok=True)

    if args.all:
        skill_paths = list_dev_skills()
        if not skill_paths:
            print("❌ No skill sources found in dev/")
            sys.exit(1)

        print(f"[skill-deploy] Found {len(skill_paths)} skills in dev/.")

        failures = []  # type: List[str]
        warnings = []  # type: List[str]

        if not args.no_validate:
            for path in skill_paths:
                print(f"[skill-deploy] Validating {path}...")
                exit_code = run_validator(path)
                if exit_code == 1:
                    print(f"❌ Validation failed: {path.name}")
                    failures.append(path.name)
                elif exit_code == 2:
                    print(f"⚠️  Validation passed with warnings: {path.name}")
                    warnings.append(path.name)
                else:
                    print(f"✅ Validation passed: {path.name}")

            if failures:
                print(
                    f"\n❌ Validation failed for {len(failures)} skill(s): {', '.join(failures)}"
                )
                print("   Fix failures and rerun skill-deploy --all.")
                sys.exit(1)
        else:
            print("[skill-deploy] --no-validate set, skipping validation for all skills.")

        if args.validate_only:
            if warnings:
                print(
                    f"✅ Validate-only mode complete with warnings on {len(warnings)} skill(s)."
                )
            else:
                print("✅ Validate-only mode complete for all skills.")
            sys.exit(0)

        for path in skill_paths:
            print(f"\n[skill-deploy] Deploying {path.name}...")
            package_status = package_artifacts(path)
            if package_status != 0:
                sys.exit(package_status)

        sync_status = run_skills_sync_push()
        if sync_status != 0:
            sys.exit(sync_status)

        print(f"\n✅ Deployed {len(skill_paths)} skills successfully (syllabus + runtime).")
        sys.exit(0)

    skill_path = resolve_skill_path(args.skill_path)
    skill_name = validate_source_path(skill_path).parts[0]

    print(f"[skill-deploy] Validating {skill_path}...")
    if (SYLLABUS_DIR / skill_name / "SKILL.md").exists() or (
        AGENT_SKILLS / skill_name / "SKILL.md"
    ).exists():
        print("[skill-deploy] Existing deployment found, running update flow.")
    else:
        print("[skill-deploy] No existing deployment found, running first deploy flow.")

    # Run validation unless --no-validate
    if not args.no_validate:
        exit_code = run_validator(skill_path)
        if exit_code == 1:
            print("❌ Validation failed. Fix issues before deploying.")
            sys.exit(1)
        elif exit_code == 2:
            print("⚠️  Validation passed with warnings.")
        else:
            print("✅ Validation passed.")

    if args.validate_only:
        print("✅ Validate-only mode, exiting.")
        sys.exit(0)

    package_status = package_artifacts(skill_path)
    if package_status != 0:
        sys.exit(package_status)

    sync_status = run_skills_sync_push()
    if sync_status != 0:
        sys.exit(sync_status)

    print(f"\n✅ Deployed {skill_name} successfully (syllabus + runtime).")
    sys.exit(0)


if __name__ == "__main__":
    main()
