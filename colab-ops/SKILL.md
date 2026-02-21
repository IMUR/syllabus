---
name: colab-ops
description: Instant operational knowledge of the Co-lab cluster's dotfiles, chezmoi,
  and mise systems. Load this skill when working on any node configuration, tool
  version management, or dotfile changes. Provides mode-aware guidance for orientation,
  daily usage, making changes, and debugging.
---

# colab-ops: Co-lab Cluster Operational Knowledge

## When to Load This Skill

Load this skill when the task involves any of:

- Cluster configuration, dotfiles, or shell environment
- Chezmoi status, alignment, or applying changes
- Mise tool versions across nodes
- SSH into cluster nodes for operational work
- Diagnosing drift, PATH failures, or DNS issues on any node

---

## Node-Aware Execution

**CRITICAL:** This cluster is managed symmetrically. You may be executing from `crtr`, `drtr`, `trtr`, or `prtr`.
Before executing cluster-wide commands:

1. Identify your current node by running `hostname`.
2. Execute commands natively for your current node (e.g., `chezmoi status`).
3. Execute commands via SSH for all *other* nodes (e.g., `ssh target 'zsh -l -c "chezmoi status"'`).
4. **Never** SSH into the node you are currently on.

---

## Cluster Topology

| Node | Hostname | SSH | Arch | CPU | RAM | Role |
|------|----------|-----|------|-----|-----|------|
| crtr | cooperator | local | aarch64 (RPi5) | Cortex-A76 4C | 16 GB | Gateway, all services |
| drtr | director | `ssh drtr` | x86_64 | i9-9900K 8C | 64 GB | Compute / AI / Ollama |
| trtr | terminator | `ssh trtr` | arm64 | Apple M4 10C | 24 GB | Desktop / Dev |
| prtr | projector | `ssh prtr` | x86_64 | i9-9900X 10C | 125 GB | Compute (headless) |

**Tailscale IPs:** crtr=100.64.0.1, drtr=100.64.0.2, trtr=100.64.0.8, prtr=100.64.0.7

**SSH rule — always use login shell:**

```bash
ssh drtr 'zsh -l -c "command"'   # CORRECT — sources .profile, PATH includes mise/chezmoi
ssh drtr 'command'                # WRONG — mise/chezmoi not in PATH
```

---

## Critical Rules (Read Before Any Action)

1. **Never edit `~/.local/share/chezmoi/` on any node** — that's chezmoi's local clone of GitHub, not the working copy.
2. **All dotfile edits happen in the local clone** (`/mnt/ops/dotfiles/` on Linux, `/Volumes/ops/dotfiles/` on macOS `trtr`).
3. **Changes propagate via git**, not direct file sync: edit → commit → push → `chezmoi update --force` per node.
4. **autoCommit/autoPush are irrelevant** — those only trigger on `chezmoi edit`, which is not the workflow here.
5. **chezmoi is managed by mise** — do not install chezmoi separately. Upgrade it by bumping the version in `dot_config/mise/config.toml`.

---

## Mode: Orientation

**Use when:** Starting a session, joining mid-task, or establishing cluster state before any work.

### Quick State Snapshot

```bash
# Verify local node first
chezmoi status
mise list
tailscale status

# Then SSH to all OTHER nodes (examples below, skip your current node!)
ssh crtr 'zsh -l -c "chezmoi status"'
ssh drtr 'zsh -l -c "chezmoi status"'
ssh trtr 'zsh -l -c "chezmoi status"'
ssh prtr 'zsh -l -c "chezmoi status"'
```

### Expected Baseline State

- **chezmoi status**: Only drift should be `M .local/bin/lightpanda` (nightly binary, expected, cosmetic)
- **mise list**: 20 tools installed, all versions matching `dot_config/mise/config.toml`
- **tailscale status**: crtr, drtr, trtr, prtr all online

### Key Paths

| Path | What It Is |
|------|-----------|
| `/mnt/ops/dotfiles/` (or `/Volumes/ops/...` on macOS) | Working copy of dotfiles repo — edit here |
| `~/.local/share/chezmoi/` | Per-node chezmoi clone — do not edit |
| `~/.config/chezmoi/chezmoi.toml` | Per-node chezmoi config (arch, hostname) |
| `/etc/caddy/Caddyfile` | Reverse proxy config (crtr only, systemd) |
| `/mnt/ops/docker/headscale/config/config.yaml` | Headscale VPN + DNS records (crtr) |
| `/mnt/ops/configs/system-report.md` | Cluster system report |
| `/mnt/ops/reports/crtr-reports/` | Session reports |

---

## Mode: Usage

**Use when:** Checking status, verifying alignment, or answering questions about the cluster.

### Check Alignment Across All Nodes

```bash
# Compare mise tool versions: crtr vs others
for tool in $(mise current | awk '{print $1}'); do
  current=$(mise current $tool 2>/dev/null)
  latest=$(mise latest $tool 2>/dev/null)
  [ "$current" != "$latest" ] && echo "UPDATE $tool $current -> $latest" || echo "OK $tool $current"
done

# Full chezmoi diff (preview only, no changes)
chezmoi diff

# What chezmoi would apply
chezmoi diff --no-pager
```

### Query Installed Tools

```bash
mise list          # All tools, versions, config source
mise current       # Active versions in current directory
mise which bun     # Where is this tool's binary?
```

### Service Status on crtr

```bash
systemctl status dot-console.service    # DotDash monitoring console
systemctl status caddy.service          # Reverse proxy
docker ps                               # All containers
```

### Domain / DNS

- Caddy domains: `/etc/caddy/Caddyfile`
- Headscale DNS: `/mnt/ops/docker/headscale/config/config.yaml` → `dns.extra_records`
- All `*.ism.la` A records point to `100.64.0.1` (crtr)
- After editing headscale config: `docker restart headscale`
- After editing Caddyfile: `sudo systemctl reload caddy`

---

## Mode: Change

**Use when:** Modifying dotfiles, bumping tool versions, adding services, or onboarding a node.

### The Change Workflow

```
1. Edit  →  /mnt/ops/dotfiles/            (or /Volumes/ops/dotfiles/ on macOS)
2. Test  →  chezmoi diff                   (preview on current node)
3. Commit→  git add <files> && git commit
4. Push  →  git push
5. Apply →  chezmoi update --force         (on each target node)
```

**Step 5 per node (Node-Aware):**

```bash
# 1. Update your current local node
chezmoi update --force

# 2. Update all OTHER nodes via SSH (skip yourself!)
ssh <other_node_1> 'zsh -l -c "chezmoi update --force"'
ssh <other_node_2> 'zsh -l -c "chezmoi update --force"'
ssh <other_node_3> 'zsh -l -c "chezmoi update --force"'
```

### Bump a Mise Tool Version

```bash
# 1. Check what's available
for tool in $(mise current | awk '{print $1}'); do
  current=$(mise current $tool 2>/dev/null)
  latest=$(mise latest $tool 2>/dev/null)
  [ "$current" != "$latest" ] && echo "$tool $current -> $latest"
done

# 2. Edit the version pin
$EDITOR /mnt/ops/dotfiles/dot_config/mise/config.toml

# 3. Commit and push
git -C /mnt/ops/dotfiles add dot_config/mise/config.toml
git -C /mnt/ops/dotfiles commit -m "chore(tools): bump <tool> <old> -> <new>"
git -C /mnt/ops/dotfiles push

# 4. Update + install on each node (adapt to current node)
# Local:
chezmoi update --force && mise install --yes
# Remotes (skip local node):
ssh <other_node_1> 'zsh -l -c "chezmoi update --force && mise install --yes"'
ssh <other_node_2> 'zsh -l -c "chezmoi update --force && mise install --yes"'
ssh <other_node_3> 'zsh -l -c "chezmoi update --force && mise install --yes"'
```

### Add a New Service to crtr

Checklist:

- [ ] Create systemd service file → `sudo systemctl enable --now <name>.service`
- [ ] Add Caddy entry to `/etc/caddy/Caddyfile` → `sudo systemctl reload caddy`
- [ ] Add headscale DNS A record → `/mnt/ops/docker/headscale/config/config.yaml` → `docker restart headscale`

### Onboard a New Node

```bash
# 1. Verify GitHub SSH access
ssh newnode 'ssh -T git@github.com'

# 2. Install chezmoi via mise (after mise is installed)
ssh newnode 'curl https://mise.run | sh && ~/.local/bin/mise use --global chezmoi@<version>'

# OR bootstrap chezmoi first if mise not yet installed
ssh newnode 'sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin'

# 3. Initialize from dotfiles repo
ssh newnode 'zsh -l -c "chezmoi init git@github.com:IMUR/dotfiles.git && chezmoi apply --force"'

# 4. Install mise tools
ssh newnode 'zsh -l -c "mise install --yes"'

# 5. Verify
ssh newnode 'zsh -l -c "chezmoi status && mise list"'
```

### Template Variable Reference

Chezmoi template variables (from `.chezmoi.toml.tmpl`):

```
.hostname        → node hostname (cooperator, director, etc.)
.arch            → architecture string (amd64, arm64)
.is_arm64        → bool (crtr, trtr)
.is_x86_64       → bool (drtr, prtr)
.cluster.domain  → ism.la
.cluster.nas_path→ /cluster-nas
```

Check current node's values: `chezmoi data`

---

## Mode: Debug

**Use when:** Something is broken — commands not found, chezmoi drift unexplained, DNS not resolving, or a node is out of alignment.

### Problem: Command Not Found Over SSH

```bash
# Symptom: mise/chezmoi/bun not found when SSH-ing to a node
# Cause: Non-login SSH doesn't source .profile (where mise is activated)
# Fix: Always use login shell
ssh node 'zsh -l -c "command"'   # not: ssh node 'command'
```

### Problem: Chezmoi Drift (Unexpected)

```bash
# See exactly what's different
chezmoi diff

# For binary files (like lightpanda), the diff is cosmetic:
# lightpanda uses a nightly URL — upstream changes weekly, refreshPeriod=168h
# Just run `chezmoi apply --force` to update the binary if needed

# If a text file is drifted unexpectedly, someone edited the destination directly
# Show what chezmoi would write:
chezmoi cat ~/.zshrc
```

### Problem: *.ism.la Domains Not Resolving on a Node

```bash
# Check if Tailscale manages DNS
tailscale dns status

# Check resolv.conf
cat /etc/resolv.conf
# Should say: nameserver 100.100.100.100 (Tailscale's DNS)
# If it says 192.168.254.10 (Pi-hole) and is NOT managed by Tailscale, *.ism.la resolves wrong

# Check for immutable flag (this was the prtr issue)
sudo lsattr /etc/resolv.conf
# If output contains 'i', run:
sudo chattr -i /etc/resolv.conf && sudo systemctl restart tailscaled
```

### Problem: Mise Tools Not Available After Chezmoi Apply

```bash
# chezmoi updates ~/.config/mise/config.toml but doesn't install tools
# Always follow chezmoi update with mise install
chezmoi update --force && mise install --yes
```

### Problem: Wrong chezmoi Version or Location

```bash
# Check which chezmoi is active
which chezmoi        # Should be ~/.local/share/mise/shims/chezmoi
chezmoi --version    # Should match version in dot_config/mise/config.toml

# If resolving to a stale binary (e.g., /usr/local/bin/chezmoi):
# 1. Check PATH order — mise shims should come first
echo $PATH
# 2. Remove the old binary
sudo rm /usr/local/bin/chezmoi     # all nodes now manage chezmoi via mise
# 3. Verify
which chezmoi && chezmoi --version
```

### Problem: Chezmoi Not Initialized on a Node

```bash
# Symptom: `chezmoi status` returns "no such file or directory: ~/.local/share/chezmoi"
chezmoi init git@github.com:IMUR/dotfiles.git
chezmoi apply --force
```

### Problem: chezmoi.toml Has Wrong Architecture Flags

```bash
# Check current values
chezmoi data | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('is_arm64'), d.get('is_x86_64'), d.get('arch'))"

# If wrong, the config was hand-edited incorrectly
# Fix: Remove the stale config and re-init
rm ~/.config/chezmoi/chezmoi.toml
chezmoi init git@github.com:IMUR/dotfiles.git
# chezmoi will regenerate the config from .chezmoi.toml.tmpl with correct values
```

### Problem: .zshrc Has Local Modifications Blocking Apply

```bash
# chezmoi asks for confirmation when destination was edited after last apply
# Use --force to override (safe — the template is the source of truth)
chezmoi apply --force ~/.zshrc

# If the modification should be kept (e.g., local toolchain lines),
# move it to ~/.zshrc.local — that file is NOT managed by chezmoi
# and is sourced at the end of .zshrc automatically
```

---

## Mise Tool Inventory (Current Baseline)

20 tools pinned in `dot_config/mise/config.toml`:

```
chezmoi   atuin     bat       bottom    bun
delta     dust      eza       fd        fzf
go        jq        node      python    ripgrep
starship  usage     uv        yq        zoxide
```

**To check for available updates (stable releases only):**

```bash
for tool in $(mise current | awk '{print $1}'); do
  c=$(mise current $tool 2>/dev/null); l=$(mise latest $tool 2>/dev/null)
  [ "$c" != "$l" ] && echo "UPDATE $tool $c -> $l" || true
done
```

`mise latest` returns stable releases only — no betas, RCs, or nightlies.

---

## Reference: Dotfiles Repo Structure

```
/mnt/ops/dotfiles/
├── .chezmoi.toml.tmpl          # Node detection, arch flags, cluster vars
├── dot_profile.tmpl            # Universal env: PATH, HAS_* flags, mise
├── dot_zshrc.tmpl              # Zsh config, plugin load order
├── dot_bashrc.tmpl             # Bash config
├── .chezmoiexternal.toml.tmpl  # Zsh plugins + lightpanda binary (nightly)
├── run_onchange_install_packages.sh.tmpl  # OS-aware package install
└── dot_config/
    └── mise/
        └── config.toml         # Tool version pins (20 tools)
```

Shell config load order: `.profile` (PATH, tool detection) → `.zshrc` (shell-specific) → `.zshrc.local` (local overrides, not managed by chezmoi).
