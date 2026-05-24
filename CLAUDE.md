# CLAUDE.md

Instructions for AI agents working on ghostty-theme-picker.

## Project overview

A curses TUI for browsing and managing Ghostty terminal themes. Two-column layout (dark/light), with starring, favorites, and browse sections. Seen themes are visually dimmed, and browse cursor persists across sessions. Uses a functional core / imperative shell architecture.

## Setup

```bash
mise install && uv sync
```

## Running tests

```bash
uv run pytest
```

Tests are in `theme_picker/tests/`. They cover the pure functional core only, no filesystem or curses dependencies. Use `mock_classify_theme()` from `test_core.py` for deterministic classification in tests.

## Architecture

- **`core.py`** is the pure functional core. All state transitions live here as functions that take `PickerState` and return `PickerState`. No I/O. This is the most important file to keep pure.
- **`data.py`** handles all filesystem I/O for theme data (`~/.config/ghostty/themes.yaml`, classification cache, theme files).
- **`config.py`** reads/writes the Ghostty config file at `~/.config/ghostty/config` and sends `USR2` to reload.
- **`cli.py`** is the curses shell. It should stay thin: read a key, dispatch to a core action, apply the side effect (set_theme), render.

## Key conventions

- Action functions return `tuple[PickerState, str | None]` where the string is a theme name to preview, or `None`.
- `classify_fn` is passed as a callback to keep core.py pure. In production it's `data.classify_theme`, in tests it's a mock.
- Data files live in `~/.config/ghostty/`, not in this repo. The repo contains only code and tests.
- `themes.yaml` is the single source of truth for favorites, starred, seen set, and browse cursor. `generate.py` only rebuilds the classification cache and refreshes metadata, never overwrites user state.

## Keybindings

When adding or changing keybindings, update all three places:

1. `cli.py` -- the actual key handling logic
2. `cli.py` title bar strings -- the in-TUI help text (both normal and g-prefix modes)
3. `README.md` "Keys" and "Jumps" sections -- the user-facing docs

## Commit messages

This repo enforces Conventional Commits in CI.

- Use `type: summary` or `type(scope): summary`
- Allowed types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`,
  `refactor`, `revert`, `style`, `test`
- Example: `docs(readme): document tmux theme reload color issue`

## Common mistakes

- Don't add I/O to `core.py`. If you need file access, add it to `data.py` or `config.py` and pass results in.
- Don't forget to call `rebuild(state)` after mutating `state.data` or `state.browse`.
- The `*` key must work on all item types (starred, favorite, browse), not just favorites.
