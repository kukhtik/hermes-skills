# Hermes Gateway Auto-start in Termux/proot

## Problem

Running `hermes` from Termux starts an interactive agent process. The gateway (`hermes gateway run`) is a separate daemon that must stay alive in the background to receive Telegram messages. After phone reboot or Termux session kill, the gateway does not restart automatically.

## Current Wrapper (Termux)

`/data/data/com.termux/files/usr/bin/hermes`:
```bash
#!/data/data/com.termux/files/usr/bin/bash
proot-distro login ubuntu -- /usr/local/bin/hermes "$@"
```

This starts `hermes` inside proot but does not manage a gateway background process.

## Working Solution — Check gateway.pid Before Starting

Replace the wrapper with:

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

**Key points:**
- Reads `~/.hermes/gateway.pid` which is JSON: `{"pid": 12345, ...}`
- `kill -0` checks if PID is still alive without sending a signal
- `set +m` in nohup prevents job-control warnings in non-interactive shells
- Gateway logs go to `/root/.hermes/logs/gateway.log`

## Verification Commands

```bash
# Inside proot: is gateway running?
pgrep -f "hermes gateway run"
cat ~/.hermes/gateway.pid 2>/dev/null

# Full state
cat ~/.hermes/gateway_state.json 2>/dev/null
```

## Boot Auto-start (Termux:Boot)

For automatic start when Android boots, install Termux:Boot and create:
`~/.termux/boot/start-hermes`:
```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
/data/data/com.termux/files/usr/bin/hermes gateway run &
disown
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Two gateway processes running | Check PID file + pgrep; kill stale processes |
| Gateway starts but Telegram not connected | Verify `TELEGRAM_BOT_TOKEN` in `~/.hermes/.env` |
| Gateway exits immediately | Check `~/.hermes/logs/` for errors; ensure proot container is running |
| `[hermes-gate] Starting gateway...` printed every time | `gateway.pid` file missing or stale; check `proot-distro login` execution context |
