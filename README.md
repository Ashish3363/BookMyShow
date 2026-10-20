# BookMyShow Clone

A movie and event ticket booking application.

## Features (planned)

- Browse movies and events by city
- View theatres and show timings
- Select seats on a seat map
- Book and pay for tickets
- User sign up, login, and booking history

## Tech Stack

To be decided.

## Getting Started

**1. Turn on the git hooks** (once, after cloning):

```bash
./scripts/setup.sh
```

**2. Turn on the Claude Code hooks:** restart Claude Code, or open `/hooks` and approve them.

**3. Test the guard:**

```bash
python3 -B hooks/test_guard.py
```

**4. Change the guardrails** (owner only):

```bash
./scripts/unlock-guardrails.sh 15   # unlock for 15 minutes
./scripts/unlock-guardrails.sh 0    # lock again
```

Install, run, and test steps will be added once the stack is chosen.

## Working With AI Agents

| File                   | Read by                                          |
|---                     |---                                               |
| `AGENTS.md`            | Main rules. Codex, Cursor, Copilot, Antigravity, and most agents |
| `CLAUDE.md`            | Claude Code (imports AGENTS.md)                  |
| `GEMINI.md`            | Gemini CLI and Antigravity (imports AGENTS.md)   |
| `hooks/consent.py`     | Consent gate. Agents act only after you say "go" |
| `hooks/guard.py`       | Shared guard. Blocks unsafe agent actions        |
| `hooks/test_guard.py`  | Tests for the guard                              |
| `.claude/settings.json`| Claude Code permissions and hooks                |
| `.codex/config.toml`   | Codex approval and sandbox settings              |
| `.githooks/`           | Blocks git actions by agents. Runs checks on commit |
| `scripts/check.sh`     | Shared checks for secrets and conflict markers   |

Add new rules to `AGENTS.md` only. See its Guardrails section.

## Project Structure

To be added.

## Status

Early setup. No code yet.
