# Desktop development

Keep changes on `feature/unified-desktop`. No camera operation occurs at startup,
in packaging, in `--offline-self-test`, or in `--smoke-test`.

## Run and build

Use native 64-bit Python 3.11 on Windows or macOS:

```text
python -m pip install -r desktop-requirements.txt pyinstaller==6.16.0 pytest==8.3.5
python -m pytest dev/desktop -q
python desktop.py
python dev/desktop/prepare_assets.py
python dev/desktop/build.py
```

Windows output: `dist/A7C2Tools/A7C2Tools.exe` and its complete ZIP. Keep the whole
folder together. macOS output: `dist/A7C2Tools.app` and a native-architecture DMG.
Packages have no developer signing certificate; physical USB behavior remains a
separate acceptance test. `.github/workflows/desktop-preview.yml` builds on native
Windows/macOS runners without publishing a Release.

## Integration contracts

- `src/desktopapp/window.py`: six pages. Every operation runs in a child process;
  camera work cannot be cancelled by the GUI. Reopening the application preserves
  workspace paths. Unknown writes never auto-retry.
- `worker.py`: dispatch to existing engines, preserving complete exceptions and
  per-job journals. `src/camera_runtime` retains the flexible FL23 planner and uses
  merged PR #5 color/curve assets; existing `src/fl23` GUI is independent. The native
  installer also supports byte-window manifests and request/result namespaces.
- Power is confirmed in a fresh dialog for each write, without a numeric field.
  `looktool.power.require_power` records the confirmation with a null percentage,
  never a fabricated USB measurement. The old CLI percentage option still works.
  Administrator logs stream while running; PnPUtil has a timeout and raw output
  preservation. The GUI also polls finished worker state to clear its busy display.
- `drivers.py`: explicit preparation of only Sony `054C:0E8A` and `054C:0336`, with
  Windows elevation only when a binding needs installation. The optional transport
  callback runs between the two authentication stages, not after firmware writing.
  No TUR/getCameraInfo gate, auth replay, or automatic driver install at startup.
  macOS uses packaged libusb and an explicit camera-volume unmount.
- `recovery.py`: metadata-only discovery/index, live same-body selection, then one
  reused service session for the existing rollback backend. No firmware SHA
  whitelist; preserve current state and perform full byte readback. Manual old
  backup2 recovery remains separate from automatic complete-ZIP selection.
- A7Look imports keep shared compressed stores, the unchanged-title no-op fix and
  independent per-slot restoration. Record the new restoration job for subsequent
  reload verification. The compiler uses `--calibration`, not the retired `--model`.
- Frozen LrC installs use `--raw-profile-worker`; its settings registry is shared
  with verified look activations. ExifTool is user-selected unless bundled at build
  time. DCP compilation additionally needs Lightroom and its configured renderer;
  direct ST/sRGB CUBE compilation does not.
- Vertical Display is shooting information/layout rotation, session-only, with
  reversible resource aliases. Do not reuse the failed image-bank/ELF display patch.
- Shutter sound keeps native on/off and custom PCM installation separate. Persist
  only the exact confirmed audition, after temporary audition recovery.

Before the owner's physical test, complete source tests, packaged offline native
compilation, GUI startup and DMG verification. None proves camera boot safety or
real preview/photo/color correctness. Do not ship private firmware, backups, photos,
DCP inputs, credentials or body calibration in source/build artifacts.


## Direct workflows (preview.2)

The owner explicitly removed mandatory backups for the new GUI workflows.
Legacy CLI/historical-backup restoration remains available; do not silently
reintroduce its two-backup prerequisite into the direct actions.

`looktool/direct.py` plans fresh current bytes, uses the existing bounded native
workers, verifies complete readback, preserves independent saved/live calibration
and keeps transaction evidence. It creates no full body archive or source-program
copy. FL23 removal changes only the two menu product flags; shared runtime remains.
Legacy single-slot ST reset neutralizes its correction and native stage, retaining
the legacy shared runtime. Standalone layouts also clear the imported-slot mask.

`factory-regions-2.01.json` contains only generic original bytes for supported
project regions and FL23 color subranges. It contains no full firmware, body data,
DCP data, photos or private paths. Its regions are derived from the current FL23,
LUT/native-photo and sound implementations plus reviewed legacy program diffs.
The default restoration preserves bytes outside those regions. Optional original
DAT import uses the vendored MIT fwtool decoder and checks model/version.

To regenerate the reference, use original 2.01 components and the optional private
legacy fixture index with `dev/desktop/build_factory_reference.py`; the build needs
`keystone-engine` for deriving the real sound windows. Do not publish the inputs.
Reference regression tests must prove exact restoration for supported variants,
per-body calibration preservation and no changes outside the owned regions.
None of these offline checks proves camera boot safety.
