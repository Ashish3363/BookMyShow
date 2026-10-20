# AGENTS.md

Single source of truth for every AI coding agent working on this repo (Claude Code, Codex, Gemini, Antigravity, Grok, Cursor, Copilot, and others).

Tool-specific files (CLAUDE.md, GEMINI.md) only import this file. Add new rules here, not there.

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

## First-Time Setup

Run this once after cloning. It turns on the shared git hooks.

```bash
./scripts/setup.sh
```

## Commands

| Task  | Command                 |
|---    |---                      |
| Setup | `./scripts/setup.sh`    |
| Check | `./scripts/check.sh`    |
| Run   | TBD                     |
| Test  | TBD                     |
| Lint  | TBD                     |

Run `./scripts/check.sh` before you finish any task.

## Shared Hooks

- Hooks live in `.githooks/` and run on every commit, for every agent and every human.
- The hook logic lives in `scripts/check.sh`. Add new checks there, so all tools share them.
- Do not skip hooks (no `--no-verify`).

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

## Guardrails

To be added.
