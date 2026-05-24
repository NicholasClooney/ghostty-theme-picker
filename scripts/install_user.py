#!/usr/bin/env python3
"""Install ghostty-theme-picker into uv's tool bin directory."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def uv_bin_dir() -> Path | None:
    try:
        result = subprocess.run(
            ["uv", "tool", "dir", "--bin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return Path(result.stdout.strip())


def install() -> int:
    cmd = [
        "uv",
        "tool",
        "install",
        "--reinstall",
        "--from",
        str(REPO_ROOT),
        "ghostty-theme-picker",
    ]
    print(f"Installing with: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print("uv is required but was not found on PATH.", file=sys.stderr)
        print("Install uv first, then rerun this script.", file=sys.stderr)
        return 1
    if result.returncode != 0:
        return result.returncode

    bin_dir = uv_bin_dir()
    print()
    print("Installed ghostty-theme-picker for the current user.")
    print("Commands:")
    print("  ghostty-theme-picker")
    print("  ghostty-theme-generate")
    if bin_dir is not None:
        print(f"uv tool bin directory: {bin_dir}")
        print(f"Expected executable: {bin_dir / 'ghostty-theme-picker'}")
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if bin_dir is not None and str(bin_dir) not in path_entries:
        print()
        print("Your current shell does not see the installed executable yet.")
        print("Run `uv tool update-shell`, then open a new terminal.")

    return 0


if __name__ == "__main__":
    raise SystemExit(install())
