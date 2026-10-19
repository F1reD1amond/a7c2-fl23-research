# FL23：给 AI 的安装与复现说明

[返回首页](../../README.zh-CN.md) · [English](../en/fl23-ai.md) · [用户安装步骤](fl23.md)

目标是在 Windows 为 A7C II 2.01 安装 FL2／FL3，完成双份备份、写入、独立读回、冷加载、拍照／回放和还原。**命令行为主，桌面版为同一后端的替代入口。** 本任务不导入自定义 LUT，也不改 LUT 的设置或资源。

## 1. 从哪里开始

先读 [AGENTS](../../AGENTS.md)、[用户说明](fl23.md)和 [compat.py](../../src/fl23/compat.py)。仅限 ILCE-7CM2；版本由用户根据相机版本页面填写 2.01，不是协议自动读出。

按仓库所有者要求，FL23 不再验证原厂/仓库完整固件哈希。不因改写窗口之外的修改拒绝安装；不检查来源。实际要改写的指令若冲突则报告位置并停止，不覆盖未知指令。已有 LUT 转换入口和 CP 不改，已有 FL23 只备份/验证。

桌面安装前显示来源风险弹窗，CLI 显示同样警告。保留本次实际文件的双备份、生成候选/逆向、写入后完整读回；本次交易的完整性校验不是原厂来源白名单。新流程尚未实机验证，USB 行为不改。

Windows 使用 64 位 Python 3.10+；启动器自动准备依赖，不需要独立编译工具操作。普通/服务 USB 身份为 054C:0E8A / 054C:0336。

## 2. 已有实现及必须保留的边界

| 源码 | 作用 |
|---|---|
| [app.py](../../src/fl23/app.py) | `Job.prepare/install/verify/restore`：阶段、备份、候选、交易与验收 |
| [gui.py](../../src/fl23/gui.py) | Windows 桌面按钮转发到同一 `app.py` 命令 |
| [core.py](../../src/fl23/core.py) | `ORIGINAL/FINAL`、固定补丁、机身数据合并、保护和原生报告判定 |
| [transport.py](../../src/fl23/transport.py) | `Session`：身份绑定、认证、有界 I/O、未知结果停止、受限临时文件／Backup 写入 |
| [assets/manifest.json](../../src/fl23/assets/manifest.json) | 已编译原生组件及其精确指纹 |
| [native/installer.c](../../src/fl23/native/installer.c) | 固定窗口、大小／inode 保留、mode0 检查／mode1 安装／mode2 还原 |
| [native/wbi.c](../../src/fl23/native/wbi.c) | 已知起点的保留启动镜像检查／失效处理 |
| [tests/test_offline.py](../../src/fl23/tests/test_offline.py) | 机身隔离、占用拒绝、额外设置变化、临时冲突与未知会话测试 |

沿用已审阅偏移；新的 prepare 根据本次实际文件生成专属 worker，不将固定原厂 worker 套入改动文件。来源不拦截，指令冲突单独报告。备份只能属于当前机身。

## 3. 离线检查与 Windows 启动

在工具根目录运行：

```text
.\FL23.cmd --check
.\FL23.cmd --setup-only
.\FL23.cmd check-package
```

三者不连接相机。准备环境可能联网安装依赖；已有不完整环境会被保留，不盲目覆盖。直接双击 `FL23.cmd` 则打开桌面版。不要同时运行 GUI 和命令行设备操作。

## 4. 命令行完整步骤

1. 新建本次工作和第二备份目录，最好在不同磁盘，两个均为空；保存原来的工作目录。
2. 执行以下 `prepare`，成功状态必须是 `prepared`，日志确认备份／候选／实机只校验完成。

```text
.\FL23.cmd prepare --firmware-version 2.01 --workspace "D:/CameraWork-A7C2-01" --backup-copy "E:/CameraBackup-A7C2-01"
```

3. 检查本机身份、双份备份、候选和 native mode0 结果，实际电量至少 50% 且能持续连接。安装命令中的 82 必须换成真实百分比，不能照抄。

```text
.\FL23.cmd install --workspace "D:/CameraWork-A7C2-01" --battery-percent 82
```

4. `installed_pending_cold_start` 与完整读回成功之后，确认所有 I/O 结束，再按用户说明拔除所有外部供电、正常关机、等存取灯熄灭、取电池至少一分钟后开机。核对 FL2／FL3 名称、无快门预览、新照片／回放及原 ST。接回大量存储模式：

```text
.\FL23.cmd verify --workspace "D:/CameraWork-A7C2-01"
```

5. 核对完整程序、保存参数及 AP 运行片段，单独记录用户观察。成功文件读回不等于真实拍摄或所有模式稳定。

## 5. 每段应该发生什么

`prepare` 读取程序和机身数据，按填写版本检查实际改写位置，合并本机外观参数、检查未占用区域、生成候选，核对两份备份后执行只校验。已启用 FL23 的识别任务跳过安装器／WBI 只校验，不生成新安装。临时诊断会运行，程序／保存配方尚不安装。

`install` 要求仍是同一机身及 `prepared` 阶段，重新核对程序／目标设置，再执行固定程序窗口、完整读回、目标参数合并保存、无关设置保留检查，以及受条件保护的保留镜像步骤。`verify` 不重复安装，检查重载后的完整文件、目标参数和相应 AP 运行片段。

所有原生模块都应在调用前记录意图，暂存读回后一次调用，按各自 magic／版本／模式／长度／错误／hash 校验结果。失败或超时后会话未知时停止继续发包，不连清理也反复发送。保留 `state.json`、日志、已有原生结果和临时文件，先查本次执行结果。

## 6. 还原与故障处理

只有明确要撤销受支持的本次 FL23 安装，保有本机完整双份备份且当前完整程序可识别时，才按用户说明选择 ST、正常完整重载、接回，再用原工作目录执行：

```text
.\FL23.cmd restore --workspace "D:/CameraWork-A7C2-01" --battery-percent 82
```

这会恢复本次程序和目标参数，不能作为任意循环重启、部分损坏或未知状态的通用恢复。结果未知时先检查已有结果和当前文件，不重发安装／还原。还原完成后同样需要完整读回、重载及实际新照片验证。

## 7. AI 的测试和交付

运行 `python -m unittest discover -s src/fl23/tests -v` 及 `python -m unittest discover -s dev/usb/tests -v`；后者覆盖真实 Windows CMD／PowerShell 5.1／7 转发、中文／空格路径、退出码和 USB 状态边界，设备 I/O 为离线模拟。相机 native 完整启动、安全断电和第二台机身兼容性不能由这些测试代替。

交付命令、退出码、源／目标及双备份哈希、`prepared`／写入／核对阶段、完整读回、保留设置和清理结果、加载检查、用户新照片／回放及还原证据。没有授权或相机可用时停在离线验证并明确剩余实机阶段，不虚构安装成功。
