# A7C II 工具

[English](README.md) · **简体中文**

适用于 **Sony A7C II（ILCE-7CM2）固件 2.01** 的机内工具：FL2／FL3 创意外观、自订 1–6 自定义外观、恢复原厂功能、竖屏显示和电子快门声音，集中在一个 Windows 桌面程序里；每一部分也有独立的命令行工具。

> [!IMPORTANT]
> **当前桌面开发版 `3.0.0-desktop-preview.10.8`**：Windows 10／11 x64。已接入 macOS 14+ Apple Silicon／Intel 的 APP／DMG 原生构建，本轮尚未产出并实机验证 DMG。当前为预览版，并非所有功能都已通过实机验收，见[验证状态](#验证状态)。
>
> 已发布的旧版 FL23 可直接升级。一键安装不要求先执行原厂恢复或补点历史核对。

**交流群：**[Telegram（推荐）](https://t.me/sonyfwlab) · [Discord](https://discord.gg/SwPdfSd9c)
**作者：**小红书 [QAQLeonard（读研版）](https://www.xiaohongshu.com/user/profile/660501f7000000000600d03c) · 抖音 **LeonardZ**（抖音号 `90860261487`）

## 目录

- [功能](#功能)
- [快速开始（Windows 安装包）](#快速开始windows-安装包)
- [常用操作](#常用操作)
- [验证状态](#验证状态)
- [安全守则](#安全守则)
- [命令行工具](#命令行工具)
- [源码运行与打包](#源码运行与打包)
- [仓库结构](#仓库结构)
- [文档索引](#文档索引)
- [发布与下载](#发布与下载)
- [来源与许可](#来源与许可)
- [滤镜效果对比](#滤镜效果对比)

## 功能

| 功能 | 说明 |
| --- | --- |
| **USB 驱动** | 准备普通（`054C:0E8A`）与服务（`054C:0336`）两种 USB 连接，沿用已有的兼容驱动，诊断连接错误，也可卸载相机驱动。只有确实需要安装绑定时才申请管理员权限。 |
| **FL2／FL3** | 启用、重新启用或移除这两个菜单项。已包含 [PR #6](https://github.com/QAQLeonard/a7c2-fl23-research/pull/6) 的照片／视频曲线分流修正。 |
| **自定义外观** | 把 `.a7look` 写入指定自订槽位并设置机内名称，或把槽位恢复为 ST。多个写入与恢复可合并为一次操作；未添加的槽位保持原样。 |
| **外观转换与 Lightroom** | 把支持的 DCP／CUBE 转成 `.a7look`，并安装 Lightroom Classic 插件，导入 RAW 时自动套用对应的原 DCP。DCP 转换需要 Lightroom 及其渲染器配置。 |
| **恢复原厂功能** | 移除本项目已支持的修改，恢复原厂 2.01 行为，**无需旧备份**，也无需下载固件。保留机身校准、计数器和无关设置；自订槽位恢复为 ST。按原始备份完整回退是另一个可选入口。 |
| **竖屏显示** | 保存原生开关：竖握相机时拍摄信息和布局随之转向。整个 MENU 不旋转。 |
| **电子快门声音** | 开启／关闭原生电子快门声，从音频／视频文件截取片段转换，并保存为自定义声音。试听为可选步骤。 |

## 快速开始（Windows 安装包）

从 [Releases](https://github.com/QAQLeonard/a7c2-fl23-research/releases) 下载完整的 **`A7C2Tools-Windows-x64.zip`**，整包解压后运行 `A7C2Tools.exe`，`_internal` 文件夹要和它放在一起，无需另装 Python。打开软件本身不会连接或写入相机。

> [!NOTE]
> **连接提示：**连接或切换驱动时，相机显示 **“请检查所连接的设备”属于正常现象**，电脑也可能不显示相机盘符。请看本工具的进度和日志，不要仅因相机这条提示就拔线或重装驱动；工具本身报告的实际错误仍需处理。
>
> **断电重开**（每次写入后都会用到）：拔掉 USB 和其他外部供电 → 等存取灯停止闪烁 → 关机，等屏幕和灯完全熄灭 → 取下电池**至少一分钟** → 装回并开机。

1. 电池充足，用数据线连接一台相机，选择**海量存储（Mass Storage）**。
2. 打开**首页 · 一键安装**并选择功能。默认把六款外观写入自订 1–6，启用 FL2／FL3、原生电子快门声和竖屏显示；Lightroom 插件可选。
3. 点击**一键安装 / 继续安装**。工具按需准备驱动，合并写入所有选项并完整读回，开头不检查历史恢复是否点过核对。
4. 按弹窗**完整断电重开**，接回 USB，再点击一次**继续安装**。最后统一核对全部已写入功能，通过后显示安装完成，不需要逐项核对。

**恢复是可选功能：**需要移除项目修改、把六个自订槽位恢复 ST 时，再使用“恢复原厂功能”；恢复本身仍要重启核对通过后才显示完成，旧配方不找回。

### 默认六款外观

| 自订槽位 | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| 外观 | Classic Neg.（NC） | Classic Chrome（CC） | Nostalgic Neg.（NN） | Astia | GR 正片 | GR 负片 |

只替换**自订**创意外观槽位，索尼原有的创意外观保持不变。内置外观是对原 DCP 的拟合近似，并非完整复现。想改用自己的文件时，在首页取消勾选内置六款并填写自定义文件区；留空的槽位保持原样。

## 常用操作

- **修改一个或多个自订槽位。**在**自定义创意外观**页，清单默认为空。每个槽位添加一项；新增项默认**恢复 ST 默认**，导入时切换为**写入 A7Look** 并选择文件。恢复槽位不会找回旧配方。
- **保存自定义快门声。**在**电子快门声音**页，先开启原生电子快门声，选择音频／视频文件，设置起点和时长，然后点 **转换所选片段 → 保存当前自定义声音**。试听和确认记录都是可选的。写入并读回后断电重开即可加载。（可选的试听会提示你**保持开机**拔掉 USB，先听再保存。）听不到声音时，先检查机内“音频信号”设置。
- **恢复原厂行为。**按第一步使用**恢复原厂功能**。中途中断时再点同一个按钮，工具会读取当前状态，只处理剩余部分。
- **Lightroom。**插件安装后，在 Lightroom 增效工具管理器中启用一次。它在 RAW 显影时选择 DCP，不会改动 RAW 传感器数据。

各页面的完整说明见 [Windows 桌面工具指南](docs/zh-CN/desktop.md)。

[LUT 格式与色彩空间：ST / sRGB，不是直接使用 S-Log3](docs/zh-CN/lut-formats.md)。

## 验证状态

| 范围 | 状态 |
| --- | --- |
| FL2／FL3、六款外观安装、恢复原厂功能 | 已在作者的 Windows + A7C II 上取得机内证据 |
| 部分外观的预览／拍照检查、临时自定义声音播放 | 已在同一台相机上测试 |
| 持久化自定义快门声 | 156 项相关离线测试、打包自检和离线保存准备通过；**实机写入、冷启动和播放验收待完成** |
| 持久化竖屏显示，以及更广的拍摄／Fn／视频行为 | 单独验证，待完成 |
| macOS USB 与打包 | 本版本未验证 |

离线测试和字节读回不能证明相机能正常启动，也不能证明颜色和声音效果正确。详见[桌面验证记录](docs/zh-CN/desktop-validation.md) · [更新日志](docs/zh-CN/changelog.md)。

## 安全守则

- **结果未知的写入绝不重复执行。**工具会停止并保留现场，先检查再做下一步。能证明在写入相机之前就失败的任务，可以新建任务重试。
- 保留完整日志。导出的诊断包含设备信息和本机路径，公开前请检查。
- 完整固件、机身备份／校准、私人照片和凭据不属于本仓库或安装包，请自行妥善保管。
- 使用充足电量的电池；每次写入前工具都会请你确认供电。

## 命令行工具

所有命令在仓库根目录运行，各工具相互独立；桌面程序调用的是同一套后端。

| 入口 | 用途 | 说明 |
| --- | --- | --- |
| `python desktop.py` | 从源码运行桌面程序 | [桌面工具](docs/zh-CN/desktop.md) |
| `FL23.cmd` | Windows FL2／FL3 准备／安装／核对（`FL23.cmd --help`）；双击打开原有界面 | [FL23](docs/zh-CN/fl23.md) |
| `python lut.py` | DCP／LUT 检查与转换、指定槽位导入、单槽恢复、任务诊断 | [自定义 LUT／DCP](docs/zh-CN/custom-lut.md) |
| `python recovery.py` | 按 FL23 原始 backup2 或完整检查点完整回退 | [Recovery](docs/zh-CN/recovery.md) |
| `python a7look_compile.py` | 离线把 DCP／CUBE 编译为 `.a7look` | [A7Look 编译器](docs/zh-CN/a7look-compiler.md) |
| `python a7look_write.py` | 写入已编译的 `.a7look`（与 `lut.py` 共用事务 CLI） | [A7Look 写入](docs/zh-CN/a7look-writer.md) |
| `python raw_auto.py`／`raw_import.py` | 安装 Lightroom 自动配置插件；记录槽位→DCP 绑定供 RAW 导入 | [RAW 流程](docs/zh-CN/raw-import.md) |
| `python shutter.py` | 电子快门声音 CLI（实验） | [快门声音](docs/zh-CN/technical/shutter-sound.md) |
| `python vertical.py` | 旧版仅当次开机有效的竖屏显示 CLI | [竖屏显示](docs/zh-CN/vertical-display.md) |

每个 CLI 都可用 `--help` 查看命令；`lut.py doctor --device` 和 `shutter.py doctor` 只检查依赖，不连接相机。

## 源码运行与打包

桌面程序使用 64 位 **Python 3.11**；独立 CLI 需要 64 位 Python 3.10+（见[安装准备](docs/zh-CN/manual.md)）。

```sh
python -m pip install -r desktop-requirements.txt
python desktop.py
```

运行离线测试（不访问相机）：

```sh
python -m pytest dev/desktop -q
```

安装包还包含未提交到 Git 的发行资源（六款外观包和打包的辅助程序，位于被忽略的 `desktop-assets/`）。自行打包请按[桌面构建说明](dev/desktop/README.md)并自备这些资源。CI（`.github/workflows/desktop-preview.yml`）在原生 runner 上构建，不会发布 Release。

## 仓库结构

```text
desktop.py              桌面程序入口（界面、worker、自检模式）
FL23.cmd, lut.py, recovery.py, shutter.py, vertical.py, a7look_*.py, raw_*.py
                        独立 CLI 入口（见上表）
src/
  desktopapp/           PySide6 界面、任务 worker、驱动、预设、一键安装流程
  camera_runtime/       桌面版使用的 FL23 规划器与原生运行时
  fl23/                 独立的 FL2／FL3 安装、备份与核对
  looks/                looktool：A7Look 编译／写入、直接设备任务、
                        原厂参考、检查点、RAW 配置工具
  vertical/             竖屏显示原生 worker
  launcher.py           CMD 入口共用的 Windows 环境准备
plugins/A7LookAuto.lrplugin/
                        Lightroom Classic 自动配置插件
dev/                    桌面构建与测试、发布脚本、快门声音、USB 与竖屏研究工具
docs/en/, docs/zh-CN/   对应的英文／简体中文文档
docs/profiles/          DCP 来源清单与原始许可文本
calibration/            固件 2.01 的虚拟校准模型
```

## 文档索引

| 主题 | 简体中文 | English |
| --- | --- | --- |
| 桌面程序 | [桌面工具](docs/zh-CN/desktop.md) · [验证](docs/zh-CN/desktop-validation.md) | [Desktop guide](docs/en/desktop.md) · [Validation](docs/en/desktop-validation.md) |
| FL2／FL3 CLI | [FL23](docs/zh-CN/fl23.md) | [FL23](docs/en/fl23.md) |
| 自定义外观 | [自定义 LUT／DCP](docs/zh-CN/custom-lut.md) · [A7Look 总览](docs/zh-CN/a7look-suite.md) | [Custom LUT/DCP](docs/en/custom-lut.md) · [A7Look overview](docs/en/a7look-suite.md) |
| 按备份回退 | [Recovery](docs/zh-CN/recovery.md) | [Recovery](docs/en/recovery.md) |
| RAW／Lightroom | [RAW 流程](docs/zh-CN/raw-import.md) | [RAW workflow](docs/en/raw-import.md) |
| Python 环境 | [安装准备](docs/zh-CN/manual.md) | [Windows/macOS setup](docs/en/manual.md) |
| 实现细节 | [集成](docs/zh-CN/technical/integration.md) · [格式](docs/zh-CN/technical/formats.md) · [历史错误](docs/zh-CN/technical/failures.md) · [验证](docs/zh-CN/technical/validation.md) | [Integration](docs/en/technical/integration.md) · [Formats](docs/en/technical/formats.md) · [Failures](docs/en/technical/failures.md) · [Validation](docs/en/technical/validation.md) |
| 开发 | [开发维护](docs/zh-CN/development.md) · [桌面构建](dev/desktop/README.md) · [AI 复现](docs/zh-CN/ai.md) | [Repository & maintenance](docs/en/development.md) · [AI reproduction](docs/en/ai.md) |
| 历史 | [更新日志](docs/zh-CN/changelog.md) | [Changelog](docs/en/changelog.md) |

参与开发或让 AI 修改代码前，请先阅读 [AGENTS.md](AGENTS.md) 和 [docs/zh-CN/ai.md](docs/zh-CN/ai.md)。

## 发布与下载

桌面程序（`A7C2Tools-Windows-x64.zip`）在 [Releases](https://github.com/QAQLeonard/a7c2-fl23-research/releases) 页面下载。此前的独立工具仍可使用：

- [v2.2-preview.1](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.2-preview.1)：FL23 CLI、单文件 `lut.py` 和 `recovery.py`、完整工具包
- [v2.1](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v2.1)：此前的非预览版
- [v1.0](https://github.com/QAQLeonard/a7c2-fl23-research/releases/tag/v1.0)：最初的 FL23 安装器
- [原始 DCP 文件](https://github.com/QAQLeonard/a7c2-fl23-research/releases/download/v2.1/a7c2-dcp-profiles-2026-10-18.zip)：独立下载（[来源](docs/zh-CN/profiles.md)）

## 来源与许可

代码采用 [MIT](LICENSE) 许可。DCP、参考外观和打包依赖保留各自原始许可与署名，见[许可说明](docs/zh-CN/notices.md)和 [DCP 来源](docs/zh-CN/profiles.md)。富士 DCP 参考来自小红书 **门萨特里顿**，理光 DCP 参考来自小红书 **爸总林先森**。

本项目为独立研究，与 Sony、Fujifilm、Ricoh、Adobe 无关。外观名称不代表官方认可或颜色完全一致，也不是索尼签名的更新。

## 滤镜效果对比

<details>
<summary>展开逐场景对比图</summary>

相机直出 JPG，仅缩放、拼接和添加标签；没有曝光、白平衡或色彩调整。拍摄参数存在变化，供效果参考，不是受控测量。

每组依次展示三张独立对比图：**ST／FL／FL2／FL3**、**ST／NC／CC／NN**、**ST／E／GR 正片／GR 负片**；每张四宫格按左上、右上、左下、右下读取。NC＝Classic Neg.，CC＝Classic Chrome，NN＝Nostalgic Neg.，E＝Eterna；这批不包含 Astia。

[下载全部 19 张高清对比图（约 152 MB）](https://github.com/QAQLeonard/a7c2-fl23-research/releases/download/v2.1/a7c2-film-comparisons-2026-10-18.zip)，含第一组 ST 补充对比及总览。

**01 · 饮料柜**

![01 · 饮料柜 — ST / FL / FL2 / FL3](docs/images/film-comparison/01_饮料柜/01-1_ST_FL_FL2_FL3.jpg)

![01 · 饮料柜 — ST / NC / CC / NN](docs/images/film-comparison/01_饮料柜/01-2_ST_NC_CC_NN.jpg)

![01 · 饮料柜 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/01_饮料柜/01-3_ST_E_GR正片_GR负片.jpg)

**02 · 绿植**

![02 · 绿植 — ST / FL / FL2 / FL3](docs/images/film-comparison/02_绿植/02-1_ST_FL_FL2_FL3.jpg)

![02 · 绿植 — ST / NC / CC / NN](docs/images/film-comparison/02_绿植/02-2_ST_NC_CC_NN.jpg)

![02 · 绿植 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/02_绿植/02-3_ST_E_GR正片_GR负片.jpg)

**03 · 柜台**

![03 · 柜台 — ST / FL / FL2 / FL3](docs/images/film-comparison/03_柜台/03-1_ST_FL_FL2_FL3.jpg)

![03 · 柜台 — ST / NC / CC / NN](docs/images/film-comparison/03_柜台/03-2_ST_NC_CC_NN.jpg)

![03 · 柜台 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/03_柜台/03-3_ST_E_GR正片_GR负片.jpg)

**04 · 旋转楼梯**

![04 · 旋转楼梯 — ST / FL / FL2 / FL3](docs/images/film-comparison/04_旋转楼梯/04-1_ST_FL_FL2_FL3.jpg)

![04 · 旋转楼梯 — ST / NC / CC / NN](docs/images/film-comparison/04_旋转楼梯/04-2_ST_NC_CC_NN.jpg)

![04 · 旋转楼梯 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/04_旋转楼梯/04-3_ST_E_GR正片_GR负片.jpg)

**05 · 书架**

![05 · 书架 — ST / FL / FL2 / FL3](docs/images/film-comparison/05_书架/05-1_ST_FL_FL2_FL3.jpg)

![05 · 书架 — ST / NC / CC / NN](docs/images/film-comparison/05_书架/05-2_ST_NC_CC_NN.jpg)

![05 · 书架 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/05_书架/05-3_ST_E_GR正片_GR负片.jpg)

**06 · 海报**

![06 · 海报 — ST / FL / FL2 / FL3](docs/images/film-comparison/06_海报/06-1_ST_FL_FL2_FL3.jpg)

![06 · 海报 — ST / NC / CC / NN](docs/images/film-comparison/06_海报/06-2_ST_NC_CC_NN.jpg)

![06 · 海报 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/06_海报/06-3_ST_E_GR正片_GR负片.jpg)

</details>
