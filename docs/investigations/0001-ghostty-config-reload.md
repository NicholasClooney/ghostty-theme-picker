# 0001 — Ghostty config reload: why theme switching stopped working

## Background

The picker writes the selected theme to `~/.config/ghostty/config` and signals the running Ghostty process to reload via `SIGUSR2`. A cross-platform refactor (commit `1768683`) replaced `killall -USR2 ghostty` with `pkill -USR2 ghostty`, which silently broke live theme preview.

## What we tried

### `pkill -USR2 ghostty` — broken on macOS

`pkill` on macOS matches against the kernel's stored process name (the `comm` field), which is capped at 15 characters. Ghostty installs as an app bundle, so its process registers a name truncated from the full path:

```
COMM: /Applications/Gh   (truncated)
```

`pkill ghostty` finds no match and exits with code 1 — silently, because we used `check=False`. Result: config is written but Ghostty never reloads.

On Linux this is not an issue; the binary is just `ghostty`, so `pkill` works fine there.

### `pgrep ghostty | kill -USR2 <pid>` — unreliable on macOS

`pgrep` has the same truncated-comm matching problem as `pkill`. In manual testing it occasionally returned a PID (from a short-lived `ghostty +show-config` subprocess that happened to be running at the right moment), which made it look like it worked once, but it does not reliably find the app process.

Confirmed: `pgrep ghostty` returns exit 1 when the Ghostty app is the only ghostty process running.

### `ps aux | grep ghostty | kill -USR2 <pid>` — dangerous

`ps aux | grep` matches against the full command line, which includes our own process path (`ghostty-theme-picker`). Sending `SIGUSR2` to the picker process itself causes it to exit with code 159 (128 + SIGUSR2).

A more targeted filter (e.g. matching `Ghostty.app` or `/MacOS/ghostty`) would work but adds fragility around install path assumptions.

### `ghostty +show-config` for verification — false positive

`ghostty +show-config` reads and parses the config file on disk. It does not query the running app's state. Using it to confirm a reload merely confirms the file was written correctly — it cannot detect a broken signal delivery.

### `killall -USR2 ghostty` — works

`killall` (from `psmisc` on Linux, built-in on macOS) matches by the basename of the executable path, not the truncated comm field. It correctly finds and signals the Ghostty process on both platforms.

## Resolution

Reverted to `killall -USR2 ghostty`. This was the original implementation before the cross-platform refactor introduced the regression.

On Linux, `killall` comes from `psmisc`, which is pre-installed on most distributions. Documented as a requirement in the README.

## Relevant commits

| Commit | Description |
|--------|-------------|
| `1768683` | Introduced the regression (pkill) |
| `4833e7e` | Fixed: switched back to killall |
