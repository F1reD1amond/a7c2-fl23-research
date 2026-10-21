# Shared shutter-sound runtime

Windows and macOS use these same sound conversion, volume, audition and installation modules.

- `media.py`, `native_codec.py`: computer-only audio processing.
- `sound_cli.py`: workflow entry used by the desktop worker and `shutter.py`.
- `trial.py`, `boot_trial.py`, `buffer_trial.py`: explicit camera-session controllers.
- `candidate.py`, `boot_sound.py`, `files_worker.py`: fixed native changes and worker construction.
- `native/`: the three AArch64 camera workers.
- `verify_beeplist.py`: offline emulator used by boot-sound preparation; it is a runtime dependency.
- `custom_sound.py`, `inspect_native.py`: sound-format helpers needed by audition/conversion.

Tests, trace experiments and standalone verification tools remain in `dev/shutter_sound/`.
Host USB drivers and administrator prompts belong to `src/desktopapp/platforms/`.
