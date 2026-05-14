#!/bin/bash
# From PowerShell use: bash -i ./ralph/once.sh <change> (loads ~/.bashrc so claude is found)

CHANGE="${1:-$CHANGE}"
if [ -z "$CHANGE" ]; then
  echo "Usage: $0 <change-name> [model]  (e.g. bash ralph/once.sh my-change claude-opus-4-7)" >&2
  echo "Default model: claude-sonnet-4-6" >&2
  exit 1
fi
MODEL="${2:-claude-sonnet-4-6}"
shopt -s nullglob
issue_files=(docs/issues/"$CHANGE"/*.md)

if [ ${#issue_files[@]} -eq 0 ]; then
  echo "No open issues found in docs/issues/$CHANGE."
  echo "<promise>NO MORE TASKS</promise>"
  exit 0
fi

issues=$(cat "${issue_files[@]}")
issue_list=$(printf '%s\n' "${issue_files[@]}")
commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat ralph/prompt.md)

claude --permission-mode auto --model "$MODEL" \
  "$prompt

# RUNTIME CONTEXT

Requested change: $CHANGE
Allowed issue directory: docs/issues/$CHANGE
Open issue files:
$issue_list

Previous commits: $commits

Issues:
$issues"
