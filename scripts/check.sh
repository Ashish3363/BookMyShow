#!/usr/bin/env bash
# Shared checks for every agent and human. Called by .githooks/pre-commit.
# Add new checks here so all tools run the same rules.
set -euo pipefail

fail=0

# Files to check: staged files inside git, otherwise all files.
# Agents never use git (Rule 2), so they always scan all files.
if ! "$(dirname "$0")/is-agent.sh" && git rev-parse --is-inside-work-tree >/dev/null 2>&1 && [ -n "$(git diff --cached --name-only)" ]; then
  files=$(git diff --cached --name-only --diff-filter=ACM)
else
  files=$(find . -type f -not -path './.git/*' -not -path '*/node_modules/*' | sed 's|^\./||')
fi

for f in $files; do
  [ -f "$f" ] || continue

  # 1. Block .env files (allow .env.example).
  case "$(basename "$f")" in
    .env|.env.*)
      if [ "$(basename "$f")" != ".env.example" ]; then
        echo "BLOCKED: $f is a secrets file. Do not commit it."
        fail=1
      fi
      ;;
  esac

  # 2. Block merge conflict markers.
  if grep -nE '^(<<<<<<<|>>>>>>>) ' "$f" >/dev/null 2>&1; then
    echo "BLOCKED: $f has merge conflict markers."
    fail=1
  fi

  # 3. Block common secret patterns.
  if grep -nE '(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' "$f" >/dev/null 2>&1; then
    echo "BLOCKED: $f looks like it has a secret key."
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "Checks failed. Fix the issues above."
  exit 1
fi

echo "All checks passed."
