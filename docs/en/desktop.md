# A7C II desktop tools (Windows development preview)

For **ILCE-7CM2 firmware 2.01**. Startup never opens the camera. All device actions require a manual click. macOS builds are deferred.

## Connection

Use Mass Storage mode. Prefer **准备两阶段驱动并测试连接** to prepare the normal `0E8A` and service `0336` identities. Compatible driver bindings are retained; WinUSB is installed when required. The separate selected-identity installer is an advanced shortcut.

Driver removal exports camera driver packages, removes only camera-specific third-party packages and preserves Windows native drivers. Reconnect USB afterward. No camera firmware is changed. A `0336` timeout means service access was not established; missing drivers are one possible cause, not a proven explanation for every timeout.

## FL23 and custom looks

**Enable/re-enable FL23** applies the desired configuration and does not repeat an already satisfied write. **Remove FL23 from the list** disables its menu entries while retaining custom looks and shared color code, allowing re-enabling later.

Select an `.a7look`, slot and title, then write directly. No backup directory or re-fitting is required. **Reset the selected slot to ST defaults** needs neither its original import job nor its former recipe. Other slots and FL23 remain. Legacy six-slot layouts retain a neutral shared runtime; newer layouts deactivate the selected imported-slot bit. Physical title/preview/photo acceptance remains separate.

The companion compiler accepts DCP/CUBE. DCP compilation requires Lightroom and its renderer bridge. Direct Sony-ST/sRGB CUBE compilation does not. The Lightroom plugin routes later RAW development; it does not bake DCP processing into RAW sensor samples.

## Restore factory functionality without an old backup

Use **恢复原厂 2.01 功能（无需旧备份）**. Original bytes for supported project regions are included, so old backups and a full firmware download are unnecessary.

This restores supported FL23, LUT/preview/name and shutter-sound program changes and sets all six custom slots to ST defaults. Body calibration, counters and unrelated settings are preserved. Former personal recipes are not recovered. This covers supported program regions and project color fields, not an entire flash image. Unreferenced project audio files/vertical aliases may remain.

Historical-backup recovery is an optional collapsed workflow. Advanced users can import an original same-model/version `BODYDATA.DAT` as a complete program reference. Service communication must still work; this is not an official updater downgrade or a guarantee of recovery for unreachable bodies.

## Operation and verification

Each write prompts for adequate power; no numeric battery entry or invented USB percentage is used. No complete body backup is automatically created. Transaction logs, required byte windows and operation results are retained; unknown writes are never replayed automatically.

After all I/O finishes, shut down normally, disconnect USB/external power, wait for the access lamp and remove the battery for at least one minute. Restart, check preview/new photographs/playback/titles, then reconnect and verify. Offline reconstruction, complete readback, loaded-state checks and physical behavior are separate evidence.

Administrator driver logs stream live. Export diagnostics when needed; review local paths and device details before public sharing.

Vertical Display rotates shooting information/layout for the current session, not the entire MENU. Custom sounds still require audition, confirmation and recovery of the temporary audition before persistent installation.

The new backup-free workflows passed offline planning/preservation checks but **have not passed physical acceptance**. Development branch only; main and formal Releases remain unchanged. Install `desktop-requirements.txt` and run `python desktop.py` for source execution. [Developer/AI notes](../../dev/desktop/README.md).
