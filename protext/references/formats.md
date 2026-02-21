# Protext Format Specifications

Complete format specifications for all protext files.

## Table of Contents

1. [PROTEXT.md](#protextmd)
2. [.protext/index.yaml](#protextindexyaml)
3. [.protext/handoff.md](#protexthandoffmd)
4. [.protext/config.yaml](#protextconfigyaml)
5. [Scope Files](#scope-files)

---

## PROTEXT.md

The orientation layer. Target: ~500 tokens.

### Template

```markdown
# Protext: [Project Name]
> Generated: YYYY-MM-DD | Scope: [active-scope] | Tokens: ~XXX

## Identity
<!-- marker:identity -->
[1-2 sentences describing what this project/system is and its purpose.]
<!-- /marker:identity -->

## Current State
<!-- marker:state -->
Active: [current work] | Blocked: [blockers or "None"] | Recent: [last completed]
<!-- /marker:state -->

## Hot Context
<!-- marker:hot -->
- [Critical point 1 - what matters RIGHT NOW]
- [Critical point 2]
- [Critical point 3]
- [Critical point 4 - optional]
- [Critical point 5 - optional]
<!-- /marker:hot -->

## Scope Signals
- `@ops` → .protext/scopes/ops.md
- `@dev` → .protext/scopes/dev.md
- `@security` → .protext/scopes/security.md
- `@deep:[name]` → Extract from .protext/index.yaml

## Links
<!-- marker:links -->
- `[path]` → [rel-type] | [one-line note]
<!-- /marker:links -->

## Handoff
<!-- marker:handoff -->
Last: [summary of last session] | Next: [suggested next steps] | Caution: [warnings]
<!-- /marker:handoff -->
```

### Field Guidelines

| Field | Max Length | Purpose |
|-------|-----------|---------|
| Project Name | 50 chars | Project identifier |
| Identity | 200 chars | What is this? |
| Current State | 150 chars | Active/Blocked/Recent status |
| Hot Context | 5 items, 80 chars each | Critical current context |
| Scope Signals | 5 entries | Links to scope files |
| Links | 5 entries, 80 chars each | Cross-project signposts |
| Handoff | 200 chars | Session continuity |

### Example (Homelab)

```markdown
# Protext: Cooperator Node
> Generated: 2026-02-05 | Scope: ops | Tokens: ~380

## Identity
<!-- marker:identity -->
Edge services and ingress node for Raspberry Pi cluster. Runs Caddy reverse proxy, Pi-hole DNS, and Headscale VPN.
<!-- /marker:identity -->

## Current State
<!-- marker:state -->
Active: Caddy TLS config | Blocked: None | Recent: Pi-hole v6 migration
<!-- /marker:state -->

## Hot Context
<!-- marker:hot -->
- Caddy config at /etc/caddy/Caddyfile - validate before reload
- Pi-hole admin: https://dns.ism.la (Port 8080)
- All secrets via Infisical - never hardcode
- Split-horizon DNS: LAN uses 192.168.254.10, mesh uses 100.64.0.1
<!-- /marker:hot -->

## Scope Signals
- `@ops` → .protext/scopes/ops.md
- `@security` → .protext/scopes/security.md
- `@deep:network` → docs/NETWORK.md
- `@deep:services` → docs/SERVICES.md

## Links
<!-- marker:links -->
- `../drtr-homelab` → sibling | same role on drtr node
- `/mnt/ops/prj/infra` → peer | shared Terraform modules
<!-- /marker:links -->

## Handoff
<!-- marker:handoff -->
Last: Completed Pi-hole v6 upgrade | Next: Test wildcard certs | Caution: Port 8080 in use
<!-- /marker:handoff -->
```

### Links Section

Cross-project signposts. Each entry points to a related project with a relationship type and brief note. These are orientation hints — the agent can follow the path to read the linked project's PROTEXT.md if context is needed.

#### Format

```
- `[path]` → [rel-type] | [note]
```

- **path**: Relative or absolute path to the linked project root
- **rel-type**: One of the five relationship types (see below)
- **note**: One-line description of why the link matters (~80 chars max)

#### Relationship Types

| Type | Meaning | Example | Path Pattern | Aggregates |
|------|---------|---------|--------------|------------|
| `child` | Subdirectory managed by this project | parent → child | `./name` only | ✅ Yes |
| `parent` | Ancestor directory managing this project | child → parent | `../` or `../../` | ❌ No |
| `sibling` | Same role, different node (same parent) | crtr ↔ drtr homelab | `../name` only | ❌ No |
| `peer` | Related project (any location) | protext ↔ infra | Any path | ❌ No |

#### Guidelines

- Max 5 links per project (same as scopes — prevent fragmentation)
- Prefer relative paths for projects on the same filesystem
- Links are one-directional — each project declares its own outbound links
- The section is optional. Omit or leave empty if a project has no meaningful links.
- Use `protext link` to add entries interactively
- **Each path can only appear once** — no duplicate links regardless of type

#### Spatial Validation Rules

**Path patterns enforce spatial relationships:**

- `child` → Must be `./name` (immediate subdirectory only)
  - Valid: `./crtr-config`, `./subdir`
  - Invalid: `./sub/nested` (too deep), `../sibling` (not subdirectory)

- `parent` → Must be `../` or ancestor
  - Valid: `../`, `../../grand-parent`
  - Invalid: `./subdir` (not an ancestor)

- `sibling` → Must be `../name` (exactly one lateral move)
  - Valid: `../dotfiles`, `../peer-project`
  - Invalid: `../parent/cousin` (different branch), `./subdir` (not lateral)

- `peer` → Any path (catch-all for related projects)
  - Valid: Any relative or absolute path
  - No restrictions

**Aggregation behavior:**
- Only `child` links aggregate status into `## Child Projects`
- All other types are orientation signposts only

### Machine-Readable Markers

All sections in PROTEXT.md are wrapped with HTML comment markers for parent protext aggregation. These markers are invisible to human readers but allow parent projects to extract child status.

**Marker format:**
```markdown
## Section Name
<!-- marker:section -->
Content here
<!-- /marker:section -->
```

**Available markers:**
- `<!-- marker:identity -->` — Project identity/description
- `<!-- marker:state -->` — Current state (Active/Blocked/Recent)
- `<!-- marker:hot -->` — Hot context list
- `<!-- marker:links -->` — Cross-project links
- `<!-- marker:handoff -->` — Session handoff

**Scope Signals section has no marker** — it's structural, not aggregatable content.

**Usage in parent protext:**
- `protext init --parent` extracts markers from children to build `## Child Projects` section
- `protext refresh --children` updates parent by re-extracting child markers
- Markers are invisible in markdown renderers and human reading
- Backward compatibility: parent can fall back to heading-based parsing if markers absent

**Example extraction:**
```markdown
<!-- In child: ./protext/PROTEXT.md -->
## Identity
<!-- marker:identity -->
Dynamic context management for AI agents
<!-- /marker:identity -->

<!-- In parent: ./PROTEXT.md -->
## Child Projects
- `./protext/` → **active** | Dynamic context management for AI agents | Recent: Links feature
```

### Parent PROTEXT.md

Parent protexts aggregate status from child projects. Created with `protext init --parent`.

**Structure differences from standard PROTEXT.md:**
- Has `## Child Projects` section listing all children with status
- Links section auto-populated with `child` relationship types
- Hot Context aggregates from active children
- No extraction index (children have their own)

**Template:**

```markdown
# Protext: [Parent Project Name]
> Generated: YYYY-MM-DD | Scope: ops | Tokens: ~400

## Identity
<!-- marker:identity -->
Meta-project containing [description of child projects]
<!-- /marker:identity -->

## Current State
<!-- marker:state -->
Active: X/Y children active | Blocked: None | Recent: [most recent child activity]
<!-- /marker:state -->

## Hot Context
<!-- marker:hot -->
- X/Y child projects active
- [child-name]: [recent activity]
- [child-name]: [recent activity]
<!-- /marker:hot -->

## Scope Signals
- `@ops` → .protext/scopes/ops.md
- `@dev` → .protext/scopes/dev.md
- `@security` → .protext/scopes/security.md

## Child Projects
- `./child-name/` → **active** | [identity] | Recent: [recent]
- `./another-child/` → **idle** | [identity] | Recent: [recent]

## Links
<!-- marker:links -->
- `./child-name` → child | [identity snippet]
- `./another-child` → child | [identity snippet]
<!-- /marker:links -->

## Handoff
<!-- marker:handoff -->
Last: [parent-level notes] | Next: [suggested] | Caution: [warnings]
<!-- /marker:handoff -->
```

**Child Status Detection:**
- `**active**` — PROTEXT.md modified < 7 days ago
- `**idle**` — PROTEXT.md modified ≥ 7 days ago
- `**stale**` — No PROTEXT.md found

**Refresh command:**
```bash
protext refresh --children
```

Re-aggregates child status and updates parent ## Child Projects section.

---

## .protext/index.yaml

Extraction index for deep context. Max 20 entries.

### Schema

```yaml
# Required header
# Protext Extraction Index

extractions:
  [name]:                    # Unique identifier (lowercase, hyphens ok)
    source: [path]           # Path relative to project root
    triggers: [list]         # Keywords that suggest this extraction
    summary: "[description]" # One-line description
    tokens: ~[estimate]      # Approximate token count
```

### Example

```yaml
# Protext Extraction Index
# Max 20 extractions. Use suggest-mode by default.

extractions:
  network:
    source: docs/NETWORK.md
    triggers: [dns, ip, tailscale, mesh, routing, headscale]
    summary: "IPs, DNS configuration, mesh nodes, domain routing"
    tokens: ~600

  services:
    source: docs/SERVICES.md
    triggers: [docker, container, service, port, compose, caddy]
    summary: "Docker services, ports, domains, health checks"
    tokens: ~800

  secrets:
    source: docs/SECRETS.md
    triggers: [secret, credential, infisical, auth, password, api-key]
    summary: "Secrets management patterns, Infisical usage"
    tokens: ~400

  architecture:
    source: docs/ARCHITECTURE.md
    triggers: [design, diagram, pattern, cluster, nodes]
    summary: "System architecture, node relationships, data flow"
    tokens: ~500

  router:
    source: docs/ROUTER.md
    triggers: [mikrotik, gateway, dhcp, firewall, port-forward, nat]
    summary: "MikroTik router configuration, port forwarding"
    tokens: ~450
```

### Trigger Guidelines

- Use 3-6 triggers per extraction
- Include synonyms and common misspellings
- Prefer lowercase
- Triggers are hints, not exact matches

---

## .protext/handoff.md

Session continuity. Auto-stales after 48h.

### Template

```markdown
# Session Handoff
> Updated: YYYY-MM-DDTHH:MM

## Last Session
**Completed:**
- [Task 1 that was finished]
- [Task 2 that was finished]

**In Progress:**
- [Task] (stopped at: [specific point])

**Deferred:**
- [Task] (blocked by: [reason])

## Cautions
- [Warning 1 for next session]
- [Warning 2]

## Agent Notes
[Observations, insights, or context that might help the next session]
```

### Behavior

- **User-initiated only:** No auto-capture at session end
- **No TTL enforcement:** Age does not trigger warnings
- **Optional:** Created only when user runs `protext handoff capture`
- **Read-only by default:** Viewing handoff does not modify it

### Example

```markdown
# Session Handoff
> Updated: 2026-02-05T14:30

## Last Session
**Completed:**
- Migrated Pi-hole to v6
- Updated split-horizon DNS config
- Tested local resolution

**In Progress:**
- Caddy wildcard cert setup (stopped at: DNS challenge config)

**Deferred:**
- Headscale ACL audit (blocked by: need drtr node online)

## Cautions
- Don't restart Caddy without validating config first
- Port 8080 temporarily used by debug server
- Pi-hole gravity update scheduled for 3am

## Agent Notes
The DNS migration went smoother than expected. Consider documenting the
split-horizon pattern for future reference. The wildcard cert requires
Cloudflare API token - check Infisical under /caddy/cloudflare.
```

---

## .protext/config.yaml

Protext configuration.

### Template

```yaml
# Protext Configuration

# Extraction behavior
extraction_mode: suggest  # suggest | auto | confirm
token_budget: 2000        # Max tokens per session

# Handoff settings
handoff_ttl_hours: 48     # Legacy field, no longer enforced

# Active scope
active_scope: ops         # Current focus area

# Hierarchy (optional)
parent: ../               # Relative path to parent protext (child only)
                         # Note: Children tracked in ## Links section, not here

# Feature flags
features:
  auto_handoff_capture: false  # Handoff is user-initiated only
  token_warnings: true         # Warn at 80% budget
  scope_switching: true        # Enable @scope shortcuts
```

### Extraction Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `suggest` | Show available extractions, don't auto-load | Default, token-conscious |
| `auto` | Load on keyword trigger | Fast iteration, higher token use |
| `confirm` | Require user approval for each load | Maximum control |

---

## Scope Files

Domain-specific orientation. Location: `.protext/scopes/[name].md`

### Template

```markdown
# Scope: [Name]

## Focus
[1-2 sentences describing what this scope covers]

## Key Resources
- [Path or resource 1]
- [Path or resource 2]
- [Path or resource 3]

## Current Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## Patterns
[Common patterns or conventions for this scope]

## Cautions
- [Scope-specific warning 1]
- [Scope-specific warning 2]
```

### Default Scopes

**ops.md** - Operations
```markdown
# Scope: Operations

## Focus
Infrastructure management, service health, deployment, monitoring.

## Key Resources
- Docker services: /mnt/ops/docker/
- Caddy config: /etc/caddy/Caddyfile
- System logs: journalctl

## Current Priorities
1. Service availability
2. Resource monitoring
3. Backup verification

## Patterns
- Always validate configs before applying
- Check logs after service restarts
- Document infrastructure changes

## Cautions
- Never restart services without checking dependencies
- Verify backup status before major changes
```

**dev.md** - Development
```markdown
# Scope: Development

## Focus
Code development, testing, debugging, workflow optimization.

## Key Resources
- Source code: /mnt/ops/
- Tests: Run with pytest or relevant test runner
- Linting: Pre-commit hooks configured

## Current Priorities
1. Code quality
2. Test coverage
3. Documentation updates

## Patterns
- Write tests for new functionality
- Use conventional commits
- Review before merge

## Cautions
- Don't commit secrets
- Run tests before pushing
```

**security.md** - Security
```markdown
# Scope: Security

## Focus
Authentication, secrets management, vulnerability assessment, access control.

## Key Resources
- Secrets: Infisical (https://env.ism.la)
- Auth patterns: docs/SECRETS.md
- ACLs: Headscale policies

## Current Priorities
1. Secret rotation schedule
2. Access review
3. Vulnerability scanning

## Patterns
- All secrets via Infisical CLI
- Never log sensitive data
- Principle of least privilege

## Cautions
- Never hardcode credentials
- Review before exposing new services
- Audit access logs regularly
```

---

## File Size Guidelines

| File | Target Size | Max Size |
|------|-------------|----------|
| PROTEXT.md | ~500 tokens | 800 tokens |
| index.yaml | ~200 lines | 300 lines |
| handoff.md | ~300 tokens | 500 tokens |
| config.yaml | ~50 lines | 100 lines |
| Scope files | ~200 tokens each | 400 tokens |

Keep total protext overhead under 2000 tokens for efficient context loading.
