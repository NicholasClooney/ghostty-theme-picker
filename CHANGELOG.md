# Changelog

## [0.4.0](https://github.com/NicholasClooney/ghostty-theme-picker/compare/v0.3.0...v0.4.0) (2026-05-28)


### Features

* **cli:** add --set flag and ghostty config verification ([dfb9d54](https://github.com/NicholasClooney/ghostty-theme-picker/commit/dfb9d544efdc497287cc4571caccb8aa5839e7b1))


### Bug Fixes

* **config:** use killall instead of pkill for USR2 reload on macOS ([4833e7e](https://github.com/NicholasClooney/ghostty-theme-picker/commit/4833e7ee120875fd4e8122a7e3fc7c1ba34e18fc))
* **paths:** treat empty env dict as explicit, not fallback to os.environ ([05ff0d1](https://github.com/NicholasClooney/ghostty-theme-picker/commit/05ff0d1480018e366c1433ff1697b72e9adb531f))


### Documentation

* add TODO for keymap config and post-action cursor behaviour ([f3c87d2](https://github.com/NicholasClooney/ghostty-theme-picker/commit/f3c87d2ba01bb3be32cf6f198f9e3f3665c4ca18))
* **investigations:** document ghostty reload signal investigation ([ab170ff](https://github.com/NicholasClooney/ghostty-theme-picker/commit/ab170ffbbcbde0d5db1259ecd0dc205310a65a11))
* **readme:** document killall requirement on linux ([ad19ad0](https://github.com/NicholasClooney/ghostty-theme-picker/commit/ad19ad0ed23ec0624b14814dfff0005519e0305d))

## [0.3.0](https://github.com/NicholasClooney/ghostty-theme-picker/compare/v0.2.0...v0.3.0) (2026-05-24)


### Features

* add cross-platform install and browse jump support ([1768683](https://github.com/NicholasClooney/ghostty-theme-picker/commit/1768683caa88667ae3c9d27771573f87520ac846))


### Documentation

* **agents:** document commit message convention ([c40d475](https://github.com/NicholasClooney/ghostty-theme-picker/commit/c40d475eb614db7d42181600602909b6b030effe))
* **readme:** add ctrl-i jump binding ([232381e](https://github.com/NicholasClooney/ghostty-theme-picker/commit/232381e694bd3a06372c8af88380254b0c7c04cb))
* **readme:** add screenshots and demo video to README ([7101619](https://github.com/NicholasClooney/ghostty-theme-picker/commit/7101619b74c7a938545baa819dd264c0e326e12c))
* **readme:** document tmux theme reload color issue ([7641642](https://github.com/NicholasClooney/ghostty-theme-picker/commit/7641642bc6edcd51f2445019af012555d1d533f7))

## [0.2.0](https://github.com/NicholasClooney/ghostty-theme-picker/compare/v0.1.0...v0.2.0) (2026-05-24)


### Features

* **jumps:** add forward history and persist browse cursor ([1f5b404](https://github.com/NicholasClooney/ghostty-theme-picker/commit/1f5b404dc384b97c025e500221a44f2e75d790c1))
* **ui:** show jump history counters ([9391080](https://github.com/NicholasClooney/ghostty-theme-picker/commit/93910803bb3099099fe397fcb914a6d667194927))
