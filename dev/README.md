# Development tools

Runtime implementations live in `src/`. This directory holds development-only tools:

- `desktop/`: native package builders, distribution asset import/export, GUI and integration tests.
- `shutter_sound/`: sound tests, standalone native emulators and reverse-engineering trace tools. Sound runtime moved to `src/shutter_sound/`.
- `vertical/`: vertical-display tests and worker build tools.
- `usb/`: historical standalone USB diagnostic experiments.
- `release/`: historical CLI/source publication tooling.

Fit checkpoints, private reference renders and generated validation evidence belong in ignored `build/`; distributed profile data belongs in ignored `desktop-assets/`.

See [source boundaries](../docs/en/code-map.md) / [代码目录与共用边界](../docs/zh-CN/code-map.md).
