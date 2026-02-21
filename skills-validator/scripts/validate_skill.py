#!/usr/bin/env python3
"""
validate_skill.py - Comprehensive skill validator

Validates a single skill directory against the 44-point cross-platform
skills checklist. Outputs PASS/WARN/FAIL/MANUAL per check.

Usage:
    python validate_skill.py <skill-path> [--json] [--strict] [--category=NAME]

Exit codes:
    0 = all checks pass
    1 = at least one FAIL
    2 = no FAILs but at least one WARN

Requires Python 3.8+. No external packages needed (PyYAML optional).
"""

import argparse
import json
import os
import re
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_FRONTMATTER_FIELDS = {
    # Base standard
    "name", "description", "license", "compatibility", "allowed-tools", "metadata",
    # Claude Code / Cursor extensions
    "argument-hint", "disable-model-invocation", "user-invocable",
    "model", "context", "agent", "hooks",
}
ALLOWED_TOP_LEVEL = {"SKILL.md", "scripts", "references", "resources", "examples", "assets", "agents", "LICENSE", "LICENSE.txt"}
AUXILIARY_DOCS = {
    "README.md", "README", "CHANGELOG.md", "CHANGELOG",
    "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md", "CONTRIBUTING.md",
    "INSTALL.md", "SETUP.md", "USAGE.md",
}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_SKILL_LINES = 500

CATEGORIES = {
    "C1": "SKILL.md Core",
    "C2": "File Structure",
    "C3": "Frontmatter & Metadata",
    "C4": "Trigger & Discovery",
    "C5": "Context & Token Efficiency",
    "C6": "Cross-Platform Portability",
}

# ---------------------------------------------------------------------------
# YAML Parsing (with PyYAML fallback)
# ---------------------------------------------------------------------------

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def parse_yaml_fallback(text: str) -> dict:
    """Regex-based YAML parser for basic frontmatter. Handles folded scalars."""
    result = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("#") or not line.strip():
            i += 1
            continue

        if not line[0].isspace() and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            # Folded scalar (description: > or description: |)
            if value in (">", "|", ">-", "|-"):
                parts = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                    if lines[i].strip():
                        parts.append(lines[i].strip())
                    i += 1
                result[key] = " ".join(parts)
                continue

            # Inline list: [item1, item2]
            if value.startswith("[") and value.endswith("]"):
                items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                result[key] = items
            elif value:
                # Strip quotes
                result[key] = value.strip("'\"")
            else:
                # Nested mapping or empty
                nested = {}
                i += 1
                while i < len(lines) and lines[i].startswith("  "):
                    nline = lines[i]
                    if ":" in nline:
                        nk, _, nv = nline.partition(":")
                        nk = nk.strip()
                        nv = nv.strip().strip("'\"")
                        nested[nk] = nv
                    i += 1
                result[key] = nested if nested else ""
                continue
        i += 1
    return result


def parse_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    """Extract YAML frontmatter and body from SKILL.md content.

    Returns (frontmatter_dict_or_None, body_text).
    """
    if not content.startswith("---"):
        return None, content

    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return None, content

    fm_text = match.group(1)
    body = match.group(2)

    if YAML_AVAILABLE:
        try:
            fm = yaml.safe_load(fm_text)
            if isinstance(fm, dict):
                return fm, body
        except Exception:
            pass

    fm = parse_yaml_fallback(fm_text)
    return fm if fm else None, body


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_code_blocks(text: str) -> Tuple[str, List[str]]:
    """Split text into non-code content and code blocks."""
    blocks = []
    outside = []
    in_block = False
    current_block = []

    for line in text.split("\n"):
        if re.match(r"^```", line):
            if in_block:
                blocks.append("\n".join(current_block))
                current_block = []
                in_block = False
            else:
                in_block = True
            continue
        if in_block:
            current_block.append(line)
        else:
            outside.append(line)

    return "\n".join(outside), blocks


def extract_markdown_links(text: str) -> List[Tuple[str, str]]:
    """Extract [label](path) links from markdown, excluding URLs."""
    links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text)
    return [(label, path) for label, path in links
            if not path.startswith("http") and not path.startswith("#")]


def count_tokens_rough(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


# ---------------------------------------------------------------------------
# Check Result
# ---------------------------------------------------------------------------

class CheckResult:
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    MANUAL = "MANUAL"
    SKIP = "SKIP"

    def __init__(self, check_id: str, category: str, description: str,
                 status: str, message: str = ""):
        self.check_id = check_id
        self.category = category
        self.description = description
        self.status = status
        self.message = message

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "description": self.description,
            "status": self.status,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Check Functions: C1 - SKILL.md Core
# ---------------------------------------------------------------------------

def c1_checks(skill_path: Path, content: str, fm: Optional[dict], body: str) -> List[CheckResult]:
    results = []

    # C1.1 SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        results.append(CheckResult("C1.1", "C1", "SKILL.md exists", CheckResult.PASS))
    else:
        results.append(CheckResult("C1.1", "C1", "SKILL.md exists", CheckResult.FAIL,
                                   "SKILL.md not found (case-sensitive)"))
        return results  # Can't continue without SKILL.md

    # C1.2 YAML frontmatter parses
    if fm is not None:
        results.append(CheckResult("C1.2", "C1", "YAML frontmatter parses", CheckResult.PASS))
    else:
        results.append(CheckResult("C1.2", "C1", "YAML frontmatter parses", CheckResult.FAIL,
                                   "Missing or malformed YAML frontmatter"))
        return results

    # C1.3 name format (name is optional in Antigravity — defaults to dirname)
    name = fm.get("name", "")
    if not name:
        results.append(CheckResult("C1.3", "C1", "name: hyphen-case, <=64 chars", CheckResult.WARN,
                                   "No 'name' field; will default to directory name"))
    elif not isinstance(name, str):
        results.append(CheckResult("C1.3", "C1", "name: hyphen-case, <=64 chars", CheckResult.FAIL,
                                   f"name must be string, got {type(name).__name__}"))
    elif not NAME_PATTERN.match(name):
        results.append(CheckResult("C1.3", "C1", "name: hyphen-case, <=64 chars", CheckResult.FAIL,
                                   f"'{name}' is not valid hyphen-case (a-z0-9 and hyphens)"))
    elif len(name) > MAX_NAME_LENGTH:
        results.append(CheckResult("C1.3", "C1", "name: hyphen-case, <=64 chars", CheckResult.FAIL,
                                   f"name is {len(name)} chars (max {MAX_NAME_LENGTH})"))
    else:
        results.append(CheckResult("C1.3", "C1", "name: hyphen-case, <=64 chars", CheckResult.PASS))

    # C1.4 description format
    desc = fm.get("description", "")
    if not desc:
        results.append(CheckResult("C1.4", "C1", "description: <=1024 chars, no <>",
                                   CheckResult.FAIL, "Missing 'description' field"))
    elif not isinstance(desc, str):
        results.append(CheckResult("C1.4", "C1", "description: <=1024 chars, no <>",
                                   CheckResult.FAIL, f"description must be string, got {type(desc).__name__}"))
    elif "<" in desc or ">" in desc:
        results.append(CheckResult("C1.4", "C1", "description: <=1024 chars, no <>",
                                   CheckResult.FAIL, "Angle brackets found in description"))
    elif len(desc) > MAX_DESCRIPTION_LENGTH:
        results.append(CheckResult("C1.4", "C1", "description: <=1024 chars, no <>",
                                   CheckResult.FAIL, f"description is {len(desc)} chars (max {MAX_DESCRIPTION_LENGTH})"))
    else:
        results.append(CheckResult("C1.4", "C1", "description: <=1024 chars, no <>", CheckResult.PASS))

    # C1.5 Description includes what + when (heuristic)
    desc_str = str(desc).lower() if desc else ""
    has_numbered = bool(re.search(r"\(\d\)", desc_str))
    has_use_when = "use when" in desc_str or "use this" in desc_str or "invoke" in desc_str
    if has_numbered or has_use_when:
        results.append(CheckResult("C1.5", "C1", "Description includes what + when",
                                   CheckResult.PASS))
    else:
        results.append(CheckResult("C1.5", "C1", "Description includes what + when",
                                   CheckResult.WARN, "No numbered use cases or 'use when' found"))

    # C1.6 Body uses imperative form (heuristic)
    non_code, _ = extract_code_blocks(body)
    sentences = re.findall(r"^[A-Z][a-z]+ing\s", non_code, re.MULTILINE)
    total_starts = re.findall(r"^[A-Z]", non_code, re.MULTILINE)
    gerund_ratio = len(sentences) / max(len(total_starts), 1)
    if gerund_ratio < 0.3:
        results.append(CheckResult("C1.6", "C1", "Body uses imperative form", CheckResult.PASS))
    else:
        results.append(CheckResult("C1.6", "C1", "Body uses imperative form", CheckResult.WARN,
                                   f"High gerund ratio ({gerund_ratio:.0%}); prefer imperative form"))

    # C1.7 Body under 500 lines
    line_count = len(content.split("\n"))
    if line_count <= MAX_SKILL_LINES:
        results.append(CheckResult("C1.7", "C1", f"Body under {MAX_SKILL_LINES} lines",
                                   CheckResult.PASS, f"{line_count} lines"))
    else:
        results.append(CheckResult("C1.7", "C1", f"Body under {MAX_SKILL_LINES} lines",
                                   CheckResult.FAIL, f"{line_count} lines (max {MAX_SKILL_LINES})"))

    return results


# ---------------------------------------------------------------------------
# Check Functions: C2 - File Structure
# ---------------------------------------------------------------------------

def c2_checks(skill_path: Path, fm: Optional[dict], content: str) -> List[CheckResult]:
    results = []

    # C2.1 Directory name matches frontmatter name
    dirname = skill_path.name
    fm_name = fm.get("name", "") if fm else ""
    if fm_name and dirname == fm_name:
        results.append(CheckResult("C2.1", "C2", "Directory name matches frontmatter name",
                                   CheckResult.PASS))
    elif fm_name:
        results.append(CheckResult("C2.1", "C2", "Directory name matches frontmatter name",
                                   CheckResult.WARN, f"dir='{dirname}' vs name='{fm_name}'"))
    else:
        results.append(CheckResult("C2.1", "C2", "Directory name matches frontmatter name",
                                   CheckResult.SKIP, "No name in frontmatter"))

    # C2.2 Only allowed dirs/files
    unexpected = []
    for item in skill_path.iterdir():
        name = item.name
        if name.startswith("."):
            continue  # Skip hidden files (git, etc.)
        if name not in ALLOWED_TOP_LEVEL:
            unexpected.append(name)
    if not unexpected:
        results.append(CheckResult("C2.2", "C2", "Only allowed dirs/files",
                                   CheckResult.PASS))
    else:
        results.append(CheckResult("C2.2", "C2", "Only allowed dirs/files",
                                   CheckResult.WARN, f"Unexpected: {', '.join(sorted(unexpected))}"))

    # C2.3 No auxiliary docs
    found_aux = [f for f in AUXILIARY_DOCS if (skill_path / f).exists()]
    if not found_aux:
        results.append(CheckResult("C2.3", "C2", "No auxiliary docs", CheckResult.PASS))
    else:
        results.append(CheckResult("C2.3", "C2", "No auxiliary docs", CheckResult.FAIL,
                                   f"Found: {', '.join(found_aux)}"))

    # C2.4 Scripts executable
    scripts_dir = skill_path / "scripts"
    if scripts_dir.is_dir():
        non_exec = []
        for f in scripts_dir.iterdir():
            if f.is_file() and f.suffix in (".py", ".sh", ".bash"):
                if not os.access(f, os.X_OK):
                    non_exec.append(f.name)
        if not non_exec:
            results.append(CheckResult("C2.4", "C2", "Scripts executable", CheckResult.PASS))
        else:
            results.append(CheckResult("C2.4", "C2", "Scripts executable", CheckResult.FAIL,
                                       f"Not executable: {', '.join(non_exec)}"))
    else:
        results.append(CheckResult("C2.4", "C2", "Scripts executable", CheckResult.SKIP,
                                   "No scripts/ directory"))

    # C2.5 All paths use forward slashes (outside code blocks)
    non_code, _ = extract_code_blocks(content)
    backslash_paths = re.findall(r"[a-zA-Z]\\[a-zA-Z]", non_code)
    if not backslash_paths:
        results.append(CheckResult("C2.5", "C2", "All paths use forward slashes", CheckResult.PASS))
    else:
        results.append(CheckResult("C2.5", "C2", "All paths use forward slashes", CheckResult.FAIL,
                                   f"Found backslash paths: {backslash_paths[:3]}"))

    # C2.6 All paths relative (outside code blocks)
    abs_paths = re.findall(r"(?<!\w)/(?:etc|usr|home|root|mnt|opt|var|tmp)/\S+", non_code)
    if not abs_paths:
        results.append(CheckResult("C2.6", "C2", "All paths relative", CheckResult.PASS))
    else:
        results.append(CheckResult("C2.6", "C2", "All paths relative", CheckResult.WARN,
                                   f"Absolute paths: {abs_paths[:3]}"))

    # C2.7 References depth + TOC for large files
    refs_dir = skill_path / "references"
    if refs_dir.is_dir():
        issues = []
        for f in refs_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(refs_dir)
                # Check depth
                if len(rel.parts) > 1:
                    issues.append(f"Nested: {rel}")
                # Check TOC for >100 line files
                if f.suffix == ".md":
                    lines = f.read_text().split("\n")
                    if len(lines) > 100:
                        headings = [l for l in lines[:20] if l.startswith("#")]
                        has_toc = any("table of contents" in l.lower() or
                                      re.match(r"\d+\.\s+\[", l) for l in lines[:30])
                        if not has_toc and len(headings) < 2:
                            issues.append(f"{rel}: >100 lines, no TOC/headings in first 20 lines")
        if not issues:
            results.append(CheckResult("C2.7", "C2", "References structure", CheckResult.PASS))
        else:
            results.append(CheckResult("C2.7", "C2", "References structure", CheckResult.WARN,
                                       "; ".join(issues[:3])))
    else:
        results.append(CheckResult("C2.7", "C2", "References structure", CheckResult.SKIP,
                                   "No references/ directory"))

    return results


# ---------------------------------------------------------------------------
# Check Functions: C3 - Frontmatter & Metadata
# ---------------------------------------------------------------------------

def c3_checks(skill_path: Path, fm: Optional[dict], body: str) -> List[CheckResult]:
    results = []
    if not fm:
        return [CheckResult("C3.1", "C3", "Allowed frontmatter properties",
                            CheckResult.SKIP, "No frontmatter to check")]

    # C3.1 Only allowed frontmatter properties
    unexpected = set(fm.keys()) - ALLOWED_FRONTMATTER_FIELDS
    if not unexpected:
        results.append(CheckResult("C3.1", "C3", "Allowed frontmatter properties", CheckResult.PASS))
    else:
        results.append(CheckResult("C3.1", "C3", "Allowed frontmatter properties", CheckResult.FAIL,
                                   f"Unexpected: {', '.join(sorted(unexpected))}"))

    # C3.2 Referenced files exist (outside code blocks only)
    non_code, _ = extract_code_blocks(body)
    links = extract_markdown_links(non_code)
    missing = []
    for label, path in links:
        ref_path = skill_path / path
        if not ref_path.exists():
            missing.append(path)
    if not missing:
        results.append(CheckResult("C3.2", "C3", "Referenced files exist", CheckResult.PASS,
                                   f"{len(links)} references checked"))
    else:
        results.append(CheckResult("C3.2", "C3", "Referenced files exist", CheckResult.FAIL,
                                   f"Missing: {', '.join(missing[:5])}"))

    # C3.3 No broken relative path references (outside code blocks only)
    inline_paths = re.findall(r"`((?:scripts|references|assets)/[^`]+)`", non_code)
    broken = [p for p in inline_paths if not (skill_path / p).exists()]
    if not broken:
        results.append(CheckResult("C3.3", "C3", "No broken path references", CheckResult.PASS,
                                   f"{len(inline_paths)} inline paths checked"))
    else:
        results.append(CheckResult("C3.3", "C3", "No broken path references", CheckResult.WARN,
                                   f"Unresolved: {', '.join(broken[:5])} (may be illustrative)"))

    # C3.4 References >100 lines have headings
    refs_dir = skill_path / "references"
    if refs_dir.is_dir():
        issues = []
        for f in refs_dir.iterdir():
            if f.is_file() and f.suffix == ".md":
                text = f.read_text()
                lines = text.split("\n")
                if len(lines) > 100:
                    headings = [l for l in lines if l.startswith("## ")]
                    if len(headings) < 3:
                        issues.append(f"{f.name}: {len(lines)} lines, only {len(headings)} headings")
        if not issues:
            results.append(CheckResult("C3.4", "C3", "Large references have headings", CheckResult.PASS))
        else:
            results.append(CheckResult("C3.4", "C3", "Large references have headings", CheckResult.WARN,
                                       "; ".join(issues)))
    else:
        results.append(CheckResult("C3.4", "C3", "Large references have headings", CheckResult.SKIP))

    # C3.5 Description is primary trigger (heuristic)
    desc = str(fm.get("description", "")).lower()
    desc_words = len(desc.split())
    if desc_words >= 15:
        results.append(CheckResult("C3.5", "C3", "Description is primary trigger", CheckResult.PASS,
                                   f"{desc_words} words"))
    else:
        results.append(CheckResult("C3.5", "C3", "Description is primary trigger", CheckResult.WARN,
                                   f"Only {desc_words} words; may not trigger reliably"))

    # C3.6 Triggers in description, not body only
    body_lower = body.lower()
    has_body_trigger = bool(re.search(r"##\s*(when to use|use this skill when)", body_lower))
    if not has_body_trigger:
        results.append(CheckResult("C3.6", "C3", "Triggers in description, not body",
                                   CheckResult.PASS))
    else:
        results.append(CheckResult("C3.6", "C3", "Triggers in description, not body",
                                   CheckResult.WARN,
                                   "Body has 'When to Use' section; triggers belong in description"))

    return results


# ---------------------------------------------------------------------------
# Check Functions: C4 - Trigger & Discovery
# ---------------------------------------------------------------------------

def c4_checks(skill_path: Path, fm: Optional[dict], body: str) -> List[CheckResult]:
    results = []
    desc = str(fm.get("description", "")).lower() if fm else ""

    # C4.1 Description has auto-detection keywords
    word_count = len(set(desc.split()))
    if word_count >= 10:
        results.append(CheckResult("C4.1", "C4", "Description has keywords", CheckResult.PASS,
                                   f"{word_count} unique words"))
    else:
        results.append(CheckResult("C4.1", "C4", "Description has keywords", CheckResult.WARN,
                                   f"Only {word_count} unique words; may not auto-detect well"))

    # C4.2 Natural language alternatives documented
    non_code, _ = extract_code_blocks(body)
    nl_patterns = ["natural language", "alternatively", "you can say",
                   "you can also say", "cross-platform"]
    has_nl = any(p in non_code.lower() for p in nl_patterns)
    # Also check for quoted phrases as NL examples
    quoted = re.findall(r'"[^"]{10,}"', non_code)
    if has_nl or len(quoted) >= 2:
        results.append(CheckResult("C4.2", "C4", "Natural language alternatives", CheckResult.PASS))
    else:
        results.append(CheckResult("C4.2", "C4", "Natural language alternatives", CheckResult.WARN,
                                   "No natural language invocation examples found"))

    # C4.3 Not slash-command-only trigger
    slash_refs = re.findall(r"/[a-z][\w-]+", body)
    has_non_slash = has_nl or len(quoted) >= 1 or "natural language" in non_code.lower()
    if not slash_refs or has_non_slash:
        results.append(CheckResult("C4.3", "C4", "Not slash-command-only trigger", CheckResult.PASS))
    else:
        results.append(CheckResult("C4.3", "C4", "Not slash-command-only trigger", CheckResult.WARN,
                                   "Only slash commands found; add natural language alternatives"))

    # C4.4 Body has concrete examples (code blocks)
    _, code_blocks = extract_code_blocks(body)
    if len(code_blocks) >= 1:
        results.append(CheckResult("C4.4", "C4", "Body has concrete examples", CheckResult.PASS,
                                   f"{len(code_blocks)} code blocks"))
    else:
        results.append(CheckResult("C4.4", "C4", "Body has concrete examples", CheckResult.WARN,
                                   "No code blocks found; add concrete examples"))

    # C4.5 Concise opening section
    # Check text between first H1/H2 and second heading
    sections = re.split(r"\n##?\s+", body)
    if len(sections) >= 2:
        opening = sections[1] if sections[0].strip() == "" else sections[0]
        opening_lines = len([l for l in opening.split("\n") if l.strip()])
        if opening_lines <= 5:
            results.append(CheckResult("C4.5", "C4", "Concise opening section", CheckResult.PASS,
                                       f"{opening_lines} lines"))
        else:
            results.append(CheckResult("C4.5", "C4", "Concise opening section", CheckResult.WARN,
                                       f"{opening_lines} lines; consider condensing"))
    else:
        results.append(CheckResult("C4.5", "C4", "Concise opening section", CheckResult.SKIP))

    # C4.6 Dependencies listed explicitly
    non_code_lower = non_code.lower()
    has_deps = any(kw in non_code_lower for kw in
                   ["requires", "dependencies", "python 3", "node", "pip install",
                    "npm install", "no external", "no dependencies"])
    scripts_dir_exists = (skill_path / "scripts").is_dir()
    if has_deps or not scripts_dir_exists:
        results.append(CheckResult("C4.6", "C4", "Dependencies listed", CheckResult.PASS))
    else:
        results.append(CheckResult("C4.6", "C4", "Dependencies listed", CheckResult.WARN,
                                   "No dependency information found"))

    # C4.7 Standard body sections (Antigravity ecosystem convention)
    has_use = bool(re.search(r"##\s+Use this skill when", body, re.IGNORECASE))
    has_donot = bool(re.search(r"##\s+Do not use", body, re.IGNORECASE))
    has_instructions = bool(re.search(r"##\s+Instructions", body, re.IGNORECASE))
    sections_found = sum([has_use, has_donot, has_instructions])
    if sections_found == 3:
        results.append(CheckResult("C4.7", "C4", "Standard body sections", CheckResult.PASS,
                                   "Has: Use this skill when, Do not use, Instructions"))
    elif sections_found > 0:
        results.append(CheckResult("C4.7", "C4", "Standard body sections", CheckResult.WARN,
                                   f"Partial: {sections_found}/3 standard sections found"))
    else:
        results.append(CheckResult("C4.7", "C4", "Standard body sections", CheckResult.WARN,
                                   "No standard sections (Use this skill when / Do not use / Instructions)"))

    return results


# ---------------------------------------------------------------------------
# Check Functions: C5 - Context & Token Efficiency
# ---------------------------------------------------------------------------

def c5_checks(skill_path: Path, body: str, content: str) -> List[CheckResult]:
    results = []

    # C5.1 Token budget estimate
    total_tokens = count_tokens_rough(content)
    ref_tokens = 0
    refs_dir = skill_path / "references"
    if refs_dir.is_dir():
        for f in refs_dir.rglob("*.md"):
            ref_tokens += count_tokens_rough(f.read_text())

    body_tokens = count_tokens_rough(body)
    if body_tokens <= 5000:
        results.append(CheckResult("C5.1", "C5", "Token budget estimate", CheckResult.PASS,
                                   f"SKILL.md ~{total_tokens} tokens, body ~{body_tokens}, refs ~{ref_tokens}"))
    else:
        results.append(CheckResult("C5.1", "C5", "Token budget estimate", CheckResult.WARN,
                                   f"Body ~{body_tokens} tokens (target <5000); refs ~{ref_tokens}"))

    # C5.2-C5.8 Manual checks
    manual_items = [
        ("C5.2", "Each paragraph justifies its token cost"),
        ("C5.3", "Avoids explaining common knowledge"),
        ("C5.4", "Prefers examples over verbose explanations"),
        ("C5.5", "No excessive options (pick one, be decisive)"),
        ("C5.6", "Embeds conversation-relevant context only"),
        ("C5.7", "Body self-contained for common use cases"),
        ("C5.8", "Few-shot patterns where applicable"),
    ]
    for cid, desc in manual_items:
        results.append(CheckResult(cid, "C5", desc, CheckResult.MANUAL))

    return results


# ---------------------------------------------------------------------------
# Check Functions: C6 - Cross-Platform Portability
# ---------------------------------------------------------------------------

def c6_checks(skill_path: Path, fm: Optional[dict], body: str) -> List[CheckResult]:
    results = []

    # C6.1 Markdown-only instructions
    skill_md = skill_path / "SKILL.md"
    if skill_md.suffix == ".md":
        results.append(CheckResult("C6.1", "C6", "Markdown-only instructions", CheckResult.PASS))
    else:
        results.append(CheckResult("C6.1", "C6", "Markdown-only instructions", CheckResult.FAIL))

    # C6.2 Forward slashes (references C2.5)
    results.append(CheckResult("C6.2", "C6", "Forward slashes only", CheckResult.SKIP,
                               "See C2.5"))

    # C6.3 Relative paths (references C2.6)
    results.append(CheckResult("C6.3", "C6", "Relative paths only", CheckResult.SKIP,
                               "See C2.6"))

    # C6.4 No hard platform dependencies
    non_code, _ = extract_code_blocks(body)
    platform_deps = re.findall(
        r"(?:only works on|requires? (?:mac|windows|linux)|platform-specific)",
        non_code, re.IGNORECASE)
    if not platform_deps:
        results.append(CheckResult("C6.4", "C6", "No hard platform dependencies", CheckResult.PASS))
    else:
        results.append(CheckResult("C6.4", "C6", "No hard platform dependencies", CheckResult.WARN,
                                   f"Platform-specific mentions: {platform_deps[:3]}"))

    # C6.5-C6.9 Manual checks
    manual_items = [
        ("C6.5", "Works as standalone Markdown document"),
        ("C6.6", "Scripts have manual equivalents documented"),
        ("C6.7", "Cross-platform testing completed"),
        ("C6.8", "Scripts tested by actually running them"),
        ("C6.9", "Extractable into platform companion files"),
    ]
    for cid, desc in manual_items:
        results.append(CheckResult(cid, "C6", desc, CheckResult.MANUAL))

    return results


# ---------------------------------------------------------------------------
# Validation Report
# ---------------------------------------------------------------------------

class ValidationReport:
    def __init__(self, skill_path: str, results: List[CheckResult]):
        self.skill_path = skill_path
        self.results = results
        self.timestamp = datetime.now().isoformat(timespec="seconds")

    def summary(self) -> Dict[str, int]:
        counts = {"pass": 0, "warn": 0, "fail": 0, "manual": 0, "skip": 0}
        for r in self.results:
            key = r.status.lower()
            counts[key] = counts.get(key, 0) + 1
        counts["total"] = len(self.results)
        return counts

    def exit_code(self, strict: bool = False) -> int:
        s = self.summary()
        if s["fail"] > 0:
            return 1
        if strict and s["warn"] > 0:
            return 1
        if s["warn"] > 0:
            return 2
        return 0

    def format_text(self, strict: bool = False) -> str:
        lines = []
        lines.append(f"Skills Validator: {self.skill_path}")
        lines.append("=" * 58)
        lines.append("")

        # Group by category
        by_cat = {}
        for r in self.results:
            by_cat.setdefault(r.category, []).append(r)

        manual_items = []

        for cat_id in sorted(by_cat.keys()):
            cat_name = CATEGORIES.get(cat_id, cat_id)
            cat_results = by_cat[cat_id]
            active = [r for r in cat_results if r.status != CheckResult.MANUAL]
            manuals = [r for r in cat_results if r.status == CheckResult.MANUAL]
            manual_items.extend(manuals)

            lines.append(f"{cat_name} ({len(cat_results)} checks)")
            for r in active:
                status = r.status
                if strict and status == CheckResult.WARN:
                    status = CheckResult.FAIL
                tag = f"[{status:4s}]"
                msg = f"  {tag} {r.check_id}  {r.description}"
                if r.message:
                    msg += f" ({r.message})"
                lines.append(msg)
            lines.append("")

        if manual_items:
            lines.append("Manual Review Required")
            for r in manual_items:
                lines.append(f"  [ ] {r.check_id}  {r.description}")
            lines.append("")

        lines.append("=" * 58)
        s = self.summary()
        if strict:
            effective_fail = s["fail"] + s["warn"]
            lines.append(
                f"Summary: {s['pass']} PASS | {effective_fail} FAIL (strict) | "
                f"{s['manual']} MANUAL | {s['skip']} SKIP"
            )
        else:
            lines.append(
                f"Summary: {s['pass']} PASS | {s['warn']} WARN | {s['fail']} FAIL | "
                f"{s['manual']} MANUAL | {s['skip']} SKIP"
            )
        ec = self.exit_code(strict)
        result_label = {0: "PASS", 1: "FAIL", 2: "WARN"}[ec]
        lines.append(f"Result: {result_label} (exit code {ec})")

        return "\n".join(lines)

    def format_json(self, strict: bool = False) -> str:
        return json.dumps({
            "skill_path": self.skill_path,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary(),
            "exit_code": self.exit_code(strict),
            "strict": strict,
        }, indent=2)


# ---------------------------------------------------------------------------
# Main Validator
# ---------------------------------------------------------------------------

def validate_skill(skill_path: Path, categories: Optional[List[str]] = None) -> ValidationReport:
    """Run all checks on a skill directory."""
    results = []
    skill_md = skill_path / "SKILL.md"

    # Read content
    content = ""
    fm = None
    body = ""
    if skill_md.exists():
        content = skill_md.read_text()
        fm, body = parse_frontmatter(content)

    # Run check categories
    cat_funcs = {
        "C1": lambda: c1_checks(skill_path, content, fm, body),
        "C2": lambda: c2_checks(skill_path, fm, content),
        "C3": lambda: c3_checks(skill_path, fm, body),
        "C4": lambda: c4_checks(skill_path, fm, body),
        "C5": lambda: c5_checks(skill_path, body, content),
        "C6": lambda: c6_checks(skill_path, fm, body),
    }

    for cat_id, func in cat_funcs.items():
        if categories and cat_id not in categories:
            continue
        try:
            results.extend(func())
        except Exception as e:
            results.append(CheckResult(f"{cat_id}.ERR", cat_id,
                                       f"Category {cat_id} error", CheckResult.FAIL,
                                       str(e)))

    return ValidationReport(str(skill_path), results)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate an AI agent skill against the 44-point cross-platform checklist.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit codes: 0=pass, 1=fail, 2=warn-only"
    )
    parser.add_argument("skill_path", type=str,
                        help="Path to the skill directory to validate")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output as JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Promote all WARNs to FAILs")
    parser.add_argument("--category", type=str, default=None,
                        help="Run only specified category (e.g., C1, C2)")

    args = parser.parse_args()
    skill_path = Path(args.skill_path).resolve()

    if not skill_path.is_dir():
        print(f"Error: Not a directory: {skill_path}", file=sys.stderr)
        sys.exit(1)

    categories = None
    if args.category:
        categories = [c.strip().upper() for c in args.category.split(",")]
        invalid = [c for c in categories if c not in CATEGORIES]
        if invalid:
            print(f"Error: Unknown categories: {', '.join(invalid)}", file=sys.stderr)
            print(f"Valid: {', '.join(sorted(CATEGORIES.keys()))}", file=sys.stderr)
            sys.exit(1)

    report = validate_skill(skill_path, categories)

    if args.json_output:
        print(report.format_json(strict=args.strict))
    else:
        print(report.format_text(strict=args.strict))

    sys.exit(report.exit_code(strict=args.strict))


if __name__ == "__main__":
    main()
