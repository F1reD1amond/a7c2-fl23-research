# AI 复现 A7Look 全流程

[English](../en/a7look-ai.md) · [用户总览](a7look-suite.md)

先读根目录 `AGENTS.md` 与 `src/looks/AGENTS.md`。在开发分支工作；离线任务不代表允许连接相机或发布。

1. **生成：**`a7look_compile.py`／`looktool.compilelook` 接收 A7C II DCP 或已明确输入空间的 CUBE。DCP 使用数值 Bayer DNG 与 Adobe 实际显影；CUBE 直接使用声明的 ST 域／桥接。`measuredmodel` 预测实测响应，`nativefit` 联合拟合并量化原生参数及全部 1,215 字节修正表。留出预测误差与实拍误差分开报告；更多计算不能证明未测条件的精度。
2. **写入：**`a7look_write.py` 通过现有 CLI 调用 `devicejob.Job`，冻结文件、不重新拟合。`photoio` 重建并逐字节核对既有原生代码，保留其他槽位参数，核对项目分配区域／加载范围。原厂首次导入先构建已有六表运行时，再读取其迁移后的 ST gamma 行。矩阵／色度来自目标机身新鲜 CP 单元，不能套用其他机身校准。
3. **还原：**保留两份可重建的压缩存储和精确逆向。单槽还原比较原 Job 对该槽的色表、原生参数、名称与配方，允许其他槽位和 FL23 后续更新；同时还原旧原生参数及已知源 DCP 关系，不添加旧固件哈希门槛。整机初始回退由 `recovery.py` 完成。
4. **Adobe：**`.a7look` 保存不可变源 DCP，只有验收成功的写入才发布带时间的历史。`raw_auto.py` 安装独立 Lightroom 监听插件；正常导入时按拍摄时间匹配标记 249–254。保留原生外观与已有编辑。必须核对实际导出，不能相信返回的配置名称；配置未加载时保留原配置并排队，重启后再尝试。RAW 没有来源版本 ID，仍依赖历史及相机时钟。CUBE 不会自动变成 Adobe 配置文件。
5. **验证：**运行 `test_photoio`、`test_lookfile`、`test_compile_cube`、`test_rawidentity`、`test_rawauto_lua`、`test_native_device_job`。最后一项需要 `A7C2_RESEARCH_FIXTURES` 和 `A7C2_NATIVE_CHECKPOINT`，使用模拟传输。将 `src/looks` 加到 `PYTHONPATH`，让子进程锁测试能导入模块。可选夹具跳过不算通过。获准上机前先编译真实安装器、验证完整字节逆向。

新插件的实际显影和跨重启队列已通过 Lightroom 验收；新通用写入器上机与六款最终色彩精度仍是独立的待测项目。不能用模拟／读回推断安全启动，也不能为旧预览状态重复安装。未知写入结果必须停止并保留证据。完整固件、机身备份、照片和私人清单不进入公开包。Camera Raw 可后续处理，目前没有独立自动插件。
