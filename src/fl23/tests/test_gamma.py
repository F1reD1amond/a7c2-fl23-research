"""FL2／FL3 Gamma 記錄的離線測試：四條記錄必須是 FX2 的照片曲線。

背景（詳見 docs/fl23-v050-gamma-and-perslot-matrix.md）：

* A7C II 2.01 原廠 cpapp-b.bin 的 +0xcfa588 已有 20 組「(照片 Gamma ID,
  影片 Gamma ID)」路由，最後兩組是 FL2=(0x30,0x30)、FL3=(0x31,0x31)，
  也就是索尼自己的 A7C II 把同一個 Gamma ID 同時給照片與影片。
* FX2 1.01 的 Gamma 表裡 ID 0x30／0x31 各有兩條：generation 3（內部槽
  0～5 共用）與 generation 6（內部槽 6）；影片曲線另在 ID 0x32／0x33。
* RAW 的 0x7806 等於 2 × CP 照片內部槽 6，所以槽 6 必須是照片曲線。

0.4.0 把 FX2 的影片槽 6 曲線（ID 0x32／0x33）寫進 A7C II 的 generation 6
記錄；本版改回照片槽 6 曲線。

0.5.2 再加一層：曲線其實一直沒被讀到。cpapp-b.bin +0x138832 是 0x323172 與
0x323298 呼叫的葉子函式，負責回傳「color → (照片列, 影片列)」路由表的基址，
回傳值 r1 = 0x012099F8 是正確的；但它還帶了一段只在 r4 == 0（照片）時生效的

    cmp r0,#0x13 ; blo skip
    cmp r0,#0x14 ; it ls ; movls r0,#0

把 FL2／FL3 的 color 索引 19／20 改寫成 0。r0 隨後用於 route_table[r0*8 +
r4*4]，於是所有 FL2／FL3 照片都落到第 0 項 (0,10) → 第 0 列 = ST 曲線。
A7M4 方法 3 記載 FL2／FL3 的 CP color 正是 19／20，可交叉驗證。
"""
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core

BASE = Path(__file__).resolve().parents[1]
GAMMA_WINDOW = 0x1100b80
BLOCK_BYTES = 3872
RECORD_BYTES = 576
HELPER_WINDOW = 0x138832
HELPER_BYTES = 26
NOP_SLIDE = b'\x00\xbf' * 7
BASE_LOAD = bytes.fromhex('49f6f811c0f22011')   # movw r1,#0x99f8 ; movt r1,#0x120
EPILOGUE = bytes.fromhex('704700bf')            # bx lr ; nop
ROUTE_TABLE = 0xe78
ROUTE_ENTRIES = 21

# 0.5.0 交付指紋
BLOCK_SHA256 = 'f40759fc338a04d07439eac12d1c6669b8819b57cbd2521bacd7fb040a88a467'
# 3872 位元組窗口中，前 2304 位元組是四條記錄，其餘是指標表與路由表，本版未動
TAIL_SHA256 = '35fedf78e080c9d0d6144cbf5abfd72f16492701640353278bf55d3c02bfc67a'
# 每條記錄：標籤（高字节＝Gamma ID）、generation、max、前四個取樣點
# 0.5.1：gen 5 與 gen 6 都寫 FX2 的照片內部槽 6 曲線（實拍對照確認機身讀的是 gen 5）
EXPECTED = [
    {'look': 'FL2', 'tag': 0x30010010, 'gen': 5, 'max': 130944,
     'first4': (0, 1158, 2316, 3474)},
    {'look': 'FL2', 'tag': 0x30010010, 'gen': 6, 'max': 130944,
     'first4': (0, 1158, 2316, 3474)},
    {'look': 'FL3', 'tag': 0x31010010, 'gen': 5, 'max': 130945,
     'first4': (0, 1282, 2564, 3845)},
    {'look': 'FL3', 'tag': 0x31010010, 'gen': 6, 'max': 130945,
     'first4': (0, 1282, 2564, 3845)},
]
# FX2 影片槽 6 的取樣點；generation 6 的記錄不得再是這兩條
MOVIE_FIRST4 = {(0, 1085, 2171, 3256), (0, 1202, 2403, 3605)}
INSTALLER_BYTES = 56864


def gamma_block():
    patches = json.loads((BASE / 'assets' / 'patches.json').read_text(encoding='utf-8'))
    hits = [w for w in patches[1]['writes'] if int(w['file_offset'], 16) == GAMMA_WINDOW]
    assert len(hits) == 1, 'Gamma 窗口在 patches.json 中應只有一筆'
    before = bytes.fromhex(hits[0]['before_hex'])
    return bytes.fromhex(hits[0]['after_hex']), before


def helper_window():
    """cpapp-b.bin +0x138832：路由表基址葉子函式的改寫前後位元組。"""
    patches = json.loads((BASE / 'assets' / 'patches.json').read_text(encoding='utf-8'))
    hits = [w for w in patches[1]['writes'] if int(w['file_offset'], 16) == HELPER_WINDOW]
    assert len(hits) == 1, '路由表基址窗口在 patches.json 中應只有一筆'
    return bytes.fromhex(hits[0]['before_hex']), bytes.fromhex(hits[0]['after_hex'])


class GammaTests(unittest.TestCase):
    def test_window_is_untouched_before_the_patch(self):
        _, before = gamma_block()
        self.assertEqual(len(before), BLOCK_BYTES)
        self.assertEqual(before, bytes(BLOCK_BYTES))

    def test_four_records_carry_the_fx2_still_curves(self):
        block, _ = gamma_block()
        self.assertEqual(len(block), BLOCK_BYTES)
        for index, want in enumerate(EXPECTED):
            record = block[index * RECORD_BYTES:(index + 1) * RECORD_BYTES]
            tag, gen, maximum = struct.unpack_from('<III', record, 0x218)
            first4 = struct.unpack_from('<4I', record, 0)[:4]
            self.assertEqual((tag, gen, maximum, first4),
                             (want['tag'], want['gen'], want['max'], want['first4']),
                             f"記錄 {index} ({want['look']})")

    def test_slot6_records_are_not_the_movie_curves(self):
        """0.4.0 在這裡放的是影片槽 6 曲線；0.5.0 必須是照片槽 6。"""
        block, _ = gamma_block()
        for index in (1, 3):
            record = block[index * RECORD_BYTES:(index + 1) * RECORD_BYTES]
            first4 = struct.unpack_from('<4I', record, 0)[:4]
            self.assertNotIn(first4, MOVIE_FIRST4, f'記錄 {index} 仍是影片曲線')
            self.assertGreater(struct.unpack_from('<I', record, 0x220)[0], 130000)

    def test_routing_table_maps_fl2_fl3_to_one_id_each(self):
        """路由表最後兩組必須仍是 (0x30,0x30)、(0x31,0x31)。"""
        block, _ = gamma_block()
        pairs = [struct.unpack_from('<II', block, offset)
                 for offset in range(0xe80, 0xf20, 8)]
        self.assertEqual(len(pairs), 20)
        self.assertEqual(pairs[-2], (0x30, 0x30))
        self.assertEqual(pairs[-1], (0x31, 0x31))

    def test_tail_tables_are_unchanged(self):
        block, _ = gamma_block()
        self.assertEqual(core.sha(block), BLOCK_SHA256)
        self.assertEqual(core.sha(block[0x900:]), TAIL_SHA256)

    def test_installer_module_carries_the_same_block_and_hash(self):
        """原生模組以等長位元組取代方式同步，長度與其餘三筆雜湊都不得變。"""
        block, _ = gamma_block()
        so = (BASE / 'assets' / 'installer.so').read_bytes()
        self.assertEqual(len(so), INSTALLER_BYTES)
        self.assertEqual(so.count(block), 1, 'new_0 在模組中應只出現一次')
        for digest in core.ORIGINAL + core.FINAL:
            self.assertIn(bytes.fromhex(digest), so, digest[:16])
        self.assertIn(bytes.fromhex(core.FINAL[1]), so)

    def test_generation5_and_6_carry_the_same_photo_curve(self):
        """0.5.1：機身讀哪一條都應得到照片槽 6 曲線。"""
        block, _ = gamma_block()
        for index in (0, 2):
            a = block[index * RECORD_BYTES:(index + 1) * RECORD_BYTES]
            b = block[(index + 1) * RECORD_BYTES:(index + 2) * RECORD_BYTES]
            self.assertEqual(a[:0x218], b[:0x218])       # 曲線取樣點與 max 相同
            self.assertEqual(struct.unpack_from('<I', a, 0x220)[0],
                             struct.unpack_from('<I', b, 0x220)[0])
            self.assertNotEqual(struct.unpack_from('<I', a, 0x21c)[0],
                                struct.unpack_from('<I', b, 0x21c)[0])   # gen 仍要分別是 5 / 6

    def test_route_helper_keeps_its_length(self):
        """原地改寫：窗口長度必須與原版一致，否則重定位會跑掉。"""
        before, after = helper_window()
        self.assertEqual(len(before), HELPER_BYTES)
        self.assertEqual(len(after), HELPER_BYTES)
        self.assertEqual(before[:2], b'\x0c\x20',
                         '原版此處應是外觀描述符建構器的 movs r0,#0xc')
        self.assertNotEqual(before, after)

    def test_route_helper_no_longer_rewrites_the_colour_index(self):
        """0.5.1 在這裡把 color 19/20 改成 0，照片因此退回第 0 列（ST）。"""
        _, after = helper_window()
        self.assertEqual(after[:14], NOP_SLIDE)
        # 0.5.1 的改寫序列：cmp r4,#0 ; bne ; cmp r0,#0x13 ; blo ; cmp r0,#0x14 ; it ls ; movls
        self.assertNotIn(b'\x13\x28', after)
        self.assertNotIn(b'\x14\x28', after)
        self.assertNotIn(b'\x98\xbf\x00\x20', after)

    def test_route_helper_still_returns_the_appended_table(self):
        _, after = helper_window()
        self.assertEqual(after[14:22], BASE_LOAD)
        self.assertEqual(after[22:26], EPILOGUE)

    def test_route_table_sends_fl2_fl3_to_rows_48_and_49(self):
        """color 19 = FL2、20 = FL3；兩者照片與影片都指到我們追加的列。"""
        block, _ = gamma_block()
        entries = [struct.unpack_from('<II', block, ROUTE_TABLE + i * 8)
                   for i in range(ROUTE_ENTRIES)]
        self.assertEqual(entries[19], (48, 48))
        self.assertEqual(entries[20], (49, 49))
        self.assertEqual(entries[0], (0, 10), '第 0 項必須仍是原廠預設，不能被移動')

    def test_final_cp_hash_is_not_the_040_value(self):
        for stale in ('60a9de1a0636c7f6b5b98607a4d25eeb48634e25294f632743a6d256e583b370',
                      '9bbaa6c5bce64c76c51ca377ccced09ea39a55e813f334d4269779f3f6e7d05f',
                      'a969a783491b8ff9131d9fedcbd31df3553f0f80aa479b9d2994a5c290d45b1a'):
            self.assertNotEqual(core.FINAL[1], stale)
        self.assertEqual(core.FINAL[1],
                         '30a595529fe842244da735c0602ca8a379a911e1d79340c624ae1f04d550f342')


if __name__ == '__main__':
    unittest.main()
