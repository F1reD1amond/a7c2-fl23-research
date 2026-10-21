# DCP／LUT → A7Look（獨立離線轉換）

[桌面工具](desktop.md) · [English](../en/a7look-compiler.md)

選擇 Sony ILCE-7CM2 的 `.dcp` 或符合輸入空間的 `.cube`，填寫名稱及新的 `.a7look` 輸出路徑，點「開始生成」。不需要 Lightroom、LR、Node、顯影插件、renderer 設定或網路；生成不連接相機。

DCP 直接解析 LookTable 及色調曲線，使用內建 ST 映射和相機響應模型擬合機內色表。來源相機的感光元件矩陣、HueSat 校準不移植；不宣稱完整重現 Adobe 顯影。內建映射是單場景近似，生成後仍需檢查預覽與照片。沒有可支援色彩階段、來源機型不符或損壞的 DCP 會顯示具體錯誤。

CUBE 的直接輸入須是 Sony ST / sRGB、輸出 sRGB；S-Log3 等需先烘焙正確變換。[格式說明](lut-formats.md)。

命令列：

```text
python a7look_compile.py "MyProfile.dcp" --name "My Look" --output "My Look.a7look"
```

輸出包含完整的本機色彩階段及 1215 位元組修正表；生成檔可在自訂外觀頁選槽寫入。舊檔不自動覆蓋，請選新名稱。原 DCP 的來源與權利記錄會保留。

「安裝 LrC 自動識別插件」是獨立可選入口，僅供使用 Lightroom 管理 RAW 的人；生成、安裝、恢復、聲音及竪屏功能均不依賴它。
