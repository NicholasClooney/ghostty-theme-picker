"""Platform-aware path helpers for Ghostty config and theme discovery."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


SUPPORTED_PLATFORMS = {"darwin", "linux"}


def platform_name() -> str:
    return sys.platform


def is_supported_platform(platform: str | None = None) -> bool:
    current = platform or platform_name()
    return current in SUPPORTED_PLATFORMS


def xdg_config_home(env: dict[str, str] | None = None, home: Path | None = None) -> Path:
    env = env or os.environ
    if value := env.get("XDG_CONFIG_HOME"):
        return Path(value).expanduser()
    return (home or Path.home()) / ".config"


def ghostty_config_dir(env: dict[str, str] | None = None, home: Path | None = None) -> Path:
    return xdg_config_home(env=env, home=home) / "ghostty"


def macos_app_support_dir(home: Path | None = None) -> Path:
    return (home or Path.home()) / "Library" / "Application Support" / "com.mitchellh.ghostty"


def config_file_candidates(
    platform: str | None = None,
    env: dict[str, str] | None = None,
    home: Path | None = None,
) -> list[Path]:
    platform = platform or platform_name()
    xdg_dir = ghostty_config_dir(env=env, home=home)
    candidates = [
        xdg_dir / "config.ghostty",
        xdg_dir / "config",
    ]
    if platform == "darwin":
        app_support = macos_app_support_dir(home=home)
        candidates.extend(
            [
                app_support / "config.ghostty",
                app_support / "config",
            ]
        )
    return candidates


def active_config_file(
    platform: str | None = None,
    env: dict[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    candidates = config_file_candidates(platform=platform, env=env, home=home)
    existing = [path for path in candidates if path.exists()]
    if existing:
        return existing[-1]
    return candidates[0]


def theme_search_dirs(
    platform: str | None = None,
    env: dict[str, str] | None = None,
    home: Path | None = None,
    executable: str | None = None,
) -> list[Path]:
    platform = platform or platform_name()
    env = env or os.environ
    dirs: list[Path] = [ghostty_config_dir(env=env, home=home) / "themes"]

    if resource_dir := env.get("GHOSTTY_RESOURCES_DIR"):
        dirs.append(Path(resource_dir).expanduser() / "ghostty" / "themes")

    if platform == "darwin":
        dirs.append(Path("/Applications/Ghostty.app/Contents/Resources/ghostty/themes"))

    ghostty_exe = executable or shutil.which("ghostty")
    if ghostty_exe:
        exe_path = Path(ghostty_exe).resolve()
        dirs.extend(
            [
                exe_path.parent.parent / "share" / "ghostty" / "themes",
                exe_path.parent.parent.parent / "share" / "ghostty" / "themes",
            ]
        )

    dirs.extend(
        [
            Path("/usr/share/ghostty/themes"),
            Path("/usr/local/share/ghostty/themes"),
            Path("/opt/homebrew/share/ghostty/themes"),
            Path("/opt/local/share/ghostty/themes"),
            Path.home() / ".local" / "share" / "ghostty" / "themes",
            Path("/app/share/ghostty/themes"),
        ]
    )

    unique_dirs: list[Path] = []
    seen: set[Path] = set()
    for path in dirs:
        if path not in seen:
            unique_dirs.append(path)
            seen.add(path)
    return unique_dirs
