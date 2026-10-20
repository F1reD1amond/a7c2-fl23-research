# 电子快门声音：实机测试候选

[首页](../../../README.zh-CN.md) · [English](../../en/technical/shutter-sound.md)

分支：`feature/electronic-shutter-sound`，基于 `80959db`。**一台 C2 2.01 的机主已确认电子快门实际发声，关闭“音频信号(拍摄)”后无声。** Windows 实机备份、原生写入、完整程序读回及设置核对通过；连拍时序、静音模式和整体稳定性仍待验证。main 和 Release 未改。

## 统一命令行工具

[shutter.py](../../../shutter.py) 是统一入口，[sound_cli.py](../../../dev/shutter_sound/sound_cli.py) 实现完整流程。Windows／macOS 使用 64 位 Python 3.10+；Mac 相机 USB 尚未实测。在解压后的源码根目录运行：

```text
python -m pip install -r shutter-requirements.txt
python shutter.py doctor
python shutter.py --help
```

**独立开关：**`on` 启用电子快门发声分支，`off` 把这个分支恢复成原厂静音。两者不改「音频信号」、对焦提示音设置、自定义声音文件或 FL23／LUT 改动。每次需要 USB 连接，执行后正常关机、拔掉所有外部供电，并取下电池至少一分钟。这是电脑端开关，**没有新增相机菜单，也不能即时切换**。要听到声音，相机仍须保持「音频信号（拍摄）开、静音模式关、电子快门」；全局静音仍优先。对焦提示音保留依据是局部 CP 改动及设置读回核对；整合后的开／关循环仍待实机验证。

```text
python shutter.py on --workspace sound-work --backup-copy sound-backup --firmware 2.01 --battery-percent 100
python shutter.py off --workspace sound-work
```

`100` 要换成实际当前电量，至少 50%。首次使用新的工作／备份目录，之后保留。`on` 后完整断电重载，确认原厂声音、拍摄正常，再导入。`off` 后重载，检查电子快门无声、**对焦提示音仍开启**。重新开启时对同一工作目录执行 `on`，工具会建立新 Job。下面的 `restore-sound` 独立还原音效，不会停用电子快门发声功能。

**导入：**选择不超过两秒的片段。`--peak 0.4` 仅将所选片段归一化至 40% 峰值，允许上限为 0.5。单声道 PCM16 WAV 不需要 FFmpeg；MP3／MP4／立体声文件使用 PATH 中的 FFmpeg、`--ffmpeg` 指定的程序或安装依赖时获取的 `imageio-ffmpeg`。视频／压缩音频须指定起点和时长。原文件不变。

```text
python shutter.py import "sound.mp4" --workspace sound-work --start 0.26 --duration 0.15 --peak 0.4
python shutter.py audition --workspace sound-work
```

`import` 只离线转换，并生成私有试听 WAV。`audition` 读取机身、往返核对编码字节，再临时注册到内存。USB 读写结束后拔线，**保持开机**，电子快门单拍一张，确认音量、失真、音调／速度及拍摄／回放，再记录实际结果：

```text
python shutter.py confirm --workspace sound-work --result correct
```

若不合适，改用 `quiet`、`noise`、`wrong-speed`、`native` 或 `silent`。随后正常关机、等存取灯熄灭，断开所有外部供电并取下电池至少一分钟；开机确认原厂声、拍摄／回放恢复，再接回并记录恢复。临时标记可能在断电后保留，工具仅在下次试听前清理该次已恢复且完全对应的标记。

```text
python shutter.py confirm-recovery --workspace sound-work
python shutter.py install --workspace sound-work --battery-percent 100
```

`install` 保存两份压缩机身备份，先写入／读回两个私有音频文件，最后启用开机调用，再完整读回两份程序并核对设置。它使用**试听确认的原字节**，不会安装时重新转换。结束后再次完整断电重载，实际听到正确声音、拍摄／回放正常，再运行：

```text
python shutter.py verify --workspace sound-work --heard-correct
python shutter.py status --workspace sound-work
```

`verify` 检查已加载 AP 代码、描述与文件；`--heard-correct` 记录实际重启后听感。`status` 只读本地记录。恢复原声用 `python shutter.py restore-sound --workspace sound-work`，结束后完整断电重载并检查；只撤销声音调用／文件，保留其他改动。换另一款声音时，先恢复原声／重载，再重复导入 → 试听 → 确认 → 恢复临时状态 → 安装。结果不明会停止，保留目录、备份和报告，不要盲目重跑或删记录。

已有开发版 Job 可离线接入，避免重新写原厂声补丁：`python shutter.py attach --workspace sound-work --backup-copy sound-backup --native-job old-native-job --audio-job old-format0-audition`。这只是复用证据，不等于已核对相机当前状态；旧目录也要保留。

**验证范围：**格式 0 自定义声音已能实机辨认，机主回报 40% 版本接近原声。统一 CLI 和持久化控制器已有离线测试，但自定义音效的持久化安装／冷启动，以及独立关闭后保留对焦声，尚未实测。这是开发分支的实验源码工具，不是已全面验证的 Release，也不是索尼签名更新。

## 候选与证据

只改 CP 一条两字节 Thumb 指令：文件偏移 `0x3935ca`／运行地址 `0x49b5ca`，`0021` → `0321`，实际仅立即数的一字节不同。普通电子快门路径中，C2 根据传感器描述将声音模式清零；A1 II 的对应分支选择模式 3。候选保留原查询，同样选择模式 3，经现有路径请求 kind 3 拍摄声音。不改 AP、菜单、声音设置、音效资源或校准，不增加运行内存钩子。

实机第一步是**只读声音登记核对**：必须在原生 AP 声音条目 0–5 中找到有缓冲区和长度的 kind 1／2／3（KA／SHA／KASHA），原厂 Audio Signals Off 策略会注销这组声音。实测机身的条目 0／1／2 对应 kind 1／2／3、优先级 6，缓冲区长度为 128／1216／1216 字节。对应不上就停在固件写入之前。静音模式和拍摄时序仍需实测。

| 离线检查 | 结果与边界 |
|---|---|
| [AP／CP 输入片段](../../../dev/shutter_sound/verify_selector_inputs.py) | 8 组将电子请求传到普通 selector 1，另 6 组检查优先级；执行实际型号特性查询、请求写入和快照复制指令，未模拟异步传播。 |
| [选择器对照](../../../dev/shutter_sound/trace_selector.py) | 300 组合成输入，共 600 次原版／候选执行；其他 selector、跳过／延后条件及计数限制保持，异步消费者尚未完整模拟。 |
| 原始 AP 声音策略 | 4 组观察登记参数；实机确认“开有声、关无声”，每次安装仍核对最新登记。 |
| [编译后事务](../../../dev/shutter_sound/verify_worker.py) | 18 项系统调用模拟，覆盖预检查、写入、逆向、部分读写、冲突、读回损坏、回滚成功／失败和挂载失败，不是相机／断电模型。 |
| [编译后读者](../../../dev/shutter_sound/verify_probe.py) | 6 项合成进程测试，另已完成一次实机声音登记预检查。 |
| 单元／流程测试 | 25 项通过；流程的相机传输是模拟的。 |

C2 有 71 行音效登记、11 项具备数据的 PIN 资源，含 KA／SHA／10fps；A1 II 为 73 行、9 项。明确的资源区间与 `SysSound.bin` 对应字节一致，文件存在不等于播放。功能参考 [A1 II 原生拍摄声音](https://helpguide.sony.net/ilc/2440/v1/en/contents/231h_audio_signal_volume.html)，C2 的[静音模式](https://helpguide.sony.net/ilc/2360/v1/en/contents/0414D_silent_mode_setting.html)必须继续关闭拍摄声音。

## 离线复现

在本分支仓库根目录，用 Python 3.10+ 和私人提取的 C2 2.01 组件：

```text
python -m pip install -r dev/shutter_sound/requirements.txt
python dev/shutter_sound/verify_selector_inputs.py --ap appFw.so --cp cpapp-b.bin --output inputs.private.json
python dev/shutter_sound/trace_selector.py cpapp-b.bin --output selector.private.json
python dev/shutter_sound/candidate.py --ap appFw.so --cp cpapp-b.bin --output private-candidate
python dev/shutter_sound/verify_worker.py --plan private-candidate/plan.private.json --output transaction.private.json
python dev/shutter_sound/verify_probe.py --worker private-candidate/probe.so --ap appFw.so --output reader.private.json
python -m unittest discover -s dev/shutter_sound/tests -v
```

[candidate.py](../../../dev/shutter_sound/candidate.py)从不打开 USB。相关指令冲突时停止，不以整份固件哈希白名单判断来源。输出含私人 CP 候选和原生事务、只读声音登记、启动快照插件，不是索尼签名的 SD 卡更新包。

## 受控实机测试

这些[开发测试命令](../../../dev/shutter_sound/trial.py)独立于 FL23／LUT 工具。沿用现有 [USB 设置](../fl23.md)，使用满电电池和稳定连接。先选 P／A／S／M、电子快门、静音模式关、拍摄声音开，记下原设置。

菜单路径：**拍摄 → 快门/静音 → 静音模式设置 → 静音模式 → 关**；**拍摄 → 快门/静音 → 快门类型 → 电子快门**；**设置 → 声音选项 → 音频信号(拍摄) → 开**。先关闭静音模式，否则拍摄声音会锁为关。区分全按拍摄时的声音与半按合焦的哔音。本版没有增加音色选择菜单。

```text
python dev/shutter_sound/trial.py preflight --firmware 2.01 --job private-shutter-job --backup-copy separate-backup-folder
python dev/shutter_sound/trial.py status --job private-shutter-job
python dev/shutter_sound/trial.py apply --job private-shutter-job
```

1. **预检查：**沿用先认证服务的 USB 会话绑定机身，读取当前程序及已保存／运行中设置，重建验证两份压缩备份，核对相关指令，再运行临时声音读者、启动快照只读检查和原生 mode 0 检查。不改固件、拍摄设置或启动快照。只有状态为 `ready` 才继续。
2. **写入：**重新读取程序／设置，再检查登记及原生 mode 0，只写这条两字节指令；将两份完整程序与最新预期结果逐字节比较，检查可写 AP 设置和受保护 CP 单元，保留其他 FL23／LUT 改动，没有固件 SHA 来源门槛。
3. **重新加载：**完整读回后，启动快照 mode 2 沿用“丢弃快照，再设 mode 0”，已为 mode 0 则跳过。全部 USB 操作结束，正常关机、等存取灯熄灭、拔 USB／其他供电，取下电池至少一分钟。磁盘读回或新内核启动都不是直接 CP RAM 证据。
4. **验证：**先拍一张电子快门照片，确认声音对应实际保存照片；半按／取消不应多出快门音。再测 Lo／Hi／Hi+ 连拍、声音关、静音模式开、机械快门／电子前帘、对焦提示、录像音轨、FL2／FL3／自定义外观及回放。记录延迟、漏声／多声和故障。单张成功不等于稳定版。

只还原这条指令，保留之后其他位置的改动：

```text
python dev/shutter_sound/trial.py restore --job private-shutter-job
```

还原同样使用最新字节、原生预检查、完整读回、设置核对和启动快照处理。结果不明时进入 `needs_review`，CLI 不会盲目重写、还原或重启，保留原 Job 和原生报告供核对。这种局部逆向与[完整 Recovery](../recovery.md)分开。

## 自定义声音导入

[custom_sound.py](../../../dev/shutter_sound/custom_sound.py)仍是**离线原型**。同长度原生 BIN 替换可更新声音包／资源别名并生成压缩字节逆向，真实 1,216 字节资源已精确往返还原。此声音包替换原型不验证任意 BIN 音频；导入使用下面单独实测的 filter0 内存路径。

单声道 PCM16 WAV 可不重采样提取，并生成实验性的格式 1 登记模板。[144 组原指令验证](../../../dev/shutter_sound/verify_registration.py)匹配原构造器对传输值 0／1 的 40 字节 ABI，停在外部发送之前。**这些验证不能证明硬件编码、采样位宽、声道布局或采样率。** 第 21 字节是**优先级**（原生范围 1–10，快门为 6），不是 RT／FIFO 访问类型；离线原型先前的标注／默认值已修正。原生快门实机版本没有使用这个自写模板。24kHz 合成测试不是机内采样率证据。

[lpcm_route.py](../../../dev/shutter_sound/lpcm_route.py)还验证了不使用跳板、在原地改写 68 字节 AP 构造代码的实验：480 组、960 次原版／候选执行，只改变启用 kind 3 时的格式字节。此改写仍**仅离线、未安装**，不能把现有 ADPCM 字节直接当成 PCM。

[buffer_trial.py](../../../dev/shutter_sound/buffer_trial.py)另行测试原厂音效加载器的 `0x70817` 缓冲区，不改 ROM。本机 AP／CP 各成功申请 51,200 字节，空缓冲区测试后均释放成功。第二次测试把私有的 13,376 字节 PCM 音频从 AP 传至 CP，清空 AP，再从 CP 读回 AP，逐字节一致，最后释放两者。[原指令接口检查](../../../dev/shutter_sound/verify_buffer_abi.py)执行原厂申请与完成等待代码；[编译后程序检查](../../../dev/shutter_sound/verify_buffer_worker.py)使用模拟的失败情况，不连接相机。原厂函数存在无超时等待，结果不明时不重复调用。

第三次实机测试再次核对往返字节，注销 kind 3，再把较低音量的 PCM16 音频以传输格式值 1 注册到独立 CP 缓冲区，两次注册调用均返回成功。但机主实拍听到**杂音或错误声音**，拍摄正常。AP 缓冲区已释放；CP 缓冲区有意保留，避免播放时使用已释放内存。固件、原 AP 描述表及拍摄设置均未修改。完整断电后，机主确认**原厂声音恢复，拍摄和回放正常**。当前已停用 PCM16／格式 1 的实机 `--temporary-register` 路径，保留离线重现和不播放的缓冲区往返测试；下面的原厂分块候选不重复这条失败路径。这**不是永久自定义音效导入**，没有异步回调指向临时程序，会话标记阻止叠加保留的缓冲区。

机主进一步确认是**沙沙、爆裂杂音**，而非能辨识的原声变速。[trace_playback.py](../../../dev/shutter_sound/trace_playback.py)执行原 CP PIN 播放描述构造／查表代码，16 组离线情况均将格式 1 保留到下一层描述；CP 原始调试说明也标注 0=ADPCM／1=LPCM。但这**不能证明**实拍经过了该构造器，也不能证明其解码器接受单声道、小端 PCM16；字节序、采样位宽、声道、采样率及后续处理仍未确认。此描述中的额外 64 字节增加缓冲区容量，并没有把音频起始指针向后移动。

根文件系统和 `nflasha8` 有两份相同的 66,368 字节 `SysSound.bin`，实际加载／缓存未追通。**两份文件均未替换。** 私有音频和生成的程序保留在本机，不公开索尼音效包或用户媒体。

### 下一版候选与持久化研究

失败的 **PCM16／格式 1** 实机路径仍停用。[native_codec.py](../../../dev/shutter_sound/native_codec.py)提供独立的格式 0 编码器：原厂样本每 32 字节分块，包含一个控制字节和 31 个有符号残差字节。编码只用 filter0，避开尚未确认的 filter1 预测器。所选声音在**尚未验证的假定 24kHz** 下为 3,776 字节，软件回解信噪比约 46dB。机主已在内存试听中辨认出所选声音，但觉得 12% 峰值太小。机主确认完整断电恢复后，已加载 40% 峰值版，AP→CP→AP 逐字节一致，注册成功；机主回报接近原声，完整的音量／失真／拍摄／回放验收仍待确认。能辨认原声不能证明准确的硬件采样率或持久化开机安全。

```text
python dev/shutter_sound/native_codec.py encode --wav selected.wav --assumed-rate 24000 --output private-native
python dev/shutter_sound/buffer_trial.py allocate-release --job private-native-trial --native-sound-job original-native-job --native-bin private-native/custom-native.private.bin --temporary-register
```

全部 USB 操作结束后拔线，**保持开机**，音频信号维持开，单拍一次电子快门，回报音量、失真、音色／音调／速度和拍摄／回放。只有实际正确才运行 `buffer_trial.py confirm --job private-native-trial --result correct`；否则选择 `quiet`、`noise`、`wrong-speed`、`native` 或 `silent`。此命令仅离线记录，不会猜测听感。`native_codec.py encode --peak 0.4` 设置所选音频的峰值上限，默认为 0.12，不改相机全局音量。

下一次试听前完整断电，确认原厂声、拍摄及回放正常，再运行 `buffer_trial.py confirm-recovery --job private-native-trial` 记录实际恢复。临时标记文件可能在完整断电后仍保留。下一次 `allocate-release` 使用新 Job 并指定 `--after-recovered-job private-native-trial`，仅在已有机主恢复记录时清理同机身、字节及令牌完全对应的旧标记，不释放旧 CP 缓冲区，不删除未知标记。标记恢复的 5 项单元测试及编译后程序的 14 种情况通过；声音单元测试共 49 项通过。

[boot_sound.py](../../../dev/shutter_sound/boot_sound.py)生成**离线持久化候选**，[boot_trial.py](../../../dev/shutter_sound/boot_trial.py)实现开发用安装／还原／核对控制器，安装前要求同机身、同音频字节的格式 0 实测确认。候选复用原厂单行 CSV 读取器和开机文件加载器处理 kind3。[读取器／启动代码检查](../../../dev/shutter_sound/verify_beeplist.py)确认只改指定描述，CSV 缺失或过大时保留原厂声音包。CSV 工作缓冲区缩为 2KiB，栈帧为 2,704 字节，免去额外七页栈空间。[原厂文件加载流程](../../../dev/shutter_sound/verify_file_loader.py)保留 CP 缓冲区所有权，按实际文件长度注册。这些仍是模拟 libc／硬件接口的离线执行，不能证明机身开机安全。

持久化候选新增 `/usr/share/avsystemsound` 下的 `custom-shutter.bin`、`custom.txt`，并修改 82 字节受检查的 AP 窗口，保留 CP 程序、原声音包及其他描述。[文件事务程序](../../../dev/shutter_sound/files_worker.py)通过了 [15 种编译后故障测试](../../../dev/shutter_sound/verify_sound_files.py)：先创建并读回音频文件，最后才启用开机调用；还原时先关闭并读回调用，再删除文件，保留后续其他程序改动。结果不明时停止，不重复写入或删文件。加载后的代码和文件型 kind3 CP 句柄会独立核对，不以磁盘读回代替机主听感。**目前尚未安装或实测任何持久化自定义音效版。** 原加载器对音频文件缺失／损坏的处理仍是限制，此开发候选不是 Release 工具。

## 参考范围

已阅读 [service-preload](https://github.com/YuuLuo/a7c2-service-preload/tree/1619f938663a36d41e72302a8cfee89a0f6acd1a)，固定提交 `1619f938663a36d41e72302a8cfee89a0f6acd1a`，它说明 USB／Senser／Jiritsu 和一次性 root 子进程预加载，没有快门音实现。本候选沿用本仓库现有临时 `libJit.so` 事务加载器，不创建永久 preload。未复制参考实现或索尼音效，参考文档采用 CC BY-SA 4.0。固件、音频、机身备份及生成报告均保密。
