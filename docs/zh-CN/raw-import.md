# Lightroom 自动应用拍摄时的 DCP（开发版）

[English](../en/raw-import.md) · [A7Look 工具组成与进度](a7look-suite.md)

安装一次 **A7Look Auto Profiles** 插件，之后使用 Lightroom Classic 自带的导入界面。插件读取 ARW 的自订槽位和拍摄时间，按写入器保留的历史匹配源 DCP。无需每次登记或手工选配置文件。

## 一次安装

需要 Python 3.10+、[ExifTool](https://exiftool.org/) 和 Lightroom Classic。在源码目录运行：

```text
python raw_auto.py install --exiftool "/完整路径/exiftool"
```

Windows 填写 `exiftool.exe` 的路径；macOS 可填写 `which exiftool` 显示的路径。再到 Lightroom「文件 → 增效工具管理器 → 添加」，选择安装器输出的 `A7LookAuto.lrplugin` 并启用。这个插件不依赖 MCP，也不连接相机。编译 DCP 所需的显影桥接程序是另一项依赖。

## 正常使用

1. 编译器在 `.a7look` 中保留源 DCP 和版本信息。
2. 写入器在相机写入、重新加载及验证成功后，自动登记槽位的生效时间，保留旧 DCP。
3. 使用 Lightroom 原来的导入界面导入新照片。插件只调整对应配置文件，保留曝光、裁切等编辑；原生 ST／FL／FL2／FL3 不变。

同一槽位从 NC 换成 CC，较早拍摄的 RAW 仍匹配 NC，较晚的匹配 CC。请保留电脑上的 `.a7look/auto-profile` 数据，并使相机时钟与电脑一致。ARW 目前只有槽位标记，没有 DCP 版本；丢失历史或调乱相机时间后，不能只凭 RAW 保证还原版本。

**当前集成范围：**自动登记已接入开发分支中的写入完成路径；旧工具包没有这些更新，也不会自动补出过去的槽位历史。不要用尚未验证的相机写入来建立记录。

## 新 DCP 的加载

Lightroom 运行中新增的 DCP 可能要重新打开 Lightroom 才能显影。源码新版插件通过小尺寸实际导出核对结果，不把接口返回的配置文件名称当成成功证据；未加载的导入项保留原配置、进入等待队列，重启后再尝试。可在「增效工具增效功能 → A7Look Auto Profiles — Status」查看状态。

普通导入及 NC／CC 按拍摄时间匹配已实际验证。新版的实际显影核验、配置未加载时保留原配置，以及重启后无需重新导入的队列恢复也已在 Lightroom 验证；macOS 插件尚未实测。

## Photoshop Camera Raw

独立的自动匹配插件尚未实现。后续先尝试共享 DCP 与 XMP，让 Lightroom 保存的配置选择被 Camera Raw 读取；目前不承诺打开 ARW 就自动匹配。Windows 看图软件通常使用内嵌预览，不会执行这套 Adobe 配置匹配。

源码：[安装器](../../raw_auto.py)、[插件](../../plugins/A7LookAuto.lrplugin)、[源 DCP 版本与写入回执](../../src/looks/looktool/rawidentity.py)。`raw_import.py` 保留为命令行诊断／备用入口，不是日常导入必需步骤。
