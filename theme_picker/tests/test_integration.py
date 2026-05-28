"""End-to-end integration tests that write to the real Ghostty config and verify
via `ghostty +show-config` that Ghostty actually picks up the change."""

import subprocess

import pytest

from theme_picker.config import get_current_theme, get_ghostty_active_theme, set_theme

PROBE_THEME = "TokyoNight"
RESTORE_THEME = "Catppuccin Frappe"


@pytest.fixture(autouse=True)
def restore_theme():
    original = get_current_theme()
    yield
    set_theme(original or RESTORE_THEME)


def test_set_theme_is_confirmed_by_ghostty():
    assert subprocess.run(["killall", "-0", "ghostty"], capture_output=True).returncode == 0, (
        "Ghostty is not running -- cannot verify theme reload end-to-end."
    )
    set_theme(PROBE_THEME)
    active = get_ghostty_active_theme()
    assert active == PROBE_THEME, (
        f"Ghostty reported '{active}' after setting '{PROBE_THEME}'. "
        "Config was written but Ghostty did not pick it up."
    )
