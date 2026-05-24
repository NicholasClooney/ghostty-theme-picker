# ghostty-theme-picker

A two-column TUI for browsing, starring, and managing [Ghostty](https://ghostty.org) terminal themes. Dark themes on the left, light on the right. Themes preview live as you navigate.

```
  DARK                          |  LIGHT
 *  Catppuccin Mocha            |  *  Bluloco Light
 -- favorites ------------------|  -- favorites ------------------
    Afterglow                   |     Belafonte Day
    Andromeda                   |     Breadog
 -- browse ----------------------|  -- browse --------------------
    Crayon Pony Fish            |     Dawnfox
    Cursor Dark                 |     ...
```

## Setup

Requires [mise](https://mise.jdx.dev) for toolchain management.

```bash
mise install          # installs python 3.12 + uv
uv sync               # creates venv and installs deps
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

### Jumps (g-prefix)

Press `g` then a second key to jump:

| Sequence | Action |
|----------|--------|
| `gg` | Top of column |
| `gd` / `gl` | Jump to dark / light column |
| `gs` | Jump to starred section |
| `gf` | Jump to favorites section |
| `gu` | Jump to browse section |

Jumping to a section remembers where you were last time. Starring, favoriting, removing, column switches, page moves, and section jumps all save your position so `Ctrl-O` can take you back.

### Workflow

1. All themes not yet in favorites or starred appear in the **browse** section.
2. Navigate browse themes. Themes you visit are dimmed (seen) so you can track your progress visually.
3. Press `Space` to promote to **favorites**, or `*` to go straight to **starred**.
4. Favorites, starred, seen state, and browse cursor position persist in `themes.yaml` across sessions.

## Data files

All data lives in `~/.config/ghostty/`:

| File | Purpose |
|------|---------|
| `themes.yaml` | Favorites, starred, seen themes, browse cursor (managed by the picker) |
| `all-themes.txt` | Full theme list from Ghostty, one per line, alphabetical |
| `classified-themes.yaml` | Auto-generated dark/light cache for all themes |
| `config` | Main Ghostty config (theme line is edited live during preview) |

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

Tests cover the functional core (no filesystem, no curses). See `theme_picker/tests/test_core.py`.
