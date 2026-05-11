#!/bin/bash
# From PowerShell use: bash -i ./ralph/once.sh <change> (loads ~/.bashrc so claude is found)

CHANGE="${1:-$CHANGE}"
if [ -z "$CHANGE" ]; then
  echo "Usage: $0 <change-name> [model]  (e.g. bash ralph/once.sh my-change claude-opus-4-7)" >&2
  echo "Default model: claude-sonnet-4-6" >&2
  exit 1
fi
MODEL="${2:-claude-sonnet-4-6}"
issues=$(cat "docs/issues/$CHANGE"/*.md 2>/dev/null || echo "No issues found")
commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat ralph/prompt.md)

claude --permission-mode auto --model "$MODEL" \
  "Previous commits: $commits Issues: $issues $prompt"
