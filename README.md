# A7C II Tools

**English** · [简体中文](README.zh-CN.md)

Camera-side tools for the **Sony A7C II (ILCE-7CM2) on firmware 2.01**: FL2/FL3 Creative Looks, custom looks in slots 1–6, factory-function recovery, Vertical Display and electronic shutter sound — in one Windows desktop application, with independent command-line tools for each part.

> [!IMPORTANT]
> **New desktop release `3.0.0-desktop-preview.10.6`** — Windows 10/11 x64 only; macOS packaging is deferred. This is a preview: not every feature has passed physical acceptance yet, see [Verification status](#verification-status).
>
> Known published FL23 versions can upgrade directly. Factory-function recovery is optional, not a prerequisite for one-click installation.

**Community:** [Telegram (recommended)](https://t.me/sonyfwlab) · [Discord](https://discord.gg/SwPdfSd9c)
**Author:** Xiaohongshu [QAQLeonard（读研版）](https://www.xiaohongshu.com/user/profile/660501f7000000000600d03c) · Douyin **LeonardZ** (ID `90860261487`)

## Contents

- [Features](#features)
- [Quick start (Windows package)](#quick-start-windows-package)
- [Everyday tasks](#everyday-tasks)
- [Verification status](#verification-status)
- [Safety rules](#safety-rules)
- [Command-line tools](#command-line-tools)
- [Run and build from source](#run-and-build-from-source)
- [Repository layout](#repository-layout)
- [Documentation](#documentation)
- [Releases and downloads](#releases-and-downloads)
- [Credits and licenses](#credits-and-licenses)
- [Film look comparisons](#film-look-comparisons)

## Features

| Feature | What it does |
| --- | --- |
| **USB drivers** | Prepares the normal (`054C:0E8A`) and service (`054C:0336`) USB connections, keeps an existing compatible driver, diagnoses connection errors and can uninstall the camera driver. Administrator access is requested only when a binding must be installed. |
| **FL2 / FL3** | Enables, re-enables or removes the two menu entries. Includes the photo/movie curve-routing fix from [PR #6](https://github.com/QAQLeonard/a7c2-fl23-research/pull/6). |
| **Custom looks** | Writes `.a7look` files into chosen custom slots with your own names, or resets slots to ST. Several writes and resets run as one operation; slots you don't list stay unchanged. |
| **Look conversion & Lightroom** | Converts supported DCP/CUBE files to `.a7look` and installs a Lightroom Classic plugin that applies the matching source DCP to RAW files on import. DCP conversion needs Lightroom and its renderer set up. |
| **Factory recovery** | Removes supported project changes and restores stock 2.01 behavior **without an old backup** or firmware download. Body calibration, counters and unrelated settings are kept; custom slots return to ST. Restoring from an original backup is a separate, optional path. |
| **Vertical Display** | Saves the native switch that rotates shooting information and layout when the camera is held vertically. The full MENU does not rotate. |
| **Electronic shutter sound** | Turns native electronic shutter sound on or off, converts a clip from an audio/video file and saves it as the custom sound. Audition is optional. |

## Quick start (Windows package)

Download the complete **`A7C2Tools-Windows-x64.zip`** from [Releases](https://github.com/QAQLeonard/a7c2-fl23-research/releases). Extract the whole archive and run `A7C2Tools.exe`, keeping the `_internal` folder next to it. No separate Python install is required. Opening the app never connects to or writes the camera by itself. The interface is in Simplified Chinese; English names below are translations.

> [!NOTE]
> **Connection message:** During connection or driver switching, the camera's **“Check the connected device” (请检查所连接的设备)** message is expected. A missing camera drive letter is also possible. Follow this tool's progress and logs; do not unplug or reinstall drivers just because of the camera message. Actual errors reported by the tool still need attention.
>
> **Cold reload** — used after every write: unplug USB and any external power → wait for the access light to stop → switch OFF and wait for the screen and light to go out → remove the battery for **at least one minute** → reinsert it and switch ON.

1. Charge the battery and connect one camera in **Mass Storage** mode with a data cable.
2. Open **首页 · 一键安装 (Home · One-click install)** and select the features. The default replaces custom slots 1–6 with the six looks below and enables FL2/FL3, native shutter sound and Vertical Display; the Lightroom plugin is optional.
3. Click **一键安装／继续上次安装**. The tool prepares drivers as needed, combines the camera changes, writes them and performs complete readback. It does not require a historical recovery-verification record.
4. Follow the dialog for a **cold reload**, reconnect, then click **继续上次安装** once. It performs the final combined loaded-state check and reports installation complete; no per-feature check buttons are needed.

**Optional recovery:** use **恢复原厂功能** only when you want to remove project modifications and reset all custom slots to ST. Its own recovery remains pending until the restart/check step succeeds. Old recipes are not recovered.

### Default six looks

| Slot | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Look | Classic Neg. (NC) | Classic Chrome (CC) | Nostalgic Neg. (NN) | Astia | GR Positive Film | GR Negative Film |

These replace the **custom** Creative Look slots only; Sony's built-in Creative Looks are untouched. The built-in looks are fitted approximations of their source DCPs, not exact reproductions. To install your own files instead, untick the built-in pack on Home and fill the custom section; empty slots are left as they are.

## Everyday tasks

- **Change one or more custom slots.** On **自定义创意外观 (Custom Creative Looks)** the list starts empty. Add an item per slot; new items default to **恢复 ST 默认 (Restore ST)**, so switch to **写入 A7Look (Write A7Look)** and pick a file when importing. Resetting a slot does not bring back its former recipe.
- **Save a custom shutter sound.** On **电子快门声音 (Electronic shutter sound)**, with native shutter sound enabled, choose an audio/video file, set the start and duration, then click **转换所选片段 (Convert selected clip) → 保存当前自定义声音 (Save current custom sound)**. Audition and listening records are optional. After the write and readback, do a cold reload to load the sound. (An optional audition instead asks you to unplug USB *with the camera still on*, so you can listen before saving.) If you hear nothing, check the camera's Audio Signals setting.
- **Go back to stock behavior.** Use **恢复原厂功能** as in Step 1. If it is interrupted, click the same button again: it reads current state and finishes only what remains.
- **Lightroom.** After installing the plugin, enable it once in Lightroom's Plug-in Manager. It chooses the DCP during RAW development; it does not alter RAW sensor data.

Full walkthrough of every page: [Windows desktop guide](docs/en/desktop.md).

## Verification status

| Area | Status |
| --- | --- |
| FL2/FL3, six-look installation, factory recovery | Camera-side evidence on the owner's Windows A7C II |
| Selected look preview/photo checks, temporary custom-audio playback | Tested on the same camera |
| Persistent custom shutter sound | 156 related offline tests, packaged self-test and offline save preparation passed; **physical write, cold boot and playback acceptance pending** |
| Persistent Vertical Display, broader shooting/Fn/video behavior | Separate checks, pending |
| macOS USB and packaging | Not validated for this build |

Offline tests and byte readback do not prove that the camera boots correctly or that colors and sound behave as intended. Details: [desktop validation](docs/en/desktop-validation.md) · [changelog](docs/en/changelog.md).

## Safety rules

- **Never repeat a write whose outcome is unknown.** The tool stops and keeps the evidence; inspect it before doing anything else. A failure that provably happened before any camera write can be retried with a fresh job.
- Keep the full logs. Support exports contain device information and local paths — review them before sharing.
- Full firmware, body backups/calibration, private photos and credentials are never part of this repository or its builds. Keep yours private.
- Use a charged battery; the tool asks you to confirm power before every write.

## Command-line tools

All tools are run from the repository root. Each one is independent; the desktop app calls the same back ends.

| Entry | Purpose | Guide |
| --- | --- | --- |
| `python desktop.py` | Desktop application from source | [Desktop guide](docs/en/desktop.md) |
| `FL23.cmd` | Windows FL2/FL3 prepare / install / verify (`FL23.cmd --help`); double-click for its original GUI | [FL23](docs/en/fl23.md) |
| `python lut.py` | DCP/LUT inspection and conversion, selected-slot import, single-slot restore, job diagnosis | [Custom LUT/DCP](docs/en/custom-lut.md) |
| `python recovery.py` | Full rollback from an original FL23 backup2 or a complete checkpoint | [Recovery](docs/en/recovery.md) |
| `python a7look_compile.py` | Offline DCP/CUBE → `.a7look` compiler | [A7Look compiler](docs/en/a7look-compiler.md) |
| `python a7look_write.py` | Write a compiled `.a7look` (shares the `lut.py` transaction CLI) | [A7Look writer](docs/en/a7look-writer.md) |
| `python raw_auto.py` / `raw_import.py` | Lightroom auto-profile plugin install; slot→DCP bindings for RAW import | [RAW workflow](docs/en/raw-import.md) |
| `python shutter.py` | Electronic shutter sound CLI (experimental) | [Shutter sound](docs/en/technical/shutter-sound.md) |
| `python vertical.py` | Older session-only Vertical Display CLI | [Vertical Display](docs/en/vertical-display.md) |

Every CLI prints its commands with `--help`; `lut.py doctor --device` and `shutter.py doctor` check dependencies without connecting.

## Run and build from source

The desktop app uses 64-bit **Python 3.11**; the standalone CLIs need 64-bit Python 3.10+ ([setup guide](docs/en/manual.md)).

```sh
python -m pip install -r desktop-requirements.txt
python desktop.py
```

Run the offline tests (no camera access):

```sh
python -m pytest dev/desktop -q
```

The packaged build also contains distribution-only assets that are not in Git (the six-look pack and bundled helpers, under the ignored `desktop-assets/`). To build a package, follow the [desktop build guide](dev/desktop/README.md) and supply those assets yourself. CI (`.github/workflows/desktop-preview.yml`) builds on native runners without publishing a Release.

## Repository layout

```text
desktop.py              Desktop app entry (GUI, worker and self-test modes)
FL23.cmd, lut.py, recovery.py, shutter.py, vertical.py, a7look_*.py, raw_*.py
                        Independent CLI entries (see above)
src/
  desktopapp/           PySide6 GUI, job workers, drivers, presets, guided setup
  camera_runtime/       FL23 planner and native runtime used by the desktop app
  fl23/                 Standalone FL2/FL3 installer, backup and verification
  looks/                looktool: A7Look compiler/writer, direct device jobs,
                        factory reference, checkpoints, RAW profile tools
  vertical/             Vertical Display native workers
  launcher.py           Shared Windows environment setup for the CMD entries
plugins/A7LookAuto.lrplugin/
                        Lightroom Classic auto-profile plugin
dev/                    Desktop build and tests, release scripts, shutter-sound,
                        USB and vertical research tooling
docs/en/, docs/zh-CN/   Matching English / Simplified Chinese documentation
docs/profiles/          DCP source inventory and original license text
calibration/            Virtual calibration model for firmware 2.01
```

## Documentation

| Topic | English | 简体中文 |
| --- | --- | --- |
| Desktop app | [Desktop guide](docs/en/desktop.md) · [Validation](docs/en/desktop-validation.md) | [桌面工具](docs/zh-CN/desktop.md) · [验证](docs/zh-CN/desktop-validation.md) |
| FL2/FL3 CLI | [FL23](docs/en/fl23.md) | [FL23](docs/zh-CN/fl23.md) |
| Custom looks | [Custom LUT/DCP](docs/en/custom-lut.md) · [A7Look overview](docs/en/a7look-suite.md) | [自定义 LUT/DCP](docs/zh-CN/custom-lut.md) · [A7Look 总览](docs/zh-CN/a7look-suite.md) |
| Backup rollback | [Recovery](docs/en/recovery.md) | [Recovery](docs/zh-CN/recovery.md) |
| RAW / Lightroom | [RAW workflow](docs/en/raw-import.md) | [RAW 流程](docs/zh-CN/raw-import.md) |
| Python setup | [Windows/macOS setup](docs/en/manual.md) | [安装准备](docs/zh-CN/manual.md) |
| Internals | [Integration](docs/en/technical/integration.md) · [Formats](docs/en/technical/formats.md) · [Failures](docs/en/technical/failures.md) · [Validation](docs/en/technical/validation.md) | [集成](docs/zh-CN/technical/integration.md) · [格式](docs/zh-CN/technical/formats.md) · [历史错误](docs/zh-CN/technical/failures.md) · [验证](docs/zh-CN/technical/validation.md) |
| Development | [Repository & maintenance](docs/en/development.md) · [Desktop build](dev/desktop/README.md) · [AI reproduction](docs/en/ai.md) | [开发维护](docs/zh-CN/development.md) · [AI 复现](docs/zh-CN/ai.md) |
| History | [Changelog](docs/en/changelog.md) | [更新日志](docs/zh-CN/changelog.md) |

Contributors and AI agents should read [AGENTS.md](AGENTS.md) and [docs/en/ai.md](docs/en/ai.md) before changing code.

## Releases and downloads

The desktop app (`A7C2Tools-Windows-x64.zip`) is on the [Releases](https://github.com/QAQLeonard/a7c2-fl23-research/releases) page. Earlier standalone tools remain available:

- [v2.2-preview.1](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.2-preview.1)** — FL23 CLI, standalone `lut.py` and `recovery.py`, full toolkit
- [v2.1](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.1) — previous non-preview release
- [v1.0](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v1.0) — original FL23 installer
- [Original DCP files](https://github.com/QAQLeonard/a7c2-fl23-research/releases/download/v2.1/a7c2-dcp-profiles-2026-10-18.zip) — separate download ([sources](docs/en/profiles.md))

## Credits and licenses

Code is licensed under [MIT](LICENSE). DCPs, reference looks and bundled dependencies keep their original licenses and attribution — see [notices](docs/en/notices.md) and [profile sources](docs/en/profiles.md). Fujifilm DCP references are credited to **门萨特里顿** and Ricoh references to **爸总林先森** on Xiaohongshu.

This is independent research, not affiliated with Sony, Fujifilm, Ricoh or Adobe. Look names imply neither endorsement nor exact color equivalence, and this is not a Sony-signed update.

## Film look comparisons

<details>
<summary>Open the scene-by-scene comparison gallery</summary>

Camera JPEGs, resized, arranged and labelled only; no exposure, white-balance or color edits. Capture settings vary, so these are visual examples rather than controlled measurements.

Each scene shows three separate comparison images in order: **ST / FL / FL2 / FL3**, **ST / NC / CC / NN**, **ST / E / GR Positive / GR Negative**. Read each grid top-left, top-right, bottom-left, bottom-right. NC = Classic Neg., CC = Classic Chrome, NN = Nostalgic Neg., E = Eterna; Astia is not included.

[Download all 19 full-resolution comparisons (about 152 MB)](https://github.com/QAQLeonard/a7c2-fl23-research/releases/download/v2.1/a7c2-film-comparisons-2026-10-18.zip), including the first scene’s extra ST comparison and the overview.

**01 · Drinks cabinet**

![01 · Drinks cabinet — ST / FL / FL2 / FL3](docs/images/film-comparison/01_饮料柜/01-1_ST_FL_FL2_FL3.jpg)

![01 · Drinks cabinet — ST / NC / CC / NN](docs/images/film-comparison/01_饮料柜/01-2_ST_NC_CC_NN.jpg)

![01 · Drinks cabinet — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/01_饮料柜/01-3_ST_E_GR正片_GR负片.jpg)

**02 · Plants**

![02 · Plants — ST / FL / FL2 / FL3](docs/images/film-comparison/02_绿植/02-1_ST_FL_FL2_FL3.jpg)

![02 · Plants — ST / NC / CC / NN](docs/images/film-comparison/02_绿植/02-2_ST_NC_CC_NN.jpg)

![02 · Plants — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/02_绿植/02-3_ST_E_GR正片_GR负片.jpg)

**03 · Counter**

![03 · Counter — ST / FL / FL2 / FL3](docs/images/film-comparison/03_柜台/03-1_ST_FL_FL2_FL3.jpg)

![03 · Counter — ST / NC / CC / NN](docs/images/film-comparison/03_柜台/03-2_ST_NC_CC_NN.jpg)

![03 · Counter — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/03_柜台/03-3_ST_E_GR正片_GR负片.jpg)

**04 · Spiral staircase**

![04 · Spiral staircase — ST / FL / FL2 / FL3](docs/images/film-comparison/04_旋转楼梯/04-1_ST_FL_FL2_FL3.jpg)

![04 · Spiral staircase — ST / NC / CC / NN](docs/images/film-comparison/04_旋转楼梯/04-2_ST_NC_CC_NN.jpg)

![04 · Spiral staircase — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/04_旋转楼梯/04-3_ST_E_GR正片_GR负片.jpg)

**05 · Bookshelves**

![05 · Bookshelves — ST / FL / FL2 / FL3](docs/images/film-comparison/05_书架/05-1_ST_FL_FL2_FL3.jpg)

![05 · Bookshelves — ST / NC / CC / NN](docs/images/film-comparison/05_书架/05-2_ST_NC_CC_NN.jpg)

![05 · Bookshelves — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/05_书架/05-3_ST_E_GR正片_GR负片.jpg)

**06 · Posters**

![06 · Posters — ST / FL / FL2 / FL3](docs/images/film-comparison/06_海报/06-1_ST_FL_FL2_FL3.jpg)

![06 · Posters — ST / NC / CC / NN](docs/images/film-comparison/06_海报/06-2_ST_NC_CC_NN.jpg)

![06 · Posters — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/06_海报/06-3_ST_E_GR正片_GR负片.jpg)

</details>
