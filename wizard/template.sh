#!/usr/bin/env bash
# Human-run wizard template. Edit only below the STAGES marker.

set -euo pipefail

WIZARD_FIXTURE_MODE="${WIZARD_FIXTURE_MODE:-0}"
WIZARD_ALLOW_BROWSER="${WIZARD_ALLOW_BROWSER:-0}"
WIZARD_ALLOW_PROVIDER="${WIZARD_ALLOW_PROVIDER:-0}"
ENV_FILE="${ENV_FILE:-.env}"

for flag in WIZARD_FIXTURE_MODE WIZARD_ALLOW_BROWSER WIZARD_ALLOW_PROVIDER; do
  value="${!flag}"
  if [[ "$value" != "0" && "$value" != "1" ]]; then
    printf 'invalid %s: expected 0 or 1\n' "$flag" >&2
    exit 2
  fi
done

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 &&
  [[ "$(tput colors 2>/dev/null || printf '0')" -ge 8 ]]; then
  BOLD=$(tput bold)
  DIM=$(tput dim)
  RESET=$(tput sgr0)
  BLUE=$(tput setaf 4)
  GREEN=$(tput setaf 2)
  YELLOW=$(tput setaf 3)
else
  BOLD=""
  DIM=""
  RESET=""
  BLUE=""
  GREEN=""
  YELLOW=""
fi

TOTAL_STAGES=0
_STAGE_INDEX=0
WRITTEN_ENV=()
WRITTEN_SECRET_NAMES=()
SKIPPED=()

_clear() {
  [[ -t 1 ]] || return 0
  if command -v tput >/dev/null 2>&1; then
    tput clear
  else
    printf '\033[2J\033[3J\033[H'
  fi
}

say() { printf '  %s\n' "$1"; }
step() { printf '  %s•%s %s\n' "$BLUE" "$RESET" "$1"; }
note() { printf '  %s%s%s\n' "$DIM" "$1" "$RESET"; }
warn() { printf '  %s⚠ %s%s\n' "$YELLOW" "$1" "$RESET"; }

pause() {
  printf '  %s%s%s ' "$DIM" "${1:-Press Enter to continue}" "$RESET"
  read -r _ || true
}

confirm() {
  local reply=""
  printf '  %s? %s [y/N]%s ' "$YELLOW" "$1" "$RESET"
  read -r reply || true
  [[ "$reply" =~ ^[Yy]$ ]]
}

banner() {
  _clear
  printf '\n%s%s  %s%s\n' "$BOLD" "$BLUE" "$1" "$RESET"
  printf '%s  %s stages%s\n\n' "$DIM" "$TOTAL_STAGES" "$RESET"
  printf '  You control every manual and external action. Stop with Ctrl-C if anything differs.\n'
  pause "Ready to start?"
}

stage() {
  _clear
  _STAGE_INDEX=$((_STAGE_INDEX + 1))
  printf '\n%s%s▸ Stage %s/%s · %s%s\n' \
    "$BOLD" "$BLUE" "$_STAGE_INDEX" "$TOTAL_STAGES" "$1" "$RESET"
}

_existing() {
  local key="$1"
  [[ -f "$ENV_FILE" ]] || return 1
  awk -v prefix="${key}=" 'index($0, prefix) == 1 { value=substr($0, length(prefix)+1) } END { if (value != "") printf "%s", value; else exit 1 }' "$ENV_FILE"
}

ask() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[Enter keeps current]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -r input || true
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

ask_secret() {
  local key="$1" prompt="$2" input
  printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  read -rs input || true
  printf '\n'
  printf -v "$key" '%s' "$input"
}

# write_env KEY VALUE — Idempotent single-line environment upsert.
write_env() {
  local key="$1" value="$2" tmp
  [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || {
    warn "invalid environment key: $key"
    return 2
  }
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || {
    warn "multi-line environment values are not supported"
    return 2
  }
  touch "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  tmp=$(mktemp "${ENV_FILE}.tmp.XXXXXX")
  awk -v prefix="${key}=" 'index($0, prefix) != 1' "$ENV_FILE" > "$tmp"
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$ENV_FILE"
  WRITTEN_ENV+=("$key")
  printf '  %s✓ wrote%s %s → %s\n' "$GREEN" "$RESET" "$key" "$ENV_FILE"
}

open_url() {
  local url="$1" opener=""
  if [[ "$WIZARD_FIXTURE_MODE" == "1" ]]; then
    note "fixture mode: browser disabled ($url)"
    return 0
  fi
  if [[ "$WIZARD_ALLOW_BROWSER" != "1" ]]; then
    warn "browser opening not authorized; visit manually: $url"
    return 0
  fi
  if command -v wslview >/dev/null 2>&1; then
    opener="wslview"
  elif command -v explorer.exe >/dev/null 2>&1; then
    opener="explorer.exe"
  elif command -v xdg-open >/dev/null 2>&1; then
    opener="xdg-open"
  elif command -v open >/dev/null 2>&1; then
    opener="open"
  else
    warn "no supported browser opener found; visit manually: $url"
    return 0
  fi
  if ! "$opener" "$url" >/dev/null 2>&1; then
    warn "browser opener failed; visit manually: $url"
  fi
}

set_secret() {
  local name="$1" value="$2"
  if [[ "$WIZARD_FIXTURE_MODE" == "1" ]]; then
    note "fixture mode: provider disabled ($name not persisted)"
    return 0
  fi
  if [[ "$WIZARD_ALLOW_PROVIDER" != "1" ]]; then
    SKIPPED+=("provider secret $name")
    warn "provider write not authorized; set $name manually"
    return 0
  fi
  if ! confirm "Write provider secret $name now?"; then
    SKIPPED+=("provider secret $name")
    warn "provider write declined; set $name manually"
    return 0
  fi
  if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1; then
    SKIPPED+=("provider secret $name")
    warn "gh is unavailable or unauthenticated; set $name manually"
    return 0
  fi
  if printf -- '%s' "$value" | gh secret set "$name" >/dev/null 2>&1; then
    WRITTEN_SECRET_NAMES+=("$name")
    printf '  %s✓ set%s provider secret %s\n' "$GREEN" "$RESET" "$name"
  else
    SKIPPED+=("provider secret $name")
    warn "provider rejected secret $name; set it manually"
  fi
}

finish() {
  _clear
  printf '\n%s%s  ✓ Wizard stages complete%s\n' "$BOLD" "$GREEN" "$RESET"
  if (( ${#WRITTEN_ENV[@]} > 0 )); then
    note "environment keys written: ${WRITTEN_ENV[*]}"
  fi
  if (( ${#WRITTEN_SECRET_NAMES[@]} > 0 )); then
    note "provider secret names written: ${WRITTEN_SECRET_NAMES[*]}"
  fi
  if (( ${#SKIPPED[@]} > 0 )); then
    warn "manual follow-up required:"
    for item in "${SKIPPED[@]}"; do note "- $item"; done
  fi
}

# ──────────────────────────────────────────────────────────────────────────
# STAGES — replace this example, set WIZARD_CONFIGURED=1, and keep the count exact.
# ──────────────────────────────────────────────────────────────────────────

WIZARD_CONFIGURED=0
TOTAL_STAGES=2

if [[ "$WIZARD_FIXTURE_MODE" != "1" && "$WIZARD_CONFIGURED" != "1" ]]; then
  printf 'wizard template is not configured; author and review its stages before human execution\n' >&2
  exit 2
fi

banner "Example setup fixture"

stage "Capture a public label"
open_url "https://example.invalid/setup"
ask WIZARD_EXAMPLE_LABEL "Enter a non-sensitive example label:"
write_env WIZARD_EXAMPLE_LABEL "$WIZARD_EXAMPLE_LABEL"

stage "Capture a provider secret"
step "Generate a temporary example secret in the reviewed provider interface."
ask_secret WIZARD_EXAMPLE_SECRET "Paste the sensitive value (hidden):"
set_secret WIZARD_EXAMPLE_SECRET "$WIZARD_EXAMPLE_SECRET"
unset WIZARD_EXAMPLE_SECRET

finish
