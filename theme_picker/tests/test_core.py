"""Unit tests for the theme_picker.core functional core."""

import pytest
from theme_picker.cli import _build_browse_cursor
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
    action_jump_section,
    action_jump_top,
    action_move,
    action_page_move,
    action_remove,
    action_star,
    action_switch_column,
    build_items,
    init_state,
    next_selectable,
    rebuild,
    track_seen,
)

# Mock classify_fn that returns predictable outputs
def mock_classify_theme(name: str) -> dict:
    mode = "light" if "light" in name.lower() or "white" in name.lower() else "dark"
    return {
        "name": name,
        "mode": mode,
        "background": "#ffffff" if mode == "light" else "#000000",
        "bg_color": "white" if mode == "light" else "black",
    }


@pytest.fixture
def sample_data():
    return {
        "starred": ["One Dark"],
        "dark": [
            {"name": "One Dark", "background": "#282c34", "bg_color": "dark gray"},
            {"name": "Dracula", "background": "#282a36", "bg_color": "black"},
        ],
        "light": [
            {"name": "Solarized Light", "background": "#fdf6e3", "bg_color": "cream"},
        ],
    }


@pytest.fixture
def sample_browse():
    return ["Gruvbox Dark", "Gruvbox Light", "Nord"]


@pytest.fixture
def sample_classifications():
    return {
        "One Dark": "dark",
        "Dracula": "dark",
        "Solarized Light": "light",
        "Gruvbox Dark": "dark",
        "Gruvbox Light": "light",
        "Nord": "dark",
    }


# ── Test Categories ──────────────────────────────────────────────────

def test_build_items(sample_data, sample_browse, sample_classifications):
    # Dark Mode
    dark_items = build_items(
        data=sample_data,
        browse=sample_browse,
        mode="dark",
        classifications=sample_classifications,
        classify_fn=mock_classify_theme,
    )
    # One Dark is starred, Dracula is favorite, Gruvbox Dark and Nord are browse
    assert len(dark_items) == 6
    assert dark_items[0] == {"type": ITEM_STARRED, "name": "One Dark"}
    assert dark_items[1] == {"type": ITEM_SEPARATOR, "label": "favorites"}
    assert dark_items[2] == {"type": ITEM_FAVORITE, "name": "Dracula", "bg_color": "black"}
    assert dark_items[3] == {"type": ITEM_SEPARATOR, "label": "browse"}
    assert dark_items[4] == {"type": ITEM_BROWSE, "name": "Gruvbox Dark"}
    assert dark_items[5] == {"type": ITEM_BROWSE, "name": "Nord"}

    # Light Mode
    light_items = build_items(
        data=sample_data,
        browse=sample_browse,
        mode="light",
        classifications=sample_classifications,
        classify_fn=mock_classify_theme,
    )
    # Solarized Light is favorite (no starred lights), Gruvbox Light is browse
    assert len(light_items) == 3
    assert light_items[0] == {"type": ITEM_FAVORITE, "name": "Solarized Light", "bg_color": "cream"}
    assert light_items[1] == {"type": ITEM_SEPARATOR, "label": "browse"}
    assert light_items[2] == {"type": ITEM_BROWSE, "name": "Gruvbox Light"}


def test_next_selectable(sample_data, sample_browse, sample_classifications):
    items = build_items(sample_data, sample_browse, "dark", sample_classifications, mock_classify_theme)
    # items list:
    # 0: Starred "One Dark"
    # 1: Separator "favorites"
    # 2: Favorite "Dracula"
    # 3: Separator "browse"
    # 4: Browse "Gruvbox Dark"

    # Check skipped separator going down
    assert next_selectable(items, 0, 1) == 2  # skips index 1
    # Check skipped separator going up
    assert next_selectable(items, 2, -1) == 0  # skips index 1
    # Check boundary down
    assert next_selectable(items, 5, 1) == 5
    # Check boundary up
    assert next_selectable(items, 0, -1) == 0


def test_action_star_unstar(sample_data, sample_browse, sample_classifications):
    # Setup initial state
    state = init_state(sample_data, sample_browse, sample_classifications, "Dracula", mock_classify_theme)

    # 1. Star Dracula (current is index 2, which is Dracula in dark column)
    assert state.columns[0][state.idx[0]]["name"] == "Dracula"
    state, preview = action_star(state, mock_classify_theme)

    # Dracula should now be in starred
    assert "Dracula" in state.data["starred"]
    # Rebuild will update items, Dracula is starred now
    starred_items = [i for i in state.columns[0] if i["type"] == ITEM_STARRED]
    assert len(starred_items) == 2
    assert {"type": ITEM_STARRED, "name": "Dracula"} in starred_items

    # 2. Unstar Dracula (which is now at index 1 of the rebuilt column)
    state.idx[0] = next(i for i, x in enumerate(state.columns[0]) if x.get("name") == "Dracula")
    state, preview = action_star(state, mock_classify_theme)
    assert "Dracula" not in state.data["starred"]


def test_action_star_from_browse(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)
    # Gruvbox Dark is browse. Let's star it.
    assert state.columns[0][state.idx[0]]["name"] == "Gruvbox Dark"
    state, preview = action_star(state, mock_classify_theme)

    assert "Gruvbox Dark" in state.data["starred"]
    assert "Gruvbox Dark" not in state.browse
    assert any(x["name"] == "Gruvbox Dark" for x in state.data["dark"])


def test_action_remove(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Dracula", mock_classify_theme)
    # Dracula is favorite
    state, preview = action_remove(state, mock_classify_theme)
    assert not any(x["name"] == "Dracula" for x in state.data["dark"])

    # Remove starred item
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    state, preview = action_remove(state, mock_classify_theme)
    assert "One Dark" not in state.data["starred"]
    assert not any(x["name"] == "One Dark" for x in state.data["dark"])


def test_action_add_favorite(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)
    # Gruvbox Dark is browse
    state, preview = action_add_favorite(state, mock_classify_theme)

    assert "Gruvbox Dark" not in state.browse
    assert any(x["name"] == "Gruvbox Dark" for x in state.data["dark"])
    assert "Gruvbox Dark" not in state.data["starred"]


def test_action_move(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    # Index 0 is One Dark. Move down.
    state, preview = action_move(state, 1)
    assert state.idx[0] == 2  # Skips separator at index 1
    assert preview == "Dracula"


def test_action_switch_column(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    assert state.col == 0 # Dark
    state, preview = action_switch_column(state, 1) # Switch right
    assert state.col == 1 # Light
    assert preview == "Solarized Light"


def test_action_page_move(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    # 5 items in dark column. Move down by 4 (half visible height of say 8).
    state, preview = action_page_move(state, 1, 8)
    assert state.idx[0] == 4  # Clamps to last selectable (Gruvbox Dark)
    assert preview == "Gruvbox Dark"


def test_track_seen(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)
    # Cursor is on a browse item
    assert state.columns[0][state.idx[0]]["type"] == ITEM_BROWSE
    assert len(state.seen) == 0

    # Track seen
    state = track_seen(state)
    assert "Gruvbox Dark" in state.seen

    # Move to Nord and track
    state, _ = action_move(state, 1)
    assert state.columns[0][state.idx[0]]["name"] == "Nord"
    state = track_seen(state)
    assert "Nord" in state.seen
    assert len(state.seen) == 2

    # Non-browse item should not be added
    state2 = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    state2 = track_seen(state2)
    assert len(state2.seen) == 0


def test_init_state(sample_data, sample_browse, sample_classifications):
    # Initialize with Dracula (dark theme)
    state = init_state(sample_data, sample_browse, sample_classifications, "Dracula", mock_classify_theme)
    assert state.col == 0
    assert state.columns[0][state.idx[0]]["name"] == "Dracula"

    # Initialize with Solarized Light (light theme)
    state2 = init_state(sample_data, sample_browse, sample_classifications, "Solarized Light", mock_classify_theme)
    assert state2.col == 1
    assert state2.columns[1][state2.idx[1]]["name"] == "Solarized Light"


# ── Position history + section jump tests ────────────────────────────


def test_position_history_push_and_back(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    assert state.idx[0] == 0  # One Dark

    # j/k moves do NOT push history (vim behavior)
    state, _ = action_move(state, 1)
    assert state.idx[0] == 2
    assert len(state.history) == 0

    # Jump actions DO push history
    state, _ = action_jump_bottom(state)  # -> Nord (idx 5)
    assert state.idx[0] == 5
    assert len(state.history) == 1

    state, _ = action_jump_top(state)  # -> One Dark (idx 0)
    assert state.idx[0] == 0
    assert len(state.history) == 2

    # Go back restores to pre-jump-top position
    state, preview = action_go_back(state)
    assert state.idx[0] == 5
    assert preview == "Nord"

    # Go back again restores to pre-jump-bottom position
    state, preview = action_go_back(state)
    assert state.idx[0] == 2
    assert preview == "Dracula"


def test_history_on_star_jump(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Dracula", mock_classify_theme)
    assert len(state.history) == 0

    # Star Dracula (it moves to starred section)
    state, _ = action_star(state, mock_classify_theme)

    # History was pushed before the star
    assert len(state.history) == 1

    # Go back pops and restores (clamped to valid position in rebuilt list)
    state, preview = action_go_back(state)
    assert len(state.history) == 0
    assert preview is not None  # lands on a selectable item


def test_history_on_add_favorite(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)
    assert len(state.history) == 0

    state, _ = action_add_favorite(state, mock_classify_theme)

    # History was pushed before the add
    assert len(state.history) == 1

    # Go back pops and restores (clamped to valid position in rebuilt list)
    state, preview = action_go_back(state)
    assert len(state.history) == 0


def test_section_jump_starred(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)
    # Start in browse section
    assert state.columns[0][state.idx[0]]["type"] == ITEM_BROWSE

    state, preview = action_jump_section(state, "starred")
    assert preview == "One Dark"
    assert state.columns[0][state.idx[0]]["type"] == ITEM_STARRED


def test_section_jump_browse(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    # Start in starred section
    assert state.columns[0][state.idx[0]]["type"] == ITEM_STARRED

    state, preview = action_jump_section(state, "browse")
    assert preview == "Gruvbox Dark"
    assert state.columns[0][state.idx[0]]["type"] == ITEM_BROWSE


def test_section_jump_favorites(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)

    state, preview = action_jump_section(state, "favorites")
    assert preview == "Dracula"
    assert state.columns[0][state.idx[0]]["type"] == ITEM_FAVORITE


def test_section_cursor_memory(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)

    # Jump to browse, move to Nord
    state, _ = action_jump_section(state, "browse")
    state, _ = action_move(state, 1)  # Gruvbox Dark -> Nord
    assert state.columns[0][state.idx[0]]["name"] == "Nord"

    # Jump to starred
    state, _ = action_jump_section(state, "starred")
    assert state.columns[0][state.idx[0]]["name"] == "One Dark"

    # Jump back to browse, should restore to Nord
    state, preview = action_jump_section(state, "browse")
    assert preview == "Nord"
    assert state.columns[0][state.idx[0]]["name"] == "Nord"


def test_jump_top_bottom(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)

    # Jump to top
    state, preview = action_jump_top(state)
    assert preview == "One Dark"
    assert state.idx[0] == 0

    # Jump to bottom
    state, preview = action_jump_bottom(state)
    assert preview == "Nord"
    assert state.idx[0] == 5  # last item in dark column


def test_jump_column(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    assert state.col == 0

    # Jump to light column
    state, preview = action_jump_column(state, 1)
    assert state.col == 1
    assert preview == "Solarized Light"

    # Jump to dark column
    state, preview = action_jump_column(state, 0)
    assert state.col == 0


def test_section_jump_pushes_history(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    orig_col = state.col
    orig_idx = state.idx[0]

    state, _ = action_jump_section(state, "browse")
    assert len(state.history) > 0

    # Go back should restore
    state, preview = action_go_back(state)
    assert state.col == orig_col
    assert state.idx[0] == orig_idx
    assert preview == "One Dark"


def test_section_cursor_not_fooled_by_moved_item(sample_data, sample_browse, sample_classifications):
    """After favoriting a browse theme, gu should not jump to that theme
    in the favorites section. It should go to the first browse item."""
    state = init_state(sample_data, sample_browse, sample_classifications, "Gruvbox Dark", mock_classify_theme)
    # Cursor is on Gruvbox Dark in browse
    assert state.columns[0][state.idx[0]]["type"] == ITEM_BROWSE
    assert state.columns[0][state.idx[0]]["name"] == "Gruvbox Dark"

    # Favorite it (moves from browse to favorites)
    state, _ = action_add_favorite(state, mock_classify_theme)

    # Jump to starred, then gu
    state, _ = action_jump_section(state, "starred")
    state, preview = action_jump_section(state, "browse")

    # Should land on an actual browse item, not Gruvbox Dark in favorites
    assert state.columns[0][state.idx[0]]["type"] == ITEM_BROWSE
    assert preview is not None


def test_go_back_empty_history(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)
    assert len(state.history) == 0

    # Should be a no-op
    state, preview = action_go_back(state)
    assert preview is None
    assert state.idx[0] == 0


def test_go_forward_restores_newer_jump(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)

    state, _ = action_jump_bottom(state)
    assert state.columns[0][state.idx[0]]["name"] == "Nord"

    state, back_preview = action_go_back(state)
    assert back_preview == "One Dark"
    assert state.columns[0][state.idx[0]]["name"] == "One Dark"

    state, forward_preview = action_go_forward(state)
    assert forward_preview == "Nord"
    assert state.columns[0][state.idx[0]]["name"] == "Nord"


def test_new_jump_clears_forward_history(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)

    state, _ = action_jump_bottom(state)
    state, _ = action_go_back(state)
    assert len(state.future) == 1

    state, _ = action_jump_section(state, "favorites")
    assert len(state.future) == 0


def test_build_browse_cursor_uses_live_browse_position(sample_data, sample_browse, sample_classifications):
    state = init_state(sample_data, sample_browse, sample_classifications, "One Dark", mock_classify_theme)

    state, _ = action_jump_section(state, "browse")
    state, _ = action_move(state, 1)  # Gruvbox Dark -> Nord
    assert state.columns[0][state.idx[0]]["name"] == "Nord"

    # Simulate quitting directly from browse without another section jump.
    state.section_cursors["browse"][0] = None

    browse_cursor = _build_browse_cursor(state)
    assert browse_cursor["dark"] == "Nord"
