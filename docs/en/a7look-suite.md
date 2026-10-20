# A7Look: three tools, one look file

[简体中文](../zh-CN/a7look-suite.md)

The intended workflow is **DCP/LUT → compile `.a7look` → write the camera → take photos → import normally into Lightroom with the matching source DCP**. Everyday use must not require AI.

| Component | Responsibility | Development status |
|---|---|---|
| Compiler | Fit tone, matrix, chroma, and the complete native correction table with an adjustable compute budget | [DCP/CUBE compilation](a7look-compiler.md) is connected; both input paths have run |
| Writer | Select custom slots 1–6; back up, write, read back, reload, verify, and restore one slot | [General writer](a7look-writer.md) supports four stages; packaged slot-4 Astia installation and camera preview/photo/playback passed; six-look color accuracy and physical slot restoration remain pending |
| Lightroom plugin | Match the source DCP at capture time through normal import; retain history when slot contents change | [Normal import, actual rendering checks, and restart recovery tested](raw-import.md) |

`.a7look` carries camera look parameters, source DCP/LUT information, and fitting evidence. DCP versions live in computer-side files and history, not as complete DCPs in camera ROM or independent RAW version markers. Generating an Adobe profile from LUT input remains pending.

Compilation and installation are separate. A precompiled look should install without refitting. Only accepted, verified camera transactions publish or restore slot history. Custom looks must also work without FL2/FL3 installation.

Photoshop Camera Raw is optional; shared DCPs and XMP are the first proposed route. Its missing automatic plugin must not block the three core components. This page describes the development target and current evidence, not a claim that the whole final suite is finished.

[AI reproduction guide](a7look-ai.md)
