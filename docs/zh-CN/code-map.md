# 代码目录与共用边界

桌面 Windows 和 macOS 使用同一套界面、安装计划、恢复、槽位操作、音频处理和相机写入逻辑。系统差异集中在驱动、权限和 USB 存储介质接管。

| 位置 | 职责 | Windows／macOS |
| --- | --- | --- |
| `desktop.py` | 桌面程序与后台任务入口 | 共用 |
| `src/desktopapp/window.py`、`lookeditor.py` | 界面与逐槽操作编辑器 | 共用 |
| `src/desktopapp/worker.py`、`allinone.py` | 后台分派与一键安装流程 | 共用 |
| `src/desktopapp/actions/` | 动作分类、外观转换与声音适配接口 | 共用；供后续前端调用 |
| `src/desktopapp/platforms/usb_drivers.py` | USB 枚举、两阶段连接准备；Windows 驱动安装／卸载与 UAC | 共用检测／连接入口，驱动变更只在 Windows 执行 |
| `src/desktopapp/platforms/macos_authorization.py` | Terminal／sudo 管理员进程 | 仅 macOS |
| `src/desktopapp/platforms/macos_media.py` | 连接页手动推出相机存储卷 | 仅 macOS |
| `src/camera_runtime/macos_host.py` | 服务连接前识别相机磁盘、卸载及接口接管 | 仅 macOS，由共用传输层调用 |
| `src/camera_runtime/` | 相机服务通信与 FL23 兼容参数 | 共用 |
| `src/looks/looktool/direct.py`、`bundle.py` | FL23、外观、声音开关、竖屏开关的合并计划与写入 | 共用 |
| `src/looks/looktool/factoryrecover.py`、`checkpointjob.py` | 内置原厂参考恢复与读回 | 共用 |
| `src/looks/looktool/compilelook.py`、`nativefit.py` | 独立 DCP／CUBE 数值拟合 | 共用，不依赖 Lightroom |
| `src/shutter_sound/` | 声音转换、音量、试听和保存运行代码 | 共用，已从 `dev/` 移出 |
| `src/shutter_sound/native/` | 声音的 AArch64 相机 worker | 共用，相机代码不按电脑系统复制 |
| `src/vertical/` | 保存竖屏开关与原有图片资源链接 | 共用；不包含线条资源整包复制 |
| `plugins/A7LookAuto.lrplugin/` | 用户可选的 Lightroom 自动匹配插件 | 共用；仅插件需要 Lightroom |

`src/desktopapp/drivers.py` 与 `macadmin.py` 保留原有导入名称，直接指向 `platforms/` 内的同一个模块对象；它们不再保存第二份实现。

## 文件夹放置规则

```text
src/                    发行程序实际运行的代码
  desktopapp/           界面、任务、一键安装与系统适配
  camera_runtime/       共用服务通信
  looks/                外观拟合、写入、恢复与 RAW 配置
  shutter_sound/        共用声音运行模块和 native/ worker
  vertical/             竖屏开关
  fl23/                 独立旧版 FL23 CLI；native/ 中的基础 worker 仍由各功能共用
dev/                    构建工具、离线测试和开发实验
  desktop/              Windows／macOS 打包、发行资源准备、界面／流程测试
  shutter_sound/        声音测试、独立模拟器与跟踪实验
  vertical/             竖屏测试和构建辅助
  release/              原有 CLI 发布工具
desktop-assets/         被 Git 忽略的发行数据和依赖，不放运行逻辑
  presets/default-six-v1/  首页默认六款
  profile-library-v1/   DCP 与 A7Look 配对库及收录清单
  windows/              Windows 驱动辅助程序
  exiftool/             平台对应的 ExifTool
build/                  被忽略的拟合缓存、参考渲染和验证证据
dist/                   最终 EXE、ZIP、DMG
```

原始照片、完整固件、机身备份与私有研究数据留在发行目录以外。Lightroom 参考生成和服务器优化是维护者的资源制作过程，放在 `build/`；用户端转换器不调用这些过程。

## 桌面与独立 CLI

`FL23.cmd`、`lut.py`、`recovery.py`、`shutter.py` 等根目录入口继续保留。旧 CLI 的备份工作流与桌面的内置参考恢复是不同入口；Windows 和 macOS 桌面版都调用 `looktool.direct`，没有各写一份恢复算法。

新增共享功能放进对应的 `src/` 功能目录。系统命令与权限处理放进 `platforms/`。测试和研究工具放进 `dev/`，构建证据放进 `build/`，预拟合文件放进 `desktop-assets/`。

前端改写时的请求、结果、状态与日志约定见 [后端接口](frontend-contract.md)。
