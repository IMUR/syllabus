# Record Examples

Annotated examples from the Co-lab records corpus. Read these to calibrate
what a strong record looks like versus a weak one.

---

## Strong: Deployment with Decisions

Source: `crtr-records/2026-02-20-gh-cli-and-termix.md`

**Why it works:**
- Captures what was deployed AND what approach was rejected (Bun runtime)
- Includes concrete details: port numbers, IPs, file paths
- Documents the reasoning behind decisions (port 8086 because Pi-hole holds 8080)
- Notes what's still relevant (one credential for all nodes, Tailscale IPs for resilience)
- A future agent reading this knows exactly what exists and why

---

## Strong: Incident / Lesson Learned

Source: `crtr-records/2026-02-03-claude-background-task-accountability.md`

**Why it works:**
- Records a failure, not just successes
- Extracts the generalizable lesson from a specific incident
- Short and dense — no padding
- A future agent reading this adjusts its behavior

---

## Strong: Detailed Technical Deployment

Source: `drtr-records/2026-02-12-native-ai-voice-stack-deployment.md`

**Why it works:**
- Every service has: path, port, model, engine, systemd unit, storage location
- References the standard it followed (POSIX AI service layout)
- Documents the bug fix (torch-to-numpy conversion)
- A future agent can reconstruct or debug this deployment from the record alone

---

## Weak: Auto-generated Exit Record

Source: `crtr-records/exit-record-20260220-0413.md`

**What's missing:**
- Reads like a changelog, not a record — lists actions without reasoning
- No "what was rejected" or "why this approach"
- No key takeaway
- A future agent learns what happened but not why

**Note:** Auto-generated records serve a different purpose (session continuity).
They're not bad — they're just not the same thing as a deliberate record.

---

## Quick Capture Example (hypothetical)

```yaml
---
date: 2026-02-20
node: crtr
type: insight
topics: [docker, tailscale]
---
```

```markdown
# Docker Bridge Containers Can Reach Tailscale IPs

Docker containers on the default bridge network CAN reach Tailscale IPs
(100.64.x.x) via host routing. No `network_mode: host` or special config
needed. Packets route: container → docker0 bridge → host → tailscale0 → target.

Confirmed with Termix container on crtr reaching drtr (100.64.0.2:22).
```

**Why this works as a quick capture:**
- Single insight, fully self-contained
- Concrete evidence (what was tested, what happened)
- A future agent hitting the same question gets an instant answer
