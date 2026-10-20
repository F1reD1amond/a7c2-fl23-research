# DCP／LUT 编译成 A7Look（实验版）

[English](../en/a7look-compiler.md) · [三个工具与当前进度](a7look-suite.md)

这个工具接收 **Sony A7C II 的 DCP 文件或已明确输入空间的 3D CUBE**，输出包含曲线、矩阵、色度参数和完整原生修正表的 `.a7look`。无需 AI，也不需要为每份 DCP 重拍色卡。相机写入是独立步骤；编译器不会连接相机。

## 支持哪些文件

| 输入 | 当前支持 |
|---|---|
| 独立 3D `.cube` | 每轴 2–129 点，包括常见的 17³、33³、65³；读取后使用三线性插值 |
| 1D `.cube`、1D shaper＋3D 混合文件 | 不支持，需预先烘焙为独立 3D CUBE |
| `.3dl`、`.csp`、`.look`、`.vlt`、`.mga`、`.clf`／`.ctf`、HALD 图片 LUT | 不直接支持，需先由其他软件导出为兼容 CUBE |
| `.dcp` | 支持目标型号为 `Sony ILCE-7CM2` 的配置文件；其他机型 DCP 不能直接套用 |
| Lightroom `.xmp` 预设、ICC／ICM | 不作为此编译器的输入 |

CUBE 支持 `TITLE`、`#` 注释、`DOMAIN_MIN`／`DOMAIN_MAX`、UTF-8 BOM 和 Windows 换行；当前不接受 `LUT_3D_INPUT_RANGE` 等额外头字段。

**文件能读取，不表示颜色空间自动匹配。** 直接输入须明确为 Sony ST／sRGB；S-Log、F-Log、LogC、ACES 等需要正确的 ST→LUT 输入转换，LUT 输出也必须已转换到 sRGB。标准 Rec.709／Gamma 2.4 不能直接当成 sRGB。程序不会根据文件名或 `TITLE` 自动识别这些空间。

高分辨率源 LUT 仍会拟合到相机支持的曲线／矩阵／色度及修正表，不会把 65³ 或 129³ 整张色表原样存进相机。

## 使用

DCP 输入需要 Python 3.10 或更新版本、Lightroom Classic，以及已安装并启用的 [Lightroom MCP 插件和桥接程序](https://github.com/Automaat/lightroom-mcp)。桥接程序在这里作为普通命令行显影接口使用，不需要 AI。

1. 在工具目录安装 Python 依赖：

   ```text
   python -m pip install -r requirements.txt
   ```

2. 将配套的实测响应文件放在 `calibration/a7c2-2.01.virtual.npz`。它保存已测得的数值响应，不含原照片、整份固件或相机备份。这个实验校准目前基于一台 2.01 机身、ISO800、5000K 的色卡测量。

3. 若尚未安装桥接程序，先安装 Node.js 18 或更新版本，在工具目录执行以下两行，再重新开启 Lightroom 并启用插件：

   ```text
   npm install --prefix renderer @mskalski/lightroom-mcp
   node renderer/node_modules/@mskalski/lightroom-mcp/dist/index.js install-plugin
   ```

   在工具目录新建 `a7look-compiler.local.json`。Windows 和 macOS 都使用相同格式；已有桥接程序也可以填写它的绝对路径：

   ```json
   {
     "renderer_command": ["node", "renderer/node_modules/@mskalski/lightroom-mcp/dist/index.js"]
   }
   ```

4. 打开 Lightroom Classic，在工具目录执行：

   ```text
   python a7look_compile.py "MyProfile.dcp" --name "My Look" --output "My Look.a7look"
   ```

需要投入更多计算时：

```text
python a7look_compile.py "MyProfile.dcp" --name "My Look" --output "My Look.a7look" --passes 12 --evaluations 200 --extra-colors 768
```

`--passes` 是候选拟合轮数，`--evaluations` 是每次求解的计算预算，`--extra-colors` 是在已测颜色范围内增加的虚拟颜色数量。修正表精度不因这些参数改变。默认是 3 轮、每次 100 次求值、256 个额外虚拟颜色。

从第 4 轮起，程序也尝试较少受大误差色块主导的误差目标，并继续按验证结果选择候选。增加计算不保证每一轮都进步；已知更好的候选会保留。

## 程序做什么

**DCP → 生成数值已知的虚拟 RAW → Lightroom 实际应用 DCP → 相机响应模型预测 → 曲线／矩阵／色度／修正表联合拟合 → `.a7look`。**

虚拟 RAW 嵌入所提供的完整 DCP，避免只读取其中的 LookTable、漏掉 HueSatMap 或其他显影阶段。拟合先优化单表解，再增加原生控制，比较多个起点／平滑强度；额外轮次继续寻找更好的候选。选择依据是独立颜色分组的验证误差，而非只看训练误差。

DCP 数值参考固定关闭 Adobe 镜头配置文件（`LensProfileEnable=0`），并保留校准所用白平衡／曝光条件。暗角和畸变随画面位置、焦段与光圈变化，应由镜头处理负责；不能混进一份全局创意外观。与真实照片比较时，应同时记录机内和 Adobe 的镜头校正设置。

程序在同名 `.work` 目录保存显影参考、每轮结果、预测对照和 `result.json`。最终文件使用全部有效虚拟颜色重新拟合，报告会另外列出验证副本的留出颜色误差。现有输出不会被覆盖。

Lightroom 会将生成的数值色卡导入当前目录库；编译器不修改你的原照片。直接使用源码时，依赖清单位于 `src/looks/requirements-compiler.txt`。

## 如何理解结果

更多计算可以改善求解，但不会自动消除相机响应模型的偏差，也不能增加相机尚未接入的参数自由度。当前拟合使用 3 个曲线控制、6 个矩阵控制、8 个色度控制及完整 1215 字节修正表。

报告里的误差是**虚拟数据上的预测误差**，不是相机新照片实测，也不包含响应模型本身的全部误差。其他白平衡、曝光、未测颜色仍需独立验证。`.a7look` 与 DCP 使用不同处理流程，双方转换都需要拟合。

四阶段文件现在可交给[通用 A7Look 写入器](a7look-writer.md)。编译完成不代表已经安装或通过相机验证。

源码入口：[a7look_compile.py](../../a7look_compile.py)；实现：[compilelook.py](../../src/looks/looktool/compilelook.py)、[nativefit.py](../../src/looks/looktool/nativefit.py)、[measuredmodel.py](../../src/looks/looktool/measuredmodel.py)。

## CUBE 输入（不需要 Lightroom）

明确以 Sony ST／sRGB 为输入、sRGB 为输出的 LUT：

```text
python a7look_compile.py "MyLook.cube" --input-space sony-st-srgb --name "My Look" --output "My Look.a7look"
```

其他输入空间需要提供明确的 ST→目标空间桥接 LUT：`--input-space 空间名称 --bridge "ST-to-input.cube"`。视频 Log LUT 不能当作 ST LUT 直接使用。程序保留源 CUBE／桥接数据，并披露超出 sRGB 输出范围的裁切量；拟合预算和校准范围与 DCP 入口相同。

CUBE 不会自动变成 Adobe RAW 配置文件。如果另有同一外观的 A7C II DCP，可加 `--raw-dcp "Matching.dcp"` 供 Lightroom 匹配；两者色彩是否一致仍需验证。未提供 DCP 时，不会假装完成 RAW 自动配色。
