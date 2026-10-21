# 前端重写的后端接口

本文件描述现有接口，不要求改变界面风格或 README。Windows 与 macOS 使用同一套动作名、参数和结果；系统授权由后端处理。

## 分层

- `window.py`、`lookeditor.py`：界面展示与用户输入。
- `jobs.py`：创建任务、生成 worker 命令、导出诊断。
- `actions/catalog.py`：相机动作与供电确认分类的唯一来源；`jobs.py` 兼容导出原名称。
- `actions/look_compiler.py`、`actions/sound.py`：独立转换与声音的适配入口。
- `worker.py`：共用动作分派、进程结果与完整异常日志。
- `allinone.py`：一键安装协调；`looktool.direct` 等模块负责计划与写入。
- `platforms/`：Windows 驱动、macOS Terminal 授权和介质处理。

新前端使用 `jobs.new_job(action, arguments)` 创建任务，再运行 `jobs.worker_command(job / 'request.private.json')`。不在 UI 线程直接调用相机、驱动、原生 worker 或转换器。

## 请求与结果

每次任务目录包含 `request.private.json`，结构保持如下：

```json
{
  "schema": "a7c2-desktop-job/1",
  "action": "sound_volume",
  "arguments": {"workspace": "用户声音工作目录", "decibels": 3},
  "job_dir": "本次任务目录",
  "version": "桌面版本"
}
```

`status.private.json` 的 `phase` 是 worker 状态：`QUEUED`、`WAITING_AUTHORIZATION`、`RUNNING`、`SUCCEEDED` 或 `FAILED`。成功时读取 `result`；失败时显示 `error` 并保留 `worker.log` 的完整 traceback。

`SUCCEEDED` 表示本次后台动作正常返回，不等于整个安装已经完成。项目进度在 `result.phase` 中：

| 返回状态 | 界面行为 |
| --- | --- |
| `AWAITING_RELOAD`／一键 `WAIT_RELOAD` | 显示断电步骤和“继续安装”，不提前显示全部完成 |
| `AWAITING_RESOURCE_RELOAD`／一键 `WAIT_RESOURCE_RELOAD` | 显示资源阶段的断电与续接说明 |
| `LOADED`、`COMPLETE` | 显示对应完成结果，区分用户是否接受实机检查 |
| `NEEDS_REVIEW` | 保留原错误、任务目录和已知完成阶段 |
| `converted_offline`、`volume_adjusted_offline` | 电脑端音频处理完成，可直接保存或继续调节 |

具体文案和动作完成判定参照 `reloadguide.py`、`completion.py`；不能只根据进度条或子进程退出码推断整个安装完成。

## 主要动作

| 动作 | 主要参数／用途 |
| --- | --- |
| `setup_all` | `workspace`、`firmware`、`power_confirmed`、`options`；一键安装与继续安装 |
| `usb_prepare` | 两阶段驱动与连接准备；Windows 保留可用绑定，Mac 使用其系统适配 |
| `driver_install`／`driver_uninstall` | Windows 指定 Sony 身份的驱动操作 |
| `direct_factory_reset` | 内置参考恢复；不依赖旧 LUT 任务或完整机身备份 |
| `direct_fl23_enable`／`direct_fl23_disable` | FL2／FL3 列表功能 |
| `direct_looks_import` | `operations`：每项 `slot`、`action=write/restore`；写入项另有 `path`、可选 `name` |
| `compile_look` | `source`、`output`、`name`、`model`（响应模型路径）；独立离线生成 A7Look |
| `vertical_enable`／`vertical_disable` | 保存竖屏开关；普通入口由共用直接写入流程执行 |
| `sound_on`／`sound_off` | 共用直接计划修改声音开关 |
| `sound_import` | `source`、`workspace`、`start`、`duration`、`peak`；电脑端音频转换 |
| `sound_volume` | `workspace`、`decibels` 或 `reset=true`；电脑端音量处理 |
| `sound_install` | `workspace`、供电确认；保存当前选定声音 |
| `plugin_install` | 可选 LrC 插件；不让其他功能依赖 Lightroom |

写入动作的固件版本与供电确认等公共参数继续沿用 `Window.common()` 和 `jobs.POWER_ACTIONS` 的现有约定。前端不新增固件哈希、旧任务核对或“先恢复才能保存声音”等门槛。转换和音量调节不请求相机或管理员权限。

## 日志与资源

持续读取本次 `worker.log` 与 `process.log`，保存原始错误；用 `jobs.export_support()` 导出诊断。`paths.data_root()` 是用户状态根目录，不能因重写前端而改变。

`profilelibrary.location()` 给出发行包中的配对库位置；Windows 是 EXE 旁的 `Profiles/`，Mac 是应用资源内的库。当前收录 15 组彩色配对，黑白三款未达标而排除。默认六款和配对库版本一致。文件选取与界面展示不重新拟合、不调用 Lightroom。

系统差异和文件夹职责参见 [代码目录](code-map.md)。
