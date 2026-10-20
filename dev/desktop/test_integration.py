"""GUI/backend contracts and driver sequencing, with camera calls replaced."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from desktopapp import drivers, jobs, worker


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'A7C2_DESKTOP_DATA': str(self.root / 'app')})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_driver_installer_only_targets_camera_ids(self):
        for pid in ('0e8a', '0336'):
            args = drivers.driver_arguments('wdi-simple.exe', pid, self.root)
            self.assertIn('0x054C', args)
            self.assertIn('0x' + pid, args)
            self.assertNotIn('--filter', args)
        with self.assertRaises(ValueError):
            drivers.driver_arguments('installer', '1234', self.root)

    def test_windows_scan_regex_and_raw_errors(self):
        seen = []
        def run(command, **kwargs):
            expression = re.search(r"-match '([^']+)'", command[-1])[1]
            self.assertIsNotNone(re.match(expression, r'USB\VID_054C&PID_0E8A\123'))
            self.assertIsNone(re.match(expression, r'USB\VID_1234&PID_0E8A\123'))
            seen.append(command)
            return SimpleNamespace(returncode=9, stdout='raw-out', stderr='raw-error')
        with patch.object(drivers.sys, 'platform', 'win32'), patch.object(drivers.subprocess, 'run', side_effect=run), \
             patch('usb.core.find', return_value=[]):
            result = drivers.scan()
        self.assertEqual(result['errors'][0]['stderr'], 'raw-error')
        self.assertEqual(result['errors'][0]['code'], 9)

    def test_two_stage_driver_setup_has_one_session_no_auth_retry(self):
        events = []
        transport = SimpleNamespace(SERVICE_DRIVER_SETUP=None)
        @contextmanager
        def camera():
            events.append('first-auth')
            transport.SERVICE_DRIVER_SETUP()
            events.append('second-auth')
            yield SimpleNamespace(identity={'model': 'ILCE-7CM2'})
            events.append('end')
        with patch.object(drivers.sys, 'platform', 'win32'), \
             patch.object(drivers, 'install', side_effect=lambda args, job: events.append(args['pid'])), \
             patch.object(drivers, 'scan', return_value={'devices': [{'id': 'USB\\VID_054C&PID_0336'}]}), \
             patch('looktool.devicesession.modules', return_value=(transport, None)), \
             patch('looktool.devicesession.Camera', side_effect=camera):
            result = drivers.prepare(self.root)
        self.assertEqual(events, ['0e8a', 'first-auth', '0336', 'second-auth', 'end'])
        self.assertFalse(result['camera_firmware_written'])
        self.assertIsNone(transport.SERVICE_DRIVER_SETUP)

    def test_compile_uses_current_cli_calibration_option(self):
        args = dict(source='look.cube', name='Look', output='look.a7look', model='response.npz')
        with patch('looktool.compilelook.main', return_value=0) as compile:
            result = worker.run('compile_look', args, self.root)
        argv = compile.call_args.args[0]
        self.assertIn('--calibration', argv)
        self.assertNotIn('--model', argv)
        self.assertEqual(result['output'], 'look.a7look')

    def test_failed_offline_job_retains_full_traceback_and_no_success(self):
        job = jobs.new_job('compile_look', {})
        with patch.object(worker, 'run', side_effect=RuntimeError('native status -28 raw error')):
            code = worker.execute_request(job / 'request.private.json')
        self.assertEqual(code, 2)
        self.assertEqual(json.loads((job / 'status.private.json').read_text())['phase'], 'FAILED')
        self.assertIn('Traceback', (job / 'worker.log').read_text())
        self.assertIn('native status -28', (job / 'worker.log').read_text())

    def test_every_device_action_is_non_cancellable(self):
        for action in ('restore_auto', 'sound_restore_sound', 'sound_audition', 'vertical_remove', 'usb_prepare'):
            self.assertIn(action, jobs.CAMERA_ACTIONS)

    def test_slot_restore_tracks_fresh_transaction_for_reload_verification(self):
        def invoke(argv):
            self.assertEqual(argv[:2], ['restore-slot', 'original-job'])
            work = Path(argv[argv.index('--work-dir') + 1])
            work.mkdir(parents=True)
            (work / 'job.private.json').write_text(json.dumps({'phase': 'RESTORED_AWAITING_RELOAD'}))
            return 0
        with patch('looktool.devicecli.main', side_effect=invoke):
            result = worker.run('look_restore', dict(workspace='original-job', battery=100, backup=str(self.root / 'backup')), self.root)
        self.assertNotEqual(result['workspace'], 'original-job')
        self.assertEqual(result['phase'], 'RESTORED_AWAITING_RELOAD')


if __name__ == '__main__':
    unittest.main()
