---
name: hermes-on-android
description: "Deploy and manage Hermes Agent on Android via Termux + proot-distro Ubuntu. Covers gateway auto-start, git setup in headless containers, file access, and Termux-specific quirks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [android, termux, linux]
metadata:
  hermes:
    tags: [android, termux, proot, hermes, gateway, mobile, linux]
    related_skills: [github-auth]
---

# Hermes on Android (Termux + proot-distro)

## Environment Anatomy

| Layer | Path | Notes |
|-------|------|-------|
| Termux (Android) | `/data/data/com.termux/files/usr/` | Package manager, bash, hermes wrapper binary |
| proot-distro Ubuntu | `/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/` | Full Ubuntu rootfs running inside proot |
| Hermes config | `/root/.hermes/` inside proot | Same as desktop, but proot isolates it from Android FS |
| Hermes binary (in proot) | `/usr/local/bin/hermes` | Symlinked from `/opt/hermes-env/bin/hermes` |
| Termux wrapper | `/data/data/com.termux/files/usr/bin/hermes` | Bash script: `proot-distro login ubuntu -- /usr/local/bin/hermes "$@"` |

**Key constraint:** proot provides a full Linux userspace but **no pseudo-terminal (PTY)** for `git credential approve`, interactive prompts, or PTY-dependent tools unless explicitly allocated.

---

## Gateway Auto-Start on `hermes` Invocation

The Termux wrapper can be modified to auto-start the gateway before running the agent.

### Current Wrapper (default)

```bash
#!/data/data/com.termux/files/usr/bin/bash
proot-distro login ubuntu -- /usr/local/bin/hermes "$@"
```

### Auto-Start Wrapper

```bash
#!/data/data/com.termux/files/usr/bin/bash
# Auto-start gateway if not running

GATEWAY_PID=$(proot-distro login ubuntu -- bash -c \
    "cat /root/.hermes/gateway.pid 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"pid\",\"\"))'" 2>/dev/null)

if [ -z "$GATEWAY_PID" ] || ! kill -0 "$GATEWAY_PID" 2>/dev/null; then
    echo "[hermes-gate] Starting gateway..."
    proot-distro login ubuntu -- bash -c \
        "set +m; nohup /usr/local/bin/hermes gateway run > /root/.hermes/logs/gateway.log 2>&1 &"
    sleep 2
fi

proot-distro login ubuntu -- /usr/local/bin/hermes "$@"
```

**Backup the original before modifying:**
```bash
cp /data/data/com.termux/files/usr/bin/hermes /data/data/com.termux/files/usr/bin/hermes.backup
```

---

## GitHub Auth in proot (No TTY)

`git credential approve` reads credentials from stdin, which fails without a PTY in proot. **Do not use stdin-based credential approval.**

### Method: Direct File Write (Python)

```python
import os, re

# token from user input or secure source
token = "ghp_..."

cred_path = "/root/.git-credentials"
with open(cred_path, "w") as f:
    f.write(f"https://kukhtik:{token}@github.com\n")
os.chmod(cred_path, 0o600)

os.system("git config --global user.name kukhtik")
os.system("git config --global user.email kukhtik@users.noreply.github.com")
os.system("git config --global credential.helper store")
```

### Verification

```python
import urllib.request, json

with open("/root/.git-credentials", "r") as f:
    line = f.read().strip()
    token = line.split(":")[2].split("@")[0]

req = urllib.request.Request("https://api.github.com/user")
req.add_header("Authorization", f"token {token}")
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    print("Login:", data.get("login"))  # Should print username
```

### Pitfall: Agent Security Scan Masks Tokens

When the agent executes `terminal` or `execute_code` with a token literal, Hermes security scan replaces it with `***` before the command reaches the shell. **This corrupts the token.**

**Fixes:**
- Load token from a file written by the user in a real Termux terminal
- Use `execute_code` with Python reading the file, then construct the request in-memory
- Never paste raw tokens into `terminal()` or `execute_code` `code` parameter when the agent executes them

---

## File Access: Android ↔ proot

| Access | Method |
|--------|--------|
| Android storage → proot | `/storage/self/primary/` mounted inside proot at `/sdcard` and `/mnt/sdcard` |
| Termux home → proot | `/data/data/com.termux/files/home` bind-mounted |
| proot → Android | Files in `/root/` are isolated; use bind mounts or shared dirs |

**Telegram file delivery:** Hermes delivers files to `~/.hermes/cache/documents/` inside proot. Read with `read_file()` or Python, not system `cat` (encoding issues possible).

---

## Disk & Memory

- Check space: `df -h /` (shows Android partition mounted in proot)
- 5GB free is a practical minimum for Hermes + models + git repos
- proot containers share the same kernel; no VM overhead, but filesystem is emulated

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `git credential approve` silently does nothing | No PTY in proot | Write `~/.git-credentials` directly with Python |
| `curl` with token returns 401 in agent | Security scan replaced token with `***` | Read token from file in Python, then use `urllib.request` |
| `hermes` command hangs | Gateway already running + interactive mode conflict | Check `ps aux \| grep hermes`, kill stale processes |
| Gateway not reconnecting after phone sleep | Android Doze kills background processes | Use `nohup`, consider Termux:Wake Lock or cron job |
| `proot-distro should not be executed as root` | Running as root in Termux | Harmless warning; proot-distro runs as root inside container anyway |

---

## Quick Checklist

- [ ] `git --version` works in proot
- [ ] `python3` available in proot
- [ ] `~/.git-credentials` exists with `600` permissions
- [ ] `git config --global credential.helper` returns `store`
- [ ] `git ls-remote https://github.com/user/repo.git` succeeds (empty repo → exit 0, no output)
- [ ] Gateway PID file at `/root/.hermes/gateway.pid` valid
- [ ] `/data/data/com.termux/files/usr/bin/hermes` wrapper auto-starts gateway
