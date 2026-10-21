# A7C II Tools

A Windows desktop tool for **Sony A7C II / ILCE-7CM2, firmware 2.01**: drivers, FL2/FL3, custom looks, recovery, Vertical Display and electronic shutter sound in one interface.

**Development summary:** `feature/desktop-overview` · **Current test build:** `3.0.0-desktop-preview.10.6` · **Platform:** Windows 10/11 x64. macOS packaging is deferred. The desktop preview is not yet a published stable Release; [existing Releases](https://github.com/QAQLeonard/a7c2-fl23-research/releases) contain earlier tools.

**Community:** [Telegram — recommended](https://t.me/sonyfwlab) · [Discord](https://discord.gg/SwPdfSd9c)

**Author:** [QAQLeonard（读研版）on Xiaohongshu](https://www.xiaohongshu.com/user/profile/660501f7000000000600d03c) · Douyin: **LeonardZ**, ID `90860261487`.

## What the desktop tool includes

| Feature | What you can do |
| --- | --- |
| USB drivers | Prepare the normal and service USB connections, retain an existing compatible driver, inspect connection errors and uninstall the camera driver. Administrator access is requested when needed. |
| FL2 / FL3 | Enable, re-enable or remove the menu entries. Includes the merged photo/movie curve-routing correction from [PR #6](https://github.com/QAQLeonard/a7c2-fl23-research/pull/6). |
| Custom Creative Looks | Import `.a7look` files into selected custom slots, choose their names, or reset selected slots to ST. Mix several writes and resets in one operation; omitted slots stay unchanged. |
| Look conversion and Lightroom | Convert supported DCP/CUBE inputs to `.a7look` and install the Lightroom Classic profile-matching plugin. DCP conversion requires Lightroom and its renderer setup. |
| Recovery | Remove supported project changes and restore stock-function behavior without an old backup. Preserve body calibration; reset custom slots to ST. Original-backup restoration is also available separately. |
| Vertical Display | Save the native switch for rotating shooting information/layout when holding the camera vertically. The entire MENU does not rotate. |
| Electronic shutter sound | Enable/disable native electronic shutter sound, convert an audio/video clip, optionally audition it, and save the current converted sound directly. |

## Start with the Windows package

Use the complete **`A7C2Tools-Windows-x64.zip`** supplied for this preview. Extract the entire archive and launch `A7C2Tools.exe`; keep its `_internal` folder beside it. The packaged application does not require a separate Python installation.

1. Use an adequately charged battery and connect the camera in **Mass Storage** mode with a data cable.
2. Open **Home** for one-click installation, or choose an individual feature page.
3. Review the selected changes. The default Home selection replaces custom slots 1–6 with the six looks below and enables FL2/FL3, native shutter sound and Vertical Display. The Lightroom plugin is optional.
4. Run the operation. Driver preparation, writing and complete readback are handled by the tool. Follow the completion dialog after all camera I/O ends.
5. When requested: **unplug USB and external power → wait for the access light to stop → switch OFF and wait for the screen/light to go out → remove the battery for at least one minute → reinstall and turn ON**. For a pending Home installation, reconnect and use the same Continue button.

Some interrupted resource updates need an intermediate reload; the tool explains when to reconnect and continue. Opening the application does not automatically connect to or write the camera.

### The default six looks

| Custom slot | Look |
| --- | --- |
| 1 | Classic Neg. (NC) |
| 2 | Classic Chrome (CC) |
| 3 | Nostalgic Neg. (NN) |
| 4 | Astia |
| 5 | GR Positive Film |
| 6 | GR Negative Film |

These replace the **custom Creative Look slots**, preserving the original built-in Creative Looks. On the individual custom-look page, the operation list starts empty. Add only the slots you want to change; each new item defaults to **Restore ST**, so choose **Write A7Look** when importing a file. Resetting a slot does not recover its former custom recipe.

### Save a custom shutter sound

With native electronic shutter sound enabled, choose an audio/video file, set the clip's start and duration, and click **Convert Selected Clip → Save Current Custom Sound**.

Audition, listening confirmation and recovery records are **optional**. Saving does not require clearing a temporary audition or recording cold recovery first. After actual write/readback, follow the cold-reload dialog to load the persistent sound. Optional audition instead asks you to unplug USB **while keeping the camera powered on**, so you can listen before saving.

## Current verification status

FL23, six-look installation and recovery have camera-side evidence from the owner's Windows A7C II; selected look preview/photo checks and temporary custom-audio playback have also been tested. This does not establish acceptance of every operation on every camera.

The latest sound update passed **156 related offline tests**, packaged application self-test, and full offline save preparation using the owner's local program backup and audio. That preparation exercised valid/missing/oversized boot CSV cases, inverse reconstruction and native worker compilation. **Persistent custom sound still requires physical write, cold-boot and playback acceptance.** Persisted Vertical Display and broader shooting/Fn/video behavior also remain separate checks. macOS USB and packaging are not validated for this desktop build.

The tool keeps full logs. A failed computer-side preparation that never started native execution can start a fresh job; an unknown camera write is preserved for inspection. Offline checks and file readback do not prove successful camera boot or sound/color behavior. [Validation details](docs/en/desktop-validation.md) · [Changelog](docs/en/changelog.md).

## Source, CLI and implementation guides

For source-based use, install 64-bit Python 3.11, then run:

```sh
python -m pip install -r desktop-requirements.txt
python desktop.py
```

The complete package includes distribution assets that are not committed to Git, including the six-look pack and bundled helpers. Source users preparing a package must follow the [desktop build guide](dev/desktop/README.md) and supply the required assets.

| Need | Guide |
| --- | --- |
| Desktop operations | [Windows desktop guide](docs/en/desktop.md) |
| Independent FL23 CLI | [FL23](docs/en/fl23.md) |
| DCP/LUT conversion, import and per-slot restoration | [Custom LUT/DCP](docs/en/custom-lut.md) |
| Original-backup restoration | [Recovery](docs/en/recovery.md) |
| RAW/Lightroom profile matching | [RAW workflow](docs/en/raw-import.md) |
| Reproduce or extend the implementation with an AI | [AI entry](docs/en/ai.md) and [A7Look implementation](docs/en/a7look-ai.md) |
| Build and development contracts | [Desktop development](dev/desktop/README.md) |

Code is licensed under [MIT](LICENSE). DCPs, reference looks and bundled dependencies retain their original licenses and attribution; see [notices](docs/en/notices.md) and [profile sources](docs/en/profiles.md). Fujifilm DCP references are credited to **门萨特里顿** and Ricoh references to **爸总林先森** on Xiaohongshu. Full camera firmware, body calibration/backups and private test photographs are not source-distribution assets.

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
