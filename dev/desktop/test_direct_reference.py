"""Optional original-firmware planning checks. No camera or driver access."""
import copy
import json
import os
from pathlib import Path
import tempfile
import importlib.util
import unittest
from unittest.mock import patch

from desktopapp import official
from desktopapp.worker import setup_runtime
setup_runtime()
from looktool import direct, photoformat, photobasis, photoio, lookfile, device_layout, nameworker
from test_checkpoint import stock_names
from looktool.devicesession import modules


@unittest.skipUnless(os.environ.get('A7C2_ORIGINAL_REFERENCE') and os.environ.get('A7C2_RESEARCH_FIXTURES'),
                     'Needs private reference and known program fixtures; never a camera')
class ReferencePlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = official.load(os.environ['A7C2_ORIGINAL_REFERENCE'])
        cls.core = modules()[1]
        index = json.loads(Path(os.environ['A7C2_RESEARCH_FIXTURES']).read_text())
        cls.ap = Path(index['six_ap']).read_bytes()
        cls.cp = Path(index['v4_cp']).read_bytes()
        cls.records = cls.core.backup_records(cls.stock['CX89700_ALLLANG.bin'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.current = {'appFw.so': self.ap, 'cpapp-b.bin': self.cp,
            **{'resources/' + n: stock_names() for n in nameworker.filenames()}}
        self.props = copy.deepcopy(self.records)
        for key, at in ((0x02a40001, 0x100), (0x02a4000d, 0x80)):
            raw = bytearray(self.props[1][key].data)
            raw[at:at + 8] = b'BODYDATA'
            self.props[1][key] = self.props[1][key]._replace(data=bytes(raw))

    def apply(self, mode, **kwargs):
        target, wanted, _ = direct.plan(self.current, self.props, mode, **kwargs)
        for chip in (0, 1):
            for key, value in wanted[chip].items():
                self.props[chip][key] = self.props[chip][key]._replace(data=value)
        self.current = target
        return target, wanted

    def test_fl23_remove_and_enable_preserves_every_lut_program_byte(self):
        enabled, _ = self.apply('fl23_enable')
        removed, _ = self.apply('fl23_disable')
        self.assertEqual(removed['cpapp-b.bin'], enabled['cpapp-b.bin'])
        expected = bytearray(enabled['appFw.so'])
        for at in direct.MENU_FLAGS:
            expected[at:at + 2] = b'\0\0'
        self.assertEqual(removed['appFw.so'], bytes(expected))
        restored, _ = self.apply('fl23_enable')
        self.assertEqual(restored, enabled)

    def test_stock_recovery_resets_project_regions_but_keeps_body_calibration(self):
        self.apply('fl23_enable')
        before = copy.deepcopy(self.props)
        result, wanted = self.apply('factory_reset', factory=self.stock)
        self.assertEqual(result['appFw.so'], self.stock['appFw.so'])
        self.assertEqual(result['cpapp-b.bin'], self.stock['cpapp-b.bin'])
        for key, spans in direct.color_regions().items():
            a, b = before[1][key].data, wanted[1][key]
            expected = bytearray(a)
            for at, size in spans:
                expected[at:at + size] = self.records[1][key].data[at:at + size]
            self.assertEqual(b, bytes(expected))
        self.assertEqual(self.props[1][0x02a40001].data[0x100:0x108], b'BODYDATA')
        self.assertEqual(self.props[1][0x02a4000d].data[0x80:0x88], b'BODYDATA')
        for key, prop in before[0].items():
            if key not in wanted[0]:
                self.assertEqual(self.props[0][key], prop)

    def test_builtin_original_regions_remove_all_known_legacy_program_changes(self):
        self.apply('fl23_enable')
        restored, wanted = self.apply('factory_reset', factory=official.builtin())
        self.assertEqual(restored['appFw.so'], self.stock['appFw.so'])
        self.assertEqual(restored['cpapp-b.bin'], self.stock['cpapp-b.bin'])

    def test_builtin_reference_preserves_unrelated_program_regions(self):
        for name in ('appFw.so', 'cpapp-b.bin'):
            changed = bytearray(self.current[name])
            changed[0x70000] ^= 1
            self.current[name] = bytes(changed)
        restored, _ = self.apply('factory_reset', factory=official.builtin())
        for name in ('appFw.so', 'cpapp-b.bin'):
            self.assertEqual(restored[name][0x70000], self.stock[name][0x70000] ^ 1)

    @unittest.skipUnless(importlib.util.find_spec('keystone'), 'Optional sound assembler')
    def test_builtin_reference_reverses_the_real_sound_hook_and_reader_changes(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'dev/shutter_sound'))
        import boot_sound
        modified = boot_sound.patch(self.stock['appFw.so'], boot_sound.windows(self.stock['appFw.so']))
        self.current['appFw.so'] = modified
        restored, _ = self.apply('factory_reset', factory=official.builtin())
        self.assertEqual(restored['appFw.so'], self.stock['appFw.so'])

    def make_look(self, slot, amount):
        bank = photoformat.extract_bank(self.current['cpapp-b.bin'],
            self.props[1][0x02a40001].data, self.props[1][0x02a4000d].data,
            gamma_table_va=0x1209480, regular_row=0, still_row=10, color_parameter=0)[0]
        delta = photobasis.pack(bank, tone=[amount, 0, 0])[1]
        path = self.root / ('look-' + str(slot) + '.a7look')
        return lookfile.write(path, 'Look ' + str(slot), bytes([slot]) * 1215,
            method='offline fixture', attribution='test', native_photo=delta)

    def test_reset_one_native_slot_retains_other_native_slot_exactly(self):
        self.apply('look_import', slot=5, look=self.make_look(5, 32))
        self.apply('look_import', slot=6, look=self.make_look(6, -32))
        before_cp = self.current['cpapp-b.bin']
        before_table = device_layout.tables(before_cp)[5]
        before_state = photoio.inspect(before_cp)
        before_settings = copy.deepcopy(self.props)
        self.apply('slot_default', slot=5)
        self.assertEqual(device_layout.tables(self.current['cpapp-b.bin'])[5], before_table)
        state = photoio.inspect(self.current['cpapp-b.bin'])
        self.assertEqual(state['knobs'][5], before_state['knobs'][5])
        self.assertEqual(state['mask'] & 16, 0)
        self.assertEqual(state['mask'] & 32, 32)
        changed_keys = direct.recipe_defaults(self.ap, [5])
        for key, value in before_settings[0].items():
            if key not in changed_keys:
                self.assertEqual(self.props[0][key], value)
        self.assertEqual(self.props[1], before_settings[1])

    def test_builtin_reset_removes_native_photo_code_and_all_tables(self):
        self.apply('look_import', slot=5, look=self.make_look(5, 32))
        restored, _ = self.apply('factory_reset', factory=official.builtin())
        self.assertEqual(restored['appFw.so'], self.stock['appFw.so'])
        self.assertEqual(restored['cpapp-b.bin'], self.stock['cpapp-b.bin'])

    def test_stock_first_import_and_default_return_need_no_original_job(self):
        self.current['appFw.so'] = self.stock['appFw.so']
        self.current['cpapp-b.bin'] = self.stock['cpapp-b.bin']
        self.apply('fl23_enable')
        self.apply('look_import', slot=2, look=self.make_look(2, 20))
        imported = device_layout.structural(self.current['appFw.so'], self.current['cpapp-b.bin'])
        self.assertEqual(imported['mask'], 2)
        self.apply('slot_default', slot=2)
        self.assertEqual(device_layout.structural(self.current['appFw.so'], self.current['cpapp-b.bin'])['mask'], 0)
        restored, _ = self.apply('factory_reset', factory=official.builtin())
        self.assertEqual(restored['appFw.so'], self.stock['appFw.so'])
        self.assertEqual(restored['cpapp-b.bin'], self.stock['cpapp-b.bin'])

    def test_direct_default_reset_has_no_firmware_sha_gate_or_scan(self):
        with patch('looktool.firmware.sha', side_effect=AssertionError('No firmware SHA in direct operations')):
            self.apply('slot_default', slot=4)
            self.apply('fl23_disable')
            self.apply('factory_reset', factory=official.builtin())


if __name__ == '__main__':
    unittest.main()
