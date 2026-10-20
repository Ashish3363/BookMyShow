#!/usr/bin/env bash
# Exits 0 if this shell was started by an AI agent, 1 otherwise.
# Best effort: checks env vars that agent tools set.
# AI_AGENT=1 is this repo's own convention for any other tool.
for v in CLAUDECODE CLAUDE_CODE_ENTRYPOINT GEMINI_CLI CODEX_SANDBOX CODEX_SANDBOX_NETWORK_DISABLED CURSOR_AGENT AI_AGENT; do
  if [ -n "${!v:-}" ]; then
    exit 0
  fi
done
exit 1
