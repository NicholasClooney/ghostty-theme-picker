"""CLI implementation and curses interface for the Ghostty theme picker."""

import argparse
import curses
import sys
from importlib.metadata import version
from typing import Any

from theme_picker.core import (
    ITEM_BROWSE,
    ITEM_FAVORITE,
    ITEM_SEPARATOR,
    ITEM_STARRED,
    PickerState,
    action_add_favorite,
    action_go_back,
    action_go_forward,
    action_jump_bottom,
    action_jump_column,
    action_jump_last_seen_browse,
    action_jump_section,
    action_jump_top,
    action_move,
    action_page_move,
    action_remove,
    action_star,
    action_switch_column,
    init_state,
    rebuild,
    track_seen,
)
from theme_picker.config import get_current_theme, reload_config, set_theme
from theme_picker.data import (
    ALL_THEMES_FILE,
    classify,
    classify_theme,
    generate_classified,
    load_browse,
    load_classified,
    load_yaml,
    luminance,
    parse_bg,
    save_yaml,
)
from theme_picker.paths import is_supported_platform, platform_name

# Color pair IDs mapped to ANSI palette colors.
C_NORMAL = 0
C_RED = 2
C_GREEN = 3
C_YELLOW = 4
C_BLUE = 5
C_MAGENTA = 6
C_CYAN = 7
C_GRAY = 8        # bright black (palette 8)
C_HIGHLIGHT = 9    # list selection
C_STATUSBG = 10    # status bar segments
C_DIM = 11         # dimmed text for unfocused column

# Box-drawing chars
BOX_TL = "\u250c"  # +
BOX_TR = "\u2510"  # +
BOX_BL = "\u2514"  # +
BOX_BR = "\u2518"  # +
BOX_H = "\u2500"   # -
BOX_V = "\u2502"   # |
BOX_ML = "\u251c"  # +
BOX_MR = "\u2524"  # +

# Width of the bat-style code box (interior)
BOX_W = 48
GUTTER_W = 4  # " 1 |"

# Code lines: list of (text, color_pair_id) segments per line.
CODE_LINES = [
    [("import ", C_MAGENTA), ("os", C_NORMAL)],
    [("from ", C_MAGENTA), ("pathlib ", C_NORMAL),
     ("import ", C_MAGENTA), ("Path", C_CYAN)],
    [],
    [("def ", C_MAGENTA), ("greet", C_BLUE),
     ("(", C_NORMAL), ("name", C_RED), (": ", C_NORMAL),
     ("str", C_CYAN), (") -> ", C_NORMAL), ("str", C_CYAN),
     (":", C_NORMAL)],
    [("    ", C_NORMAL), ("# Say hello", C_GRAY)],
    [("    ", C_NORMAL), ("if ", C_MAGENTA),
     ("name ", C_NORMAL), ("== ", C_RED),
     ('"world"', C_GREEN), (":", C_NORMAL)],
    [("        ", C_NORMAL), ("return ", C_MAGENTA),
     ("f", C_GREEN), ('"Hello, ', C_GREEN), ("{", C_NORMAL),
     ("name", C_RED), ("}", C_NORMAL), ('!"', C_GREEN)],
    [("    ", C_NORMAL), ("count", C_NORMAL),
     (" = ", C_RED), ("42", C_YELLOW)],
]

PROMPT_SEGMENTS = [
    (" ~/projects ", C_BLUE, True),
    (" on ", C_NORMAL, False),
    (" \ue0a0 main ", C_MAGENTA, False),
    ("[+] ", C_YELLOW, False),
    ("via ", C_NORMAL, False),
    ("v3.12 ", C_GREEN, False),
    ("\u276f ", C_CYAN, False),
]

BODY_TEXT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Cras hendrerit aliquet turpis non dictum."
)


def init_colors() -> None:
    curses.use_default_colors()
    curses.init_pair(C_RED, curses.COLOR_RED, -1)
    curses.init_pair(C_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(C_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_BLUE, curses.COLOR_BLUE, -1)
    curses.init_pair(C_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(C_GRAY, 8, -1)
    curses.init_pair(C_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(C_STATUSBG, curses.COLOR_BLACK, curses.COLOR_BLUE)
    curses.init_pair(C_DIM, 8, -1)  # same as gray for dimmed unfocused


def _addstr(stdscr: Any, y: int, x: int, text: str, attr: int = 0) -> int:
    """Safe addstr that avoids writing to the bottom-right corner."""
    h, w = stdscr.getmaxyx()
    if y >= h or x >= w:
        return x + len(text)
    maxlen = w - x - 1 if y == h - 1 else w - x
    if maxlen <= 0:
        return x + len(text)
    stdscr.addnstr(y, x, text, maxlen, attr)
    return x + len(text)


def draw_preview(stdscr: Any, y: int, w: int) -> int:
    """Draw bat-style code box, prompt line, and body text. Returns next y."""
    box_w = min(BOX_W, w - 4)
    total_w = box_w + 2  # +2 for left/right border
    x0 = 1

    # -- "-> bat example.py" header --
    _addstr(stdscr, y, x0, "\u2192 ", curses.color_pair(C_CYAN))
    _addstr(stdscr, y, x0 + 2, "bat ", curses.color_pair(C_NORMAL))
    _addstr(stdscr, y, x0 + 6, "example.py", curses.color_pair(C_BLUE) | curses.A_UNDERLINE)
    y += 1

    # -- top border --
    header_text = " File: example.py "
    bar_left = (box_w - len(header_text)) // 2
    bar_right = box_w - len(header_text) - bar_left
    top = BOX_TL + BOX_H * bar_left + header_text + BOX_H * bar_right + BOX_TR
    _addstr(stdscr, y, x0, top, curses.color_pair(C_GRAY))
    y += 1

    # -- code lines inside box --
    for i, segments in enumerate(CODE_LINES):
        lineno = f" {i + 1} "
        _addstr(stdscr, y, x0, BOX_V, curses.color_pair(C_GRAY))
        _addstr(stdscr, y, x0 + 1, lineno, curses.color_pair(C_GRAY))
        _addstr(stdscr, y, x0 + 1 + len(lineno), BOX_V, curses.color_pair(C_GRAY))
        cx = x0 + 1 + len(lineno) + 1 + 1
        for text, color_id in segments:
            cx = _addstr(stdscr, y, cx, text, curses.color_pair(color_id))
        pad = total_w - 1 - (cx - x0)
        if pad > 0:
            _addstr(stdscr, y, cx, " " * pad, curses.color_pair(C_NORMAL))
        _addstr(stdscr, y, x0 + total_w - 1, BOX_V, curses.color_pair(C_GRAY))
        y += 1

    # -- bottom border --
    bottom = BOX_BL + BOX_H * box_w + BOX_BR
    _addstr(stdscr, y, x0, bottom, curses.color_pair(C_GRAY))
    y += 1

    # -- blank line --
    y += 1

    # -- prompt line --
    px = x0
    for text, color_id, bold in PROMPT_SEGMENTS:
        attr = curses.color_pair(color_id)
        if bold:
            attr |= curses.A_BOLD
        px = _addstr(stdscr, y, px, text, attr)
    y += 1

    # -- blank line --
    y += 1

    # -- body text --
    body = BODY_TEXT[:min(len(BODY_TEXT), (w - 2))]
    _addstr(stdscr, y, x0, body, curses.color_pair(C_NORMAL))
    y += 1
    if len(BODY_TEXT) > w - 2:
        _addstr(stdscr, y, x0, BODY_TEXT[w - 2:min(len(BODY_TEXT), 2 * (w - 2))],
                curses.color_pair(C_NORMAL))
        y += 1

    # -- separator --
    y += 1
    sep = BOX_H * min(total_w, w - 2)
    _addstr(stdscr, y, x0, sep, curses.color_pair(C_GRAY))
    y += 1

    return y


def draw_column(stdscr: Any, items: list[dict], idx: int, scroll: int,
                col_x: int, col_w: int, y_start: int, visible: int,
                focused: bool, seen: set[str]) -> None:
    """Draw one column of the theme list."""
    h, w = stdscr.getmaxyx()

    for row in range(visible):
        ti = scroll + row
        y = y_start + row
        if y >= h:
            break
        if ti >= len(items):
            break
        item = items[ti]

        if item["type"] == ITEM_SEPARATOR:
            label = item["label"]
            sep_line = f" {BOX_H*2} {label} {BOX_H * max(1, col_w - len(label) - 6)}"
            sep_line = sep_line[:col_w]
            attr = curses.color_pair(C_GRAY) if focused else curses.color_pair(C_DIM)
            _addstr(stdscr, y, col_x, sep_line, attr)
            continue

        # Gutter marker
        if item["type"] == ITEM_STARRED:
            gutter = " \u2605  "  # star
        else:
            gutter = "    "

        name = item["name"]
        line = f"{gutter}{name}"
        if len(line) > col_w:
            line = line[:col_w - 1]
        else:
            line = line.ljust(col_w)

        if ti == idx and focused:
            _addstr(stdscr, y, col_x, line,
                    curses.color_pair(C_HIGHLIGHT) | curses.A_BOLD)
        elif item["type"] == ITEM_STARRED:
            attr = curses.color_pair(C_YELLOW) if focused else curses.color_pair(C_DIM)
            _addstr(stdscr, y, col_x, line, attr)
        elif item["type"] == ITEM_BROWSE and name in seen:
            # Dim seen browse items
            _addstr(stdscr, y, col_x, line, curses.color_pair(C_DIM))
        else:
            attr = curses.color_pair(C_NORMAL) if focused else curses.color_pair(C_DIM)
            _addstr(stdscr, y, col_x, line, attr)


def _build_browse_cursor(state: PickerState) -> dict[str, str]:
    """Build browse_cursor dict from current section_cursors."""
    cursor = {}
    mode_map = {0: "dark", 1: "light"}
    for c in range(2):
        items = state.columns[c]
        idx = state.idx[c]
        if items and 0 <= idx < len(items) and items[idx]["type"] == ITEM_BROWSE:
            cursor[mode_map[c]] = items[idx]["name"]
            continue
        saved = state.section_cursors["browse"][c]
        if saved is not None:
            cursor[mode_map[c]] = saved[0]  # saved is (name, idx)
    return cursor


def _build_title(state: PickerState, pending_g: bool) -> str:
    """Build the top status/help bar text."""
    if pending_g:
        return "g-prefix: g=top d=dark l=light s=star f=fav u=browse j=seen (Esc=cancel)"
    jump_counts = f"jumps {len(state.history)}<- {len(state.future)}->"
    return (
        "j/k ^D/^U h/l Enter Esc *=star x=rm Space=add "
        f"G=bot g..=jump ^O/^I=back/fwd   {jump_counts}"
    )


def main_tui(stdscr: Any, state: PickerState, original_theme: str) -> bool:
    curses.curs_set(0)
    curses.raw()  # disable terminal driver so Ctrl-O isn't eaten as DISCARD
    init_colors()

    if not state.columns[0] and not state.columns[1]:
        return False

    pending_g = False

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        title = _build_title(state, pending_g)
        _addstr(stdscr, 0, 0, title[:w - 1], curses.A_BOLD)

        list_start = draw_preview(stdscr, 2, w)

        # Column headers
        col_w = (w - 1) // 2
        divider_x = col_w
        _addstr(stdscr, list_start, 0, "  DARK".ljust(col_w),
                curses.A_BOLD if state.col == 0 else curses.color_pair(C_DIM))
        _addstr(stdscr, list_start, divider_x, BOX_V, curses.color_pair(C_GRAY))
        _addstr(stdscr, list_start, divider_x + 1, "  LIGHT".ljust(col_w),
                curses.A_BOLD if state.col == 1 else curses.color_pair(C_DIM))
        list_start += 1

        visible = h - list_start - 1
        if visible < 1:
            visible = 1

        # Update scroll for both columns
        for c in range(2):
            items = state.columns[c]
            if not items:
                continue
            state.scroll[c] = max(0, state.idx[c] - visible // 2)
            state.scroll[c] = min(state.scroll[c], max(0, len(items) - visible))

        # Draw left column (dark)
        draw_column(stdscr, state.columns[0], state.idx[0], state.scroll[0],
                    0, col_w, list_start, visible, state.col == 0, state.seen)

        # Draw divider
        for row in range(visible):
            y = list_start + row
            if y >= h:
                break
            _addstr(stdscr, y, divider_x, BOX_V, curses.color_pair(C_GRAY))

        # Draw right column (light)
        draw_column(stdscr, state.columns[1], state.idx[1], state.scroll[1],
                    divider_x + 1, w - divider_x - 1, list_start, visible,
                    state.col == 1, state.seen)

        stdscr.refresh()

        # Track seen browse items
        state = track_seen(state)

        key = stdscr.getch()

        # g-prefix two-key sequences
        if pending_g:
            pending_g = False
            preview = None
            if key == ord("g"):
                state, preview = action_jump_top(state)
            elif key == ord("d"):
                state, preview = action_jump_column(state, 0)
            elif key == ord("l"):
                state, preview = action_jump_column(state, 1)
            elif key == ord("s"):
                state, preview = action_jump_section(state, "starred")
            elif key == ord("f"):
                state, preview = action_jump_section(state, "favorites")
            elif key == ord("u"):
                state, preview = action_jump_section(state, "browse")
            elif key == ord("j"):
                state, preview = action_jump_last_seen_browse(state)
            elif key == 27:  # Esc cancels g-prefix
                continue
            # else: unknown second key, ignore
            if preview:
                set_theme(preview)
            continue

        if key in (ord("q"), 27, 3):  # quit/cancel (3 = Ctrl-C in raw mode)
            break
        elif key == ord("g"):
            pending_g = True
        elif key == ord("G"):
            state, preview = action_jump_bottom(state)
            if preview:
                set_theme(preview)
        elif key == 15:  # Ctrl-O: go back
            state, preview = action_go_back(state)
            if preview:
                set_theme(preview)
        elif key == 9:  # Ctrl-I / Tab: go forward
            state, preview = action_go_forward(state)
            if preview:
                set_theme(preview)
        elif key in (curses.KEY_DOWN, ord("j")):
            state, preview = action_move(state, 1)
            if preview:
                set_theme(preview)
        elif key in (curses.KEY_UP, ord("k")):
            state, preview = action_move(state, -1)
            if preview:
                set_theme(preview)
        elif key == 4:  # Ctrl-D: half page down
            state, preview = action_page_move(state, 1, visible)
            if preview:
                set_theme(preview)
        elif key == 21:  # Ctrl-U: half page up
            state, preview = action_page_move(state, -1, visible)
            if preview:
                set_theme(preview)
        elif key in (curses.KEY_LEFT, ord("h")):
            state, preview = action_switch_column(state, -1)
            if preview:
                set_theme(preview)
        elif key in (curses.KEY_RIGHT, ord("l")):
            state, preview = action_switch_column(state, 1)
            if preview:
                set_theme(preview)
        elif key in (curses.KEY_ENTER, 10, 13):
            browse_cursor = _build_browse_cursor(state)
            save_yaml(state.data, state.seen, browse_cursor, state.last_seen_browse)
            return True
        elif key == ord("*"):
            state, _ = action_star(state, classify_theme)
            items = state.columns[state.col]
            if items and state.idx[state.col] < len(items):
                set_theme(items[state.idx[state.col]]["name"])
        elif key == ord("x"):
            state, _ = action_remove(state, classify_theme)
            items = state.columns[state.col]
            if items and state.idx[state.col] < len(items):
                set_theme(items[state.idx[state.col]]["name"])
        elif key == ord(" "):
            state, _ = action_add_favorite(state, classify_theme)
            items = state.columns[state.col]
            if items and state.idx[state.col] < len(items):
                set_theme(items[state.idx[state.col]]["name"])

    # Cancel: save state but restore original theme
    browse_cursor = _build_browse_cursor(state)
    save_yaml(state.data, state.seen, browse_cursor, state.last_seen_browse)
    return False


def run() -> None:
    if not is_supported_platform():
        print(
            "ghostty-theme-picker currently supports Ghostty on macOS and Linux. "
            f"Detected platform: {platform_name()}."
        )
        sys.exit(1)

    data = load_yaml()
    seen = set(data.pop("seen", []))
    browse_cursor = data.pop("browse_cursor", {})
    last_seen_browse = data.pop("last_seen_browse", None)

    # Filter out themes already in favorites or starred
    all_favorite_names = set(
        t["name"] for t in data["dark"]
    ) | set(
        t["name"] for t in data["light"]
    ) | set(data["starred"])
    browse = load_browse(all_favorite_names)

    # Load or generate classifications
    classifications = load_classified()
    if not classifications:
        print("Classification cache not found. Building...")
        classifications = generate_classified()

    if not data["dark"] and not data["light"] and not data["starred"] and not browse:
        print("No themes found.")
        sys.exit(1)

    original_theme = get_current_theme()

    state = init_state(
        data=data,
        browse=browse,
        classifications=classifications,
        original_theme=original_theme,
        classify_fn=classify_theme,
        seen=seen,
        browse_cursor=browse_cursor,
        last_seen_browse=last_seen_browse,
    )

    saved = curses.wrapper(main_tui, state, original_theme)

    if saved:
        final = get_current_theme()
        print(f"Saved: {final}")
    else:
        set_theme(original_theme)
        print(f"Cancelled. Restored: {original_theme}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ghostty-theme-picker",
        description="Browse and preview Ghostty themes in a curses TUI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('ghostty-theme-picker')}",
    )
    parser.parse_args()
    try:
        run()
    except KeyboardInterrupt:
        print("\nExited.")
        sys.exit(0)

if __name__ == "__main__":
    raise SystemExit(main())
