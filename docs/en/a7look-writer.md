# Write an A7Look to the camera (development)

[简体中文](../zh-CN/a7look-writer.md) · [Tool overview](a7look-suite.md)

The writer consumes a compiled `.a7look` without refitting it. It supports slots 1–6, the complete correction table, and tone/matrix/chroma represented by the current native integer basis. Unsupported stages are rejected rather than silently omitted. Custom looks work independently of FL2/FL3 installation.

## Install and write

Windows and macOS use the same Python CLI. Requires 64-bit Python 3.10+:

```text
python -m pip install -r src/looks/requirements-device.txt
```

Follow the [USB connection guide](custom-lut.md). With Mass Storage mode and adequate power:

```text
python a7look_write.py import "Astia.a7look" --slot 4 --work-dir "jobs/astia" --backup-dir "/independent-backup/astia" --write --battery-percent 100
```

Report the actual battery level. Replace the backup placeholder with a real path, such as `E:/A7Look-Backups/astia` on Windows or `/Volumes/Backup/astia` on macOS. Use two new empty work/backup directories. The command reads current state, creates two compressed incremental backups, rebuilds native parameters from this body's ST data, preflights, writes names/programs/the selected recipe, reads back completely, and prepares reloading. Other slots, native looks, and body calibration are preserved. The selected recipe is set to ST; its base picker remains editable, so keep ST selected when using this look.

For prepare-only operation omit `--write --battery-percent 100`, then run:

```text
python a7look_write.py install "jobs/astia" --battery-percent 100
```

## Reload and accept

After all I/O ends, disconnect USB and other external power, shut down normally, wait for the access lamp, remove the battery for at least a minute, and restart. Switch ST/selected slot without pressing the shutter; check immediate preview changes, a new photo/playback, other slots, and FL2/FL3 if installed. Reconnect in Mass Storage mode:

```text
python a7look_write.py verify "jobs/astia" --accept-photos
```

`--accept-photos` records checks you actually performed. Complete disk readback and a new kernel boot do not replace preview/photo acceptance or directly read running CP memory.

## Restore one slot

```text
python a7look_write.py restore-slot "jobs/astia" --work-dir "jobs/undo-astia" --backup-dir "/independent-backup/undo-astia" --battery-percent 100
```

This creates a fresh transaction restoring that slot's table, native stages, name, and recipe over current state, retaining later changes to other slots. A later change to the selected slot requires its latest Job. Restoration compares actual bytes and does not require old firmware hashes. Reload and verify the restoration in the same way.

If source-DCP history and matching observed slot bytes were retained, accepted restoration also restores Lightroom attribution. Unknown sources suspend matching rather than guessing. Complete initial rollback belongs to the separate [Recovery tool](recovery.md).

## Validation scope

Development validation includes real program fixtures, compiled native installers, complete byte inverses, and simulated native-stage transactions. The delivered general writer installed the final slot-4 Astia file on one Windows A7C II; complete readback, fresh-boot/AP loaded checks, owner preview/photo/playback and FL2/FL3 checks passed. All six final fitted looks are now installed with complete readbacks; all-six cold reload and owner acceptance are pending. Final six-look color accuracy and physical single-slot restoration remain unverified. macOS USB was not tested in this round.

Source: [entry](../../a7look_write.py), [transactions](../../src/looks/looktool/devicejob.py), [native-stage I/O](../../src/looks/looktool/photoio.py).
