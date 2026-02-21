
# Protext Command Reference

All protext commands with syntax, examples, and natural language alternatives.

## Table of Contents

1. [/protext (Primary Command)](#protext-primary-command)
2. [protext init](#protext-init)
3. [protext status](#protext-status)
4. [protext scope](#protext-scope)
5. [protext handoff](#protext-handoff)
6. [protext extract](#protext-extract)
7. [protext link](#protext-link)
8. [Spatial Validation Rules](#spatial-validation-rules)
9. [protext init --parent](#protext-init---parent)
10. [protext refresh --children](#protext-refresh---children)
11. [protext refresh](#protext-refresh)
12. [Error Messages](#error-messages)
13. [Quick Reference Card](#quick-reference-card)

---

## Command Summary

| Command | Purpose | Shorthand |
|---------|---------|-----------|
| **`/protext`** | **Load orientation (primary)** | "Load protext" |
| `protext init` | Initialize protext in project | "Set up protext" |
| `protext status` | Show current state | "What's the context?" |
| `protext scope` | Switch active scope | `@scope-name` |
| `protext handoff` | Capture/show handoff | "Save session state" |
| `protext extract` | Pull deep context | `@deep:name` |
| `protext link` | Add cross-project link | "Link to project" |
| `protext init --parent` | Initialize parent protext | "Init as parent" |
| `protext refresh --children` | Re-aggregate children | "Refresh children" |
| `protext refresh` | Update PROTEXT.md | "Refresh the protext" |

---

## /protext (Primary Command)

**Load project orientation at session start.** This is the main entry point.

### Syntax

```
/protext                    # Load orientation + scope + handoff
/protext @[scope]           # Load with specific scope
/protext --full             # Include extraction list
/protext --minimal          # PROTEXT.md only, no scope/handoff
```

### Natural Language (Cross-Platform)

- "Load protext"
- "Show me the project context"
- "What's the current state of this project?"
- "Orient me to this codebase"
- "Load the context"

### What It Loads

1. **PROTEXT.md** - Project identity, current state, hot context
2. **Active scope** - Domain-specific orientation (ops/dev/security)
3. **Handoff status** - Session continuity with FRESH/AGING/STALE indicator
4. **(--full)** Available extractions from index.yaml

### Example Output

```
═══════════════════════════════════════════════════════
 PROTEXT: Cooperator Node (crtr-config)
 Scope: @ops | Handoff: FRESH (2h ago)
═══════════════════════════════════════════════════════

## Identity
Edge services and ingress node for Raspberry Pi home cluster.
Runs Caddy reverse proxy, Pi-hole v6 DNS, Headscale VPN.

## Current State
Active: Protext system design | Blocked: None | Recent: Docs consolidation

## Hot Context
• Caddy config: /etc/caddy/Caddyfile - validate before reload
• Pi-hole admin: https://dns.ism.la (Port 8080)
• All secrets via Infisical - never hardcode
• Split-horizon DNS: LAN=192.168.254.10, Mesh=100.64.0.1

## Handoff
Last: Protext initialized | Next: Test in sessions | Caution: First usage

───────────────────────────────────────────────────────
Extractions available: @deep:network, @deep:services, @deep:secrets...
Use @deep:[name] to load additional context.
═══════════════════════════════════════════════════════
```

### Flags

| Flag | Effect |
|------|--------|
| `@[scope]` | Override active scope for this load |
| `--full` | Show all available extractions |
| `--minimal` | Skip scope and handoff, just PROTEXT.md |
| `--json` | Output as JSON (for tooling integration) |

---

## protext init

Initialize protext in a project.

### Syntax

```
protext init [--tier beginner|intermediate|advanced]
```

Default: `--tier advanced`

### Natural Language

- "Initialize protext for this project"
- "Set up protext here"
- "Create protext context"
- "Bootstrap protext"

### What It Creates

**Beginner tier:**
- `PROTEXT.md` only

**Intermediate tier:**
- `PROTEXT.md`
- `.protext/handoff.md`

**Advanced tier (default):**
- `PROTEXT.md`
- `.protext/config.yaml`
- `.protext/index.yaml`
- `.protext/handoff.md`
- `.protext/scopes/ops.md`
- `.protext/scopes/dev.md`
- `.protext/scopes/security.md`

### Examples

```
# Initialize with all features (default)
"Initialize protext"

# Minimal setup
"Initialize protext with beginner tier"

# With handoff only
"Set up protext, intermediate tier"
```

### Script Usage

```bash
python scripts/init_protext.py /path/to/project
python scripts/init_protext.py /path/to/project --tier beginner
```

---

## protext status

Display current protext state.

### Syntax

```
protext status
```

### Natural Language

- "Show protext status"
- "What's the current context state?"
- "Protext info"
- "Context status"

### Output Includes

- Current tier (beginner/intermediate/advanced)
- Active scope
- Handoff status and age
- Token budget usage
- Available extractions count
- File modification times

### Example Output

```
==================================================
 Protext Status: crtr-config
==================================================

  Tier:           [A] Advanced
  Active Scope:   @ops (3/5 scopes)
  Handoff:        FRESH (age: 2.5h)
  Token Budget:   ~380/2000 (19%)
  Extractions:    5/20 defined

  Files:
    PROTEXT.md          (modified: 2026-02-05 14:30)
    .protext/handoff.md (modified: 2026-02-05 14:30)
    .protext/index.yaml
    .protext/config.yaml
```

### Script Usage

```bash
python scripts/protext_status.py /path/to/project
python scripts/protext_status.py  # Uses current directory
```

---

## protext scope

Switch active scope context.

### Syntax

```
protext scope [name]
protext scope list
```

### Shorthand

```
@ops
@dev
@security
@[scope-name]
```

### Natural Language

- "Switch to ops scope"
- "Focus on security context"
- "Change scope to development"
- "I'm working on security stuff"
- "List available scopes"

### Behavior

1. Updates `active_scope` in `.protext/config.yaml`
2. Loads corresponding scope file from `.protext/scopes/[name].md`
3. Updates scope indicator in PROTEXT.md header

### Examples

```
# Switch scope
"Switch to security scope"
"@security"
"Focus on ops"

# List scopes
"What scopes are available?"
"protext scope list"
```

### Scope Limits

- Maximum 5 scopes per project
- Default scopes: ops, dev, security
- Custom scopes: Create `.protext/scopes/[name].md`

---

## protext handoff

Capture or display session handoff. **User-initiated only** — handoff is an optional scratchpad for session continuity, not a mandatory protocol.

### Syntax

```
protext handoff                    # Show current handoff
protext handoff capture [notes]    # Capture new handoff
protext handoff clear              # Clear handoff
```

### Natural Language

**View:**
- "What was the last handoff?"
- "Show handoff notes"
- "What did we do last time?"

**Capture:**
- "Capture handoff: stopped mid-refactor"
- "Save session state"
- "Remember this for next time: [notes]"

**Clear:**
- "Clear the handoff"
- "Reset session notes"

### Handoff Structure

```markdown
## Last Session
**Completed:** [list]
**In Progress:** [task] (stopped at: [point])
**Deferred:** [task] (blocked by: [reason])

## Cautions
[warnings for next session]

## Agent Notes
[observations]
```

### Behavior

- **No auto-capture:** Agents do not automatically update handoff at session end
- **No TTL enforcement:** Handoff age does not trigger warnings
- **Opt-in:** `.protext/handoff.md` is created only when user captures a handoff
- **Read-only by default:** Viewing handoff does not modify it

### Examples

```
# View
"Show the last handoff"

# Capture (explicit user request)
"Capture handoff: completed the DNS migration, next step is testing certs"
"Save this: stopped at Caddy config, needs Cloudflare token from Infisical"

# With structure
"Capture handoff:
  Completed: Pi-hole upgrade
  In progress: Caddy wildcards (at DNS challenge)
  Caution: Don't restart Pi-hole during gravity update"
```

---

## protext extract

Pull deep context from extraction index.

### Syntax

```
protext extract [name]
protext extract list
```

### Shorthand

```
@deep:network
@deep:services
@deep:[extraction-name]
```

### Natural Language

- "Extract network context"
- "Load the services documentation"
- "I need details about the router config"
- "Pull in the architecture docs"
- "What extractions are available?"

### Extraction Modes

Configured in `.protext/config.yaml`:

| Mode | Behavior |
|------|----------|
| `suggest` | Shows "context available: X" - you confirm to load |
| `auto` | Loads automatically on keyword trigger |
| `confirm` | Always asks before loading |

### Examples

```
# List available
"What extractions are defined?"
"protext extract list"

# Extract specific
"@deep:network"
"Extract the services documentation"
"I need the secrets management context"

# Keyword trigger (suggest mode)
Agent: "I see there's DNS-related context available: network (~600 tokens). Load it?"
You: "Yes, load it"
```

### Budget Enforcement

- Default budget: 2000 tokens per session
- Warning at 80%: "Approaching context budget (1600/2000)"
- At 100%: "Budget reached. Use @force-extract to override."

---

## protext link

Add a cross-project link to PROTEXT.md.

### Syntax

```
protext link [path]
protext link list
protext link remove [path]
```

### Natural Language

- "Link this project to ../skills-validator"
- "Add a link to the homelab project"
- "What projects are linked?"
- "Remove the link to ../old-project"

### Guided Flow

When the user invokes `protext link [path]`:

1. **Validate path** — Confirm the target directory exists. Note whether it has its own `.protext/` (but don't require it).
2. **Ask relationship type** — Present the four types:
   - `child` — Subdirectory managed by this project (must be `./name`)
   - `parent` — Ancestor directory managing this project (must be `../`)
   - `sibling` — Same role, different node (must be `../name`)
   - `peer` — Related project (any path)
3. **Validate spatial relationship** — Check path matches type pattern:
   - `child` but path is `../foo` → ERROR: "child must be subdirectory (./name)"
   - `sibling` but path is `../../foo` → ERROR: "sibling must be adjacent (../name)"
4. **Check for duplicates** — ERROR if path already exists in Links section
5. **Ask for note** — One-line description of why the link matters (~80 chars)
6. **Append** — Add the entry to the `## Links` section in PROTEXT.md
7. **Warn on missing reciprocal** (optional):
   - Added `./child → child` → INFO: "Consider adding `parent → ../` to child/PROTEXT.md"

If no `## Links` section exists, create it between Scope Signals and Handoff.

### Examples

```
# Add a link (guided with validation)
User: "protext link ../skills-validator"
Agent: "What's the relationship? child | parent | sibling | peer"
User: "sibling"
Agent: ✅ Valid sibling path (../name pattern)
      "One-line note?"
User: "validates SKILL.md format"
Agent: Added to PROTEXT.md:
  - `../skills-validator` → sibling | validates SKILL.md format

# Invalid path pattern
User: "protext link ./subdir"
Agent: "What's the relationship?"
User: "sibling"
Agent: ❌ ERROR: sibling must be adjacent (../name)
      Path './subdir' does not match pattern for sibling

# List links
"protext link list"
"What projects are linked?"

# Remove
"protext link remove ../old-project"
```

### Constraints

- Maximum 5 links per project
- Paths should be relative when possible (portable)
- Links are one-directional — each project manages its own
- The linked project does not need protext initialized

---

## Spatial Validation Rules

Protext enforces spatial relationship validation to ensure filesystem structure matches declared relationships. Each link type has a specific path pattern that must be satisfied.

### Path Pattern Validation

| Type | Pattern (Regex) | Valid Examples | Invalid Examples |
|------|-----------------|----------------|------------------|
| `child` | `^\.\/[^/]+$` | `./protext`, `./configs` | `protext` (no ./), `./sub/deep` (too deep), `../other` (wrong direction) |
| `parent` | `^\.\.$\|^\.\./.*` | `..`, `../`, `../../` | `.` (self), `../sibling` (lateral move) |
| `sibling` | `^\.\./[^/]+$` | `../dotfiles`, `../skills` | `./subdir` (child), `../../cousin` (too far) |
| `peer` | `.*` | Any path | None (always valid) |

### Validation Flow

When `protext link [path]` is invoked:

1. **Path existence check** — Verify target directory exists
2. **Relationship prompt** — User selects type (child/parent/sibling/peer)
3. **Spatial validation** — Check path matches relationship pattern
4. **Duplicate check** — ERROR if path already exists in Links
5. **Mutual exclusivity check** — ERROR if path linked with different type
6. **Note prompt** — User provides one-line description
7. **PROTEXT.md update** — Append to `## Links` section

### Validation Levels

| Level | Meaning | Blocks Operation | Example |
|-------|---------|------------------|---------|
| **ERROR** | Spatial rule violated, operation fails | ✅ Yes | `child` with path `../sibling` |
| **WARN** | Bidirectional mismatch or missing reciprocal | ❌ No | Added `./child → child` but child has no `parent → ../` link |
| **INFO** | Target has `.protext/` but not aggregating | ❌ No | Linked `../peer` has PROTEXT.md but relationship doesn't aggregate |

### Spatial Semantics

**child**: Must be a direct subdirectory
- Pattern: `^\.\/[^/]+$` (exactly one level down)
- Valid: `./protext`, `./configs/`, `./homelab`
- Invalid: `protext` (missing ./), `./sub/dir` (nested), `../other` (lateral)
- Aggregates: ✅ Yes (parent aggregates child status)

**parent**: Must be an ancestor directory
- Pattern: `^\.\.$|^\.\./.*` (upward only, any depth)
- Valid: `..`, `../`, `../../`, `../../../ops`
- Invalid: `.` (self), `./sub` (downward), `../sibling` (lateral at same level)
- Aggregates: ❌ No (children don't aggregate parent status)

**sibling**: Must be exactly one lateral move (adjacent directory)
- Pattern: `^\.\./[^/]+$` (up one, down one)
- Valid: `../dotfiles`, `../skills-validator`, `../homelab`
- Invalid: `./subdir` (child), `../../cousin` (up two), `../sub/deep` (nested)
- Aggregates: ❌ No (siblings are peers at same organizational level)
- Use case: Same role, different node (e.g., crtr-config ↔ drtr-config)

**peer**: No spatial constraint
- Pattern: `.*` (any path)
- Valid: Anything that exists
- Aggregates: ❌ No (general relationship, no ownership)
- Use case: Related but not hierarchically connected

### Common Edge Cases

**Cousin directories** (`../../parent/cousin`):
- ❌ Fails `sibling` pattern (not adjacent)
- ✅ Valid as `peer` instead
- Reason: Sibling requires exactly `../name` pattern (one level lateral)

**Deeply nested children** (`./sub/dir/deep`):
- ❌ Fails `child` pattern (too deep)
- ✅ Direct child should link to `./sub` instead
- Reason: Hierarchy is one level only (parent → children, no grandchildren)

**Self-reference** (`.` or `./`):
- ❌ Fails all patterns
- Reason: Linking to self has no semantic meaning

**Absolute paths** (`/mnt/ops/prj/skills`):
- ⚠️ Technically valid for `peer` pattern
- ❌ Discouraged (not portable across nodes/environments)
- Recommendation: Use relative paths when possible

### Aggregation Rules

Only `child` relationships aggregate status:

```markdown
## Child Projects

### protext
**Status:** active | **Scope:** @dev
**Current:** Implementing spatial validation rules
**Recent:** Added parent protext mode

### skills-validator
**Status:** active | **Scope:** @dev
**Current:** 44-point validation checklist complete
**Recent:** Added platform path matrix
```

Other relationships (`parent`, `sibling`, `peer`) appear in `## Links` but do not create status blocks:

```markdown
## Links

- `..` → parent | Root projects directory
- `../dotfiles` → sibling | Cluster-wide configuration (drtr/trtr variants exist)
- `../homelab/docs` → peer | Infrastructure documentation
```

### Mutual Exclusivity

Each path can only appear once in the `## Links` section, with one relationship type:

**Valid:**
```markdown
- `../skills-validator` → sibling | SKILL.md format checker
```

**Invalid:**
```markdown
- `../skills-validator` → sibling | SKILL.md format checker
- `../skills-validator` → peer | Also related project  ❌ DUPLICATE PATH
```

**Enforcement:**
- Duplicate path detection blocks `protext link` operation
- To change relationship: remove old link, add new one
- Bidirectional links are separate (parent has `./child → child`, child has `.. → parent`)

### Bidirectional Consistency (Optional WARN)

When creating a link, protext can optionally warn if the reciprocal is missing:

**Example: Adding child link**
```
User: "protext link ./homelab"
Agent: "Relationship type?"
User: "child"
Agent: ✅ Valid child path (./name pattern)
      "One-line note?"
User: "Home cluster infrastructure"
Agent: Added to PROTEXT.md
      ⚠️  WARN: Consider adding reciprocal link in ./homelab/PROTEXT.md:
          `.. → parent | Projects root`
```

**Note:** This is a suggestion, not an error. Links are one-directional by design.

### Implementation Notes

**Path normalization:**
- Strip trailing slashes before validation: `../foo/` → `../foo`
- Pattern `^\.\.$` handles `..` after stripping
- Pattern `^\.\./.*` handles `../` and deeper (`../../`)

**Validation order matters:**
1. Existence check (target must exist)
2. Relationship type selection
3. Spatial pattern validation (type-specific)
4. Duplicate check (path uniqueness)
5. Note prompt (semantic context)
6. Append to PROTEXT.md

**Why spatial validation?**
- Prevents logical errors (claiming `../sibling` is a `child`)
- Makes relationships verifiable from filesystem structure
- Enforces consistent semantics (sibling = adjacent, child = subdirectory)
- Enables reliable aggregation (only `child` relationships aggregate)

---

## protext init --parent

Initialize protext in parent mode — aggregates child protext projects.

### Syntax

```
protext init --parent [--tier advanced]
```

### Natural Language

- "Initialize parent protext"
- "Set up protext as parent"
- "Create aggregating protext"

### Behavior

1. **Scans for children** — Looks for subdirectories with `PROTEXT.md` files
2. **Extracts child status** — Reads each child's PROTEXT.md (markers or headings)
3. **Generates parent PROTEXT.md** — Includes `## Child Projects` section with aggregated status
4. **Creates child links** — Adds `./child-name → child |` entries to `## Links` section
5. **No extraction index** — Parent doesn't have its own extractions (children do)
6. **No handoff by default** — Parent handoff is for parent-level notes only

### Examples

```
# Initialize as parent
"protext init --parent"

# With explicit tier
"protext init --parent --tier advanced"

# In a directory with existing children
cd /mnt/ops/prj
protext init --parent
```

### Output

```
Initializing parent protext (tier: advanced)...
  Project: Projects Root
  Found 3 child projects: protext, skills-validator, homelab
    - protext: active
    - skills-validator: active
    - homelab: idle
  Created: PROTEXT.md (parent mode)
  Created: .protext/config.yaml (with children list)
  Created: .protext/scopes/ops.md
  Created: .protext/scopes/dev.md
  Created: .protext/scopes/security.md

Parent protext initialized successfully!
```

### Constraints

- **One level only** — Parent → children, no grandchildren
- **No auto-execution** — Parent doesn't auto-refresh when loaded
- **Children optional** — If no children found, falls back to standard init

---

## protext refresh --children

Re-aggregate child status and update parent PROTEXT.md.

### Syntax

```
protext refresh --children
```

### Natural Language

- "Refresh children status"
- "Update parent protext from children"
- "Re-aggregate child projects"

### Behavior

**User-initiated only** — Parent protext is never auto-refreshed.

1. **Validates parent** — Checks for `→ child |` links in PROTEXT.md
2. **Reads Links section** — Extracts all `child` relationship paths
3. **Verifies children** — Ensures each child path has valid PROTEXT.md
4. **Extracts child status** — Reads each child's PROTEXT.md with marker/heading fallback
5. **Updates parent PROTEXT.md** — Regenerates `## Child Projects` section

### Examples

```
# From parent directory
cd /mnt/ops/prj
protext refresh --children

# Explicit path
protext refresh /mnt/ops/prj --children
```

### Output

```
Refreshing parent protext...
  Found 3 child projects: protext, skills-validator, homelab
    - protext: active
    - skills-validator: active
    - homelab: idle
  Updated: PROTEXT.md
  Updated: .protext/config.yaml

Parent protext refreshed successfully!
  2/3 children active
```

### When to Use

- After children have been modified
- When adding new child projects
- When removing child projects
- Periodically to sync status

**Zero auto-execution:** Parent never auto-refreshes on load. Always explicit user request.

---

## protext refresh

Update PROTEXT.md hot context.

### Syntax

```
protext refresh
protext refresh hot [new items]
protext refresh state [new state]
```

### Natural Language

- "Refresh the protext"
- "Update hot context"
- "Change current state to: working on tests"
- "Add to hot context: new priority item"

### Examples

```
# Full refresh
"Refresh protext based on current work"

# Update specific sections
"Update hot context: Caddy migration complete, now on DNS"
"Change state to: Active: Testing | Recent: Caddy config"

# Add item
"Add to hot context: Remember to check backup job"
```

---

## Error Messages

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| "Protext not initialized" | No PROTEXT.md found | Run `protext init` |
| "Scope not found: X" | Scope file doesn't exist | Create `.protext/scopes/X.md` |
| "Max scopes reached (5)" | Too many scopes | Merge or archive existing scopes |
| "Extraction not found: X" | Not in index.yaml | Add to `.protext/index.yaml` |
| "Token budget exceeded" | Over 2000 tokens loaded | Use `@force-extract` or increase budget |
| "Max links reached (5)" | Too many links | Remove one before adding |
| "Link target not found" | Path doesn't exist | Check the path |

### Recovery Commands

```
# Reset to defaults
"Reset protext config to defaults"

# Force operations
"@force-extract:network"  # Bypass budget
"Force scope switch even if over limit"

# Clear state
"Clear all protext state and reinitialize"
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│                 PROTEXT QUICK REF                   │
├─────────────────────────────────────────────────────┤
│ ▶ LOAD     /protext              ← START HERE       │
│            /protext @security    (with scope)       │
│            /protext --full       (show extractions) │
├─────────────────────────────────────────────────────┤
│ INIT       protext init [--tier X]                  │
│ STATUS     protext status                           │
│ SCOPE      @ops  @dev  @security                    │
│ EXTRACT    @deep:network  @deep:services            │
│ LINK       protext link [path]  (guided)            │
│ HANDOFF    "capture handoff: [notes]"               │
│ REFRESH    "refresh protext"                        │
├─────────────────────────────────────────────────────┤
│ LIMITS     5 scopes | 5 links | 20 ext | 2000 tok   │
│ HANDOFF    FRESH <24h | AGING 24-48h | STALE >48h   │
└─────────────────────────────────────────────────────┘
```
