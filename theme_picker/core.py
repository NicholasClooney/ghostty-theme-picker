"""Pure functional core for the Ghostty theme picker — state transitions with no side effects."""

from dataclasses import dataclass, field
from typing import Callable

# ── Item type constants ──────────────────────────────────────────────

ITEM_STARRED = "starred"
ITEM_FAVORITE = "favorite"
ITEM_BROWSE = "browse"
ITEM_SEPARATOR = "separator"

# ── State ────────────────────────────────────────────────────────────


@dataclass
class PickerState:
    """All mutable state for the theme picker TUI."""
    data: dict                                     # {starred, dark, light}
    browse: list[str]                              # browse theme names
    classifications: dict[str, str]                 # name -> "dark"/"light"
    seen: set[str] = field(default_factory=set)     # themes cursor has visited in browse
    last_seen_browse: str | None = None
    col: int = 0                                    # 0=dark, 1=light
    idx: list[int] = field(default_factory=lambda: [0, 0])
    scroll: list[int] = field(default_factory=lambda: [0, 0])
    columns: list[list[dict]] = field(default_factory=lambda: [[], []])
    history: list[tuple[int, int, int]] = field(default_factory=list)
    future: list[tuple[int, int, int]] = field(default_factory=list)
    section_cursors: dict[str, list[tuple[str, int] | None]] = field(
        default_factory=lambda: {"starred": [None, None],
                                 "favorites": [None, None],
                                 "browse": [None, None]}
    )


# ── Pure helper functions ────────────────────────────────────────────


def build_items(data: dict, browse: list[str], mode: str,
                classifications: dict[str, str],
                classify_fn: Callable | None = None) -> list[dict]:
    """Build display list for one column (dark or light)."""
    items = []

    # Starred section (filtered to this mode)
    for name in data["starred"]:
        theme_mode = classifications.get(name)
        if theme_mode is None and classify_fn is not None:
            info = classify_fn(name)
            theme_mode = info["mode"] if info else None
        if theme_mode != mode:
            continue
        items.append({"type": ITEM_STARRED, "name": name})

    # Separator between starred and favorites
    if items:
        items.append({"type": ITEM_SEPARATOR, "label": "favorites"})

    # Favorites for this mode, excluding starred
    starred_set = set(data["starred"])
    section = data[mode]
    favorites = []
    for t in section:
        if t["name"] not in starred_set:
            favorites.append({"type": ITEM_FAVORITE, "name": t["name"],
                              "bg_color": t.get("bg_color", "")})
    favorites.sort(key=lambda x: x["name"].lower())
    items.extend(favorites)

    # Browse section (filtered to this mode)
    mode_browse = [n for n in browse if classifications.get(n) == mode]
    if mode_browse:
        items.append({"type": ITEM_SEPARATOR, "label": "browse"})
        for name in mode_browse:
            items.append({"type": ITEM_BROWSE, "name": name})

    return items


def next_selectable(items, idx, direction=1):
    """Find next selectable item in given direction."""
    i = idx + direction
    while 0 <= i < len(items):
        if items[i]["type"] != ITEM_SEPARATOR:
            return i
        i += direction
    return idx


def _find_item(items, name) -> int | None:
    for i, item in enumerate(items):
        if item.get("name") == name:
            return i
    return None


def _clamp_to_selectable(items, idx):
    if not items:
        return 0
    if idx < 0:
        idx = 0
    if idx >= len(items):
        idx = len(items) - 1
    if items[idx]["type"] == ITEM_SEPARATOR:
        fwd = next_selectable(items, idx - 1, 1)
        if fwd != idx - 1:
            return fwd
        return next_selectable(items, idx + 1, -1)
    return idx


def _remove_from_favorites(data, name):
    data["dark"] = [t for t in data["dark"] if t["name"] != name]
    data["light"] = [t for t in data["light"] if t["name"] != name]


def _current_section(items, idx) -> str | None:
    """Return section type for the item at idx."""
    if not items or idx < 0 or idx >= len(items):
        return None
    item = items[idx]
    if item["type"] == ITEM_SEPARATOR:
        return None
    return {"starred": "starred", "favorite": "favorites",
            "browse": "browse"}.get(item["type"])


def _find_section_start(items, section_type) -> int | None:
    """Find first selectable item in a section."""
    type_map = {"starred": ITEM_STARRED, "favorites": ITEM_FAVORITE,
                "browse": ITEM_BROWSE}
    target = type_map.get(section_type)
    if target is None:
        return None
    for i, item in enumerate(items):
        if item["type"] == target:
            return i
    return None


def _save_section_cursor(state: 'PickerState') -> 'PickerState':
    """Save current theme name and index to section_cursors for the current section."""
    items = state.columns[state.col]
    if not items:
        return state
    section = _current_section(items, state.idx[state.col])
    if section is None:
        return state
    name = items[state.idx[state.col]].get("name")
    idx = state.idx[state.col]
    state.section_cursors[section][state.col] = (name, idx)
    return state


# ── Rebuild ──────────────────────────────────────────────────────────


def rebuild(state: PickerState,
            classify_fn: Callable | None = None) -> PickerState:
    """Rebuild columns from current state data."""
    state.columns[0] = build_items(
        state.data, state.browse, "dark",
        state.classifications, classify_fn)
    state.columns[1] = build_items(
        state.data, state.browse, "light",
        state.classifications, classify_fn)
    return state


# ── History + jump actions ────────────────────────────────────────────


def action_push_history(state: PickerState) -> PickerState:
    """Push current position onto history stack."""
    state.history.append((state.col, state.idx[0], state.idx[1]))
    state.future.clear()
    return state


def action_go_back(state: PickerState) -> tuple[PickerState, str | None]:
    """Pop history and restore position. No-op if history is empty."""
    if not state.history:
        return state, None
    state.future.append((state.col, state.idx[0], state.idx[1]))
    col, idx0, idx1 = state.history.pop()
    state.col = col
    state.idx[0] = _clamp_to_selectable(state.columns[0], idx0) if state.columns[0] else 0
    state.idx[1] = _clamp_to_selectable(state.columns[1], idx1) if state.columns[1] else 0
    items = state.columns[state.col]
    if items and state.idx[state.col] < len(items):
        return state, items[state.idx[state.col]]["name"]
    return state, None


def action_go_forward(state: PickerState) -> tuple[PickerState, str | None]:
    """Pop future history and restore position. No-op if future is empty."""
    if not state.future:
        return state, None
    state.history.append((state.col, state.idx[0], state.idx[1]))
    col, idx0, idx1 = state.future.pop()
    state.col = col
    state.idx[0] = _clamp_to_selectable(state.columns[0], idx0) if state.columns[0] else 0
    state.idx[1] = _clamp_to_selectable(state.columns[1], idx1) if state.columns[1] else 0
    items = state.columns[state.col]
    if items and state.idx[state.col] < len(items):
        return state, items[state.idx[state.col]]["name"]
    return state, None


def action_jump_section(state: PickerState,
                        section: str) -> tuple[PickerState, str | None]:
    """Jump to a section in the current column. Pushes history first."""
    items = state.columns[state.col]
    if not items:
        return state, None
    # Check if section exists in current column
    target = _find_section_start(items, section)
    if target is None:
        return state, None
    state = _save_section_cursor(state)
    state = action_push_history(state)
    # Try to restore saved cursor for this section
    saved = state.section_cursors[section][state.col]
    if saved is not None:
        saved_name, saved_idx = saved
        found = _find_item(items, saved_name)
        if found is not None and _current_section(items, found) == section:
            # Theme still in this section, jump to it
            state.idx[state.col] = found
            return state, items[found]["name"]
        # Theme moved out of section. Try the same index position,
        # clamped to a selectable item. Try forward first, then backward.
        candidate = _clamp_to_selectable(items, saved_idx)
        if _current_section(items, candidate) == section:
            state.idx[state.col] = candidate
            return state, items[candidate]["name"]
        # Clamped outside the section, try the neighbor before saved_idx
        candidate = next_selectable(items, saved_idx, -1)
        if _current_section(items, candidate) == section:
            state.idx[state.col] = candidate
            return state, items[candidate]["name"]
    state.idx[state.col] = target
    return state, items[target]["name"]


def action_jump_column(state: PickerState,
                       col: int) -> tuple[PickerState, str | None]:
    """Jump to a specific column (0=dark, 1=light). Pushes history first."""
    if col < 0 or col > 1 or not state.columns[col]:
        return state, None
    if col == state.col:
        return state, None
    state = _save_section_cursor(state)
    state = action_push_history(state)
    state.col = col
    items = state.columns[col]
    if items:
        return state, items[state.idx[col]]["name"]
    return state, None


def action_jump_top(state: PickerState) -> tuple[PickerState, str | None]:
    """Jump to first selectable item in current column."""
    items = state.columns[state.col]
    if not items:
        return state, None
    state = _save_section_cursor(state)
    state = action_push_history(state)
    target = next_selectable(items, -1, 1)
    state.idx[state.col] = target
    return state, items[target]["name"]


def action_jump_bottom(state: PickerState) -> tuple[PickerState, str | None]:
    """Jump to last selectable item in current column."""
    items = state.columns[state.col]
    if not items:
        return state, None
    state = _save_section_cursor(state)
    state = action_push_history(state)
    target = next_selectable(items, len(items), -1)
    state.idx[state.col] = target
    return state, items[target]["name"]


def action_jump_last_seen_browse(state: PickerState) -> tuple[PickerState, str | None]:
    """Jump to the most recently seen browse item across both columns."""
    if state.last_seen_browse is None:
        return state, None

    for col, items in enumerate(state.columns):
        found = _find_item(items, state.last_seen_browse)
        if found is None or _current_section(items, found) != "browse":
            continue
        state = _save_section_cursor(state)
        state = action_push_history(state)
        state.col = col
        state.idx[col] = found
        return state, items[found]["name"]

    return state, None


# ── Action functions ─────────────────────────────────────────────────


def action_move(state: PickerState, direction: int) -> tuple[PickerState, str | None]:
    """Move cursor up (direction=-1) or down (direction=1).

    Single-step motion does not push history (matches vim behavior where
    j/k are not jumps).
    """
    items = state.columns[state.col]
    if not items:
        return state, None
    new_idx = next_selectable(items, state.idx[state.col], direction)
    if new_idx != state.idx[state.col]:
        state = _save_section_cursor(state)
        state.idx[state.col] = new_idx
        return state, items[new_idx]["name"]
    return state, None


def action_page_move(state: PickerState, direction: int,
                     visible: int) -> tuple[PickerState, str | None]:
    """Move cursor by half a page."""
    items = state.columns[state.col]
    if not items:
        return state, None
    half = max(1, visible // 2)
    target = state.idx[state.col] + (half * direction)
    target = max(0, min(target, len(items) - 1))
    target = _clamp_to_selectable(items, target)
    if target != state.idx[state.col]:
        state = _save_section_cursor(state)
        state = action_push_history(state)
        state.idx[state.col] = target
        return state, items[target]["name"]
    return state, None


def action_switch_column(state: PickerState,
                         direction: int) -> tuple[PickerState, str | None]:
    """Switch to other column. direction: -1=left, 1=right."""
    new_col = state.col + direction
    if new_col < 0 or new_col > 1:
        return state, None
    if not state.columns[new_col]:
        return state, None
    state = _save_section_cursor(state)
    state = action_push_history(state)
    state.col = new_col
    items = state.columns[state.col]
    if items:
        return state, items[state.idx[state.col]]["name"]
    return state, None


def action_star(state: PickerState,
                classify_fn: Callable) -> tuple[PickerState, str | None]:
    """Toggle star on current item, or star directly from browse."""
    items = state.columns[state.col]
    if not items:
        return state, None
    item = items[state.idx[state.col]]
    state = _save_section_cursor(state)
    state = action_push_history(state)

    if item["type"] == ITEM_STARRED:
        # Unstar: remove from starred list
        name = item["name"]
        state.data["starred"].remove(name)
        state = rebuild(state, classify_fn)
        found = _find_item(state.columns[state.col], name)
        state.idx[state.col] = (
            found if found is not None
            else _clamp_to_selectable(state.columns[state.col], state.idx[state.col])
        )

    elif item["type"] == ITEM_FAVORITE:
        # Star a favorite
        name = item["name"]
        state.data["starred"].append(name)
        state = rebuild(state, classify_fn)
        found = _find_item(state.columns[state.col], name)
        state.idx[state.col] = (
            found if found is not None
            else _clamp_to_selectable(state.columns[state.col], state.idx[state.col])
        )

    elif item["type"] == ITEM_BROWSE:
        # Star from browse: add to favorites + starred
        name = item["name"]
        info = classify_fn(name)
        if info:
            entry = {"name": name, "background": info["background"],
                     "bg_color": info["bg_color"]}
            if info["mode"] == "dark":
                state.data["dark"].append(entry)
            else:
                state.data["light"].append(entry)
            state.data["starred"].append(name)
            state.browse.remove(name)
            state = rebuild(state, classify_fn)
            found = _find_item(state.columns[state.col], name)
            state.idx[state.col] = (
                found if found is not None
                else _clamp_to_selectable(state.columns[state.col], state.idx[state.col])
            )

    return state, None


def action_remove(state: PickerState,
                  classify_fn: Callable | None = None) -> tuple[PickerState, str | None]:
    """Remove current item from favorites/starred."""
    items = state.columns[state.col]
    if not items:
        return state, None
    item = items[state.idx[state.col]]
    state = _save_section_cursor(state)
    state = action_push_history(state)

    if item["type"] == ITEM_STARRED:
        name = item["name"]
        state.data["starred"].remove(name)
        _remove_from_favorites(state.data, name)
        state = rebuild(state, classify_fn)
        state.idx[state.col] = min(state.idx[state.col], len(state.columns[state.col]) - 1)
        state.idx[state.col] = _clamp_to_selectable(state.columns[state.col], state.idx[state.col])

    elif item["type"] == ITEM_FAVORITE:
        name = item["name"]
        _remove_from_favorites(state.data, name)
        state = rebuild(state, classify_fn)
        state.idx[state.col] = min(state.idx[state.col], len(state.columns[state.col]) - 1)
        state.idx[state.col] = _clamp_to_selectable(state.columns[state.col], state.idx[state.col])

    return state, None


def action_add_favorite(state: PickerState,
                        classify_fn: Callable) -> tuple[PickerState, str | None]:
    """Add browse theme to favorites (Space key)."""
    items = state.columns[state.col]
    if not items:
        return state, None
    item = items[state.idx[state.col]]

    if item["type"] != ITEM_BROWSE:
        return state, None

    state = _save_section_cursor(state)
    state = action_push_history(state)

    name = item["name"]
    info = classify_fn(name)
    if info:
        entry = {"name": name, "background": info["background"],
                 "bg_color": info["bg_color"]}
        if info["mode"] == "dark":
            state.data["dark"].append(entry)
        else:
            state.data["light"].append(entry)
        state.browse.remove(name)
        state = rebuild(state, classify_fn)
        found = _find_item(state.columns[state.col], name)
        if found is not None:
            state.idx[state.col] = found
        else:
            state.idx[state.col] = min(state.idx[state.col], max(0, len(state.columns[state.col]) - 1))
            state.idx[state.col] = _clamp_to_selectable(state.columns[state.col], state.idx[state.col])

    return state, None


# ── Seen tracking / init ─────────────────────────────────────────────


def track_seen(state: PickerState) -> PickerState:
    """If cursor is on a browse item, add its name to seen set."""
    items = state.columns[state.col]
    if items and state.idx[state.col] < len(items):
        item = items[state.idx[state.col]]
        if item["type"] == ITEM_BROWSE:
            state.seen.add(item["name"])
            state.last_seen_browse = item["name"]
    return state


def init_state(data: dict, browse: list[str],
               classifications: dict[str, str],
               original_theme: str,
               classify_fn: Callable | None = None,
               seen: set[str] | None = None,
               browse_cursor: dict[str, str] | None = None,
               last_seen_browse: str | None = None) -> PickerState:
    """Create and initialize a PickerState for the given data."""
    state = PickerState(
        data=data,
        browse=browse,
        classifications=classifications,
        seen=seen if seen is not None else set(),
        last_seen_browse=last_seen_browse,
    )
    state = rebuild(state, classify_fn)

    if not state.columns[0] and not state.columns[1]:
        return state

    # Find current theme position
    for c in range(2):
        for i, item in enumerate(state.columns[c]):
            if item.get("name") == original_theme:
                state.col = c
                state.idx[c] = i
                break
        else:
            if state.columns[c]:
                state.idx[c] = next_selectable(state.columns[c], -1, 1)

    # Restore browse cursor from previous session
    if browse_cursor:
        mode_map = {0: "dark", 1: "light"}
        for c in range(2):
            mode = mode_map[c]
            cursor_name = browse_cursor.get(mode)
            if cursor_name:
                found = _find_item(state.columns[c], cursor_name)
                if found is not None and _current_section(state.columns[c], found) == "browse":
                    state.section_cursors["browse"][c] = (cursor_name, found)

    return state
