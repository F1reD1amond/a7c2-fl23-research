# A7C II Windows desktop tools

For **ILCE-7CM2 firmware 2.01, 64-bit Windows 10–11**. This is a development preview. Startup does not open or flash a camera. macOS builds are deferred.

## Home: guided one-click installation

1. Connect the powered camera in Mass Storage mode with a data cable.
2. The six built-in looks, FL23, native electronic shutter sound and Vertical Display are selected by default. Optionally select the Lightroom plugin.
3. **No file selection is needed. Custom slots 1–6 are replaced with NC (Classic Neg.), CC (Classic Chrome), NN (Nostalgic Neg.), Astia, GR Positive Film and GR Negative Film**, in that order. Original Creative Looks remain. To use your own files, uncheck the built-in pack and expand the custom section; empty slots in that mode are preserved.
4. Click the main install/continue button. The tool prepares both driver identities, composes the selected persistent changes, writes them and reads them back completely. Windows requests administrator access when necessary.
5. A completion dialog explains the steps: **disconnect USB/all external power → wait until the access light stops blinking → switch OFF and wait for the screen/light to go out → remove the battery for at least one minute → reinstall it and turn ON**. The reload help button also opens these instructions.
6. Restart, reconnect in Mass Storage and click **the same button**. It verifies a new boot and loaded state, including the saved Vertical Display switch, then connects the sound tools and optional plugin. Continuing does not repeat the firmware installation.

When finished, an **Installation complete** dialog lists the selected looks and features; unselected sound is not reported as installed. **View previous installation result** on Home reads local records without opening the camera or reinstalling. Resolved errors remain in history instead of appearing as active failures.

**New setups save Vertical Display in the combined installation.** Resources are verified before the native switch is saved; it loads with the other selected features after the final cold restart. No per-boot computer connection is intended. Older jobs keep their original plan and can be upgraded from the Vertical Display page. Persistent operation still requires the owner's physical acceptance.

If the dialog says names are complete but programs are not yet written, old resources remain occupied and the read-only mount must recover first. Follow the full power-removal instructions, reconnect and use the same button; no photographs, driver reinstall or file reselection are needed at this stage. Names are not rewritten. A final reload prompt follows the program installation. If the read-only state has already recovered, no extra power cycle is requested.

An unchanged target does not request an unnecessary power cycle. Factory recovery, driver removal and slot deletion are not installation steps. Custom audio still requires audition and owner confirmation before persistence. Enable the installed Lightroom plugin once in its Plug-in Manager. It routes later RAW development; it does not bake DCP processing into RAW sensor samples.

Enabling FL23 after factory recovery is a new program change and needs another restart to load it; loaded-state verification is read-only. In-progress older setups keep their saved plan without silently adding the six looks. Built-in looks approximate their source DCPs. Attribution and original rights are recorded in the bundle's `desktop-assets/presets/default-six-v1/credits.json`.

## Connection and drivers

Prefer two-stage driver preparation. Normal Mass Storage and service commonly use `054C:0E8A` and `054C:0336`. Compatible installed bindings are retained. Driver removal exports camera packages before returning to Windows default binding.

Diagnostics enumerate all Sony identities, names and interfaces. A different PID does not establish the same model. The source of the reported `054C:0D68` remains unconfirmed; unknown PIDs are reported rather than automatically receiving a replacement driver. Check the actual model and USB mode.

## Individual controls

- **FL23:** enable, re-enable or hide the two menu entries. After writing/readback, follow the cold-restart instructions and check the camera; the computer's loaded-state check is optional diagnostics, not a prerequisite for use. Hiding preserves custom-look/shared code so it can be enabled again.
- **Custom looks:** start with an empty list. Add an operation, choose its slot and Restore ST or Write A7Look; new items default to Restore. File and optional camera name share the same item. Mix imports and resets in one batch; omitted slots stay unchanged. Reset does not recover former recipes. Imported slots use ST; the base picker remains editable.
- **Vertical Display:** shooting information/icons/layout rotate, not the entire MENU. Off also removes the tool's auxiliary resources; no separate alias-removal button is needed. The native switch is saved; disabling saves OFF before removing resources.
- **Sound:** native on/off and direct saving after conversion; temporary audition and confirmation records are optional. Existing sound enabled by one-click setup can be adopted without rewriting firmware. Check the camera's Audio Signals setting if silent.

Repeated identical titles do not append new records. Names complete before programs reference them. New byte-based name transactions replace one file atomically at a time, avoiding 68 simultaneous staging copies; restart instructions appear after complete readback.

Driver preparation reports both USB identities. Existing WinUSB/libusbK/libusb0 bindings are retained without reinstalling or requesting elevation; only missing compatible bindings require installation.

For an older one-click name-stage `ENOSPC / -28` failure, Continue first reviews the completed report, current program windows and original name bindings. Only zero name/program commits with successful rollback/cleanup/read-only remount permit removal of the exact matching temporary worker/report and a fresh transaction. The original failed directory is preserved. Partial commits, unknown outcomes or differing bytes remain stopped.

For fully committed names with only read-only remount `EBUSY / -16`, the new path verifies every name and original program, prepares reload and shows the resource-stage instructions above. Missing reports, incomplete commits, failed rollback/cleanup or differing contents remain blocked.

This desktop build includes [FL23 PR #6](https://github.com/QAQLeonard/a7c2-fl23-research/pull/6): separate native photo/movie curve routing, with the proper FL2/FL3 movie curves and custom LUTs preserved. This does not establish photographic color calibration.

## Factory functionality recovery

A historical recovery with completed loaded-state/read-only verification does not block a new restore. After later feature installation, the main Restore button creates a fresh current-state plan; only genuinely unfinished transactions are continued automatically.

Use the unified restore/continue button, without an old backup or complete firmware download. Supported project modifications are removed and all six custom recipes return to ST defaults. Body calibration, counters and unrelated settings are preserved. Optional historical-backup recovery remains separate. This is neither an updater downgrade nor a full flash-image overwrite.

After interruption use the same button. It reads existing results/current bytes and plans remaining work; unknown outcomes stop with evidence retained. Resource-space exhaustion and a busy read-only remount are handled separately. Deferral is allowed only after complete program/name verification with no further program/name edits needed. Settings/reload preparation can then finish; a new boot and read-only mount must be verified afterward.

## Errors and verification limits

Full exceptions remain in the window and private logs. Support exports contain device information/local paths; review them before sharing. Do not repeatedly flash an unconfirmed outcome.

Offline regressions cover individual/repeated imports, selected-slot reset, mixed-slot preservation, installation order, drivers, recovery, sound, Vertical Display and guided setup. The owner's current factory recovery passed full readback, new-boot/loaded-state and read-only-mount checks. **The new one-click workflow and every feature have not all passed physical shooting acceptance.** Color fidelity, live preview, photographs and long-term stability remain separate checks.

For source use, install `desktop-requirements.txt` and run `python desktop.py`. [Validation and limits](desktop-validation.md) · [Developer notes](../../dev/desktop/README.md). Development branch/local test bundle only; main and formal Releases are unchanged.

The custom page previews its complete operation list before power confirmation. After write/readback follow the cold-reload dialog; the same button becomes loaded-state verification. Pending plans are locked and cleared on completion. Proven pre-write failures allow editing/retry; unknown outcomes preserve evidence and stop. Home still offers the default six-look installation separately.

Audio conversion is an independent offline operation: every attempt creates a new job, without prior camera enable or old camera-job locks. Failed/cancelled attempts clean their partial output; source files and the last successful result remain. The candidate is selected in a separate conversion record; conversion success does not mean camera audition or installation.

Before the first camera audition, enable electronic shutter sound and follow the cold-reload instructions. Already-enabled support can be adopted through fresh read-only checks. A failed enable job releases its active binding on the next click only if all read-only results and cleanup completed without entering a write; its original log remains. Unknown outcomes remain stopped. If support is disabled, click Enable first; temporary audition does not write the permanent switch.

Sound retains its original Sony service body identity; legacy sound jobs do not need LUT USB-descriptor fields. Sound CLI `check-connection --workspace <sound workspace>` reads body identity/current sound programs without audio registration, program or settings writes. `status` remains local-only with no camera connection.

Before audition, completed owned markers are archived/replaced automatically; normal use does not require deleting files. An attempt rejected only by a marker before allocation can start fresh on the next click. Old CP storage is reclaimed by cold power-off, not released through potentially stale addresses. Unknown executions or markers without a matching completed report retain evidence and stop with details.

After conversion, click Save Current Custom Sound directly; no prior audition, confirmation or cold recovery is required. Optional audition opens powered-on listening instructions; reconnect afterward and save directly. Listening/recovery records are optional controls. Follow the cold-reload dialog only after actual write/readback: unplug USB, wait for access activity to stop, switch off, remove the battery for at least one minute, then restart to load the change.
