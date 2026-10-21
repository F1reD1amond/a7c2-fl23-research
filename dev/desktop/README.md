# Desktop development

Current integration branch: `feature/desktop-overview`. No camera operation occurs at startup,
in packaging, in `--offline-self-test`, or in `--smoke-test`.

## Run and build

Use native 64-bit Python 3.11 on Windows or macOS:

```text
python -m pip install --no-build-isolation -r desktop-requirements.txt pyinstaller==6.16.0 pytest==8.3.5
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
  macOS uses packaged libusb, unmounts only media under the identified camera USB device, then explicitly claims its normal/service interfaces. It does not install Windows drivers or use pre-authentication TUR/getCameraInfo gates.
- `recovery.py`: metadata-only discovery/index, live same-body selection, then one
  reused service session for the existing rollback backend. No firmware SHA
  whitelist; preserve current state and perform full byte readback. Manual old
  backup2 recovery remains separate from automatic complete-ZIP selection.
- A7Look imports keep shared compressed stores, the unchanged-title no-op fix and
  independent per-slot restoration. Record the new restoration job for subsequent
  reload verification. The compiler uses `--calibration`, not the retired `--model`.
- Frozen LrC installs use `--raw-profile-worker`; its settings registry is shared
  with verified look activations. ExifTool 13.59 and its complete official runtime are bundled; missing/stale
  paths automatically fall back to bundled/PATH/download preparation. DCP and ST/sRGB CUBE compilation run offline without Lightroom or a renderer;
  Lightroom is needed only to use the optional Lightroom plugin.
- Vertical Display saves its native shooting-information/layout switch, with
  reversible resource aliases. Do not reuse the failed image-bank/ELF display patch.
- Sound uses the current converted payload directly. Audition/confirmation/recovery
  records are optional and do not gate sound on/off or saving.
  Volume decrease/increase/reset are host-only actions; each re-encodes the unchanged
  selected PCM, updates the matching preview, and never opens USB or changes camera-job state.

Before the owner's physical test, complete source tests, packaged offline native
compilation, GUI startup and DMG verification. None proves camera boot safety or
real preview/photo/color correctness. Do not ship private firmware, backups, photos,
DCP inputs, credentials or body calibration in source/build artifacts.


## Default six-look pack (preview.6)

Home explicitly selects `default-six-v1`. `desktopapp.presets.resolve` expands it
to NC/CC/NN/Astia/GR Positive/GR Negative, validates all six before USB, and the
coordinator copies the exact documents into its `inputs/` directory. Continuing
uses saved options and never injects presets into an old transaction. Custom-file
mode does not add defaults and preserves empty slots.

Prepare distribution-only assets before building:

```text
python dev/desktop/prepare_presets.py --look NC.a7look --look CC.a7look --look NN.a7look --look Astia.a7look --look GR-Positive.a7look --look GR-Negative.a7look
```

Use the existing fitted, supported native-photo documents, not synthetic examples
or residual-only substitutes. Files are copied unchanged with their original DCP
payload/rights, plus per-look credits; they are ignored under `desktop-assets/`
and are not source-code assets. Packing fails if a slot is missing. The frozen
self-test resolves/copies all six and exercises setup with a simulated dispatch;
it does not open USB. `test_direct_reference.py` also plans the real pack against
stock programs and checks six tables/titles, calibration, FL23/sound and repeated
planning without growth. These checks do not establish physical color fidelity.

`reloadguide.py` supplies the post-I/O dialog. It appears only after the worker
exits successfully with a reload-waiting phase, never on a failed/unknown write,
and does not mark physical acceptance. Users can reopen the steps manually.

## Direct workflows (preview.5)

Preview.8 adds a separate `AWAITING_RESOURCE_RELOAD` boundary for fully
committed stream names whose final RO remount returns EBUSY. Only an exact
phase-9/count-complete/clean report may take it. Verify all name bytes and
untouched programs, prepare retained-image invalidation, close I/O, then ask
for cold power removal. `namespause.py` preserves prior evidence and restricts
cleanup to the exact finished /tmp artifacts. No program installer RW
prerequisite is relaxed. New boot and RO must be confirmed before a fresh
program transaction; repeated clicks before that remain waiting. Once names
already match, the program transaction performs no name writes. A final normal
reload is still required after program installation.

PR #6 is copied into the FL23 source and runtime asset mirror. Preserve the
service-first runtime transport. `fl23-native-history.json` records only the
two previously published native CP field values, allowing edited-byte upgrades
from the prior curve revision while preserving custom code. It is not a full
firmware identity whitelist. Photo/movie routes are (48,46)/(49,47).

`desktopapp.allinone` persists the guided install stages. `looktool.bundle`
composes selected looks/FL23/native sound into one direct program plan; empty
slots remain untouched. Cold reload is a manual boundary; the same button
verifies loaded state before adopting already enabled sound and enabling
session-only Vertical Display. Unknown native results are never replayed.

Forward name transactions complete before program edits. Legacy transactions
retain old resource hardlinks until a verified new boot: mapped replaced files can
make a read-only remount return EBUSY. Factory inverse mode may defer that
specific remount only after phase-9/all-files-complete evidence and complete
host program/name readback, with no remaining program/name writes. Record the
deferral explicitly, finish settings/WBI, and require a new boot plus `/usr`
read-only proof before loaded-state acceptance. Do not ignore other errors.

`RecoverySession` acquires an existing service endpoint without authentication
or stop requests, reads its AP serial, and matches the recorded body. Recovery
still proves the native model and current bytes before writing. Unknown session
teardown sends no auth.stop. This is not a generic service-identity bypass.

Desktop native photo/code paths require both Keystone and Capstone; package
their native libraries and exercise assembly/disassembly in the frozen smoke
test. Source tests alone do not validate a frozen dependency bundle.

The GUI and worker both discover pending factory transactions with
`factoryrecover.pending`; a later pre-write failure must not hide the original
interruption. `DirectJob.continue_factory` captures fresh bytes/settings,
accounts for the last native result, and builds only remaining changes. It
persists plans before staging and phases before names/settings/WBI. Finished
transactions use loaded-state verification, not another write. Use the single
main recovery button; manual transaction selection is collapsed.

Missing host evidence can be recovered from a complete camera-side native
result. Unknown outcomes, active plugins, foreign temporary bytes or failed
rollback/remount are not cleaned or replayed. Delete the result last so a
cleanup interruption still has a report. Tests in `test_factory_recovery.py`
exercise discovery, partial recovery, repeated failure and cleanup interruption.

Factory inverse names now use `CHECKPOINT_STREAM_RESTORE`: one new inode at a
time, fsync after replacement, with a single-file statfs preflight. Byte-based
forward imports now use `BYTE_NAME_STREAM_INSTALL`: stage one resource,
atomically replace it, and reserve space to reconstruct the exact original
from preserved payload/count/pointers on failure. They do not retain 68 old
hardlinks. Legacy forward mode remains unchanged. A live mmap keeps its
old inode, so space can still run out during streaming; partial progress is
reported and pending newly created files are cleaned. Never truncate live UXC
inodes or delete unaccounted historical hardlinks to make space.

`desktopapp.lookbatch` validates 1–6 selected files and calls the same composed
writer once with FL23/sound explicitly false. The normal look page defaults to
the six catalog files; clearing a field preserves that slot. Optional title
overrides are validated before connecting. The batch uses the look page's
verification workspace, not the Home coordinator, and creates no driver or
sound/vertical operations.

`desktopapp.reviewnames` accounts only for completed zero-commit ENOSPC reports:
no program write intent, native rollback/cleanup/RO all successful, source program
windows and original name bindings match. It removes only exact completed temp
artifacts with the report last. It never executes native code, edits resources
or rewrites programs/settings. Home then uses a fresh child directory; the old
failed child stays unchanged. Other failures still stop. Regression evidence is
in `test_review_names.py` and `test_names_forward_native.py`.

`directresume.py` and `DirectJob.resume_factory_names` retain the narrow
preview.3 path for forensic regression tests. The GUI uses the unified
`continue_factory` path above. Native syscall fault tests live in
`test_names_native.py`; no offline test establishes camera boot safety.

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

New desktop setup plans set `vertical_persistent=true` and include native AP
key `02cf1906` (00 ON / 01 OFF) in the combined settings commit. The reviewed
descriptor at AP file offset `57bbb90` identifies this byte field. The existing
vertical workers verify resources first; no new AP/CP hook is introduced.
Saved OFF precedes runtime OFF and exact-alias removal. Loaded verification
checks native primary RAM as well as both saved/Backup-RAM records, without
silently replacing a failed cold-load with a RAM-only enable. Older setup
plans without this marker retain their session-only behavior. Persisted
startup and physical Fn/shooting behavior still require owner acceptance.

Recovery discovery excludes both COMPLETE and LOADED with verified RO; physical
photo acceptance is independent. A later Restore click must start a new plan.
`test_lifecycle.py` exercises two import/recovery cycles through the real worker
and transaction storage with a simulated camera/planner. Guided setup recovers
completed child proof after parent interruption, unstarted resource dispatch
and the exact nested `program-install` child. It verifies rather than replaying
completed writes; unknown nonempty children stop with their evidence intact.

During development, run focused checks for the changed paths. Defer the full regression and complete package acceptance to the formal release, as requested by the owner. One-click setup checks the final combined camera state once after reload; individual look operations check/write/read back together, without a separate verify button. Factory recovery alone must remain pending until its loaded-state check passes.

## macOS native builds

Build **on a Mac**, with native 64-bit Python 3.11. Windows cannot cross-build an APP/DMG. macOS packages support Apple Silicon only; minimum advertised OS is macOS 14. Apple Silicon has passed actual native packaging, packaged offline/GUI checks and DMG/signature verification; its DMG has been downloaded locally. Intel packaging was cancelled at the owner’s request and is not offered. Physical Mac USB is untested.

```sh
python3 -m venv .venv-desktop
source .venv-desktop/bin/activate
python -m pip install cmake==3.31.6 setuptools==80.9.0 setuptools-scm==8.3.1 wheel==0.45.1 backports.tarfile==1.2.0
python -m pip install --no-build-isolation -r desktop-requirements.txt pyinstaller==6.16.0 pytest==8.3.5
python dev/desktop/prepare_assets.py --preset-archive /path/to/desktop-presets.zip
python dev/desktop/build.py
```

Keystone 0.9.2 and Unicorn 2.1.3 have no Apple Silicon wheels on PyPI. On ARM64 they build from their source distributions using Xcode Command Line Tools and CMake 3.31.6 (install the command-line tools if absent). Use Zig 0.13.0. Do not insert Intel dylibs into an ARM64 app. Rosetta is not required; Intel builds are not offered.

Outputs: `dist/A7C2Tools.app` and `dist/A7C2Tools-macOS-arm64.dmg`. Staging is fresh per build; packaging verifies the ad-hoc app signature and DMG structure. There is no Developer ID signature/notarization. Mount the DMG and drag the app to Applications; run packaged offline self-test and GUI smoke checks before distribution. Native binaries and all helper imports must pass on each architecture; Windows mocks alone do not establish this.

The six compiled looks contain distribution-only source profiles and must stay outside Git. On an existing build machine, export the exact existing pack and notices:

```text
python dev/desktop/prepare_assets.py --export-presets dist/desktop-presets.zip
```

Transfer that ZIP to the Mac. `--preset-archive` also accepts the existing Windows desktop ZIP, but extracts only the six looks and their attribution/license files, never the Windows executable or DLLs. macOS bundles the official portable Perl ExifTool distribution and its modules/license, never a Windows helper. `prepare_assets.py` prepares it automatically or accepts `--exiftool-archive`. The runtime can also fall back to an installed helper or official download.

The manual `desktop-preview.yml` workflow has Windows and `macos-15` (ARM64) native runners. Supply `preset_archive_url` pointing to the exported pack or an accessible desktop ZIP. The workflow must be available on the default branch to appear for manual dispatch; choose the feature ref for its code when available. On the feature branch, updating `dev/desktop/native-build-request.json` also triggers an Apple Silicon build without modifying main; manual dispatch selects macos / windows / all. The current public v2 CLI ZIP is not a desktop preset pack. CI runs focused contracts, native packaging, packaged offline/GUI checks, signature/DMG verification and uploads artifacts, without publishing a Release. Local source presets alone cannot populate a clean hosted runner.

macOS host preparation is informed by [MDHan/a7c2-fl23-macos](https://github.com/MDHan/a7c2-fl23-macos) at commit `1491f734df07f02fb77da6ea7062828bce0e30e7`: identify camera descendants in IORegistry, unmount camera storage normally, then claim libusb ownership. Its MIT notice is retained at `docs/licenses/a7c2-fl23-macos-MIT.txt`. We retain this project's service-first admission; the reference's pre-authentication camera-info and backup requirements are not imported. No camera operations occur while building.

## macOS Terminal authorization (preview.10.20 USB test)

Explicit camera jobs open a per-job Terminal script and use sudo. The login-user
GUI never reads or stores the password. The shared Windows installation/recovery
engines are retained. Original user HOME/app-data/cache paths and file ownership
are preserved. LIBUSB_DEBUG defaults to 4 in the privileged process; full backend
stderr is retained in the support bundle.

The recipient's probes motivate testing this launch route. They do not establish
that the packaged app or full service/firmware flow works on that Mac.

mac_authorization_smoke.py syntax-checks the Terminal script and runs the exact
privileged-worker command with CI sudo, without USB. It checks root execution,
original user paths and returned ownership. Native tests do not exercise the
recipient's interactive password prompt or physical camera.

This branch deliberately uses the old portrait aliases and excludes the recent
Fn/submenu line-bank rework. Resource compression and volume controls remain
separate work. Main and the Windows development folder are unchanged.
