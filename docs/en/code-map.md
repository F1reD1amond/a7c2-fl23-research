# Source layout and shared boundaries

The Windows and macOS desktop apps use the same GUI, operation planner, recovery engine, selected-slot operations, audio processing, and camera writes. Host differences are USB drivers, privilege elevation, and media/interface capture.

| Location | Responsibility | Host scope |
| --- | --- | --- |
| `desktop.py` | GUI and background-worker entry | Shared |
| `src/desktopapp/` | GUI, jobs, one-click coordination and feature dispatch | Shared |
| `src/desktopapp/actions/` | Shared action categories and look/sound adapters | Stable backend entrypoints for frontend replacement |
| `src/desktopapp/platforms/usb_drivers.py` | Shared USB inventory/setup entry; Windows driver bindings, UAC and uninstall | Driver changes run on Windows only |
| `src/desktopapp/platforms/macos_authorization.py` | Terminal/sudo worker authorization | macOS |
| `src/desktopapp/platforms/macos_media.py` | Explicit connection-page media unmount | macOS |
| `src/camera_runtime/macos_host.py` | Camera media identification/unmount and interface capture | macOS adapter called by the shared transport |
| `src/camera_runtime/` | Camera service communication and compatible FL23 parameters | Shared |
| `src/looks/looktool/` | Combined direct writes, recovery, selected looks and standalone DCP/CUBE fitting | Shared |
| `src/shutter_sound/` | Audio conversion/volume, audition and persistent sound | Shared runtime moved out of `dev/` |
| `src/shutter_sound/native/` | AArch64 sound workers | Shared camera code |
| `src/vertical/` | Persistent display switch and original image aliases | Shared |
| `plugins/` | Optional Lightroom auto-profile plugin | Shared plugin; only this feature needs Lightroom |

`desktopapp.drivers` and `desktopapp.macadmin` retain compatibility import names pointing to the exact implementation module objects in `platforms/`; they contain no duplicate implementation. Shared low-level workers remain under `src/fl23/native/` and are reused by feature engines.

| Folder | Contents |
| --- | --- |
| `src/` | Distributed runtime code |
| `dev/desktop/` | Native packaging, build-asset preparation and desktop tests |
| `dev/shutter_sound/` | Sound tests, standalone emulators and trace experiments |
| `dev/vertical/`, `dev/release/` | Vertical tests/build helpers and historical CLI release tools |
| `desktop-assets/` | Ignored distribution data: six defaults, paired profiles, host helpers |
| `build/` | Ignored fitting caches, maintainer Lightroom references and validation evidence |
| `dist/` | Final EXE, ZIP and DMG outputs |

Root CLI entries remain available. Their historical backup workflows are distinct from desktop built-in recovery. Both desktop host versions call `looktool.direct`; they do not maintain separate recovery implementations. The standalone end-user converter does not call the maintainer's Lightroom or server fitting scripts.
