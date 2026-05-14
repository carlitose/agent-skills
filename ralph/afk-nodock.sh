#!/bin/bash
# From PowerShell use: bash -i ./ralph/afk-nodock.sh <iterations> <change> (loads ~/.bashrc so claude is found)
set -eo pipefail

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <iterations> <change-name> [model]  (e.g. bash -i ralph/afk-nodock.sh 10 my-change claude-opus-4-7)" >&2
  echo "Default model: claude-sonnet-4-6" >&2
  exit 1
fi

ITERATIONS="$1"
CHANGE="$2"
MODEL="${3:-claude-sonnet-4-6}"

stream_text='select(.type == "assistant").message.content[]? | select(.type == "text").text // empty | gsub("\n"; "\r\n") | . + "\r\n\n"'
final_result='select(.type == "result").result // empty'

LOG_DIR="ralph/logs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"
echo "Logs: $LOG_DIR"

PROMPT_FILE="ralph/.tmp-prompt.md"
shopt -s nullglob

for ((i=1; i<=ITERATIONS; i++)); do
  logfile="$LOG_DIR/iter-$(printf '%02d' $i).jsonl"
  issue_files=(docs/issues/"$CHANGE"/*.md)

  if [ ${#issue_files[@]} -eq 0 ]; then
    echo "No open issues found in docs/issues/$CHANGE. Ralph complete before iteration $i."
    echo "<promise>NO MORE TASKS</promise>"
    exit 0
  fi

  commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
  issues=$(cat "${issue_files[@]}")
  issue_list=$(printf '%s\n' "${issue_files[@]}")
  prompt=$(cat ralph/prompt.md)

  printf '%s' "$prompt

# RUNTIME CONTEXT

Requested change: $CHANGE
Allowed issue directory: docs/issues/$CHANGE
Open issue files:
$issue_list

Previous commits: $commits

Issues:
$issues" > "$PROMPT_FILE"

  echo "=== Iteration $i ==="

  claude \
    --model "$MODEL" \
    --permission-mode auto \
    --verbose \
    --print \
    --output-format stream-json \
    "Read $PROMPT_FILE and follow the instructions in it." \
  | grep --line-buffered '^{' \
  | tee "$logfile" \
  | jq --unbuffered -rj "$stream_text"

  result=$(jq -r "$final_result" "$logfile")

  if [[ "$result" == *"<promise>NO MORE TASKS</promise>"* ]]; then
    echo "Ralph complete after $i iterations."
    exit 0
  fi
done
