#!/usr/bin/env bash
#
# colab-learn - Deploy skills to all Co-lab cluster nodes
#
# Usage:
#   colab-learn              # Sync all nodes
#   colab-learn crtr drtr    # Sync specific nodes
#   colab-learn --local      # Sync current node only
#   colab-learn --dry-run    # Show what would happen
#
# Exit codes:
#   0 = all nodes synced
#   1 = one or more nodes failed
#   2 = SSH connection failed
#   3 = skills-sync not found
#

set -euo pipefail

# Node configuration
declare -A NODE_HOSTNAMES=(
    [crtr]=cooperator
    [drtr]=drtr
    [trtr]=trtr
    [prtr]=prtr
)

ALL_NODES=(crtr drtr trtr prtr)

# Detect monorepo root
if [[ -d "/Volumes/ops/prj/skills" ]]; then
    REPO_ROOT="/Volumes/ops/prj/skills"
else
    REPO_ROOT="/mnt/ops/prj/skills"
fi

SKILLS_SYNC="$REPO_ROOT/skills-sync"

# Parse arguments
DRY_RUN=false
LOCAL_ONLY=false
TARGET_NODES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --local)
            LOCAL_ONLY=true
            shift
            ;;
        crtr|drtr|trtr|prtr)
            TARGET_NODES+=("$1")
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: cluster-skills-sync [--dry-run|--local] [node1 node2 ...]"
            exit 1
            ;;
    esac
done

# Default to all nodes if none specified
if [[ ${#TARGET_NODES[@]} -eq 0 ]] && [[ "$LOCAL_ONLY" == "false" ]]; then
    TARGET_NODES=("${ALL_NODES[@]}")
fi

if [[ "$LOCAL_ONLY" == "true" ]]; then
    TARGET_NODES=()
fi

# Detect current node
CURRENT_HOSTNAME=$(hostname -s 2>/dev/null || hostname)
CURRENT_NODE=""

for node in "${!NODE_HOSTNAMES[@]}"; do
    if [[ "${NODE_HOSTNAMES[$node]}" == "$CURRENT_HOSTNAME" ]]; then
        CURRENT_NODE="$node"
        break
    fi
done

if [[ -z "$CURRENT_NODE" ]]; then
    echo "⚠️  Could not detect current node from hostname: $CURRENT_HOSTNAME"
    echo "   Assuming local execution only"
    CURRENT_NODE="unknown"
fi

echo "[colab-learn] Detecting current node... $CURRENT_NODE"
echo ""

# Track results
declare -A RESULTS
TOTAL=0
SUCCESS=0
FAILED=0

# Function to sync a node
sync_node() {
    local node="$1"
    local is_local=false

    if [[ "$node" == "$CURRENT_NODE" ]]; then
        is_local=true
    fi

    echo "[colab-learn] Syncing $node${is_local:+ (local)}..."

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  (dry-run) Would run: skills-sync push"
        RESULTS[$node]="dry-run"
        ((TOTAL++)) || true
        return 0
    fi

    if [[ "$is_local" == "true" ]]; then
        # Run locally
        if [[ ! -x "$SKILLS_SYNC" ]]; then
            echo "  ❌ $node: skills-sync not found at $SKILLS_SYNC"
            RESULTS[$node]="failed: skills-sync not found"
            ((TOTAL++)) || true
            ((FAILED++)) || true
            return 1
        fi

        if output=$("$SKILLS_SYNC" push 2>&1); then
            echo "$output" | sed 's/^/  /'
            echo "  ✅ $node: synced"
            RESULTS[$node]="success"
            ((SUCCESS++)) || true
        else
            echo "  ❌ $node: skills-sync failed"
            echo "$output" | sed 's/^/  /'
            RESULTS[$node]="failed: skills-sync error"
            ((FAILED++)) || true
        fi
    else
        # Run via SSH
        local hostname="${NODE_HOSTNAMES[$node]}"

        if ! ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$hostname" 'echo ok' &>/dev/null; then
            echo "  ❌ $node: SSH connection failed"
            RESULTS[$node]="failed: SSH connection"
            ((FAILED++)) || true
            ((TOTAL++)) || true
            return 2
        fi

        # Determine remote path
        local remote_root
        if [[ "$node" == "trtr" ]]; then
            remote_root="/Volumes/ops/prj/skills"
        else
            remote_root="/mnt/ops/prj/skills"
        fi

        local cmd="zsh -l -c '$remote_root/skills-sync push'"

        if output=$(ssh -o StrictHostKeyChecking=accept-new "$hostname" "$cmd" 2>&1); then
            echo "$output" | sed 's/^/  /'
            echo "  ✅ $node: synced"
            RESULTS[$node]="success"
            ((SUCCESS++)) || true
        else
            echo "  ❌ $node: skills-sync failed"
            echo "$output" | sed 's/^/  /'
            RESULTS[$node]="failed: skills-sync error"
            ((FAILED++)) || true
        fi
    fi

    ((TOTAL++)) || true
}

# Sync local first if in target list
for node in "${TARGET_NODES[@]}"; do
    if [[ "$node" == "$CURRENT_NODE" ]]; then
        sync_node "$node"
        break
    fi
done

# Then sync remote nodes
for node in "${TARGET_NODES[@]}"; do
    if [[ "$node" != "$CURRENT_NODE" ]]; then
        sync_node "$node"
    fi
done

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"

if [[ $FAILED -eq 0 ]]; then
    echo "✅ Cluster sync complete: $SUCCESS/$TOTAL nodes synced"
else
    echo "⚠️  Cluster sync complete: $SUCCESS/$TOTAL nodes synced ($FAILED failed)"
    for node in "${!RESULTS[@]}"; do
        if [[ "${RESULTS[$node]}" != "success" ]] && [[ "${RESULTS[$node]}" != "dry-run" ]]; then
            echo "  ❌ $node: ${RESULTS[$node]}"
        fi
    done
fi

echo "═══════════════════════════════════════════════════════════"

# Exit with appropriate code
if [[ $FAILED -gt 0 ]]; then
    exit 1
fi

exit 0
