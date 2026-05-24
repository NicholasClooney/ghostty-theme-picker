"""Tests for platform-aware Ghostty path and config helpers."""

from pathlib import Path

from theme_picker import config, paths


def test_config_file_candidates_include_macos_app_support(tmp_path):
    home = tmp_path / "home"
    candidates = paths.config_file_candidates(platform="darwin", home=home, env={})

    assert candidates == [
        home / ".config" / "ghostty" / "config.ghostty",
        home / ".config" / "ghostty" / "config",
        home / "Library" / "Application Support" / "com.mitchellh.ghostty" / "config.ghostty",
        home / "Library" / "Application Support" / "com.mitchellh.ghostty" / "config",
    ]


def test_active_config_file_prefers_highest_precedence_existing(tmp_path):
    home = tmp_path / "home"
    xdg_config = home / ".config" / "ghostty" / "config.ghostty"
    mac_config = home / "Library" / "Application Support" / "com.mitchellh.ghostty" / "config"
    xdg_config.parent.mkdir(parents=True)
    mac_config.parent.mkdir(parents=True)
    xdg_config.write_text("theme = early\n")
    mac_config.write_text("theme = late\n")

    selected = paths.active_config_file(platform="darwin", home=home, env={})

    assert selected == mac_config


def test_theme_search_dirs_include_user_and_executable_relative_paths(tmp_path):
    home = tmp_path / "home"
    bin_dir = tmp_path / "prefix" / "bin"
    executable = bin_dir / "ghostty"
    executable.parent.mkdir(parents=True)
    executable.write_text("")

    dirs = paths.theme_search_dirs(
        platform="linux",
        env={},
        home=home,
        executable=str(executable),
    )

    assert dirs[0] == home / ".config" / "ghostty" / "themes"
    assert tmp_path / "prefix" / "share" / "ghostty" / "themes" in dirs


def test_get_current_theme_uses_last_loaded_config(tmp_path, monkeypatch):
    first = tmp_path / "config.ghostty"
    second = tmp_path / "config"
    first.write_text("theme = One Dark\n")
    second.write_text("theme = Dracula\n")
    monkeypatch.setattr(config, "config_file_candidates", lambda: [first, second])

    assert config.get_current_theme() == "Dracula"


def test_set_theme_creates_preferred_config_file(tmp_path, monkeypatch):
    target = tmp_path / "ghostty" / "config.ghostty"
    monkeypatch.setattr(config, "active_config_file", lambda: target)
    monkeypatch.setattr(config, "reload_config", lambda: None)

    config.set_theme("Nord")

    assert target.read_text() == "theme = Nord\n"
