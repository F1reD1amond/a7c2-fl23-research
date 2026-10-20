import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import buffer_trial
import boot_trial
import native_codec
import sound_cli as cli
import trial


class IntegratedSoundTests(unittest.TestCase):
    def scenario(self, check):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            native, audio = base / 'native', base / 'audio'
            native.mkdir(); audio.mkdir()
            identity = {'model': 'ILCE-7CM2', 'serial_sha256': 'synthetic'}
            trial.save(native, {'phase': 'written', 'identity': identity,
                               'complete_readback_and_settings_verified': True})
            trial.save(audio, {'phase': 'temporary_pcm_registered_cold_reload_required_after_test',
                              'identity': identity, 'wire_format': 0,
                              'result': {'temporary_pcm_registered': True}})
            (audio / 'payload.private.bin').write_bytes(bytes(64))
            root, state = cli.workspace(base / 'workspace', True, base / 'backup2')
            cli.attach(root, state, native, audio)
            check(base, root, state, native, audio)

    def test_off_uses_only_narrow_CP_inverse_not_global_audio_settings(self):
        def check(base, root, state, native, audio):
            cli.confirm_audio(root, state, 'correct')
            cli.confirm_recovery(root, state)
            with patch.object(trial, 'change', return_value={'phase': 'restored'}) as change:
                cli.off(root, state)
                change.assert_called_once_with(native, restore=True, zig=None)
            self.assertIsNone(state['pending'])
            self.assertEqual(state['audio_job'], str(audio))
        self.scenario(check)

    def test_quiet_audio_cannot_be_persisted_even_after_recovery(self):
        def check(base, root, state, native, audio):
            cli.confirm_audio(root, state, 'quiet')
            cli.confirm_recovery(root, state)
            with patch.object(boot_trial, 'install') as install:
                with self.assertRaisesRegex(ValueError, 'acceptable volume'): cli.install(root, state, 100)
                install.assert_not_called()
        self.scenario(check)

    def test_install_uses_exact_accepted_trial_bytes_without_reconverting_source(self):
        def check(base, root, state, native, audio):
            cli.confirm_audio(root, state, 'correct')
            cli.confirm_recovery(root, state)
            converted = base / 'converted'; converted.mkdir()
            (converted / 'custom-native.private.bin').write_bytes(bytes(64))
            (converted / 'selected.private.wav').write_bytes(b'source has since changed')
            state['conversion'] = str(converted)
            with patch.object(boot_trial, 'install', return_value={'phase': 'installed_cold_test_pending'}) as install:
                cli.install(root, state, 100)
                args = install.call_args.args
                self.assertEqual(args[4], bytes(64))
                self.assertEqual(args[2:4], (native, audio))
                self.assertEqual(args[5], 100)
        self.scenario(check)

    def test_new_selected_conversion_cannot_install_old_accepted_sound(self):
        def check(base, root, state, native, audio):
            cli.confirm_audio(root, state, 'correct'); cli.confirm_recovery(root, state)
            converted = base / 'other'; converted.mkdir()
            (converted / 'custom-native.private.bin').write_bytes(b'different audio')
            state['conversion'] = str(converted)
            with patch.object(boot_trial, 'install') as install:
                with self.assertRaisesRegex(ValueError, 'differs from the accepted'): cli.install(root, state, 100)
                install.assert_not_called()
        self.scenario(check)

    def test_current_temporary_buffer_is_not_stacked_or_persisted_without_cold_recovery(self):
        def check(base, root, state, native, audio):
            cli.confirm_audio(root, state, 'correct')
            with patch.object(buffer_trial, 'run') as run, patch.object(boot_trial, 'install') as install:
                for action in (lambda: cli.audition(root, state), lambda: cli.install(root, state, 100),
                               lambda: cli.off(root, state)):
                    with self.assertRaisesRegex(ValueError, 'Cold-recover'): action()
                run.assert_not_called(); install.assert_not_called()
        self.scenario(check)

    def test_unknown_off_result_is_durable_and_not_replayed(self):
        def check(base, root, state, native, audio):
            cli.confirm_audio(root, state, 'correct'); cli.confirm_recovery(root, state)
            with patch.object(trial, 'change', side_effect=TimeoutError('lost native reply')) as change:
                with self.assertRaises(TimeoutError): cli.off(root, state)
                with self.assertRaisesRegex(ValueError, 'unresolved'): cli.off(root, state)
                self.assertEqual(change.call_count, 1)
            saved = json.loads((root / 'sound.private.json').read_text())
            self.assertEqual(saved['pending']['outcome'], 'needs_review')
        self.scenario(check)

    def test_on_fresh_job_runs_backup_preflight_before_CP_write(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root, state = cli.workspace(base / 'workspace', True, base / 'backup2')
            calls = []
            with patch.object(trial, 'preflight', side_effect=lambda *a: calls.append('backup-preflight')), \
                 patch.object(trial, 'change', side_effect=lambda *a, **k: calls.append('write') or {'phase': 'written'}):
                cli.on(root, state, 100)
            self.assertEqual(calls, ['backup-preflight', 'write'])

    def test_convert_and_help_never_open_a_camera(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(trial, 'factory', side_effect=AssertionError('USB')):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as exit_status: cli.main(['--help'])
            self.assertEqual(exit_status.exception.code, 0)
            source = Path(temp) / 'source.wav'
            native_codec.write_wav(source, [0, 300, -600, 1200] * 100, 24000)
            from media import convert
            report = convert(source, Path(temp) / 'candidate')
            self.assertFalse(report['camera_io'])


if __name__ == '__main__': unittest.main()
