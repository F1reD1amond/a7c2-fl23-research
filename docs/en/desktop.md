# A7C II desktop tools (development preview)

For ILCE-7CM2 firmware 2.01. One window groups connection/driver setup, Recovery, FL23, custom looks, Vertical Display and electronic shutter sounds. Starting the application never opens the camera. The integrated desktop workflows still require physical testing.

## One-click recovery

Open **完整恢复 (Recovery) → 一键还原 (One-click recovery)**, enter the actual battery percentage, and confirm. In one service session, the application identifies the connected body and selects its **earliest available complete checkpoint** from registered/configured backup locations. It preserves the current state, restores programs, names and project look settings, then reads back the complete files. Later FL23/LUT/program modifications do not require uninstalling in reverse order. No stock firmware hash whitelist is used.

This cannot invent a missing original backup. “Earliest available” only covers indexed/configured locations. Select a backup directory or ZIP manually for archives stored elsewhere. Original legacy FL23 backup2 directories are supported through manual recovery without a LUT job.

After all USB I/O finishes, follow the log: disconnect USB/external power, shut down normally, wait for the access lamp, remove the battery for at least one minute, then restart. Check shooting, photographs and playback; reconnect and verify loaded state. Full readback alone is not boot acceptance.

**Scope:** AP/CP programs, captured name resources and project look fields, preserving body calibration, counters and unrelated settings. This is not a sector image of the entire flash. Legacy backup2 lacks an independent historical saved-settings snapshot and uses its recorded RAM recipes. Additional sound files and vertical aliases are outside old checkpoints; restoring old programs disables their added code paths, while their respective tools handle file cleanup.

The body must still support service communication. This is not recovery for an unreachable camera. Official `BODYDATA.DAT` packages are not supported backup inputs.

## Fake downgrade?

[a7c2-service-preload](https://github.com/YuuLuo/a7c2-service-preload) documents authentication, temporary root execution and preloading. Its public repository currently provides no fake-downgrade recovery utility or demonstrated official same-version reflash workflow. Temporary execution does not permanently disable signature checks. One-click recovery therefore uses your body backup; official firmware downgrade/reflash is not implemented.

## Other workflows

| Page | Operation |
| --- | --- |
| Connection | Windows retains usable WinUSB/libusbK/libusb0 bindings and installs camera-specific WinUSB when requested. macOS uses libusb without Zadig. |
| FL23 | Prepare backups → install → cold restart → verify. |
| Custom looks | Select `.a7look`, title and slot → prepare → install → cold restart and check preview/photos. Single-slot restoration, a compiler and Lightroom plugin installer are included. |
| Vertical Display | Shooting information/icons/layout follow portrait orientation. This is not full MENU rotation; the current switch is session-only. |
| Shutter sound | Enable native sound; custom clips require conversion, camera audition, confirmation and audition recovery before persistent installation. |

Keep failed workspaces and export diagnostics. Complete tracebacks and original errors are retained; unknown writes are never automatically replayed. Diagnostic bundles contain local paths and device information: review before posting publicly.

For source execution, install `desktop-requirements.txt`, then run `python desktop.py`. Packaging and offline tests are separate from physical Windows/macOS USB acceptance.
