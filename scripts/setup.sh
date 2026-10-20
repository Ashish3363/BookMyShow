#!/usr/bin/env bash
# One-time setup after cloning. Turns on the shared git hooks.
# Owner only. Agents may not run this (it uses git).
set -euo pipefail

cd "$(dirname "$0")/.."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repo. Run 'git init' first."
  exit 1
fi

git config core.hooksPath .githooks
chmod +x .githooks/* scripts/*.sh hooks/*.py

echo "Setup done. Shared hooks are on."
