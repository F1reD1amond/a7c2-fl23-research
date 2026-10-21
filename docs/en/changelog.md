# Changelog

## Desktop preview.10.9 — 2026-10-21

- Fix one-click installation stopping when the optional Lightroom plugin is selected but the caller has no valid ExifTool path. Use bundled or installed ExifTool automatically; otherwise download the official distribution before camera work, retaining complete connection errors.
- Bundle ExifTool 13.59 and its complete Windows companion files / macOS Perl modules and original licenses. The separate plugin button uses the same automatic preparation, with no hidden file-selection prerequisite. Missing paths saved on another computer fall back to the local helper.
- 50 focused offline tests passed for helper resolution/extraction, one-click setup and plugin integration. The Windows EXE installed the plugin into an isolated Adobe directory without an ExifTool argument, ran its real bundled helper and read JPEG metadata successfully, without camera I/O. Native Mac packaging now runs on real Intel and Apple Silicon runners; physical Mac camera USB is a separate untested boundary.


## Desktop preview.10.8 — 2026-10-21

- Rename Home continuation to “继续安装” (Continue installation). The post-restart dialog and persistent status explicitly tell users to reconnect USB and click it. Standalone look instructions no longer direct users to a removed verification button.
- Verified factory recovery clears active one-click / FL23 / look continuation pointers and the look editor, restoring a fresh Home state. Keep diagnostic evidence and pending recovery until its completion check succeeds.
- Add visible LUT guidance in the compiler/import page plus a bilingual format guide: direct GUI CUBE input is Sony ST / sRGB and output is sRGB, not S-Log3. Explain Log bridging, 3D CUBE structure, DCP rendering and approximation limits.
- Add separate ARM64 / Intel native Mac APP/DMG builds and CI asset import/export. Exclude Windows helpers, use fresh DMG staging and verify signatures/container structure. Targeted Mac storage unmount and interface capture draw on MDHan's adapter; preserve service-first admission.
- 62 focused offline cases passed before the final documentation edits. Windows output path stays unchanged. Native Mac build/DMG and physical USB validation have not run on this Windows host. No camera I/O in this update; formal full regression remains deferred.


## Desktop preview.10.7 — 2026-10-21

- Simplify workflow: no historical recovery-verification check at one-click startup. Custom looks perform checks/write/full readback through Apply, without a separate verification button or a post-write editor lock. Sound on/off and repeated completed auditions no longer require a recovery record. One-click installation retains one final combined check after all selected camera changes and restart; recovery retains its own mandatory completion check.
- After these workflow changes, use focused checks only (50 relevant cases); defer the next full regression to formal release. The earlier 334/20 result below predates the last workflow simplification.

- Fix direct upgrade from the project's published v2-era FL23 helper/curve table. Reproduce its `cpapp-b.bin + 0x138832` conflict using the original 2.01 programs and published patch list; migrate both reviewed old windows while preserving unrelated code and LUTs.
- Continue can re-plan an accounted read-only failure in a fresh child without reinstalling drivers. Preserve failed jobs and unknown native outcomes. Diagnostic exports now include original child-stage/error summaries without program or calibration snapshots.
- Show a startup notice explaining the camera's “Check the connected device” message during tool connection/driver switching, and distinguish it from actual tool errors.
- Recovery remains at 70% with “not complete; restart and verify” until loaded-state verification passes. Update the main button and restart dialog accordingly; keep physical acceptance separate.
- 334 tests passed / 20 skipped. Full offline one-click plans passed for stock, published old FL23 and old FL23 with LUTs; recovery/startup dialogs were rendered and inspected. No camera operations were performed for this update. The external reports lack actual source bytes/child state, so their exact original states still require recipient validation.

## Desktop preview.10.6 — 2026-10-21

- Save converted audio directly. Audition, listening confirmation and cold-recovery records are optional; cold reload is requested after actual write/readback.
- Bundle the missing Unicorn Python package/native DLL, pin the build dependency and execute a real ARM64 instruction in frozen self-test. Resolve compiler/emulator dependencies before creating a write intent.
- Automatically retire a failed host preparation with no native invocation, preserving its evidence and starting a new job. Unknown native writes are not replayed.
- 156 related cases passed. The packaged EXE used the owner's local program backup/current payload to verify valid/missing/oversized CSV, exact inverse and compile five native workers without camera I/O. Physical persistent installation remains owner-operated validation.

## Desktop preview.10.5 — 2026-10-21

- Successful audition now opens instructions to unplug USB while keeping the camera powered, test an electronic exposure, reconnect and confirm, then cold-recover before saving.
- Missing audition/listening/recovery steps return a guided waiting state instead of a `Cold-recover` exception. Show the appropriate dialog, do not report installation complete, create a write job or accept owner checks automatically.
- 151 related regressions passed, including exactly-once dialogs after worker exit. Both dialogs were rendered and inspected. The packaged EXE handled saving from a copy of the owner's current state with no camera I/O; physical persistent installation remains owner-operated acceptance.

## Desktop preview.10.4 — 2026-10-21

- Replace an exact owned marker from a completed prior registration before audition, fixing pre-allocation `-17 / EEXIST` without manual file cleanup. Archive the marker; never release an old CP address that may be stale after reboot. Cold power-off reclaims leased temporary buffers.
- A completed report proving no allocation/transfer/registration, with native cleanup verified, allows a fresh attempt. Preserve original evidence; unknown executions and unmatched markers remain stopped.
- Registration errors expose native phase/status/call fields. 144 related regressions passed. The packaged EXE replaced the owner's old marker on camera without registering new audio or writing firmware; listening remains owner-operated acceptance.

## Desktop preview.10.3 — 2026-10-21

- Fix legacy sound jobs being routed through LUT USB-descriptor binding, producing “Legacy job has no stable USB body binding”. Sound sessions retain their original Sony service body identity for normal USB, existing service sessions and re-enumeration waiting.
- Connection regressions execute the actual sound connector with only USB/protocol boundaries replaced, reproducing the same exception before the fix. 129 related offline tests passed.
- Add integrated read-only sound `check-connection`: no native worker, audition registration, program or settings write. The packaged EXE successfully connected to the owner's camera and read its current programs; sound support was disabled. Enable/audition still require owner-operated physical testing.

## Desktop preview.10.2 — 2026-10-21

- Release the active binding of a failed sound-enable job only when its read-only checks and temporary cleanup completed without any write invocation. Retain original evidence; unknown outcomes remain blocked.
- Audition can freshly adopt already-enabled sound support without writing the permanent switch. If disabled, it specifically asks the user to enable and cold-reload first.
- Sound sessions now use USB re-enumeration waiting and body-bound attachment to an existing service endpoint between preflight and apply.
- 77 audio-related offline tests passed; the owner's old failed job passed read-only classification. No camera operations were performed; physical audition acceptance remains pending.

## Desktop preview.10.1 — 2026-10-21

- Decouple audio conversion from camera jobs. Each conversion gets a fresh offline job; unresolved enable/audition/install records no longer block conversion. No prior camera enable or backup is needed.
- Store the selected conversion separately, preserving camera transaction state. Audition/install retain their own checks and accepted-payload binding.
- Remove partial outputs after failure/cancellation, preserving source files and the previous successful candidate. Conversion errors no longer imply unknown camera writes.
- 62 audio cases passed. The packaged EXE converted the owner's selected source/parameters successfully with the old camera record and source bytes unchanged.

## Desktop preview.10 — 2026-10-21

- Replace the custom-look page with an incremental operation list. No slots are selected initially; new items default to Restore ST. Slot, action, file and optional name share one item, supporting mixed batches.
- Compose imports/resets into one plan and full readback, preserving omitted slots, calibration, FL23, sound and Vertical Display. Support legacy layouts and clear restored-slot RAW profile mappings.
- Restore/lock pending plans, retain actual returned workspaces and clear completed lists. Proven pre-write failures can be edited/retried; unknown writes are not replayed.
- Fix Home's stale new-install label after entering reload wait.
- Include the missing `wave` module. Real EXE WAV/MP3 import passed; frozen self-test now converts generated mono WAV, stereo WAV and stereo MP3.

## Desktop preview.9.2 — 2026-10-21

- Audit two full stock → import → cold verification → restore cycles. New recovery does not require a physical-photo checkbox; historical jobs are not replayed.
- Recover child completion when the parent lost its result, using fresh read-only evidence. Handle unstarted resource dispatch, ready resource checkpoints and nested program children; preserve unknown nonempty children instead of replaying writes.
- Mark an already-original, read-only-verified no-op as finished immediately. Restore missing completed-step bookkeeping after parent interruption.

## Desktop preview.9.1 — 2026-10-21

- Fix Restore being redirected to verification of an old `LOADED` recovery with an already verified read-only mount. Later feature installation then caused a program mismatch instead of starting a new restore.
- Completed device verification exits automatic continuation. Restore now creates a fresh current-state plan; awaiting reload, unverified read-only state and unknown writes still take precedence. Physical acceptance remains separate and old evidence is preserved.
- 78 related offline tests passed, plus local-only discovery against the owner's existing records. No new camera I/O.

## Desktop preview.9 — 2026-10-21

- Include the saved native Vertical Display switch in new combined FL23/look/sound plans. Install and fully read back its three resources before saving ON, then load all selected features at the final cold restart; remove the separate session-only final step.
- Verify stored, Backup-RAM and native running values plus resources after reload. Stop on mismatch instead of faking persistence with a temporary RAM enable.
- The Vertical Display page saves ON/OFF. Disable and factory recovery save OFF before turning off runtime display and removing resources. Older jobs retain their plan without silently adding new writes.
- Retain preview.8.1 completion dialogs, archived errors and local result viewing. Persistence has offline validation only; no owner-camera write/cold-restart acceptance has occurred for this new path.

## Desktop preview.8.1 — 2026-10-21

- Show a final guided-setup completion dialog with selected looks/features, unselected sound and the current-run-only Vertical Display scope. Add a local-only previous-result button on Home.
- Archive resolved errors while keeping failed child transactions and full logs. Print a short result summary; new errors remain fully reported.
- The owner manually completed the resource reload, combined program write/readback and final loaded-state check: `COMPLETE` / `LOADED`. Vertical Display reported running `ON`, saved `OFF`; sound was unselected. Physical shooting, video color and long-term stability still require acceptance.

## Desktop preview.8 — 2026-10-21

- Handle fully committed names followed by read-only remount `EBUSY / -16`: verify all names and untouched programs, prepare reload and request explicit power removal. Verify a new boot and read-only mount before remaining program writes; do not rewrite names/drivers. The program installer's read-only prerequisite stays intact.
- Distinguish name-stage pause from program completion. Wait if reload was incomplete; skip extra power removal if the mount already recovered. Verification of names alone cannot mark the program installed.
- Preserve failed jobs and remove only exact completed temporary artifacts. Missing/partial reports, changed bytes and failed rollback/cleanup remain stopped.
- Integrate main PR #6: native FL23 photo/movie curve routing and missing-USB-device handling. Synchronize desktop curve assets and support edited-byte upgrades from prior curves while preserving LUT hooks/slots, without firmware provenance hash gates.
- Live read-only checks on the owner's body verified all 68 target names/original program windows, a writable mount and image mode 2. Complete continuation and video appearance still require physical acceptance; offline passing tests are not installation evidence.

## Desktop preview.7 — 2026-10-21

- Add six-slot batch import on the normal Creative Looks page, defaulting to NC/CC/NN/Astia/GR Positive/GR Negative. Empty fields preserve slots; optional titles and individual ST reset remain.
- Look-only batches preserve FL23/sound switches, combine inputs into one transaction and finish with complete readback and one reload prompt.
- Show bindings/skipped installation for both USB identities. Retain WinUSB/libusbK/libusb0 without reinstall/elevation; reuse the fresh service scan and bound installer waiting to 180 seconds with original errors retained.
- Fix approximately 9 MB of simultaneous name staging causing `phase=3/status=-28`. Byte-based writes replace files atomically one at a time, preserve original data/index information for rollback and reserve rollback space. Native fault tests cover writes, renames and synchronization.
- Preserve errno, staging/commit counts, rollback, cleanup and read-only results. Continue can review an older zero-commit ENOSPC, remove exact completed temporary artifacts and use a new transaction; failed evidence remains intact. Unknown outcomes stay stopped.
- Offline passing results do not establish physical preview/color/stability acceptance. This update does not automatically reflash the camera.

## Desktop preview.6 — 2026-10-21

- Home setup now installs six built-in looks by default: NC, CC, NN, Astia, GR Positive Film and GR Negative Film in custom slots 1–6. No per-slot file selection is required; custom-file mode remains available.
- Save look inputs before device access and retain that plan during continuation. A missing pack stops before USB; existing jobs never silently receive new presets.
- Show a completion dialog with USB removal, access-light waiting, shutdown, battery removal for at least one minute, restart and loaded-state verification. Add detailed confirmation text and a reusable help button.
- Fix installation progress incorrectly labeled as restoration. Explain that enabling FL23 after factory recovery is a new change requiring restart; verification does not flash again.
- Move standalone FL23 loaded-state checks into collapsed optional diagnostics. After the restart and camera checks, reconnecting to the computer is not required for use.
- Standalone FL23 enable/disable finishes at 100% after writing and complete readback. Release the UI controls immediately; power removal loads the finished change and is not a pending computer-side installation step.
- All successful cold-reload paths show detailed guidance, including sound toggles/persistence/restoration, post-audition cleanup and historical recovery. Temporary audition and adoption of enabled sound do not request restart. Failed/unknown outcomes do not tell users to unplug. Rename misleading “validation only complete” progress to “pre-write checks passed.”
- No camera writes in this update; the new complete installer still needs manual physical acceptance.

## Desktop preview.5 — 2026-10-21

- Add guided home installation: driver preparation, composed FL23/selected A7Look/native-sound writes and complete readback; continue with the same button after cold reload for loaded-state checks, sound-tool adoption, optional Lightroom plugin and session-only Vertical Display. Unselected slots remain; unknown writes are not replayed.
- Vertical Display Off also cleans auxiliary resources; remove the separate alias-removal button.
- Fix duplicate title appends during verification. Finish names before program references, clean old resources after verified cold reload, and invoke the rebuilt cleanup worker.
- Separate completed name content from a busy read-only remount. Only fully verified program/name targets with no remaining edits may finish settings/reload preparation before cold-boot mount verification. Reattach a recorded body's existing service session without re-authentication.
- Fix native FL23 curve differences between installation orders; include Keystone/Capstone in desktop packaging.
- Enumerate all Sony USB identities/interfaces without installing drivers for unknown PIDs. The reported `054C:0D68` remains unidentified; this body used normal/service `0E8A`/`0336`.
- Expand individual/repeated six-slot imports, selective reset, mixed-slot preservation, interruption/mount cleanup and guided workflow tests. **The owner's factory recovery passed new-boot, complete readback, loaded-state and read-only mount verification; new one-click installation/every feature have not all passed physical shooting acceptance.** Development branch/local test bundle only.

## Desktop preview.4 — 2026-10-21

- Unify factory recovery: discover unfinished transactions, ignore later attempts stopped before writes, and verify loaded state after completed recovery.
- Re-plan remaining program windows, names, settings and reload preparation from current bytes, preserving prior evidence and skipping matching content.
- Recover a complete native report directly from the camera after host download failure. Account for execution/cleanup/read-only mount before removing exact temporary contents; delete the result last so cleanup interruption remains recoverable.
- 92 offline cases passed; 9 skipped without private fixtures. Coverage includes name ENOSPC/I/O errors, partial programs/names, settings interruption, missing results, foreign temporary files, multiple bodies, repeated clicks and missing temporary state with an unconfirmed outcome. The owner's actual saved report was parsed and simulated offline. Manual camera continuation remains pending.

## Desktop preview.3.1 — 2026-10-21

- The main factory-recovery button recognizes the selected accounted name-space failure and, after write confirmation, dispatches continuation. A later failed full attempt does not hide the original source; completed continuations are not replayed.

## Desktop preview.3 — 2026-10-21

- Fix factory-name ENOSPC from staging all 68 resources: reconstruct and atomically replace one file at a time; check capacity before program writes.
- Add explicit continuation for accounted name-space failures: validate completed program bytes and the failed report; continue names/settings/reload preparation without program replay, preserving the failed transaction.
- Compiled ARM64 offline tests cover the original failure, 68 resources, space/inode limits, write/rename/fsync faults and mapped old inodes. Manual camera acceptance remains pending. Development branch only.

## Desktop development preview — 2026-10-21

**preview.2:** direct FL23 enable/removal and custom-slot import/ST-default reset no longer require complete backups. Factory functionality restoration uses included original 2.01 project regions, preserving body calibration without old backups or a full firmware download. Former recipes are not recovered. New flows have offline validation only and await manual physical acceptance.

- Added a six-page Windows/macOS desktop front end, native packaging and complete background-job error logs.
- Integrated explicit two-stage Windows driver preparation; macOS uses libusb without Zadig.
- Added manual camera driver removal with package export and Windows native-driver rebinding; no automatic system restart.
- Fixed rejection of Zadig/libusbK INF files using `USB\%DeviceID%` references; elevated worker failures now preserve the original error.
- Replaced the desktop battery field with per-operation power confirmation; stream administrator progress, retain raw Windows output and recover the finished GUI state.
- Added same-body automatic initial-checkpoint selection alongside manual complete recovery and independent LUT slot restoration.
- Connected FL23, A7Look import/compiler/LrC plugin installation, session-only Vertical Display and custom electronic shutter sound workflows.
- Retained the unchanged-name no-op fix and restored the byte-window native installer interface needed by recovery.

Development branch only. Packaged offline checks and physical camera acceptance are separate; this is not a new formal Release. [Desktop guide](desktop.md).

[Home](../../README.md) · [简体中文](../zh-CN/changelog.md)

## v2.2-preview.1 — updated 2026-10-20

- **Independent Recovery:** restore the selected complete checkpoint or original FL23 backup2 without the original workspace or any LUT job. The tool saves a compressed copy of the current state, restores programs, project names/settings, and fully reads back the result. [Recovery instructions](recovery.md).
- **Separate responsibilities:** FL23 installs/verifies; LUT imports/restores individual slots; Recovery performs complete rollback. FL23's restore command and desktop button have been removed.
- **Both installation orders:** FL23 → LUT and LUT → FL23 preserve each other's changes. Verification accepts the expected later changes.
- **Smaller LUT backups:** share a compressed foundation and record the selected slot's pre-write state. Later imports retain changed data instead of repeated complete copies. Keep the shared storage directories with the jobs/backups.
- **Single-slot restoration:** restore its previous table, title and recipe, including undoing first activation, while preserving other slots and FL23. No firmware or backup-file hash admission checks; edited-byte checks and full readback remain.
- **FL23 admission:** check the camera model and user-entered firmware version 2.01, without a firmware-provenance hash whitelist. Warn about other projects' modifications; retain actual patch-position conflict checks.
- **USB connection:** authenticate directly instead of blocking on storage `02/04/01` or application-query Busy. Confirm the USB model and bind the service backup's four-byte AP serial (`0x00E70003`) using the original hex-text digest, retaining existing backups. No separate USB-fix tool is required; Windows device drivers are still required.
- **Failure explanations:** integrated LUT job diagnostics explain native-name transaction failures from saved evidence without reopening USB or blindly repeating a write.

**Validation:** offline suites passed: 131 LUT cases (35 skipped without private fixtures), 22 FL23 cases and 46 host/USB cases, including nine service-first connection/failure cases. Historical real backup data reproduces its original body binding. Separately, 7 real-file order/slot cases and 44 native-name syscall/failure cases passed. This release update did not operate a camera; the user's reported service-route installation is separate evidence. Physical complete Recovery and Mac USB remain untested. [Evidence and limits](technical/validation.md).

These fixes are included in `main` and the updated v2.2-preview.1 commit/release, as authorized by the owner. Existing v2.1/v1.0 releases remain available. ZIP and single-file tools are in the [preview release](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.2-preview.1).

## v2.1

Published FL23 and the independent LUT/DCP CLI, with single-camera Windows slot-update observations, original DCP attachments and film comparisons. [Release notes](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.1).

## v1.0

FL23-only tool. [Release notes](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v1.0).
