# Custom LUT / DCP: from a file to the camera

[Home](../../README.md) · [简体中文](../zh-CN/custom-lut.md)

**You can operate this manually; no AI is required.** `lut.py` includes conversion, backups, actual device writes, full readback and restoration, independently of FL23 installation. It accepts recognized ILCE-7CM2 2.01 programs only. An existing-six-look slot update passed on one Windows camera, including preview/photos and standalone reload verification. Stock first-install and Mac USB writing remain untested.

Download the tool, then follow [setup](manual.md) for Python and USB:

| What you need | Download / source |
|---|---|
| Run the tool, recommended | [Single-file lut.py](https://github.com/QAQLeonard/a7c2-fl23-research/releases/download/v2.1/lut.py); save the file rather than copying the webpage |
| Complete tools, source and guides | [Tools ZIP](https://github.com/QAQLeonard/a7c2-fl23-research/releases/download/v2.1/a7c2-tools-2.1.zip); extract it and enter the folder containing `lut.py` |
| Read / modify the source | [This version's source](https://github.com/QAQLeonard/a7c2-fl23-research/tree/v2.1) · [LUT implementation](https://github.com/QAQLeonard/a7c2-fl23-research/tree/v2.1/src/looks) |

All attachments and checksums are on the [release page](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.1). Current source is on [main](https://github.com/QAQLeonard/a7c2-fl23-research/tree/main); [LUT implementation](https://github.com/QAQLeonard/a7c2-fl23-research/tree/main/src/looks). For a first installation, use the fixed version linked above.

Open a terminal in the folder containing `lut.py` and run the commands below there. Use `python` on Windows or `python3` on Mac; if you created a virtual environment, use its interpreter with the installed dependencies. Both downloads use the same commands; only [dependency setup](manual.md#python-and-dependencies) differs.

## 1. Choose DCP / LUT

Obtain your `.dcp` or `.cube`; the [reference pack](profiles.md) contains original DCPs. Choose custom slot 1–6 and its displayed name. Import one slot per job; repeat for additional looks and keep each job's restoration history.

DCP conversion defaults to the bundled **one-scene A7C II rendering approximation**, extracting LookTable/tone without transplanting donor sensor matrices. This is not the complete Adobe renderer or guaranteed Fuji/Ricoh matching. Override with your measured `--calibration "model.json"`. Factory per-body calibration is preserved.

CUBE output must be sRGB. For Sony ST sRGB input, add `--input-space sony-st-srgb`; other inputs such as Log also need `--input-space "space name" --bridge "ST-to-that-space.cube"`. A Log LUT is never silently treated as an ST LUT.

## 2. Convert

```text
python lut.py import "look.dcp" --name "Classic Neg." --slot 1
```

Without `--write`, this prepares, backs up and preflights without installing tables. It connects for diagnostics but does not modify firmware/names/recipes. You do not need project JSON editing, patch authoring or an AI implementation.

## 3. Back up the camera

Development branch `feature/lut-compact-backups` uses a **shared compressed foundation plus a per-slot pre-write checkpoint**. Initial data is saved once; subsequent jobs add changed blocks. No repeated complete program copies, complete name targets or full readback files are retained. Complete reads/readbacks still verify current data; only their results are saved. This storage/slot-restore workflow awaits physical validation and is not in the old v2.1 download.

The step-2 command handles backup automatically. Each job has one `slot-N-before.private.json` with the prior table, names and recipe. The complete source can be reconstructed from the foundation and this snapshot's direct deltas. Output reports newly added compressed bytes.

Keep the printed **Job path**, its backup directory, and the sibling `.a7c2-lut-work-store` / `.a7c2-lut-backup-store` directories. A small checkpoint alone is not self-contained. Default paths reuse the foundation automatically. For custom paths, keep successive jobs/backups under consistent parents; prefer another drive for the second copy. Existing plain backups remain readable and are not deleted.

## 4. Write

After `PREFLIGHT_VERIFIED`, supply the actual battery percentage:

```text
python lut.py install "JOB_PATH" --battery-percent 90
```

Or combine preparation and installation:

```text
python lut.py import "look.dcp" --name "Classic Neg." --slot 1 --write --battery-percent 90
```

Program windows, name resources and the selected ST recipe are separate transactions. Unselected recipes and existing FL2/FL3 are preserved. Keep imported slots on ST; the base picker is not hard-locked. Maintain power and USB, and leave the camera alone during writing.

## 5. Full readback

The tool checks complete AP/CP files, every name resource and saved settings, rather than only patched bytes. Errors stop the job and retain evidence. Continue only after `AWAITING_RELOAD`.

## 6. Reload

Once all I/O has ended, disconnect USB and other external power, shut down normally, wait for the access lamp, then remove the battery for at least one minute. Reinstall it and start the camera. The first startup may be slower. Do not reflash to force a reload.

## 7. Verify preview and photos

Before pressing the shutter, switch repeatedly/randomly between ST and imported looks and check immediate live-view updates. Then capture/play back new photos, check names and original looks. Working photos do not establish working preview.

Reconnect in Mass Storage mode:

```text
python lut.py verify "JOB_PATH" --accept-photos
```

Use `--accept-photos` only after those physical checks succeed. The tool additionally checks a new boot, disk programs, loaded AP spans and recipes; it does not directly dump running CP instructions/tables.

## 8. Restore if needed

```text
python lut.py restore "JOB_PATH" --battery-percent 90
```

The job restores its original recipes/programs/names and reads them back, then reports `RESTORED_AWAITING_RELOAD`. Repeat steps 6–7 and `verify ... --accept-photos`. Restore multiple imports in reverse order: later jobs change complete-source fingerprints, so an older job cannot be forced over them.

**Disconnect or unknown result:** keep the folders and first run `python lut.py recover "JOB_PATH"`. It reads existing results, classifies state and cleans confirmed owned temporary files without reexecuting a loader. Only a proven phase permits `python lut.py resume "JOB_PATH" --battery-percent 90`. If it remains `NEEDS_REVIEW`, stop; do not repeat import/install blindly.

[The AI guide](lut-ai.md) covers implementation/reproduction; ordinary installation does not require it.

The development version can also undo the replacement of a **previously imported slot**, preserving later changes to other slots:

```text
python lut.py restore-slot "ORIGINAL_JOB" --battery-percent 90
```

This creates a fresh restoration job over current state; reload/verify using steps 6–7. A subsequent change to the same slot stops restoration rather than overwriting it. Slot-only removal of shared functionality after a slot's first activation is not implemented; use the exact `restore` flow above. Compressed snapshots do not depend on intermediate job directories, but retain their shared foundation.
