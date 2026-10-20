#!/usr/bin/env python3
"""Shared safety guard for every AI agent working on this repo.

Claude Code runs this as a PreToolUse hook (tool call as JSON on stdin).
Any other agent can call it before an action:

  python3 hooks/guard.py --cmd "<shell command>"
  python3 hooks/guard.py --read "<path>"
  python3 hooks/guard.py --write "<path>"

Exit codes: 0 = allow, 1 = ask the owner first, 2 = blocked.
The rules are listed in AGENTS.md (Guardrails and Always Blocked).
If this script fails for any reason, it blocks (fail closed).
"""
import hashlib
import json
import os
import re
import shlex
import sys
import time

ROOT = os.path.realpath(
    os.environ.get("CLAUDE_PROJECT_DIR")
    or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)

# Consent and unlock state lives outside the project, where agents cannot write.
STATE_DIR = os.path.join(
    os.path.expanduser("~"), ".agent-guard", hashlib.sha1(ROOT.encode()).hexdigest()[:12]
)
APPROVAL_MAX_AGE = 2 * 60 * 60

ALLOW, ASK, BLOCK = "allow", "ask", "block"

NO_APPROVAL = 'Rule 1 and 6: no approval yet. Share the plan and wait for the owner to reply "go".'

# Guardrail files. Locked unless the owner runs scripts/unlock-guardrails.sh.
PROTECTED = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".gitignore",
    "hooks/",
    ".claude/",
    ".codex/",
    ".githooks/",
    "scripts/check.sh",
    "scripts/is-agent.sh",
    "scripts/setup.sh",
    "scripts/unlock-guardrails.sh",
)

# Scripts that may contain blocked words (they are the guards themselves).
TRUSTED_SCRIPTS = {
    "hooks/guard.py", "hooks/test_guard.py", "hooks/consent.py",
    "scripts/check.sh", "scripts/is-agent.sh",
}
# Guard scripts an agent may run.
GUARD_RUNNERS = {"hooks/guard.py", "hooks/test_guard.py", "scripts/check.sh"}

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "write_file", "replace", "edit"}
SAFE_MCP = {"mcp__claude-vscode__getDiagnostics"}
BLOCKED_TOOLS = {
    "WebFetch": "Rule 7: web access is blocked.",
    "WebSearch": "Rule 7: web search is blocked.",
    "Artifact": "Rule 7: publishing pages is blocked.",
    "ArtifactData": "Rule 7: publishing data is blocked.",
    "ArtifactComments": "Rule 7: publishing comments is blocked.",
    "DesignSync": "Rule 7: syncing designs is blocked.",
    "PushNotification": "Rule 7: push notifications are blocked.",
    "RemoteTrigger": "Agent actions: remote jobs are blocked.",
    "CronCreate": "Agent actions: scheduled jobs are blocked.",
    "CronDelete": "Agent actions: scheduled jobs are blocked.",
    "ScheduleWakeup": "Agent actions: scheduled wakeups are blocked.",
    "Workflow": "Agent actions: multi-agent workflows are blocked.",
    "EnterWorktree": "Rule 2: git worktrees are blocked.",
    "ExitWorktree": "Rule 2: git worktrees are blocked.",
}

INTERPRETERS = {
    "bash", "sh", "zsh", "dash", "python", "python3", "node", "ts-node",
    "tsx", "deno", "bun", "ruby", "perl", "source", ".",
}
DB_TOOLS = {
    "psql", "mysql", "mariadb", "mongo", "mongosh", "redis-cli", "sqlite3", "pg_dump",
    "pg_restore", "mongodump", "mongorestore", "mongoimport", "prisma", "sequelize",
    "knex", "typeorm", "drizzle-kit",
}
READ_CMDS = {
    "cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "ls", "wc",
    "diff", "file", "stat", "shasum", "sha1sum", "sha256sum", "md5", "cmp", "tree", "find",
}
SCRIPT_EXT = (".sh", ".bash", ".zsh", ".py", ".js", ".mjs", ".cjs", ".ts", ".rb", ".pl", ".sql")
SAFE_ABS = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"}
DB_FILE_DIRS = {"migration", "migrations", "seed", "seeds", "seeder", "seeders"}

SEP = r"\s;&|(`'" + '"'


def cmd_word(names):
    """Match a program name used as a command word (also /path/to/name)."""
    return re.compile(
        r"(^|[" + SEP + r"])(\S*/)?(" + "|".join(names) + r")(?=$|[" + SEP + r")])"
    )


# Rule 2: git. Only status, diff, and log are allowed.
GIT_WORD = cmd_word(["git"])
READ_GIT = {"status", "diff", "log"}
BAD_GIT_FLAGS = {
    "--output", "--ext-diff", "--textconv", "--exec-path", "--git-dir",
    "--work-tree", "--no-index", "--open-files-in-pager", "-c", "-C",
}

# Rule 3: destructive database operations.
DB_DESTRUCTIVE = re.compile(
    r"(\bdrop\s+(table|database|schema|collection|index|view|user)\b|\bdelete\s+from\b"
    r"|\btruncate\s+(table\s+)?\w|\b(deleteMany|deleteOne|findOneAndDelete|findByIdAndDelete"
    r"|findOneAndRemove|dropDatabase|dropCollection|dropIndexes)\b|\.drop\(|\bflushall\b|\bflushdb\b"
    r"|\bmigrate\s+reset\b|force-reset|accept-data-loss|db:drop|db:reset|migrate:rollback"
    r"|migrate:reset|migrate:fresh|\s--drop\b)",
    re.IGNORECASE,
)

# Checks used on commands and on the scripts they run.
COMMON_BLOCKS = [
    (cmd_word(["gh", "hub"]), "Rule 2: the GitHub CLI is not allowed."),
    (cmd_word(["rm", "rmdir", "unlink", "shred", "srm", "trash", "trash-put", "rimraf", "del", "erase", "Remove-Item"]),
     "Rule 4: deleting files or folders is not allowed. Ask the owner to do it."),
    (re.compile(
        r"(\s-delete\b|\bos\.(remove|unlink|rmdir|removedirs)\b|\bshutil\.rmtree\b|\.unlink\(|\.rmdir\("
        r"|\bfs\.(promises\.)?(rm|rmSync|unlink|unlinkSync|rmdir|rmdirSync)\b|\bunlinkSync\b|\brmSync\b"
        r"|\s--delete\b|\bmv\s+\S+\s+/dev/null)"),
     "Rule 4: deleting files or folders is not allowed. Ask the owner to do it."),
    (DB_DESTRUCTIVE, "Rule 3: deleting database data (delete, drop, truncate, reset) is never allowed."),
    (cmd_word(["curl", "wget", "nc", "ncat", "netcat", "socat", "ssh", "scp", "sftp", "ftp", "telnet",
               "rsync", "ping", "dig", "nslookup", "whois", "traceroute", "npx", "bunx", "pnpx", "uvx",
               "brew", "apt", "apt-get", "yum", "dnf", "pip", "pip3", "pipx", "uv", "gem", "cargo",
               "conda", "poetry", "docker", "podman"]),
     "Rule 7: network access and downloads are not allowed. Ask the owner to run this."),
    (re.compile(
        r"(^|[" + SEP + r"])(npm|yarn|pnpm|bun)\s+(install|i|in|add|ci|publish|unpublish|update|up|upgrade"
        r"|dlx|create|exec|x|audit|outdated|login|adduser|view|info|search|link|deprecate|dist-tag"
        r"|owner|token|access|fund|init|global)\b"
        r"|-m\s+pip\b|\bhttp\.server\b|\bgo\s+(get|install|mod\s+download)\b"),
     "Rule 7: installing or publishing packages needs the network. Ask the owner to run this."),
    (cmd_word(["aws", "gcloud", "gsutil", "az", "vercel", "netlify", "heroku", "kubectl", "helm",
               "terraform", "pulumi", "flyctl", "railway", "doctl", "firebase", "supabase", "wrangler",
               "serverless", "sls"]),
     "Rule 7: cloud and deploy tools are not allowed."),
    (cmd_word(["sudo", "su", "doas"]), "Critical: sudo and su are not allowed."),
    (re.compile(r"\|\s*(\S*/)?(python[0-9.]*|node|deno|perl|ruby|php|(ba|z|da|k)?sh)\b"),
     "Critical: piping text into a shell or interpreter is not allowed."),
    (re.compile(r"\.agent-guard|hooksPath"), "Guardrails: touching the guard state or git hook path is not allowed."),
]

# Checks used on commands only.
COMMAND_BLOCKS = [
    (cmd_word(["kill", "pkill", "killall", "shutdown", "reboot", "halt", "launchctl", "crontab",
               "systemctl", "osascript", "open", "dd", "diskutil", "mkfs", "fdisk", "chown", "chgrp",
               "chflags", "xattr", "defaults", "mount", "umount", "nvram", "csrutil", "spctl",
               "networksetup", "scutil", "pmset", "truncate", "nohup", "disown"]),
     "Critical: system-level commands are not allowed."),
    (cmd_word(["env", "printenv", "security"]), "Secrets: printing environment or keychain data is not allowed."),
    (re.compile(r"(^|[;&|]\s*)(export|declare|typeset)\s+-p\b|(^|[;&|]\s*)set\s*($|[;&|])"),
     "Secrets: printing environment variables is not allowed."),
    (cmd_word(["eval", "exec", "source"]), "Hidden code: eval, exec, and source are not allowed."),
    (re.compile(
        r"(^|[" + SEP + r"])(\S*/)?(python[0-9.]*|node|nodejs|deno|bun|perl|ruby|php|lua)\s+(-\S+\s+)*"
        r"(-\w*[ceEp]\b|--eval\b|--print\b|-\s|-$|eval\b)"
        r"|(^|[" + SEP + r"])(\S*/)?(ba|z|da|k|fi)?sh\s+(-\S+\s+)*(-\w*c\b|-s\b|-\s|-$)"),
     "Hidden code: inline code (bash -c, python -c, node -e) is not allowed. Write a file instead."),
    (re.compile(r"<<|<\("), "Hidden code: heredocs and process substitution are not allowed. Use the Write tool."),
    (re.compile(r"(?<![&>|])&(?![&>])"), "Critical: background processes (&) are not allowed."),
]

# Rule 3: direct database access (allowed only when the owner asks).
DB_CLIENT = cmd_word(sorted(DB_TOOLS))

# Rule 5: paths outside the project folder.
HOME = re.compile(r"(^|[\s=:'\"])~(?=/|$|[\s'\";|&)])|\$HOME\b|\$\{HOME\}")
ABS_PATH = re.compile(r"(?<![\w.:/~$-])/[^\s;|&'\"`()<>]*")
PARENT_PATH = re.compile(r"[^\s;|&'\"`()<>]*\.\.[^\s;|&'\"`()<>]*")

# Redirects: group 2 is > or >>, group 3 is the target.
REDIRECT = re.compile(r"(?<![<>])(\d*|&)?(>>?)(?![>&])\|?\s*([^\s;&|)<>]+)")

# Secrets.
ENV_FILE = re.compile(r"(^|[\s/'\"=<])(\.env(\.[\w.-]+)?)(?=$|[\s'\";|&)<>])")


# ---------- state ----------

def read_state(name):
    try:
        with open(os.path.join(STATE_DIR, name)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def approved(session_id):
    s = read_state("approval.json")
    if s.get("approved") is not True:
        return False
    if time.time() - float(s.get("time", 0)) > APPROVAL_MAX_AGE:
        return False
    if session_id and s.get("session_id") and s["session_id"] != session_id:
        return False
    return True


def unlocked():
    return time.time() < float(read_state("unlock.json").get("until", 0))


# ---------- paths ----------

def inside(real_path):
    return real_path == ROOT or real_path.startswith(ROOT + os.sep)


def resolve(path, cwd):
    return os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))


def rel(real_path):
    return os.path.relpath(real_path, ROOT)


def is_secret_name(name):
    return re.match(r"^\.env(\..+)?$", name) is not None and name != ".env.example"


def is_protected(rel_path):
    for p in PROTECTED:
        if p.endswith("/"):
            if rel_path == p.rstrip("/") or rel_path.startswith(p):
                return True
        elif rel_path == p:
            return True
    return False


def is_db_file(rel_path):
    parts = rel_path.lower().split(os.sep)
    return parts[-1].endswith(".sql") or parts[-1].startswith("seed") or any(p in DB_FILE_DIRS for p in parts[:-1])


# ---------- commands ----------

def segments(cmd):
    """Split a shell command into simple commands, as token lists (best effort)."""
    for part in re.split(r"&&|\|\||[;|&\n]", cmd):
        try:
            tokens = shlex.split(part, posix=True)
        except ValueError:
            tokens = part.split()
        while tokens and re.match(r"^\w+=", tokens[0]):
            tokens = tokens[1:]
        if tokens:
            yield tokens


def git_problem(text):
    for m in GIT_WORD.finditer(text):
        rest = re.split(r"[;&|)\n`]", text[m.end():], maxsplit=1)[0]
        tokens = rest.split()
        if not tokens or tokens[0] not in READ_GIT:
            return "Rule 2: only git status, git diff, and git log are allowed. The owner runs every other git command."
        if any(t.split("=")[0] in BAD_GIT_FLAGS for t in tokens[1:]):
            return "Rule 2: this git option can write files or run programs."
    return None


def is_read_only_git(cmd):
    if re.search(r"[<>`]|\$\(", cmd):
        return False
    segs = list(segments(cmd))
    return bool(segs) and all(
        os.path.basename(s[0]) == "git" and len(s) > 1 and s[1] in READ_GIT for s in segs
    )


def first_arg(tokens):
    for t in tokens[1:]:
        if not t.startswith("-"):
            return t
    return ""


def is_read_only_segment(tokens, cwd):
    cmd0 = os.path.basename(tokens[0])
    if cmd0 in READ_CMDS:
        return True
    if cmd0 == "sed":
        return not any(t.startswith("-i") or t.startswith("--in-place") for t in tokens[1:])
    if cmd0 == "git":
        return len(tokens) > 1 and tokens[1] in READ_GIT
    runs = first_arg(tokens) if cmd0 in INTERPRETERS else tokens[0]
    return bool(runs) and rel(resolve(runs, cwd)) in GUARD_RUNNERS


def scan_script(text):
    """Return a reason if a script has a blocked operation, else None."""
    reason = git_problem(text)
    if reason:
        return reason
    for pattern, reason in COMMON_BLOCKS:
        if pattern.search(text):
            return reason
    return None


def scripts_run_by(cmd, cwd):
    """Find project files that the command would run or feed to a database."""
    found = []
    for tokens in segments(cmd):
        cmd0 = os.path.basename(tokens[0])
        candidates = [(tokens[0], False)]
        if cmd0 in INTERPRETERS or cmd0 in DB_TOOLS:
            candidates += [(t, True) for t in tokens[1:] if not t.startswith("-")]
        if cmd0 in ("npm", "yarn", "pnpm", "bun"):
            candidates.append(("package.json", True))
        if cmd0 == "make":
            candidates.append(("Makefile", True))
        candidates += [(t.lstrip("<"), True) for t in tokens if t.lstrip("<").lower().endswith(".sql")]
        for c, always in candidates:
            rp = resolve(c, cwd)
            if not inside(rp) or not os.path.isfile(rp) or rel(rp) in TRUSTED_SCRIPTS:
                continue
            if always or rp.endswith(SCRIPT_EXT) or os.access(rp, os.X_OK):
                found.append(rp)
    return found


def script_text(real_path):
    with open(real_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if os.path.basename(real_path) == "package.json":
        try:
            return "\n".join(str(v) for v in json.loads(text).get("scripts", {}).values())
        except (ValueError, AttributeError):
            return text
    return text


def check_segment(tokens, cwd):
    cmd0 = os.path.basename(tokens[0])
    args = [t for t in tokens[1:] if not t.startswith("-")]
    opts = [t for t in tokens[1:] if t.startswith("-")]

    if cmd0 == "chmod" and not (len(tokens) >= 3 and tokens[1] in ("+x", "u+x")):
        return "Critical: only chmod +x is allowed."
    if cmd0 == "find" and any(t in ("-exec", "-execdir", "-ok", "-okdir", "-fls") or t.startswith("-fprint") for t in tokens):
        return "Hidden code: find -exec is not allowed."

    if cmd0 in ("mv", "cp", "install", "ln") and len(args) >= 2:
        no_clobber = any(o == "--no-clobber" or (not o.startswith("--") and "n" in o) for o in opts)
        if cmd0 == "ln":
            no_clobber = not any(not o.startswith("--") and "f" in o for o in opts) and "--force" not in opts
        if not no_clobber:
            dest = resolve(args[-1], cwd)
            targets = [os.path.join(dest, os.path.basename(s.rstrip("/"))) for s in args[:-1]] if os.path.isdir(dest) else [dest]
            if any(os.path.exists(t) for t in targets):
                return "Rule 4: this would overwrite an existing file. Use the Edit tool instead."
    if cmd0 == "tee" and not any(o in ("-a", "--append") for o in opts):
        if any(os.path.exists(resolve(a, cwd)) for a in args):
            return "Rule 4: tee would overwrite an existing file."

    if not unlocked() and not is_read_only_segment(tokens, cwd):
        for t in tokens[1:] + [tokens[0]]:
            if is_protected(rel(resolve(t, cwd))):
                return "Guardrails: " + t + " is a locked guardrail file. Only the owner can unlock it."
    return None


def check_command(cmd, cwd):
    reason = git_problem(cmd)
    if reason:
        return BLOCK, reason
    for pattern, reason in COMMON_BLOCKS + COMMAND_BLOCKS:
        if pattern.search(cmd):
            return BLOCK, reason
    for m in ENV_FILE.finditer(cmd):
        if m.group(2) != ".env.example":
            return BLOCK, "Secrets: agents may not read or touch .env files."

    if HOME.search(cmd):
        return BLOCK, "Rule 5: paths outside the project folder (~ or $HOME) are not allowed."
    for m in ABS_PATH.finditer(cmd):
        p = m.group(0)
        if p in SAFE_ABS or p.startswith("/dev/fd/"):
            continue
        if not inside(os.path.realpath(p)):
            return BLOCK, "Rule 5: path outside the project folder is not allowed: " + p
    for m in PARENT_PATH.finditer(cmd):
        if not inside(resolve(m.group(0), cwd)):
            return BLOCK, "Rule 5: path outside the project folder is not allowed: " + m.group(0)
    if not inside(os.path.realpath(cwd)):
        return BLOCK, "Rule 5: the working folder is outside the project."

    for m in REDIRECT.finditer(cmd):
        target = m.group(3).strip("'\"")
        if target in SAFE_ABS:
            continue
        rp = resolve(target, cwd)
        if is_protected(rel(rp)) and not unlocked():
            return BLOCK, "Guardrails: " + target + " is a locked guardrail file."
        if m.group(2) == ">" and os.path.isfile(rp):
            return BLOCK, "Rule 4: > would overwrite " + target + ". Use the Edit tool instead."

    for tokens in segments(cmd):
        reason = check_segment(tokens, cwd)
        if reason:
            return BLOCK, reason

    for rp in scripts_run_by(cmd, cwd):
        reason = scan_script(script_text(rp))
        if reason:
            return BLOCK, "File " + rel(rp) + " has a blocked operation. " + reason

    if DB_CLIENT.search(cmd):
        return ASK, "Rule 3: DATABASE ACCESS. Allow only if the owner asked for this exact action."
    return ALLOW, ""


# ---------- files ----------

def check_path(path, cwd, writing):
    if path.startswith("~"):
        return BLOCK, "Rule 5: paths outside the project folder are not allowed."
    rp = resolve(path, cwd)
    if not inside(rp):
        return BLOCK, "Rule 5: path outside the project folder is not allowed: " + path
    if is_secret_name(os.path.basename(rp)):
        return BLOCK, "Secrets: agents may not read or write .env files."
    if writing and is_protected(rel(rp)) and not unlocked():
        return BLOCK, "Guardrails: " + rel(rp) + " is a locked guardrail file. Only the owner can unlock it."
    return ALLOW, ""


def new_text(tool, inp):
    if tool == "MultiEdit":
        return "\n".join(str(e.get("new_string", "")) for e in inp.get("edits") or [])
    for key in ("content", "new_string", "new_source"):
        if inp.get(key):
            return str(inp[key])
    return ""


# ---------- decision ----------

def decide(tool, inp, cwd, session_id=None):
    if tool in BLOCKED_TOOLS:
        return BLOCK, BLOCKED_TOOLS[tool]
    if tool.startswith("mcp__") and tool not in SAFE_MCP:
        return BLOCK, "Rule 7: MCP connectors reach outside services and are blocked."
    if tool == "Agent" and inp.get("isolation") in ("worktree", "remote"):
        return BLOCK, "Rule 2 and 7: worktree and remote agents are blocked."
    if inp.get("dangerouslyDisableSandbox"):
        return BLOCK, "Critical: running outside the sandbox is not allowed."
    if tool == "NotebookEdit" and inp.get("edit_mode") == "delete":
        return BLOCK, "Rule 4: deleting notebook cells is not allowed."

    if inp.get("command"):
        cmd = str(inp["command"])
        decision, reason = check_command(cmd, cwd)
        if decision == BLOCK or is_read_only_git(cmd):
            return decision, reason
        if not approved(session_id):
            return BLOCK, NO_APPROVAL
        return decision, reason

    writing = tool in WRITE_TOOLS
    paths = [str(inp[k]) for k in ("file_path", "notebook_path", "path") if inp.get(k)]
    pattern = str(inp.get("pattern") or "") if tool == "Glob" else ""
    if pattern.startswith(("/", "~")) or ".." in pattern:
        paths.append(pattern.split("*")[0] or "/")
    for p in paths:
        decision, reason = check_path(p, cwd, writing)
        if decision == BLOCK:
            return decision, reason

    if writing:
        text = new_text(tool, inp)
        for p in paths:
            if is_db_file(rel(resolve(p, cwd))) and DB_DESTRUCTIVE.search(text):
                return BLOCK, "Rule 3: database files (migrations, seeds, .sql) may not delete data."
        if not approved(session_id):
            return BLOCK, NO_APPROVAL
    return ALLOW, ""


def cli(args):
    if len(args) != 2 or args[0] not in ("--cmd", "--read", "--write"):
        print(__doc__, file=sys.stderr)
        return 2
    cwd = os.getcwd()
    if args[0] == "--cmd":
        decision, reason = check_command(args[1], cwd)
        if decision == ALLOW and not is_read_only_git(args[1]):
            decision, reason = ASK, "Rule 1: every command needs the owner's approval."
    else:
        decision, reason = check_path(args[1], cwd, args[0] == "--write")
        if decision == ALLOW and args[0] == "--write":
            decision, reason = ASK, "Rule 6: every file change needs the owner's approval."
    if decision == BLOCK:
        print("BLOCKED: " + reason)
        return 2
    if decision == ASK:
        print("ASK THE OWNER: " + reason)
        return 1
    print("ALLOW")
    return 0


def main():
    if len(sys.argv) > 1:
        return cli(sys.argv[1:])
    data = json.loads(sys.stdin.read() or "{}")
    tool = str(data.get("tool_name") or "")
    inp = data.get("tool_input") or {}
    if not tool and data.get("command"):
        inp = {"command": data["command"]}
    cwd = data.get("cwd") or os.getcwd()

    decision, reason = decide(tool, inp, cwd, data.get("session_id"))
    if decision == BLOCK:
        print("BLOCKED by project guardrails. " + reason + " Do not try another way. Tell the owner.", file=sys.stderr)
        return 2
    if decision == ASK:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # fail closed
        print("BLOCKED: guard error (" + str(e) + "). Ask the owner.", file=sys.stderr)
        sys.exit(2)
