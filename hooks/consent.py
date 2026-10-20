#!/usr/bin/env python3
"""Consent gate for Claude Code.

  python3 hooks/consent.py prompt   (UserPromptSubmit hook)
  python3 hooks/consent.py stop     (Stop hook)

prompt: opens the approval window when the owner's message is a "go" or "ok"
(a line that is only go/ok, or a message that starts with "go "). Every other
message closes it.
stop: closes the window when Claude finishes its reply.

The state lives outside the project (guard.STATE_DIR), so agents cannot write it.
This hook never blocks the owner's message. It always exits 0.
"""
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard  # noqa: E402

GO_LINE = re.compile(r"^\s*(go|ok|okay|गो|ओके)\s*[.!]*\s*$", re.IGNORECASE | re.MULTILINE)
GO_START = re.compile(r"^\s*go\b", re.IGNORECASE)


def write_state(approved, session_id):
    os.makedirs(guard.STATE_DIR, exist_ok=True)
    with open(os.path.join(guard.STATE_DIR, "approval.json"), "w") as f:
        json.dump({"approved": approved, "session_id": session_id, "time": time.time()}, f)


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    data = json.loads(sys.stdin.read() or "{}")
    session_id = data.get("session_id") or ""
    if event == "prompt":
        prompt = str(data.get("prompt") or "")
        write_state(bool(GO_LINE.search(prompt) or GO_START.match(prompt)), session_id)
    else:
        write_state(False, session_id)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        try:
            write_state(False, "")
        except Exception:
            pass
    sys.exit(0)
