#!/usr/bin/env python3
"""Tests for hooks/guard.py.

  python3 -B hooks/test_guard.py

No files are created or changed. Approval and unlock state are faked.
Exit code 0 = all passed, 1 = some failed.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard  # noqa: E402

B, A, K = guard.BLOCK, guard.ALLOW, guard.ASK


def bash(cmd):
    return ("Bash", {"command": cmd})


def write(path, content="x"):
    return ("Write", {"file_path": path, "content": content})


def edit(path, new):
    return ("Edit", {"file_path": path, "old_string": "a", "new_string": new})


def read(path):
    return ("Read", {"file_path": path})


# (state, expected, call). States: "go" = approved, "none" = no approval,
# "unlocked" = approved and guardrail files unlocked.
CASES = [
    # Rule 2: git
    ("go", B, bash("git push")),
    ("go", B, bash("git push origin main --force")),
    ("go", B, bash("git commit -m 'x'")),
    ("go", B, bash("git add .")),
    ("go", B, bash("git rm a.txt")),
    ("go", B, bash("git reset --hard")),
    ("go", B, bash("git checkout main")),
    ("go", B, bash("git clean -fd")),
    ("go", B, bash("git config core.hooksPath x")),
    ("go", B, bash("git")),
    ("go", B, bash("/usr/bin/git push")),
    ("go", B, bash("git status && git push")),
    ("go", B, bash("git status; git commit -m x")),
    ("go", B, bash("echo $(git push)")),
    ("go", B, bash("echo `git push`")),
    ("go", B, bash("git -C src status")),
    ("go", B, bash("git log --output=out.txt")),
    ("go", B, bash("git diff --ext-diff")),
    ("go", B, bash("gh pr create")),
    ("go", A, bash("git status")),
    ("go", A, bash("git diff")),
    ("go", A, bash("git log --oneline -5")),
    ("go", A, bash("git diff hooks/guard.py")),
    ("none", A, bash("git status")),
    ("none", A, bash("git diff && git log")),
    ("none", B, bash("git log > out.txt")),

    # Rule 4: delete
    ("go", B, bash("rm a.txt")),
    ("go", B, bash("rm -rf /")),
    ("go", B, bash("rmdir src")),
    ("go", B, bash("unlink a.txt")),
    ("go", B, bash("shred a.txt")),
    ("go", B, bash("find . -name '*.log' -delete")),
    ("go", B, bash("find . -exec cat {} ;")),
    ("go", B, bash("ls | xargs rm")),
    ("go", B, bash("mv README.md /dev/null")),

    # Overwrite
    ("go", B, bash("echo x > README.md")),
    ("go", B, bash("cp .editorconfig README.md")),
    ("go", B, bash("mv .env.example README.md")),
    ("go", B, bash("ls | tee README.md")),
    ("go", B, bash("truncate -s 0 README.md")),
    ("go", B, bash("dd if=a of=b")),
    ("go", A, bash("echo hi > new_file.txt")),
    ("go", A, bash("mv a.txt b.txt")),
    ("go", A, bash("cp -n .editorconfig README.md")),
    ("go", A, bash("echo hi >> notes.txt")),

    # Rule 3: database
    ("go", B, bash("psql -c 'DELETE FROM users'")),
    ("go", B, bash("mysql -e 'DROP TABLE shows'")),
    ("go", B, bash("mongosh --eval 'db.users.deleteMany({})'")),
    ("go", B, bash("prisma migrate reset")),
    ("go", B, bash("prisma db push --force-reset")),
    ("go", B, bash("redis-cli FLUSHALL")),
    ("go", B, bash("sqlite3 app.db 'truncate table bookings'")),
    ("go", K, bash("psql -c 'SELECT 1'")),
    ("go", K, bash("prisma generate")),
    ("go", B, write("migrations/001_init.sql", "DROP TABLE users;")),
    ("go", B, write("db/seeds/users.js", "await User.deleteMany({})")),
    ("go", B, edit("prisma/migrations/x/migration.sql", "DELETE FROM bookings;")),
    ("go", A, write("migrations/001_init.sql", "CREATE TABLE users (id INT);")),

    # Rule 7: network
    ("go", B, bash("curl https://example.com")),
    ("go", B, bash("wget https://example.com")),
    ("go", B, bash("ssh user@host")),
    ("go", B, bash("scp a.txt user@host:")),
    ("go", B, bash("nc -l 8080")),
    ("go", B, bash("ping google.com")),
    ("go", B, bash("npm install express")),
    ("go", B, bash("npm i")),
    ("go", B, bash("npm publish")),
    ("go", B, bash("npx create-react-app web")),
    ("go", B, bash("yarn add react")),
    ("go", B, bash("pip install requests")),
    ("go", B, bash("python3 -m pip install requests")),
    ("go", B, bash("brew install node")),
    ("go", B, bash("docker pull postgres")),
    ("go", B, bash("python3 -m http.server")),
    ("go", B, ("WebFetch", {"url": "https://example.com"})),
    ("go", B, ("WebSearch", {"query": "x"})),
    ("go", B, ("mcp__claude_ai_Claude_Docs__create", {})),
    ("go", B, ("Artifact", {"file_path": "README.md"})),
    ("go", A, ("mcp__claude-vscode__getDiagnostics", {})),

    # Cloud
    ("go", B, bash("aws s3 ls")),
    ("go", B, bash("vercel deploy")),
    ("go", B, bash("kubectl get pods")),
    ("go", B, bash("terraform apply")),
    ("go", B, bash("firebase deploy")),

    # System
    ("go", B, bash("sudo ls")),
    ("go", B, bash("kill 123")),
    ("go", B, bash("pkill node")),
    ("go", B, bash("shutdown -h now")),
    ("go", B, bash("launchctl list")),
    ("go", B, bash("crontab -l")),
    ("go", B, bash("open .")),
    ("go", B, bash("chown me a.txt")),
    ("go", B, bash("chmod 777 a.sh")),
    ("go", B, bash("chmod -R +x .")),
    ("go", A, bash("chmod +x run.sh")),
    ("go", B, bash("nohup node app.js")),
    ("go", B, bash("node app.js &")),

    # Hidden code
    ("go", B, bash("bash -c 'ls'")),
    ("go", B, bash("sh -c ls")),
    ("go", B, bash("python3 -c 'import os'")),
    ("go", B, bash("node -e '1'")),
    ("go", B, bash("perl -e 1")),
    ("go", B, bash("eval ls")),
    ("go", B, bash("source x.sh")),
    ("go", B, bash("cat <<EOF > a.txt")),
    ("go", B, bash("echo ls | bash")),
    ("go", B, bash("cat a.py | python3")),

    # Secrets
    ("go", B, bash("env")),
    ("go", B, bash("printenv")),
    ("go", B, bash("security find-generic-password -s x")),
    ("go", B, bash("export -p")),
    ("go", B, bash("cat .env")),
    ("go", B, bash("cp .env.example .env")),
    ("go", B, read(".env")),
    ("go", B, read(".env.local")),
    ("go", B, write(".env", "KEY=1")),
    ("go", A, read(".env.example")),

    # Rule 5: outside folder
    ("go", B, bash("cat ~/.ssh/id_rsa")),
    ("go", B, bash("ls ~")),
    ("go", B, bash("ls $HOME")),
    ("go", B, bash("ls ..")),
    ("go", B, bash("cat /etc/passwd")),
    ("go", B, bash("cd /")),
    ("go", B, read("/etc/passwd")),
    ("go", B, read("../other/file.txt")),
    ("go", B, read("~/.zshrc")),
    ("go", B, write("/tmp/x.txt")),
    ("go", B, write("../x.txt")),
    ("go", B, ("Glob", {"pattern": "../**/*.js"})),
    ("go", B, ("Grep", {"pattern": "x", "path": "/Users"})),
    ("go", A, bash("echo hi 2>/dev/null")),
    ("go", A, bash("ls 2>&1")),

    # Locked guardrail files
    ("go", B, write("hooks/guard.py")),
    ("go", B, edit("AGENTS.md", "x")),
    ("go", B, write(".claude/settings.json")),
    ("go", B, write(".githooks/pre-push")),
    ("go", B, write(".gitignore")),
    ("go", B, bash("sed -i '' 's/a/b/' hooks/guard.py")),
    ("go", B, bash("echo x >> AGENTS.md")),
    ("go", B, bash("chmod -x hooks/guard.py")),
    ("go", B, bash("./scripts/setup.sh")),
    ("go", B, bash("bash scripts/unlock-guardrails.sh 30")),
    ("go", B, bash("cat x > ~/.agent-guard/x/approval.json")),
    ("go", A, bash("cat hooks/guard.py")),
    ("go", A, bash("grep -n rule AGENTS.md")),
    ("go", A, bash("python3 -B hooks/test_guard.py")),
    ("go", A, bash("./scripts/check.sh")),
    ("go", A, read("hooks/guard.py")),
    ("unlocked", A, write("hooks/guard.py")),
    ("unlocked", A, bash("sed -i '' 's/a/b/' hooks/guard.py")),

    # Agent actions
    ("go", B, ("CronCreate", {})),
    ("go", B, ("RemoteTrigger", {})),
    ("go", B, ("Workflow", {})),
    ("go", B, ("PushNotification", {})),
    ("go", B, ("EnterWorktree", {})),
    ("go", B, ("Agent", {"prompt": "x", "isolation": "remote"})),
    ("go", A, ("Agent", {"prompt": "x"})),
    ("go", B, ("Bash", {"command": "ls", "dangerouslyDisableSandbox": True})),
    ("go", B, ("NotebookEdit", {"notebook_path": "a.ipynb", "edit_mode": "delete"})),

    # Rule 1 and 6: consent
    ("none", B, bash("ls")),
    ("none", B, bash("mkdir src")),
    ("none", B, write("src/app.js")),
    ("none", B, edit("README.md", "x")),
    ("none", A, read("README.md")),
    ("none", A, ("Glob", {"pattern": "**/*.md"})),
    ("none", A, ("Grep", {"pattern": "rule"})),
    ("go", A, bash("ls")),
    ("go", A, bash("mkdir src")),
    ("go", A, bash("npm test")),
    ("go", A, bash("npm run dev")),
    ("go", A, write("src/app.js", "console.log(1)")),
    ("go", A, edit("README.md", "x")),
]


def run_case(state, call):
    guard.approved = lambda session_id: state in ("go", "unlocked")
    guard.unlocked = lambda: state == "unlocked"
    tool, inp = call
    return guard.decide(tool, inp, guard.ROOT)


def main():
    real_approved, real_unlocked, real_text = guard.approved, guard.unlocked, guard.script_text
    failed = 0

    for state, expected, call in CASES:
        got, reason = run_case(state, call)
        if got != expected:
            failed += 1
            print("FAIL [%s] expected %s, got %s: %s %s  (%s)" % (state, expected, got, call[0], call[1], reason))

    # A script that hides a blocked command is caught when it runs.
    guard.script_text = lambda path: "git push origin main"
    got, _ = run_case("go", bash("python3 README.md"))
    guard.script_text = real_text
    if got != B:
        failed += 1
        print("FAIL script scan: expected block, got %s" % got)

    guard.approved, guard.unlocked = real_approved, real_unlocked
    total = len(CASES) + 1
    print("%d of %d passed." % (total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
