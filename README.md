# ghostty-theme-picker

A two-column TUI for browsing, starring, and managing [Ghostty](https://ghostty.org) terminal themes. Dark themes on the left, light on the right. Themes preview live as you navigate.

Ghostty itself is currently supported on macOS and Linux, and this picker follows that support model.

<table>
<tr>
<td align="center">

<img width="800" alt="Dark Themes" src="https://github.com/user-attachments/assets/4fdea84d-fddb-4683-ad61-e670627e02b8" />

**Dark Themes**

</td>
<td align="center">

<img width="800" alt="Light Themes" src="https://github.com/user-attachments/assets/fd2c75c1-d796-4d4b-8df2-75e583f065b9" />

**Light Themes**

</td>
</tr>
</table>

<p align="center">
  <a href="https://youtu.be/nwjMTlvUArk">
    ▶️ Watch Demo Video on YouTube
  </a>
</p>

## Setup

Requires [mise](https://mise.jdx.dev) for toolchain management.

```bash
mise install          # installs python 3.12 + uv
uv sync               # creates venv and installs deps
```

## Install

For a user-level install that places the commands in uv's managed tool path:

```bash
python scripts/install_user.py
```

That installs these commands:

```bash
ghostty-theme-picker
ghostty-theme-generate
```

If your shell does not pick them up right away, run:

```bash
uv tool update-shell
```

## Usage

```bash
ghostty-theme-picker          # browse and pick themes
ghostty-theme-generate        # rebuild classification cache + refresh metadata
# or via uv
uv run ghostty-theme-picker
uv run ghostty-theme-generate
```

### Keys

| Key | Action |
|-----|--------|
| `j` / `k` / arrows | Navigate within column |
| `h` / `l` / left / right | Switch column |
| `Ctrl-D` / `Ctrl-U` | Half-page scroll |
| `Space` | Add browse theme to favorites |
| `*` | Star/unstar (works on favorites and browse) |
| `x` | Remove from favorites or starred |
| `Enter` | Save chosen theme and quit |
| `Esc` / `q` | Cancel, restore original theme, quit |
| `G` | Jump to bottom of column |
| `Ctrl-O` | Go back to previous position |
| `Ctrl-I` | Go forward to newer jump position |

### Jumps (g-prefix)

Press `g` then a second key to jump:

| Sequence | Action |
|----------|--------|
| `gg` | Top of column |
| `gd` / `gl` | Jump to dark / light column |
| `gs` | Jump to starred section |
| `gf` | Jump to favorites section |
| `gu` | Jump to browse section |
| `gj` | Jump to the last browse item you visited, across both columns |

Jumping to a section remembers where you were last time. Starring, favoriting, removing, column switches, page moves, and section jumps all save your position so `Ctrl-O` can take you back and `Ctrl-I` can move forward again.

### Workflow

1. All themes not yet in favorites or starred appear in the **browse** section.
2. Navigate browse themes. Themes you visit are dimmed (seen) so you can track your progress visually.
3. Press `Space` to promote to **favorites**, or `*` to go straight to **starred**.
4. Favorites, starred, seen state, last seen browse item, and browse cursor position persist in `themes.yaml` across sessions.

## Requirements

On Linux, live theme reload requires `killall` (from the `psmisc` package). It is pre-installed on most distributions but may be absent on minimal systems. Install it with your package manager if theme switching has no effect:

```
# Debian/Ubuntu
sudo apt install psmisc

# Fedora/RHEL
sudo dnf install psmisc

# Arch
sudo pacman -S psmisc
```

## Known issue

If you use the picker inside `tmux`, hot-reloading a new Ghostty theme can leave terminal colors looking wrong until the `tmux` client is detached and reattached. Restarting the picker alone may not be enough because `tmux` can keep stale terminal color/background information for the current client.

Workaround: detach with `Ctrl-b d`, then run `tmux attach`.

## Data files

Picker state lives in Ghostty's XDG config dir, usually `~/.config/ghostty/`:

| File | Purpose |
|------|---------|
| `themes.yaml` | Favorites, starred, seen themes, last seen browse item, browse cursor (managed by the picker) |
| `all-themes.txt` | Full theme list from Ghostty, one per line, alphabetical |
| `classified-themes.yaml` | Auto-generated dark/light cache for all themes |
| `config.ghostty` / `config` | Main Ghostty config (theme line is edited live during preview) |

## Architecture

Functional core / imperative shell:

- **`core.py`** -- Pure state machine. `PickerState` dataclass + action functions (`action_star`, `action_move`, `action_remove`, etc.) that take state and return state. No I/O, no curses.
- **`data.py`** -- Theme data I/O: YAML load/save, classification cache, background color parsing from Ghostty theme files.
- **`config.py`** -- Ghostty config read/write and live reload (sends `USR2` to Ghostty).
- **`cli.py`** -- Thin curses shell. Reads keys, calls core actions, renders two-column layout.
- **`generate.py`** -- Rebuilds `classified-themes.yaml` and refreshes background metadata in `themes.yaml`. Safe to re-run, never touches starred or review progress.

## Tests

```bash
uv run pytest
```

Tests cover the functional core plus targeted path and YAML persistence helpers. See `theme_picker/tests/`.
