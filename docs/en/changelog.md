# Changelog

## Desktop development preview — 2026-10-21

- Added a six-page Windows/macOS desktop front end, native packaging and complete background-job error logs.
- Integrated explicit two-stage Windows driver preparation; macOS uses libusb without Zadig.
- Added manual camera driver removal with package export and Windows native-driver rebinding; no automatic system restart.
- Fixed rejection of Zadig/libusbK INF files using `USB\%DeviceID%` references; elevated worker failures now preserve the original error.
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
