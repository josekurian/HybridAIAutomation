#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/Users/josekurian/HybridAIAutomation"
WORKTREE_ONE="/Users/josekurian/.codex/worktrees/778c/HybridAIAutomation"
WORKTREE_TWO="/Users/josekurian/.codex/worktrees/7807/HybridAIAutomation"

cd "$PROJECT_ROOT"

git worktree remove "$WORKTREE_ONE"
git worktree remove "$WORKTREE_TWO" --force
git worktree prune

echo "Removed HybridAIAutomation worktrees:"
echo "  - $WORKTREE_ONE"
echo "  - $WORKTREE_TWO"
