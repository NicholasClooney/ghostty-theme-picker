"""Ghostty configuration management — read, write, and reload the active theme."""

import re
import subprocess

from theme_picker.paths import active_config_file, config_file_candidates, platform_name


def get_current_theme() -> str:
    theme = ""
    for path in config_file_candidates():
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if re.match(r"^theme\s*=", line):
                theme = line.split("=", 1)[1].strip()
    return theme


def _reload_command() -> list[str] | None:
    platform = platform_name()
    if platform in {"darwin", "linux"}:
        return ["pkill", "-USR2", "ghostty"]
    return None


def reload_config() -> None:
    cmd = _reload_command()
    if cmd is None:
        return
    try:
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def set_theme(name: str) -> None:
    config_path = active_config_file()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    text = config_path.read_text() if config_path.exists() else ""
    if re.search(r"^theme\s*=", text, re.MULTILINE):
        text = re.sub(r"^theme\s*=.*$", f"theme = {name}", text, flags=re.MULTILINE)
    elif text:
        text += f"\ntheme = {name}\n"
    else:
        text = f"theme = {name}\n"
    config_path.write_text(text)
    reload_config()
