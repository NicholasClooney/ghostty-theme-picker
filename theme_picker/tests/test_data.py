"""Tests for theme_picker.data YAML persistence."""

from theme_picker import data


def test_save_and_load_yaml_round_trips_last_seen_browse(tmp_path, monkeypatch):
    yaml_file = tmp_path / "themes.yaml"
    monkeypatch.setattr(data, "YAML_FILE", yaml_file)

    payload = {
        "starred": ["One Dark"],
        "dark": [{"name": "Dracula", "background": "#282a36", "bg_color": "black"}],
        "light": [],
    }

    data.save_yaml(
        payload,
        seen={"Nord", "Gruvbox Dark"},
        browse_cursor={"dark": "Nord"},
        last_seen_browse="Gruvbox Dark",
    )

    loaded = data.load_yaml()

    assert loaded["starred"] == ["One Dark"]
    assert loaded["dark"] == [{"name": "Dracula", "background": "#282a36", "bg_color": "black"}]
    assert loaded["seen"] == ["Gruvbox Dark", "Nord"]
    assert loaded["browse_cursor"] == {"dark": "Nord"}
    assert loaded["last_seen_browse"] == "Gruvbox Dark"
