"""Driver removal planning/ordering only; no real driver command is run."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from desktopapp import drivers


class DriverUninstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'INF').mkdir()
        (self.root / 'INF/oem42.inf').write_text(
            '[Models]\nCamera=Install,USB\\VID_054C&PID_0E8A\n', encoding='utf-8')
        self.rows = [{'id': r'USB\VID_054C&PID_0E8A\CAMERA', 'inf': 'oem42.inf'}]

    def test_only_camera_oem_package_selected(self):
        self.assertEqual(drivers.uninstall_plan(self.rows, {'0e8a', '0336'}, self.root / 'INF'), ['oem42.inf'])
        self.assertFalse(drivers.is_camera_id(r'USB\VID_1234&PID_0E8A\OTHER', {'0e8a'}))
        self.assertFalse(drivers.is_camera_id(r'USB\VID_054C&PID_0E8A0\OTHER', {'0e8a'}))

    def test_windows_native_driver_never_deleted(self):
        rows = [dict(self.rows[0], inf='usbstor.inf')]
        self.assertEqual(drivers.uninstall_plan(rows, {'0e8a'}, self.root / 'INF'), [])

    def test_shared_non_camera_package_is_not_removed(self):
        rows = self.rows + [{'id': r'USB\VID_1234&PID_5678\OTHER', 'inf': 'oem42.inf'}]
        with self.assertRaisesRegex(ValueError, 'shared'):
            drivers.uninstall_plan(rows, {'0e8a', '0336'}, self.root / 'INF')

    def test_inf_cannot_hide_other_supported_hardware_ids(self):
        with (self.root / 'INF/oem42.inf').open('a') as stream:
            stream.write('Other=Install,USB\\VID_1234&PID_5678\n')
        with self.assertRaisesRegex(ValueError, 'exclusively'):
            drivers.uninstall_plan(self.rows, {'0e8a', '0336'}, self.root / 'INF')

    def test_export_before_uninstall_then_rescan_no_force_or_reboot(self):
        commands = []
        fake = SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: True))
        with patch.object(drivers.sys, 'platform', 'win32'), \
             patch.object(drivers.ctypes, 'windll', fake, create=True), \
             patch.dict(os.environ, {'WINDIR': str(self.root)}), \
             patch.object(drivers, 'driver_inventory', side_effect=[self.rows, []]), \
             patch.object(drivers, 'run_pnputil', side_effect=lambda a: commands.append(a) or 0):
            result = drivers.uninstall({}, self.root / 'job')
        self.assertEqual([row[0] for row in commands], ['/export-driver', '/delete-driver', '/scan-devices'])
        self.assertEqual(commands[1], ['/delete-driver', 'oem42.inf', '/uninstall'])
        self.assertNotIn('/force', sum(([str(x) for x in row] for row in commands), []))
        self.assertFalse(result['camera_firmware_written'])

    def test_failed_export_prevents_deletion(self):
        fake = SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: True))
        with patch.object(drivers.sys, 'platform', 'win32'), \
             patch.object(drivers.ctypes, 'windll', fake, create=True), \
             patch.dict(os.environ, {'WINDIR': str(self.root)}), \
             patch.object(drivers, 'driver_inventory', return_value=self.rows), \
             patch.object(drivers, 'run_pnputil', side_effect=RuntimeError('export failed')) as command:
            with self.assertRaisesRegex(RuntimeError, 'export failed'):
                drivers.uninstall({}, self.root / 'job')
        self.assertEqual(command.call_count, 1)

    def test_elevation_routes_to_uninstall_not_install(self):
        fake = SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: False))
        with patch.object(drivers.sys, 'platform', 'win32'), \
             patch.object(drivers.ctypes, 'windll', fake, create=True), \
             patch.object(drivers, 'elevate_request', return_value={'ok': True}) as elevate:
            self.assertEqual(drivers.uninstall({}, self.root), {'ok': True})
        self.assertEqual(elevate.call_args.kwargs['action'], 'driver_uninstall')


if __name__ == '__main__':
    unittest.main()
