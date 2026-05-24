"""Rebuild classification cache and refresh theme metadata.

Reads themes.yaml (the source of truth) and Ghostty's bundled theme files.
Updates background colors and bg_color labels for existing favorites,
and regenerates classified-themes.yaml for all themes in all-themes.txt.

Safe to re-run at any time. Never touches starred or review progress.
"""

import argparse
from importlib.metadata import version

from theme_picker.data import (
    classify,
    generate_classified,
    load_yaml,
    parse_bg,
    save_yaml,
)


def refresh_metadata(data: dict) -> int:
    """Re-read background colors from Ghostty theme files for all favorites.

    Returns the number of themes updated.
    """
    updated = 0
    for section in ("dark", "light"):
        for entry in data[section]:
            bg = parse_bg(entry["name"])
            if bg is None:
                continue
            mode, label = classify(bg)
            if entry.get("background") != bg or entry.get("bg_color") != label:
                entry["background"] = bg
                entry["bg_color"] = label
                updated += 1
    return updated


def main():
    parser = argparse.ArgumentParser(
        prog="ghostty-theme-generate",
        description="Refresh Ghostty theme metadata and classification cache.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('ghostty-theme-picker')}",
    )
    parser.parse_args()

    # Refresh metadata for existing favorites in themes.yaml
    data = load_yaml()
    updated = refresh_metadata(data)
    if updated:
        save_yaml(
            data,
            set(data.get("seen", [])),
            data.get("browse_cursor", {}),
            data.get("last_seen_browse"),
        )
        print(f"Updated metadata for {updated} themes in themes.yaml")
    else:
        print("All theme metadata up to date")

    # Rebuild classification cache
    generate_classified()


if __name__ == "__main__":
    main()
