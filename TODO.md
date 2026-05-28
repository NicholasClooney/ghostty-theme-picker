# TODO

## Keymap configuration

Allow users to remap keybindings via a config file (e.g. `~/.config/ghostty/theme-picker.yaml`) instead of being locked to the defaults hardcoded in `cli.py`.

The config should map action names to key sequences so users can swap e.g. star from `*` to `s`, or remap navigation to arrow keys only.

## Post-action cursor behaviour

When an item is starred, favorited, or removed, the cursor currently follows the item to its new position. Users should be able to configure what happens instead:

- **Stay**: cursor stays at the same index in the list (now pointing at the next item)
- **Follow**: cursor jumps to where the item landed (current behaviour)

This should be configurable per action (star, favorite, remove) in the same `theme-picker.yaml` config file.
