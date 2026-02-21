#!/usr/bin/env python3
"""
protext_status.py - Display Protext status for a project

Shows current protext state including tier, active scope, handoff age,
token budget status, and available extractions.

Usage:
    python protext_status.py <project-path>
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import re

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def parse_yaml_simple(content: str) -> dict:
    """Simple YAML parser for basic key-value extraction."""
    result = {}
    current_section = None

    for line in content.split('\n'):
        # Skip comments and empty lines
        if line.strip().startswith('#') or not line.strip():
            continue

        # Check for top-level key
        if not line.startswith(' ') and ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = value
            else:
                result[key] = {}
                current_section = key
        elif current_section and line.startswith('  ') and ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if isinstance(result[current_section], dict):
                result[current_section][key] = value

    return result


def load_yaml(path: Path) -> dict:
    """Load YAML file with fallback to simple parser."""
    if not path.exists():
        return {}

    content = path.read_text()

    if YAML_AVAILABLE:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            pass

    return parse_yaml_simple(content)


def detect_tier(project_path: Path) -> str:
    """Detect the protext tier based on existing files."""
    protext_md = project_path / "PROTEXT.md"
    protext_dir = project_path / ".protext"
    handoff_md = protext_dir / "handoff.md"
    index_yaml = protext_dir / "index.yaml"

    if not protext_md.exists():
        return "none"
    if not protext_dir.exists():
        return "beginner"
    if not index_yaml.exists():
        return "intermediate"
    return "advanced"


def parse_handoff_status(project_path: Path) -> dict:
    """Parse handoff.md for status information."""
    handoff_path = project_path / ".protext" / "handoff.md"

    result = {
        "exists": False,
        "updated": None,
        "status": "UNKNOWN",
        "age_hours": None,
    }

    if not handoff_path.exists():
        return result

    result["exists"] = True
    content = handoff_path.read_text()

    # Extract timestamp from header
    # Format: > Updated: YYYY-MM-DDTHH:MM | TTL: 48h | Status: FRESH
    header_match = re.search(
        r'Updated:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})',
        content
    )

    if header_match:
        try:
            updated = datetime.fromisoformat(header_match.group(1))
            result["updated"] = updated
            age = datetime.now() - updated
            result["age_hours"] = age.total_seconds() / 3600

            if result["age_hours"] < 24:
                result["status"] = "FRESH"
            elif result["age_hours"] < 48:
                result["status"] = "AGING"
            else:
                result["status"] = "STALE"
        except ValueError:
            pass

    # Check for explicit status in header
    status_match = re.search(r'Status:\s*(\w+)', content)
    if status_match:
        explicit_status = status_match.group(1).upper()
        if explicit_status in ("FRESH", "AGING", "STALE"):
            result["status"] = explicit_status

    return result


def count_extractions(project_path: Path) -> int:
    """Count extractions in index.yaml."""
    index_path = project_path / ".protext" / "index.yaml"

    if not index_path.exists():
        return 0

    data = load_yaml(index_path)
    extractions = data.get("extractions", {})

    if isinstance(extractions, dict):
        return len(extractions)
    return 0


def count_scopes(project_path: Path) -> int:
    """Count scope files."""
    scopes_dir = project_path / ".protext" / "scopes"

    if not scopes_dir.exists():
        return 0

    return len(list(scopes_dir.glob("*.md")))


def get_active_scope(project_path: Path) -> str:
    """Get active scope from config."""
    config_path = project_path / ".protext" / "config.yaml"

    if not config_path.exists():
        return "none"

    data = load_yaml(config_path)
    return data.get("active_scope", "ops")


def get_token_budget(project_path: Path) -> int:
    """Get token budget from config."""
    config_path = project_path / ".protext" / "config.yaml"

    if not config_path.exists():
        return 2000  # Default

    data = load_yaml(config_path)
    try:
        return int(data.get("token_budget", 2000))
    except (ValueError, TypeError):
        return 2000


def estimate_protext_tokens(project_path: Path) -> int:
    """Rough estimate of PROTEXT.md token count."""
    protext_md = project_path / "PROTEXT.md"

    if not protext_md.exists():
        return 0

    content = protext_md.read_text()
    # Rough estimate: ~4 chars per token
    return len(content) // 4


def format_age(hours: float) -> str:
    """Format age in human-readable form."""
    if hours is None:
        return "unknown"
    if hours < 1:
        return f"{int(hours * 60)}m"
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"


def status_color(status: str) -> str:
    """Return ANSI color for status."""
    colors = {
        "FRESH": "\033[32m",  # Green
        "AGING": "\033[33m",  # Yellow
        "STALE": "\033[31m",  # Red
        "UNKNOWN": "\033[90m",  # Gray
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    return f"{color}{status}{reset}"


def print_status(project_path: Path):
    """Print formatted protext status."""
    tier = detect_tier(project_path)

    print(f"\n{'='*50}")
    print(f" Protext Status: {project_path.name}")
    print(f"{'='*50}\n")

    if tier == "none":
        print("  Status: NOT INITIALIZED")
        print("\n  Run 'protext init' to initialize protext in this project.")
        print()
        return

    # Tier
    tier_icons = {
        "beginner": "[B]",
        "intermediate": "[I]",
        "advanced": "[A]",
    }
    print(f"  Tier:           {tier_icons.get(tier, '[ ]')} {tier.title()}")

    # Active scope
    if tier == "advanced":
        scope = get_active_scope(project_path)
        scope_count = count_scopes(project_path)
        print(f"  Active Scope:   @{scope} ({scope_count}/5 scopes)")

    # Handoff status
    if tier in ("intermediate", "advanced"):
        handoff = parse_handoff_status(project_path)
        if handoff["exists"]:
            age_str = format_age(handoff["age_hours"])
            status_str = status_color(handoff["status"])
            print(f"  Handoff:        {status_str} (age: {age_str})")
        else:
            print(f"  Handoff:        Not captured")

    # Token budget
    if tier == "advanced":
        budget = get_token_budget(project_path)
        protext_tokens = estimate_protext_tokens(project_path)
        usage_pct = (protext_tokens / budget) * 100 if budget > 0 else 0
        print(f"  Token Budget:   ~{protext_tokens}/{budget} ({usage_pct:.0f}%)")

    # Extractions
    if tier == "advanced":
        extraction_count = count_extractions(project_path)
        print(f"  Extractions:    {extraction_count}/20 defined")

    print()

    # Files summary
    print("  Files:")
    protext_md = project_path / "PROTEXT.md"
    if protext_md.exists():
        mtime = datetime.fromtimestamp(protext_md.stat().st_mtime)
        print(f"    PROTEXT.md         (modified: {mtime.strftime('%Y-%m-%d %H:%M')})")

    if tier in ("intermediate", "advanced"):
        handoff_path = project_path / ".protext" / "handoff.md"
        if handoff_path.exists():
            mtime = datetime.fromtimestamp(handoff_path.stat().st_mtime)
            print(f"    .protext/handoff.md (modified: {mtime.strftime('%Y-%m-%d %H:%M')})")

    if tier == "advanced":
        index_path = project_path / ".protext" / "index.yaml"
        if index_path.exists():
            print(f"    .protext/index.yaml")
        config_path = project_path / ".protext" / "config.yaml"
        if config_path.exists():
            print(f"    .protext/config.yaml")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Display Protext status for a project"
    )
    parser.add_argument(
        "project_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to the project directory (default: current directory)"
    )

    args = parser.parse_args()
    project_path = args.project_path.resolve()

    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    if not project_path.is_dir():
        print(f"Error: Not a directory: {project_path}")
        sys.exit(1)

    print_status(project_path)


if __name__ == "__main__":
    main()
