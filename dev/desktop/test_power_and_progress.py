"""Power confirmations and progress display; no camera or driver is touched."""
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stdout

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6 import QtCore, QtWidgets as W
from desktopapp import drivers, jobs, worker
from desktopapp.window import Window
from looktool.power import require_power


class PowerProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = W.QApplication.instance() or W.QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        env = patch.dict(os.environ, {'A7C2_DESKTOP_DATA': str(self.root / 'app')})
        env.start()
        self.addCleanup(env.stop)

    def window(self):
        value = Window()
        value.timer.stop()
        def close():
            value.process = None
            value.close()
        self.addCleanup(close)
        return value

    def test_confirmation_does_not_invent_a_battery_percentage(self):
        value = require_power(confirmed=True)
        self.assertIsNone(value['battery_percent'])
        self.assertFalse(value['usb_battery_measured'])
        for charge in (None, 0, 49, 101):
            with self.assertRaises(ValueError):
                require_power(charge)
        self.assertEqual(require_power(82)['battery_percent'], 82)

    def test_header_has_no_battery_input_and_cancel_opens_no_job(self):
        window = self.window()
        self.assertFalse(hasattr(window, 'battery'))
        self.assertNotIn('battery', window.common())
        with patch.object(W.QMessageBox, 'question', return_value=W.QMessageBox.Cancel) as question, \
             patch.object(jobs, 'new_job') as job:
            window.launch('look_install', {'workspace': 'not-opened'})
        self.assertIn('电量充足', question.call_args.args[2])
        job.assert_not_called()

    def test_each_write_requires_a_fresh_popup_and_records_confirmation(self):
        window = self.window()
        with patch.object(W.QMessageBox, 'question', return_value=W.QMessageBox.Yes) as question, \
             patch('desktopapp.window.QtCore.QProcess') as process:
            for action in ('look_install', 'sound_off'):
                window.launch(action, {'workspace': 'offline-mocked'})
                request = json.loads((window.current_job / 'request.private.json').read_text())
                self.assertTrue(request['arguments']['power_confirmed'])
                self.assertNotIn('battery', request['arguments'])
                window.process = None
        self.assertEqual(question.call_count, 2)

    def test_lut_worker_forwards_confirmation_instead_of_fake_charge(self):
        work = self.root / 'look'
        work.mkdir()
        (work / 'job.private.json').write_text('{"phase":"AWAITING_RELOAD"}')
        args = {'workspace': str(work), 'power_confirmed': True}
        with patch('looktool.devicecli.main', return_value=0) as backend:
            worker.run('look_install', args, self.root)
        argv = backend.call_args.args[0]
        self.assertIn('--power-confirmed', argv)
        self.assertNotIn('--battery-percent', argv)
        self.assertIsNone(json.loads((self.root / 'power-confirmation.private.json').read_text())['battery_percent'])

    def test_missing_confirmation_stops_before_any_camera_dispatch(self):
        for action in jobs.POWER_ACTIONS:
            with self.subTest(action=action), self.assertRaises(ValueError):
                worker.run(action, {}, self.root)

    def test_cancelled_direct_action_keeps_previous_verification_job(self):
        window = self.window()
        window.settings['fl23_direct_work'] = 'previous-completed-job'
        args = window.direct_args('fl23', mode='fl23_enable')
        with patch.object(W.QMessageBox, 'question', return_value=W.QMessageBox.Cancel):
            window.launch('direct_fl23_enable', args)
        self.assertEqual(window.direct_verify_args('fl23')['workspace'], 'previous-completed-job')

    def test_live_log_streams_partial_utf8_without_duplicates(self):
        path = self.root / 'log'
        tail = drivers.LiveLog(path)
        text = '正在卸载相机驱动\n'
        raw = text.encode('utf-8')
        output = io.StringIO()
        with redirect_stdout(output):
            path.write_bytes(raw[:5])
            tail.forward()
            with path.open('ab') as stream:
                stream.write(raw[5:])
            tail.forward()
            tail.forward(final=True)
        self.assertEqual(output.getvalue(), text)

    def test_driver_output_decode_and_raw_record(self):
        message = '驱动卸载完成'
        self.assertEqual(drivers.decode_windows_output(message.encode('utf-8')), message)
        self.assertEqual(drivers.decode_windows_output(message.encode('utf-16')), message)
        result = SimpleNamespace(stdout=message.encode('utf-8'), stderr=b'', returncode=0)
        with patch.object(drivers.subprocess, 'run', return_value=result) as command:
            drivers.run_pnputil(['/scan-devices'], log_dir=self.root)
        self.assertEqual(command.call_args.kwargs['timeout'], 180)
        self.assertEqual(next(self.root.glob('*stdout.raw')).read_bytes(), message.encode('utf-8'))

    def test_finished_worker_clears_busy_indicator_even_without_signal(self):
        window = self.window()
        window.current_job = jobs.new_job('driver_uninstall', {})
        (window.current_job / 'status.private.json').write_text('{"phase":"SUCCEEDED"}')
        process = Mock()
        process.state.return_value = QtCore.QProcess.NotRunning
        process.exitCode.return_value = 0
        window.process = process
        window.progress.setRange(0, 0)
        window.poll_job()
        self.assertIsNone(window.process)
        self.assertEqual(window.progress.value(), 100)
        self.assertIn('完成', window.status.text())


if __name__ == '__main__':
    unittest.main()
