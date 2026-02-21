---
name: colab-learn
description: Deploy skills to all Co-lab cluster nodes from anywhere. SSHs to each
  node and runs skills-sync push. Use when you want to fan out skills across the
  entire cluster without manually SSHing to each node.
---

# colab-learn: Cluster-Wide Skill Deployment

## When to Use This Skill

Use when:
- You want to deploy skills to all nodes from any machine
- You've updated `.agent/skills/` and need to fan out cluster-wide
- You're on trtr/drtr and want to sync without SSHing to crtr first

---

## Cluster Topology

```
crtr (cooperator)  — /mnt/ops/prj/skills/.agent/skills/  ← canonical clone
drtr (director)    — /mnt/ops/prj/skills/.agent/skills/  ← shared mount
trtr (terminator)  — /Volumes/ops/prj/skills/.agent/skills/  ← shared mount
prtr (projector)   — /mnt/ops/prj/skills/.agent/skills/  ← shared mount
```

All nodes see the same `.agent/skills/` via shared storage. Running `skills-sync push` on any node deploys to that node's platform paths.

---

## Commands

### Sync All Nodes

```bash
colab-learn
```

**What it does:**
1. Detects current node
2. Runs `skills-sync push` locally
3. SSHs to each other node and runs `skills-sync push`
4. Reports results for all nodes

### Sync Specific Nodes

```bash
colab-learn crtr drtr
colab-learn trtr
```

### Sync Current Node Only

```bash
colab-learn --local
```

### Dry Run (Show What Would Happen)

```bash
colab-learn --dry-run
```

---

## Expected Output

```bash
$ colab-learn

[colab-learn] Detecting current node... crtr

[colab-learn] Syncing crtr (local)...
  ~/.claude/skills
  ~/.gemini/antigravity/skills
  ~/.cursor/skills
  ~/.config/opencode/skills
  ~/.agents/skills
  ✅ crtr: synced

[colab-learn] Syncing drtr via SSH...
  ~/.claude/skills
  ~/.gemini/antigravity/skills
  ~/.cursor/skills
  ~/.config/opencode/skills
  ~/.agents/skills
  ✅ drtr: synced

[colab-learn] Syncing trtr via SSH...
  ~/.claude/skills
  ~/.gemini/antigravity/skills
  ~/.cursor/skills
  ~/.config/opencode/skills
  ~/.agents/skills
  ✅ trtr: synced

[colab-learn] Syncing prtr via SSH...
  ~/.claude/skills
  ~/.gemini/antigravity/skills
  ~/.cursor/skills
  ~/.config/opencode/skills
  ~/.agents/skills
  ✅ prtr: synced

═══════════════════════════════════════════════════════════
✅ Cluster sync complete: 4/4 nodes synced
═══════════════════════════════════════════════════════════
```

---

## SSH Requirements

This skill requires passwordless SSH access between all cluster nodes.

**Verify SSH works:**

```bash
# From any node
ssh drtr 'echo connected'
ssh trtr 'echo connected'
ssh prtr 'echo connected'
ssh crtr 'echo connected'
```

**Login shell requirement:**

SSH commands use login shells to ensure mise/chezmoi are in PATH:

```bash
ssh drtr 'zsh -l -c "skills-sync push"'
```

---

## Node Detection

The script auto-detects the current node via hostname:

| Hostname | Node |
|----------|------|
| cooperator | crtr |
| drtr | drtr |
| trtr | trtr |
| prtr | prtr |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All nodes synced successfully |
| 1 | One or more nodes failed |
| 2 | SSH connection failed |
| 3 | skills-sync not found on a node |

---

## Troubleshooting

### "SSH connection failed"

Verify the node is reachable:
```bash
ssh <node> 'echo ok'
```

Check Tailscale:
```bash
tailscale status
```

### "skills-sync: command not found" over SSH

The remote shell isn't sourcing profile. The script uses login shells (`zsh -l -c`) to fix this. If still failing, check that `/mnt/ops/prj/skills/skills-sync` exists on the remote.

### "Permission denied" on skills-sync

Ensure `skills-sync` is executable:
```bash
chmod +x /mnt/ops/prj/skills/skills-sync
```

### Partial sync (some nodes failed)

The script continues even if one node fails. Check the summary at the end:
```
⚠️ Cluster sync complete: 3/4 nodes synced (1 failed)
  ❌ prtr: SSH connection timed out
```

---

## Integration with skill-deploy

Typical workflow after making changes:

```bash
# 1. Deploy skill to .agent/skills/
skill-deploy dev/my-skill

# 2. Fan out to all nodes
colab-learn
```

Or combined:
```bash
skill-deploy dev/my-skill && colab-learn
```

---

## Scripts

- `scripts/colab_learn.sh` — Main cluster sync script
