---
name: termux-android-dev
description: "Develop on Android via Termux + proot-distro Ubuntu. Environment quirks, no-TTY workarounds, git setup, Hermes gateway auto-start."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [android, termux, proot, dev-environment, no-tty, git, gateway]
    related_skills: [github-auth]
---

# Android Termux + proot-distro Development

Target environment: Android phone/tablet running Termux, with an Ubuntu container via `proot-distro login ubuntu`. Hermes Agent runs inside the proot.

## Detection

```bash
# Confirmed by:
uname -a  # contains "PRoot-Distro"
echo $TERMUX_EXEC__PROC_SELF_EXE  # points to termux binary
echo $ANDROID_DATA  # set
which termux-info
```

## Key Environment Quirks

### No TTY / No Interactive Stdin

Inside proot, Hermes terminal sessions lack a true TTY. Commands that read from `/dev/stdin` or expect interactive input **silently fail or hang**.

**Affected:**
- `git credential approve` — expects credential lines on stdin; silently produces empty file
- `ssh-keygen` without `-N ""` — prompts for passphrase
- Any command with interactive prompts (`gh auth login`, `docker login`, etc.)

**Workaround 1: write files via Python instead of stdin**

```python
import os

def write_git_credentials(username, token, path='/root/.git-credentials'):
    """Write git credentials directly to file when stdin is unavailable."""
    with open(path, 'w') as f:
        f.write(f'https://{username}:{token}@github.com\n')
    os.chmod(path, 0o600)
```

**Workaround 2: receive token via Telegram file**

When Hermes security scan blocks token input (see below), the user can send the token as a `.txt` file in Telegram. The file lands in `~/.hermes/cache/documents/` and can be read by Python without triggering the security mask:

```python
import os, glob

# Find the latest .txt file from Telegram
cache_dir = '/root/.hermes/cache/documents/'
files = glob.glob(os.path.join(cache_dir, '*.txt'))
latest = max(files, key=os.path.getmtime)

with open(latest, 'r') as f:
    token = f.read().strip()

# Write to git credentials
with open('/root/.git-credentials', 'w') as f:
    f.write(f'https://kukhtik:{token}@github.com\n')
os.chmod('/root/.git-credentials', 0o600)
```

This avoids both the no-TTY problem and the security-scan masking problem simultaneously.

### Home Directory Persistence

`~/.hermes/` lives inside the proot filesystem (`/root` in the Ubuntu container). Proot-distro bind-mounts Android storage, so:
- `/storage/emulated/0` → Android internal storage (accessible from Android apps)
- `/data/data/com.termux/files/home` → Termux home (persistent across proot restarts)
- Proot container rootfs is NOT persistent if the container is removed — store critical data under bind-mounted paths or in Termux home

### Git Configuration in proot

Standard `git credential approve` does not work. Use the Python file-write pattern above, then:

```bash
git config --global credential.helper store
git config --global user.name "YourName"
git config --global user.email "your@email.com"
```

Verify with a public repo first, then private:
```bash
git ls-remote https://github.com/torvalds/linux.git  # public test
git ls-remote https://github.com/YOURUSER/private.git   # private test
```

### Hermes Gateway Auto-start

The Termux wrapper for Hermes is typically:

```bash
#!/data/data/com.termux/files/usr/bin/bash
proot-distro login ubuntu -- /usr/local/bin/hermes "$@"
```

**Problem:** Running `hermes` starts an interactive agent. The gateway (`hermes gateway run`) is a separate daemon that must stay alive in the background to receive Telegram messages. After phone reboot or Termux session kill, the gateway does not restart automatically.

**Solution — wrapper that checks gateway.pid before starting:**

```bash
#!/data/data/com.termux/files/usr/bin/bash
# Hermes wrapper: auto-start gateway if not running

# Check if gateway is already running inside proot
GATEWAY_PID=$(proot-distro login ubuntu -- bash -c "
  cat /root/.hermes/gateway.pid 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"pid\",\"\"))'
" 2>/dev/null)

if [ -z "$GATEWAY_PID" ] || ! kill -0 "$GATEWAY_PID" 2>/dev/null; then
    echo "[hermes-gate] Starting gateway..."
    proot-distro login ubuntu -- bash -c "set +m; nohup /usr/local/bin/hermes gateway run > /root/.hermes/logs/gateway.log 2>&1 &"
    sleep 2
fi

# Run hermes with passed arguments
proot-distro login ubuntu -- /usr/local/bin/hermes "$@"
```

Store gateway state in `~/.hermes/gateway.pid` (JSON format: `{"pid": 12345, ...}`) and check it before starting a second instance.

## References

- `references/git-no-tty.md` — Full transcript of the git credential debug session and the Python workaround.
- `references/gateway-autostart.md` — Gateway auto-start wrapper script and troubleshooting.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `git credential approve` silently fails | No TTY / stdin closed | Use Python file-write pattern |
| `git ls-remote` asks for password despite credentials file | `GIT_TERMINAL_PROMPT=0` or missing `credential.helper store` | Re-run `git config --global credential.helper store` |
| GitHub token 401 after showing in chat | GitHub auto-revoked leaked token | Generate new token via browser, never paste in plain text |
| Hermes gateway not receiving messages | Gateway not running | Check `pgrep -f "hermes gateway run"`, start if missing |
| Proot container resets on update | Container rootfs replaced on proot-distro upgrade | Keep dotfiles and configs in Termux home, not proot `/root` |

## Security Scan Token Masking

Hermes redacts GitHub PATs in terminal output (`ghp_...` → `***`). When the user pastes a raw token in chat, it is masked before reaching the shell, causing:
- Token written as literal `***` instead of real value
- GitHub API returns 401 Unauthorized
- Subsequent `git` operations fail

**Do NOT paste tokens in chat.** The two working alternatives on Android/Termux:

1. **User types locally in Termux** (if TTY available):
   ```bash
   python3 -c "
   token = input('Paste token: ')
   with open('/root/.git-credentials', 'w') as f:
       f.write('https://kukhtik:' + token + '@github.com\n')
   import os; os.chmod('/root/.git-credentials', 0o600)
   "
   ```

2. **User sends token as Telegram `.txt` file** — see "No TTY workaround 2" above.

Hermes redacts GitHub PATs in terminal output (`ghp_...` → `***`). When the user pastes a raw token in chat, it is masked before reaching the shell, causing:
- Token written as literal `***` instead of real value
- GitHub API returns 401 Unauthorized
- Subsequent `git` operations fail

**Do NOT paste tokens in chat.** The two working alternatives on Android/Termux:

1. **User types locally in Termux** (if TTY available):
   ```bash
   python3 -c "
   token = input('Paste token: ')
   with open('/root/.git-credentials', 'w') as f:
       f.write('https://kukhtik:' + token + '@github.com\n')
   import os; os.chmod('/root/.git-credentials', 0o600)
   "
   ```

2. **User sends token as Telegram `.txt` file** — see "No TTY workaround 2" above.