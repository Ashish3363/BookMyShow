#!/usr/bin/env bash
# Owner only. Unlocks the guardrail files for agents for a few minutes.
# Usage: ./scripts/unlock-guardrails.sh [minutes]   (default 15, 0 = lock now)
# The state is stored outside the project, where agents cannot write.
set -euo pipefail

minutes="${1:-15}"
if ! [[ "$minutes" =~ ^[0-9]+$ ]]; then
  echo "Minutes must be a whole number."
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd -P)"
id="$(printf '%s' "$root" | shasum | cut -c1-12)"
dir="$HOME/.agent-guard/$id"
mkdir -p "$dir"

until=$(( $(date +%s) + minutes * 60 ))
printf '{"until": %s}\n' "$until" > "$dir/unlock.json"

if [ "$minutes" -eq 0 ]; then
  echo "Guardrail files are locked."
else
  echo "Guardrail files are unlocked for $minutes minutes."
fi
