# 将 A7Look 写入相机（开发版）

[English](../en/a7look-writer.md) · [工具总览](a7look-suite.md)

输入已编译的 `.a7look`，不再重新拟合。工具支持自订 1–6 的修正表，以及当前原生整数基底表示的曲线、矩阵和色度参数；不会悄悄丢掉不支持的参数。自定义外观可独立于 FL2／FL3 使用。

## 安装与写入

Windows／macOS 使用同一份 Python 命令行。需要 64 位 Python 3.10+：

```text
python -m pip install -r src/looks/requirements-device.txt
```

相机连接方式沿用[USB 说明](custom-lut.md)。准备好大量存储模式和充足电量后：

```text
python a7look_write.py import "Astia.a7look" --slot 4 --work-dir "jobs/astia" --backup-dir "/独立备份位置/astia" --write --battery-percent 100
```

电量填实际值。将命令里的备份占位路径换成实际路径：Windows 例如 `E:/A7Look-Backups/astia`，macOS 例如 `/Volumes/Backup/astia`。工作与备份位置使用两个新的空目录。命令依次执行：**读取当前状态 → 压缩增量备份两份 → 用本机 ST 数据重建原生参数 → 只校验 → 名称／程序／所选配方写入 → 完整读回 → 准备重新加载**。其他槽位、原生外观和机身校准保留。工具将所选自订栏位设为 ST 基底；相机仍能手动改基底，使用此外观时请保持 ST。

想先只准备，去掉 `--write --battery-percent 100`；之后运行：

```text
python a7look_write.py install "jobs/astia" --battery-percent 100
```

## 重新加载与验收

等工具显示所有读写结束，再拔 USB 和其他供电，正常关机、等存取灯熄灭，取下电池至少一分钟后重新开机。先不按快门切换 ST 与目标槽位，检查实时变色；再试拍、回放，确认 FL2／FL3（若已安装）及其他槽位正常。接回大量存储模式后：

```text
python a7look_write.py verify "jobs/astia" --accept-photos
```

`--accept-photos` 记录你实际完成的检查。完整文件读回和新内核启动不能代替照片／取景验收，也不是直接读取 CP 运行内存。

## 还原一个槽位

```text
python a7look_write.py restore-slot "jobs/astia" --work-dir "jobs/undo-astia" --backup-dir "/独立备份位置/undo-astia" --battery-percent 100
```

这是基于当前相机状态的新事务，同时还原该槽的色表、原生参数、名称和配方；后来更新的其他槽位保留。该槽若又被改过，会停止并要求使用它最新的 Job。还原采用实际字节比较，不要求旧固件哈希一致。还原后同样重新加载并 `verify --accept-photos`。

如果原来源 DCP 的历史及对应槽位字节已留存，还原成功后也会恢复其 Lightroom 匹配关系；来源未知时暂停匹配，不猜测。整机回到初始存档点使用独立的 [Recovery](recovery.md)。

## 当前验证范围

开发版已完成离线实程序适配、真实安装器编译、逐字节正反向验证及带原生参数的模拟事务测试。打包的通用写入器已在一台 Windows A7C II 上安装第 4 槽最终 Astia 文件，完整读回、新启动与 AP 加载检查，以及用户的预览／拍摄／回放和 FL2／FL3 检查均通过。六款最终拟合文件均已通过同一打包工具写入并完整读回，等待统一断电重载和六款实机验收。六款最终色彩准确度和单槽实机还原尚未验证。macOS USB 本轮未实测。

源码：[入口](../../a7look_write.py)、[事务流程](../../src/looks/looktool/devicejob.py)、[原生参数读写](../../src/looks/looktool/photoio.py)。
