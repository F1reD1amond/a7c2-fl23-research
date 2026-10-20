# Apply the captured DCP on normal Lightroom import (development)

[简体中文](../zh-CN/raw-import.md) · [A7Look tools and status](a7look-suite.md)

Install **A7Look Auto Profiles** once, then use Lightroom Classic's normal import dialog. The plugin reads the ARW custom-slot marker and capture time and matches the source DCP using the writer's retained history. No per-import binding command is required.

## One-time setup

Requires Python 3.10+, [ExifTool](https://exiftool.org/), and Lightroom Classic. From the source directory:

```text
python raw_auto.py install --exiftool "/absolute/path/to/exiftool"
```

Use the `exiftool.exe` path on Windows or the path reported by `which exiftool` on macOS. In Lightroom's Plug-in Manager, add the `A7LookAuto.lrplugin` directory reported by the installer and enable it. This plugin needs neither MCP nor camera USB access. The DCP compiler's rendering bridge is a separate dependency.

## Everyday use

1. The compiler retains the source DCP and version information inside `.a7look`.
2. After the camera write, reload, and acceptance succeed, the writer automatically records the slot's activation time and keeps older DCP versions.
3. Import new photos through Lightroom's usual dialog. The plugin changes the matching profile while retaining exposure, crop, and other edits. Native ST/FL/FL2/FL3 are left alone.

If a slot changes from NC to CC, older captures still match NC and later captures match CC. Keep the computer's `.a7look/auto-profile` data and synchronize the camera and computer clocks. ARWs currently identify the slot, not the DCP version; RAW alone cannot reconstruct missing history or resolve an incorrect camera clock.

**Current integration:** automatic registration is connected to development-branch writer completion paths. Older distributed tools lack these hooks and cannot reconstruct past activation history. An unverified camera transaction must not publish an activation.

## Loading a new DCP

A DCP added while Lightroom is running may require reopening Lightroom before it can render. The revised source plugin checks an actual small export rather than trusting the profile-name getter. Unavailable profiles retain the imported profile and enter a queue for another attempt after restart. Check the A7Look Auto Profiles status item under Lightroom's Plug-in Extras menu.

Normal UI import and historical NC/CC matching have been verified in Lightroom. The revised plugin also passed actual-rendition verification, preservation of the imported profile when a new DCP is unavailable, and automatic queue recovery after restart without re-import. The macOS plugin has not been physically tested.

## Photoshop Camera Raw

A separate automatic matching plugin is not implemented. Shared DCP installation and Lightroom-written XMP are the first proposed integration; opening an ARW does not yet guarantee automatic Camera Raw matching. Windows photo viewers commonly use the embedded preview and do not run this Adobe-profile workflow.

Source: [installer](../../raw_auto.py), [plugin](../../plugins/A7LookAuto.lrplugin), [source versions and activation receipts](../../src/looks/looktool/rawidentity.py). `raw_import.py` remains a diagnostic/fallback CLI, not a required everyday import step.
