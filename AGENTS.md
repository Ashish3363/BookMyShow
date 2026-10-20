# AGENTS.md

Single source of truth for every AI coding agent working on this repo (Claude Code, Codex, Gemini, Antigravity, Grok, Cursor, Copilot, and others).

Tool-specific files (CLAUDE.md, GEMINI.md) only import this file. Add new rules here, not there.

## Guardrails (must follow, no exceptions)

These rules bind every agent and every subagent, in every mode (default, auto, or any other). When you start a subagent, pass these rules to it.

| # | Rule | Details |
|---|---|---|
| 1 | No execution without permission | Never run any command, script, or tool action until the owner says "go" or "ok". The mode you run in does not matter. |
| 2 | No git or GitHub commands | Only `git status`, `git diff`, and `git log` are allowed. Every other git command (add, commit, push, pull, reset, anything) and `gh` is for the owner only. If any agent or subagent tries, stop it at once and tell the owner. |
| 3 | Never delete database data | Never run delete, drop, truncate, or reset on a database. Never touch the database directly unless the owner asks for that exact action. |
| 4 | Never delete files | Never delete or overwrite-to-destroy any file or folder, in any way. If something should go, ask the owner to remove it. |
| 5 | Stay inside this folder | Never read, write, or run anything outside the project folder. If you need something from outside, ask the owner. |
| 6 | Plan first, wait for "go" | Never create or change anything until the owner has seen the plan and said "go". |
| 7 | No outside contact | Never use the network: no web, no downloads, no installs, no MCP connectors, no deploys. Ask the owner to run them. |
| 8 | Soft delete only | App code never removes database rows. Mark them instead (for example `deleted_at` or `is_deleted = true`). |

### Workflow

1. Understand the task. Ask questions if anything is unclear.

2. Share a short plan: files to create or change, commands to run.

3. Wait for the owner to say "go" or "ok".

4. Do only what was approved. If a new need comes up, stop and ask again.

5. Report what was done, honestly. Say what failed or was skipped.

### When a hook blocks you

- Do not try another way around it.

- Stop and tell the owner what was blocked and why.

## Always Blocked

| Area | Examples |
|---|---|
| Git | Everything except `git status`, `git diff`, `git log`. Also `gh` |
| File delete | `rm`, `rmdir`, `unlink`, `shred`, `find -delete`, `os.remove`, `fs.unlink` |
| Overwrite | `>` into an existing file, `mv` or `cp` over a file, `tee`, `truncate`, `dd` |
| Database | `DELETE FROM`, `DROP`, `TRUNCATE`, `deleteMany`, `dropDatabase`, `FLUSHALL`, `migrate reset`, `--force-reset` (in commands, scripts, `.sql`, migration, and seed files) |
| Network | `curl`, `wget`, `ssh`, `scp`, `nc`, `ping`, WebFetch, WebSearch, MCP connectors |
| Installs | `npm install`, `npx`, `pip install`, `brew`, `docker`, `cargo`, `gem` |
| Cloud | `aws`, `gcloud`, `az`, `vercel`, `netlify`, `heroku`, `kubectl`, `terraform`, `firebase` |
| System | `sudo`, `kill`, `shutdown`, `launchctl`, `crontab`, `chown`, `chmod` (except `+x`), `open`, `osascript` |
| Hidden code | `bash -c`, `python -c`, `node -e`, `eval`, heredocs (`<<`), piping into a shell |
| Background | `nohup`, `disown`, trailing `&` |
| Secrets | `.env` files, `env`, `printenv`, `security` |
| Outside folder | `~`, `$HOME`, `..` that leaves the folder, absolute paths outside it |
| Agent actions | Cron jobs, remote triggers, workflows, worktrees, publishing, push notifications |

## Enforcement (hooks)

Rules are also enforced by code, so a mistake cannot slip through.

| Layer | File | What it does |
|---|---|---|
| Consent gate | `hooks/consent.py` | Opens an approval window only when the owner's message says "go" or "ok". Closes it when the reply ends. |
| Guard | `hooks/guard.py` | Checks every tool call. Blocks everything in "Always Blocked". Denies every command and file change when there is no approval. |
| Claude Code | `.claude/settings.json` | Runs both hooks for Claude and its subagents. Sandbox keeps writes inside the folder and cannot be turned off. |
| Codex | `.codex/config.toml` | Asks before commands. Writes only inside the folder. No network. |
| Git hooks | `.githooks/` | Blocks commit, push, rebase, and branch changes made by agents. |
| Checks | `scripts/check.sh` | Blocks `.env` files, secret keys, and merge conflict markers in commits. |
| Tests | `hooks/test_guard.py` | Proves the guard blocks and allows the right things. |

### How "go" works

- A message that is only "go" or "ok" (on its own line), or that starts with "go ", opens the window.

- Any other message closes it.

- The window also closes when the agent's reply ends.

- The approval file lives outside the project, so no agent can open the window itself.

### Agents without native hooks

Gemini, Antigravity, Grok, Cursor, and others must call the guard themselves before each action:

```bash
python3 hooks/guard.py --cmd "<shell command>"
python3 hooks/guard.py --read "<path>"
python3 hooks/guard.py --write "<path>"
```

Exit code `0` = allowed, `1` = ask the owner first, `2` = blocked (stop).

### Guardrail files are locked

AGENTS.md, CLAUDE.md, GEMINI.md, `.gitignore`, `hooks/`, `.claude/`, `.codex/`, `.githooks/`, and the guard scripts in `scripts/` are locked. Agents cannot change them.

To change them, the owner runs this in their own terminal:

```bash
./scripts/unlock-guardrails.sh 15   # unlock for 15 minutes
./scripts/unlock-guardrails.sh 0    # lock again now
```

## Project

A BookMyShow clone: a movie and event ticket booking application.

- Stage: setup (no code yet)
- Tech stack: TBD

## Core Features (planned)

- Browse movies and events by city
- View theatres and show timings
- Select seats on a seat map
- Book and pay for tickets
- User sign up, login, and booking history

## Commands

| Task          | Command                              | Who                 |
|---            |---                                   |---                  |
| Setup         | `./scripts/setup.sh`                 | Owner only          |
| Unlock rules  | `./scripts/unlock-guardrails.sh 15`  | Owner only          |
| Test guard    | `python3 -B hooks/test_guard.py`     | Agent, after "go"   |
| Check         | `./scripts/check.sh`                 | Agent, after "go"   |
| Run           | TBD                                  |                     |
| Test          | TBD                                  |                     |
| Lint          | TBD                                  |                     |

## Response Style

| Rule                | Meaning                                               |
|---                  |---                                                    |
| No over-explain     | Get to the point. Skip extra background.              |
| Simple words        | Use easy words. Avoid heavy jargon.                   |
| English in the repo | Every file in the repo stays in English.              |
| No long paragraphs  | Break the answer into short pieces.                   |
| Points and tables   | Use bullets or tables.                                |
| Proper spacing      | Leave space between lines. Do not pack text together. |
| Crisp               | Say only what is needed.                              |
| No em-dashes        | Do not use an em-dash. Use a comma or a period.       |

Apply this to code, explanations, and discussion.

## Secrets

- Never commit `.env` files or real keys.
- Put sample values in `.env.example`.
- Do not read or print `.env` contents.
