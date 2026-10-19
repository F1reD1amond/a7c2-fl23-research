# LUT importer: AI reproduction guide

[Home](../../README.md) · [简体中文](../zh-CN/lut-ai.md)

The [user guide](custom-lut.md) is an eight-stage manual workflow. Its device commands are implemented; do not replace installation with offline manifest generation. Read [source rules](../../src/looks/AGENTS.md), [integration](technical/integration.md) and [historical failures](technical/failures.md). FL23's entry and files must remain unchanged.

## Run the user's workflow

```text
python -m pip install -r src/looks/requirements-device.txt
python lut.py doctor --device
python lut.py import "REFERENCE.dcp" --name "DISPLAY NAME" --slot 1
python lut.py install "JOB_PATH" --battery-percent 90
```

The default bridge is a shared one-scene approximation, not factory calibration or a full Adobe renderer. Use `--calibration` for better measurements. CUBE needs its declared ST input or an explicit bridge; never assume a Log cube is ST. Use actual battery readings, not the example value.

After all I/O ends, the user performs the cold reload and preview/new-photo/playback checks. Then run `verify JOB --accept-photos`. Do not manufacture acceptance or infer boot safety from readback/emulation. Individual restoration uses `restore-slot JOB` and then reload/verification of the new job. Complete rollback uses independent [Recovery](recovery.md).

## Implementation map

| Source | Responsibility |
|---|---|
| `devicecli.py`, `devicejob.py` | Human commands; durable job, fitting, duplicate backups, native phases, readback, reload/restore/recovery |
| `device_layout.py`, `assets/runtime-v1.json` | Exact stock/FL23/standalone sources and legacy full7-v4 updates; no arbitrary firmware |
| `devicesession.py`, `usbidentity.py`, `usbservice.py`, `devicelock.py` | Stable normal-USB serial binding, guarded busy-only service acquisition, pinned programs/native model, temporary allowlist and locks |
| `devicesettings.py` | Descriptor-derived ST fields, other AP settings and four protected CP units; runtime telemetry is diagnostic |
| `resources.py`, `nameworker.py`, `native/names.c` | 68-resource atomic inode replacement, selected names, stock2860→2866 extension and exact inverse |
| `nativebuild.py` | Job-pinned native compilation using Zig; no imports, correct ELF/relocations and staging bound |
| `dev/release/build_lut.py` | Single-file bundle with verified extraction; no body data or external inputs |

All paths except the last are under `src/looks`. Programs/names/settings remain separate transactions, even when one command orchestrates them. Original factory calibration/protected CP units are never imported from a DCP or written. The selected base picker remains editable; do not describe it as a hard lock.

## Exact adapter boundaries

- Full7-v4 AP is exact `six.AP_SHA`; CP identity excludes only six table/checksum bytes and pins every other byte. Each job still stores full before/after hashes.
- First install accepts the exact stock or matching FL23 pair listed in `runtime-v1.json`. Standalone AP masks are validated by complete reconstruction; unselected default recipes/caps are preserved. Partial imports retain native dynamic titles.
- The standalone title dispatcher fits the existing132-byte converter window. The old switch's10 entries plus its2-byte aligned padding become the12-entry native map. Its sole page/add consumer, incoming branches, original virtual call site, program headers and relocations were checked offline. This is not physical boot proof.
- First-install CP reuses the v4 runtime with its retired DCP payloads removed and zero tables in unselected positions. Stock AP does not enable FL23 menus; no FL23 color/calibration units are provisioned. Unknown programs stop.
- Resource changes preserve old mmaps via atomic inode replacement. Exact inverse supports original hardlinks or reconstruction. Do not reuse the failed display/segment/icon approach.

## Interrupted operations

Preserve `job.private.json`, both source copies, input/model, candidates, manifests, workers and raw evidence. Never edit a job to advance its phase.

| State | Allowed next action |
|---|---|
| `PREFLIGHT_VERIFIED` | Explicit install |
| `AWAITING_RELOAD` | Physical reload/acceptance, then verify |
| `NEEDS_REVIEW` | Recover existing result only; no loader replay |
| Proven program/name/settings phase | Explicit resume of remaining work |
| `RESTORED_AWAITING_RELOAD` | Reload and verify restoration |

Every reconnect requires the normal Mass Storage USB serial hash to match the job before authentication. A service-only connection stops and requires a normal reconnect. `readHasp()` is diagnostic only: its 88-byte response varies across sessions and cannot identify a body. Legacy jobs without a stable binding cannot be forced forward; retain them and prepare a fresh job. Unknown native output remains untouched. An authenticated failed report can permit continuation only after rollback/read-only evidence and complete source/target classification. Settings comparison covers the writable AP group `02cf` and all four protected CP units. The known `02cf0b6e` diagnostic value and unrelated runtime groups are backed up but do not block installation; their values are never written.

If the initial storage query stays in recognized busy states or standard missing-card sense `02/3a/00`, the LUT layer can acquire service access once. USB timeouts, unknown sense codes and other manufacturers stop. On a first capture, complete AP/CP files must match a supported layout before the pinned read-only probe confirms native model index 16. No program/name/settings write is allowed before that confirmation. FL23 transport source is unchanged.

## Reproduce tests and package

```text
python -m unittest discover -s tests -v
```

Run that from `src/looks`. Optional instruction/native replay dependencies are in `requirements-research.txt`. Exact full-image tests require private owner fixtures through `A7C2_RESEARCH_FIXTURES`; absence means skipped, not passed. From root also run the existing FL23 and host suites, `dev/release/check_publication.py`, then `dev/release/build_lut.py` and test the emitted standalone CLI.

Separate software tests, exact-image reproduction, device readback, loaded state, physical camera behavior and Mac USB acceptance in every report. One Windows existing-six-look slot update passed physical checks and standalone reload verification; stock first-install, Mac USB and this job's physical restoration remain untested. Do not weaken source checks to finish a demonstration.

## Compressed foundations and slot restoration (development)

`backupstore.py` separates bodies, compresses/deduplicates 1 MiB chunks and stores changed chunks as XOR deltas against raw foundations, never earlier jobs. Primary/independent stores may have different foundations; both manifests must reconstruct identical complete files. Use `Job.source()` for legacy/plain and compressed storage. Retain both shared stores; no automatic garbage collection or historical-backup deletion. Readbacks retain results only, large setting evidence uses gzip, name targets are reconstructed, and compiler caches are shared.

`restore-slot` creates a new job over fresh current programs/names/recipes, restoring one old table/name/recipe after checking that the selected result has not subsequently changed. Preserve later other slots and native FL2/FL3. First activation clears the chosen AP bit and restores native base/name lookup. Shared code remains available; Recovery removes it on full rollback. Offline simulation is not physical validation.

## Independent Recovery and slot restoration

Complete rollback belongs to [Recovery](recovery.md); FL23 and LUT must not expose competing full-restore entries. Original raw FL23 backup2 works independently. New prepare/import workflows retain complete initial checkpoints. Never require a first LUT job to undo FL23.

`restore-slot` uses current programs/resources/recipes as the new transaction source, restoring just the selected historical table/title/recipe. First activation clears its AP mask bit and restores native name/base lookup; shared code remains, including the valid zero-mask layout. Keep other tables/recipes and current FL23 flags. No firmware/backup/worker hash admission is used for slot recovery: compressed CRC, actual changed-byte conditions and full byte readback remain. Native FNV table checksums are generated because the camera format requires them. Hashes used as storage addresses or body IDs are not file admission gates.

Run the public suites, `test_checkpoint`, `test_install_order`, native byte-only workers and the actual packaged entries. Test later FL23 and later other-slot changes. Preserve unknown outcomes; do not repeat firmware writes or mix in the withdrawn UI experiments.
