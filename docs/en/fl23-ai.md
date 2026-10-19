# FL23: AI installation and reproduction guide

[Home](../../README.md) · [简体中文](../zh-CN/fl23-ai.md) · [User installation guide](fl23.md)

Goal: install FL2/FL3 on A7C II 2.01 under Windows, with duplicate backups, writing, independent readback, cold-load, capture/playback and restoration. **Use the CLI first; the desktop interface is an alternative to the same backend.** FL23 installation does not import LUTs; full initial-checkpoint rollback also removes later LUT changes to restore the selected initial state.

## 1. Starting point

Read [AGENTS](../../AGENTS.md), [the user guide](fl23.md) and [compat.py](../../src/fl23/compat.py). Only ILCE-7CM2 is supported. The user enters 2.01 from the camera version screen; the version is not automatically queried.

At the owner's request, FL23 has no stock/repository whole-firmware provenance whitelist. Changes outside actual patch positions do not disqualify a body. Instruction conflicts at write positions still stop with an address. Preserve existing LUT conversion and CP data; already enabled FL23 is backed up/verified without reinstalling.

The desktop shows a pre-install provenance-risk warning and CLI prints the same warning. Keep duplicate actual-file backups, exact candidates/inverses and full post-write readback. Per-job integrity is distinct from stock provenance. This workflow awaits physical validation; USB behavior is unchanged.

Use 64-bit Python 3.10+ on Windows. The launcher installs dependencies, with no separate compiler operation. Normal/service USB IDs are 054C:0E8A / 054C:0336.

## 2. Existing implementation and boundaries

| Source | Role |
|---|---|
| [app.py](../../src/fl23/app.py) | `Job.prepare/install/verify/restore`: stages, backups, candidates, transactions and verification |
| [gui.py](../../src/fl23/gui.py) | Windows buttons dispatch to the same `app.py` commands |
| [core.py](../../src/fl23/core.py) | `ORIGINAL/FINAL`, fixed patches, per-body merging, guards and native report validation |
| [transport.py](../../src/fl23/transport.py) | `Session`: identity/authentication/bounded I/O, unknown-result stop, restricted staging/Backup writes |
| [assets/manifest.json](../../src/fl23/assets/manifest.json) | Exact fingerprints of compiled native assets |
| [native/installer.c](../../src/fl23/native/installer.c) | Fixed windows, retained size/inode, mode0 check/mode1 install/mode2 restore |
| [native/wbi.c](../../src/fl23/native/wbi.c) | Retained-image inspection/invalidation from the known precondition |
| [tests/test_offline.py](../../src/fl23/tests/test_offline.py) | Body isolation, occupied storage, unrelated changes, temp conflict and unknown-session checks |

Use the reviewed offsets. New preparation generates a worker for the actual files instead of using the fixed stock worker on modified files. Do not gate provenance; report instruction conflicts separately. Backups must belong to this body.

## 3. Offline startup checks

From the extracted root:

```text
.\FL23.cmd --check
.\FL23.cmd --setup-only
.\FL23.cmd check-package
```

These do not connect to the camera. Environment setup may install dependencies; incomplete existing environments are retained. Double-click `FL23.cmd` for desktop mode. Never run GUI and CLI device operations concurrently.

## 4. Complete CLI sequence

1. Select two new empty workspace/backup directories, preferably on separate disks. Retain previous workspaces.
2. Run `prepare`, requiring phase `prepared` and explicit backup/candidate/native-preflight success:

```text
.\FL23.cmd prepare --firmware-version 2.01 --workspace "D:/CameraWork-A7C2-01" --backup-copy "E:/CameraBackup-A7C2-01"
```

3. Check identity, both backups, candidates and native mode0 evidence. With actual battery at least 50% and continuous connection, install. Replace the example 82 with the real percentage:

```text
.\FL23.cmd install --workspace "D:/CameraWork-A7C2-01" --battery-percent 82
```

4. After `installed_pending_cold_start`, full readback and all I/O completion, disconnect all external power, shut down normally, wait for the access lamp and remove the battery for at least one minute. Test names, no-shutter preview, new FL2/FL3/ST captures and playback. Reconnect Mass Storage:

```text
.\FL23.cmd verify --workspace "D:/CameraWork-A7C2-01"
```

5. Check complete programs, saved parameters and AP runtime spans, keeping user observations separate. Matching readback does not prove photographic behavior or all-mode stability.

## 5. Expected work at each stage

`prepare` reads programs/body data, checks entered version and actual patch positions, merges this body's parameters, rejects occupied storage, builds candidates, verifies duplicate originals and runs native check-only. An already enabled FL23 inspection skips installer/WBI preflight and creates no new install. Temporary diagnostics execute; programs/saved recipes are not installed.

`install` requires the same body and `prepared` phase, rechecks source/settings, applies fixed program windows/full readback, merges/saves target parameters, checks unrelated-property preservation and performs guarded retained-image handling. `verify` does not reinstall; it checks post-reload files/parameters and AP spans.

Persist intent before each native invocation, verify staging, invoke once and validate magic/version/mode/length/errors and write counts. New FL23 workers use `BYTE_WINDOWS_ONLY` and complete host byte readback, with no whole-firmware hash checks. After timeout/unknown session, stop further packets including repeated cleanup. Retain `state.json`, logs, existing results and temporary files; inspect the actual outcome first.

## 6. Restoration and failures

New prepare saves a complete private checkpoint in backup2 before candidate construction. Restore that target directly over later LUT modifications; do not compare the camera to an old job's output hash:

```text
.\FL23.cmd rollback --backup-copy "E:/CameraBackup-A7C2-01" --workspace "D:/RollbackWork" --firmware-version 2.01 --battery-percent 82
```

Shared implementation: [checkpoint.py](../../src/looks/looktool/checkpoint.py), [checkpointjob.py](../../src/looks/looktool/checkpointjob.py) and [checkpointworker.py](../../src/looks/looktool/checkpointworker.py). The native worker keeps program inodes and edited-window byte guards. Name rollback reconstructs project append-only resources and compares the complete result to the archive before any writes. Unreconstructable external changes stop before writing. Restore only FL23 fields and six custom recipes, preserving other settings/calibration. Inspect retained-image mode; invalidate only 2→0. Cold restart, `rollback-verify --workspace ... --accept-photos` and physical checks remain separate.

Legacy backup2 requires the original workspace and pre-custom name resources; [upgrade-checkpoint](custom-lut.md#8-restore-if-needed) records that a separate historical flash snapshot was never captured. Never invent missing originals or replay unknown native outcomes. New full rollback is not physically validated.

## 7. AI tests and handoff

Run `python -m unittest discover -s src/fl23/tests -v` and `python -m unittest discover -s dev/usb/tests -v`. The host suite includes actual CMD/PowerShell 5.1/7 forwarding, Unicode/spaced paths, exit codes and simulated USB states. These are not full camera boot, power-loss recovery or second-body validation.

Deliver commands/exit codes, backup locations, preparation/write/verify phases, complete byte readbacks, preservation/cleanup, load evidence, user capture/playback and restoration results. Do not reintroduce unnecessary hash gates. Without device access/authorization, complete offline checks and state remaining physical stages rather than inventing installation success.
