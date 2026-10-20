"""Direct transactions use no original job/backup and preserve unrelated data."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src/looks/tests'))
from test_checkpoint import Camera, SimRollback, values, fake_compile, KEYS
from looktool import direct, checkpointworker, checkpoint, nameworker


class SimDirect(direct.DirectJob, SimRollback):
    def native(self, camera, kind, mode, build=None):
        result = super().native(camera, kind, mode, build)
        if kind == 'runtime':
            result['boot_id'] = getattr(camera, 'boot', 'test-boot-1')
        return result


class DirectTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before = values()
        self.camera = Camera(self.before)
        original = self.camera.__class__.__call__
        self.open = patch.object(Camera, '__call__', lambda obj, expected=None: obj if expected is None else original(obj, expected))
        self.open.start()
        self.addCleanup(self.open.stop)
        self.compile = patch.object(checkpointworker, 'compile_worker', side_effect=fake_compile)
        self.compile.start()
        self.addCleanup(self.compile.stop)

    def plan(self, current, records, mode, **kw):
        target = dict(current)
        changed = bytearray(current['appFw.so'])
        changed[3:5] = b'\x12\x34'
        target['appFw.so'] = bytes(changed)
        return target, [{KEYS[0]: b'\x05'}, {}], None

    def test_no_backup_and_full_readback_with_selected_settings_only(self):
        job = SimDirect(self.root / 'direct', factory=self.camera)
        before = copy.deepcopy(self.camera.ram)
        with patch.object(direct, 'plan', side_effect=self.plan):
            result = job.run_direct('slot_default', version='2.01', power_confirmed=True, slot=1)
        self.assertEqual(result['phase'], 'AWAITING_RELOAD')
        self.assertFalse(result['backup_created'])
        self.assertEqual(list(self.root.rglob('*.zip')), [])
        self.assertEqual(self.camera.files['/usr/lib/appFw.so'][3:5], b'\x12\x34')
        self.assertEqual(self.camera.ram[0][KEYS[0]].data, b'\x05')
        for chip in (0, 1):
            for key, prop in before[chip].items():
                if (chip, key) != (0, KEYS[0]):
                    self.assertEqual(self.camera.ram[chip][key], prop)

    def test_unknown_native_outcome_never_reaches_settings(self):
        job = SimDirect(self.root / 'unknown', factory=self.camera)
        job.lose_after_program = True
        with patch.object(direct, 'plan', side_effect=self.plan), self.assertRaises(TimeoutError):
            job.run_direct('slot_default', version='2.01', power_confirmed=True, slot=1)
        self.assertEqual(job.state['phase'], 'NEEDS_REVIEW')
        self.assertEqual(self.camera.saves, [])
        with self.assertRaises(ValueError):
            job.run_direct('slot_default', version='2.01', power_confirmed=True, slot=1)

    def test_verification_requires_a_new_boot_not_only_matching_disk_bytes(self):
        job = SimDirect(self.root / 'cold', factory=self.camera)
        with patch.object(direct, 'plan', side_effect=self.plan):
            job.run_direct('slot_default', version='2.01', power_confirmed=True, slot=1)
            with self.assertRaisesRegex(ValueError, '冷启动'):
                job.verify_direct()
            self.camera.boot = 'test-boot-2'
            self.assertEqual(job.verify_direct()['phase'], 'LOADED')

    def test_already_set_does_not_drop_retained_image_or_write(self):
        job = SimDirect(self.root / 'noop', factory=self.camera)
        with patch.object(direct, 'plan', side_effect=lambda current, *a, **kw: (dict(current), [{}, {}], None)):
            result = job.run_direct('fl23_disable', version='2.01', power_confirmed=True)
        self.assertEqual(result['phase'], 'LOADED')
        self.assertFalse(any(kind == 'wbi' or mode == 1 for kind, mode in self.camera.native_calls))
        self.assertFalse(self.camera.saves)

    def test_wrong_version_or_missing_power_stops_before_camera(self):
        job = SimDirect(self.root / 'stop', factory=self.camera)
        with patch.object(job, 'factory') as factory:
            for version, confirmed in [('3.00', True), ('2.01', False)]:
                with self.assertRaises(ValueError):
                    job.run_direct('factory_reset', version=version, power_confirmed=confirmed)
            factory.assert_not_called()

    def test_saved_and_live_calibration_stay_independent_during_group_save(self):
        for key, size in zip(checkpoint.CP_KEYS, (8192, 28672)):
            live = bytearray(size)
            stored = bytearray(size)
            live[0x80:0x88] = b'RAMDATA!'
            stored[0x80:0x88] = b'FLASHDAT'
            self.camera.ram[1][key] = self.camera.ram[1][key]._replace(data=bytes(live))
            self.camera.saved[1][key] = self.camera.saved[1][key]._replace(data=bytes(stored))
        def planned(current, records, *args, **kwargs):
            wanted = {}
            for key, spans in direct.color_regions().items():
                data = bytearray(records[1][key].data)
                for at, size in spans:
                    data[at:at + size] = bytes([7]) * size
                wanted[key] = bytes(data)
            return dict(current), [{}, wanted], None
        job = SimDirect(self.root / 'calibration', factory=self.camera)
        with patch.object(direct, 'plan', side_effect=planned):
            job.run_direct('factory_reset', version='2.01', power_confirmed=True)
        for key in checkpoint.CP_KEYS:
            self.assertEqual(self.camera.ram[1][key].data[0x80:0x88], b'RAMDATA!')
            self.assertEqual(self.camera.saved[1][key].data[0x80:0x88], b'FLASHDAT')
        self.assertEqual(list(self.root.rglob('*.zip')), [])


if __name__ == '__main__':
    unittest.main()
