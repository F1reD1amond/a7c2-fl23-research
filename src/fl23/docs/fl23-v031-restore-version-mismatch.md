# 0.3.1：回復原版為何會說「CP 設定狀態未知」

## 現象

用 0.2.0 的套件裝好 FL2／FL3 之後，改用 0.3.0 的 `Start.ps1` 按「回復原版」，在寫入任何東西之前中止：

```text
File ".../0.3.0/a7c2_fl23_preview/app.py", line 204, in restore
  self.save('restoring_settings');self.settings(session,True)
File ".../0.3.0/a7c2_fl23_preview/app.py", line 133, in settings
  if current_cp[key] not in accepted or before[1][key].data!=current_cp[key]:
     raise ValueError('CP 設定狀態未知，拒絕寫入')
ValueError: CP 設定狀態未知，拒絕寫入
```

## 根因：回復流程用「當前套件」重算白名單

`settings()` 的白名單來自 `self.units()`，而後者是把工作目錄裡的**原始**色彩單元，用**當前套件**的 `assets/colors.json` 重新合併一次：

```python
originals, merged = self.units()                  # merged 取決於當前套件
accepted = [originals[key], merged[key]] if restore else [originals[key]]
if current_cp[key] not in accepted or ...: raise ValueError(...)
```

同一個工作目錄、同一份原始備份，換一個套件就得到不同的 `merged`：

| 對象 | unit-02a40001 | unit-02a4000d |
|---|---|---|
| 原始備份 | `f6897866e2014a97…` | `fbb16bb0ac1e43d0…` |
| 0.2.0 合併＝當時寫入機身 | `995eb4e13af0616d…` | `c1974c18101488bb…` |
| 0.3.0 合併 | `995eb4e13af0616d…` | `b40e143aef0c5197…` |

（前 16 位 SHA-256。）差異只在 `unit-02a4000d`：0.2.0 只把 R5 矩陣寫進每個端點的槽 0，0.3.0 鋪滿 48 槽。

於是機身讀回的 `c1974c18…` 既不是 `originals`，也不是 0.3.0 的 `merged`，白名單把它判成「未知狀態」。**判斷本身沒有錯，錯的是白名單只認得一個版本。**

## 沒有寫入任何東西

`settings()` 的第 133 行在第 137 行的寫入迴圈之前，例外在檢查階段就拋出。工作目錄的 `journal` 可以佐證：兩次嘗試都只有

```text
host_full_file_readback_verified
native_about_to_run  wbi mode 0
native_verified      wbi mode 0
```

沒有任何 `about_to_write_cp`、`about_to_save_cp`、`about_to_write_ap` 或非零 mode 的 installer。`wbi` mode 0 是唯讀處理，不寫入。所以失敗後機身仍停在「0.2.0 已安裝、尚未冷啟動」的狀態，程式雜湊仍是 `FINAL`。

## 0.3.1 的判準：看窗口，不看版本

`merge_colors` 只會改動固定幾個位址，其餘位元組必須原封不動。`core.colour_write_spans()` 把這些範圍明確列出（半開區間）：

| 單元 | 範圍 | 內容 |
|---|---|---|
| `unit-02a40001`（8192 B） | `0x1237–0x1239` | 參數 55／56 的槽位映射 |
| | `0x1810–0x1850` | 槽 23 的色度記錄（64 B） |
| | `0x1890–0x18d0` | 槽 25 的色度記錄（64 B） |
| `unit-02a4000d`（28672 B） | `0x01cd–0x01cf` | 參數 55／56 的槽位映射 |
| | `0x46e0–0x4920` | 槽 23 的矩陣記錄（576 B） |
| | `0x4ce0–0x4f20` | 槽 25 的矩陣記錄（576 B） |

新的前置條件是 `core.matches_outside_colour(current, original, index)`：**窗口以外一位元組都不能與原版不同**。窗口內是 0.1.0、0.2.0 還是 0.3.x 寫的都無所謂——反正接下來的動作就是把整段記錄覆寫回原版。

這樣比原本的白名單更嚴格，也更貼近回復的目的：

- 原白名單只要「等於某一版輸出的完整檔案」；
- 新判準要求「除了本工具會寫的地方，其他都不許被動過」。若有人手動改過 CP 的其他位址，舊邏輯要看運氣（取決於是否剛好等於某版），新邏輯一定拒絕。

拒絕時會附上第一個越界差異的偏移，例如：

```text
CP 設定狀態未知，拒絕寫入（0x2a4000d 於色彩窗口外不符：1024）
```

### 安裝流程沒有放寬

`settings(session, restore=False)` 仍要求 `current_cp[key] == originals[key]`，逐位元組相同。只有「回復原版」接受窗口內的版本差異。

## 順帶修好中斷後的重跑

原本 `restore()` 第一步是 `self.files(session, core.FINAL)`：只要程式已經是原版就再也跑不動，例如「程式已回復、設定寫到一半斷線」就會卡死。

0.3.1 改成 `program_state(session)` 先判斷兩個完整程式是 `final` 還是 `original`：

- `final`：照舊走 設定 → installer mode 2 → 讀回；
- `original`：只處理設定與開機快照，跳過 installer；
- 兩個不一致，或既非原版也非已安裝版：立刻中止，要求保存 readback。

本體案例（程式仍 `FINAL`、設定未動）不受這段影響，但它讓「回復」成為可重複執行的操作。

## 驗證

- 新增 `tests/test_colour.py` 三項：寫入足跡必須完全落在窗口內；模擬 0.2.0 那種只填槽 0 的產物必須被接受；窗口外改一個位元組必須被拒絕並回報偏移。
- 新增 `tests/test_restore.py` 四項，用樁 `Session` 跑完整的 `settings(restore=True)`：
  - 其他版本寫入的記錄 → 回復成功，CP 與 AP 都回到原版；
  - 當前版本寫入的記錄 → 回復成功；
  - 窗口外改一位元組 → 以 `0x2a4000d 於色彩窗口外不符：1024` 中止；
  - 單元長度不符 → 拒絕。
- 離線測試 29 項通過；`fl23_color.py verify` 與 `app.py check-package` 通過。
- 色彩資產、`patches.json`、四個原生 `.so` 與 `VALIDATION.json` 記錄的程式雜湊皆與 0.3.0 相同；本版只動 `app.py`、`core.py`、`fl23_color.py` 的版本字串、測試與文件。

## 邊界

- 以上是離線邏輯驗證。**沒有在實機上重跑 0.3.1 的回復流程**；本文件描述的機身狀態來自工作目錄 `journal` 與 `state.json`，不是從相機重新讀回。
- 窗口外的判準假設 CP 單元的其他位址不該被任何流程改動。若日後新增會寫 CP 其他區域的功能，`colour_write_spans()` 必須同步擴大，否則回復會被誤拒。
- 「任一版都能回復」僅限只改色彩參數的版本。程式補丁不同的版本（`FINAL` 雜湊不同）仍會被 `program_state()` 拒絕。
