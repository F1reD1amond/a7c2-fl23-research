"""Integrated sound workflow; status/help/conversion/confirmation stay offline.

on/off changes the narrow CP electronic-capture branch, not Audio Signals or AF
beeps. install/restore-sound controls the separate persistent kind3 sound hook.
Every device operation retains its own native report and body-bound job.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import uuid

import trial

SCHEMA = 'a7c2-sound-workspace/1'
RELOAD = ('USB I/O ended. Shut down normally, wait for the access light, unplug '
          'USB/all external power and remove the battery for at least one minute. '
          'Reinstall, power on and test. Disk readback is not a loaded-state test.')


def load_job(path):
    return json.loads((Path(path) / 'job.private.json').read_text(encoding='utf-8'))


def save(root, state):
    root = Path(root)
    temp = root / 'sound.pending'
    temp.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    temp.replace(root / 'sound.private.json')


def workspace(root, create=False, backup_copy=None):
    root = Path(root).resolve()
    path = root / 'sound.private.json'
    if path.exists():
        state = json.loads(path.read_text(encoding='utf-8'))
        if state.get('schema') != SCHEMA:
            raise ValueError('Not a sound workspace')
        if backup_copy and str(Path(backup_copy).resolve()) != state['backup_root']:
            raise ValueError('Use the original backup root for this workspace')
    elif create:
        if not backup_copy:
            raise ValueError('A new workspace requires --backup-copy outside the workspace')
        other = Path(backup_copy).resolve()
        if other == root or root in other.parents or other in root.parents:
            raise ValueError('Keep the second backup outside the workspace, in a separate directory')
        root.mkdir(parents=True, exist_ok=False)
        state = {'schema': SCHEMA, 'backup_root': str(other), 'history': [], 'pending': None}
        save(root, state)
    else:
        raise ValueError('Create a workspace with on or attach first')
    return root, state


def new_path(root, label):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return root / 'jobs' / (stamp + '-' + label + '-' + uuid.uuid4().hex[:8])


def require_idle(state):
    if state.get('pending'):
        raise ValueError('Previous operation is unresolved. Use status and keep its job; do not replay it.')


def native_job(state, *, enabled=True):
    path = state.get('native_job')
    if not path:
        raise ValueError('Run on first, or attach an existing completed native-sound job')
    value = load_job(path)
    if enabled and (value['phase'] != 'written' or not value.get('complete_readback_and_settings_verified')):
        raise ValueError('Electronic-sound support is not recorded as enabled; run on and reload first')
    return Path(path), value


def require_recovered_trial(state):
    if state.get('audio_job'):
        previous = load_job(state['audio_job'])
        if not previous.get('owner_cold_recovery_confirmed'):
            raise ValueError('Cold-recover the temporary audition first, then run confirm-recovery')


def operate(root, state, command, job, operation):
    # Durable intent precedes any camera action. Failure is retained, never retried.
    require_idle(state)
    state['pending'] = {'command': command, 'job': str(job)}
    save(root, state)
    try:
        result = operation()
    except BaseException:
        state['pending']['outcome'] = 'needs_review'
        save(root, state)
        raise
    state['history'].append({'command': command, 'job': str(job), 'phase': result['phase']})
    state['pending'] = None
    save(root, state)
    return result


def on(root, state, battery, zig=None, *, power_confirmed=False):
    import trial
    require_idle(state)
    require_recovered_trial(state)
    from looktool.power import require_power
    state['power_confirmation'] = require_power(battery, confirmed=power_confirmed)
    if state.get('native_job') and load_job(state['native_job'])['phase'] != 'restored':
        raise ValueError('Existing support is enabled or unresolved; inspect status instead of writing again')
    job = new_path(root, 'native-on')
    state['native_job'] = str(job)
    def run():
        trial.preflight(job, Path(state['backup_root']) / job.name, zig)
        return trial.change(job, zig=zig)
    result = operate(root, state, 'on', job, run)
    print(RELOAD)
    return result


def off(root, state, zig=None):
    require_idle(state)
    require_recovered_trial(state)
    job, _ = native_job(state)
    result = operate(root, state, 'off', job, lambda: trial.change(job, restore=True, zig=zig))
    print(RELOAD)
    return result


def attach(root, state, original, audio=None):
    require_idle(state)
    if any(state.get(key) for key in ('native_job', 'audio_job', 'boot_job')):
        raise ValueError('Attach only to a new workspace; existing evidence is retained')
    original = Path(original).resolve()
    value = load_job(original)
    if value.get('phase') != 'written' or not value.get('complete_readback_and_settings_verified'):
        raise ValueError('Attach a completed native-sound job')
    if audio:
        audio = Path(audio).resolve()
        evidence = load_job(audio)
        if evidence.get('identity') != value['identity'] or evidence.get('wire_format') != 0:
            raise ValueError('Attach only a same-body format0 audio trial')
        if not evidence.get('result', {}).get('temporary_pcm_registered'):
            raise ValueError('The audio trial did not complete registration')
        state['audio_job'] = str(audio)
    state['native_job'] = str(original)
    save(root, state)
    return {'phase': 'attached_existing_evidence', 'camera_io': False}


def import_audio(root, state, source, **options):
    import media
    require_idle(state)
    if state.get('boot_job') and load_job(state['boot_job'])['phase'] != 'restored_cold_test_pending':
        raise ValueError('Run restore-sound and cold-reload before replacing a persistent sound')
    folder = new_path(root, 'converted')
    report = media.convert(source, folder, **options)
    state['conversion'] = str(folder)
    save(root, state)
    return {'phase': 'converted_offline', 'camera_io': False, 'bytes': report['encoded_bytes'],
            'preview': str(folder / 'preview.private.wav')}


def audition(root, state, zig=None):
    import buffer_trial
    require_idle(state)
    original, _ = native_job(state)
    if state.get('boot_job') and load_job(state['boot_job'])['phase'] != 'restored_cold_test_pending':
        raise ValueError('Restore the persistent sound and cold-reload before a new audition')
    require_recovered_trial(state)
    if not state.get('conversion'):
        raise ValueError('Convert a source with import first')
    previous = Path(state['audio_job']) if state.get('audio_job') else None
    payload = (Path(state['conversion']) / 'custom-native.private.bin').read_bytes()
    job = new_path(root, 'audition')
    state['audio_job'] = str(job)
    result = operate(root, state, 'audition', job, lambda: buffer_trial.run(job, original,
        zig, payload=payload, register=True, wire_format=0, recovered_job=previous))
    print('USB I/O ended. Unplug USB WITHOUT switching off, removing the battery or changing Audio Signals. '
          'Take one electronic exposure; check volume/distortion/pitch/speed and normal shooting/playback. '
          'Then record confirm --result correct (or the actual failure). No ROM was written.')
    return result


def confirm_audio(root, state, result):
    import buffer_trial
    require_idle(state)
    if not state.get('audio_job'):
        raise ValueError('No audition to confirm')
    value = buffer_trial.confirm(Path(state['audio_job']), result)
    print('Confirmation recorded offline. Cold-recover before install or another audition, then run confirm-recovery.')
    return value


def confirm_recovery(root, state):
    import buffer_trial
    require_idle(state)
    if not state.get('audio_job'):
        raise ValueError('No temporary audition to cold-recover')
    return buffer_trial.confirm_recovery(Path(state['audio_job']))


def install(root, state, battery, zig=None, *, power_confirmed=False):
    import boot_trial
    require_idle(state)
    from looktool.power import require_power
    state['power_confirmation'] = require_power(battery, confirmed=power_confirmed)
    original, _ = native_job(state)
    require_recovered_trial(state)
    if not state.get('audio_job'):
        raise ValueError('First audition and confirm this sound')
    if state.get('boot_job') and load_job(state['boot_job'])['phase'] != 'restored_cold_test_pending':
        raise ValueError('Restore the previous persistent sound before installing another')
    audio = Path(state['audio_job'])
    payload = (audio / 'payload.private.bin').read_bytes()
    if not load_job(audio).get('owner_audio_correct'):
        raise ValueError('Confirm acceptable volume, pitch/speed and normal shooting/playback first')
    if state.get('conversion') and (Path(state['conversion']) / 'custom-native.private.bin').read_bytes() != payload:
        raise ValueError('The selected conversion differs from the accepted audition; audition it first')
    # Reuse the exact accepted payload, never reconvert the source during install.
    job = new_path(root, 'persistent')
    state['boot_job'] = str(job)
    options = {'power_confirmed': True} if power_confirmed else {}
    result = operate(root, state, 'install', job, lambda: boot_trial.install(job,
        Path(state['backup_root']) / job.name, original, audio, payload, battery, zig, **options))
    print(RELOAD)
    return result


def restore_sound(root, state, zig=None):
    import boot_trial
    require_idle(state)
    require_recovered_trial(state)
    if not state.get('boot_job'):
        raise ValueError('No persistent sound is recorded; RAM auditions clear by cold power-off')
    job = Path(state['boot_job'])
    result = operate(root, state, 'restore-sound', job, lambda: boot_trial.restore(job, zig))
    print(RELOAD)
    return result


def verify(root, state, heard_correct=False):
    import boot_trial
    require_idle(state)
    if not state.get('boot_job'):
        raise ValueError('No persistent installation to verify')
    job = Path(state['boot_job'])
    return operate(root, state, 'verify', job, lambda: boot_trial.verify_loaded(job, heard_correct))


def status(state):
    result = {'phase': 'local_status_only', 'camera_io': False, 'pending': state.get('pending'),
              'hardware_state_not_inferred_from_local_status': True}
    for key in ('native_job', 'audio_job', 'boot_job'):
        path = state.get(key)
        if path:
            job_file = Path(path) / 'job.private.json'
            phase = load_job(path)['phase'] if job_file.is_file() else 'job_not_created_or_missing'
            result[key] = {'path': path, 'phase': phase}
        else:
            result[key] = None
    result['conversion'] = state.get('conversion')
    return result


def doctor():
    names = ('numpy', 'scipy', 'usb', 'libusb_package', 'Cryptodome', 'yaml', 'elftools',
             'unicorn', 'keystone')
    missing = [name for name in names if importlib.util.find_spec(name) is None]
    if not shutil.which('zig') and importlib.util.find_spec('ziglang') is None:
        missing.append('ziglang (or zig on PATH)')
    return {'camera_io': False, 'python': sys.version.split()[0], 'bits': struct.calcsize('P') * 8,
            'platform': sys.platform, 'missing': missing,
            'ffmpeg_available': bool(shutil.which('ffmpeg') or importlib.util.find_spec('imageio_ffmpeg')),
            'mac_camera_USB_verified': False}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Offline dependency inventory; never connects')
    for name, help_text in (
        ('on', 'Enable electronic shutter sound independently of AF beeps; CP patch, cold reload'),
        ('off', 'Disable only the electronic-capture sound branch; AF audio setting preserved'),
        ('attach', 'Offline: reuse a completed native-sound job and optional RAM audition'),
        ('import', 'Offline: extract selected WAV/MP3/MP4 audio and encode a private candidate'),
        ('audition', 'Temporarily register converted audio in RAM, no ROM write'),
        ('confirm', 'Offline: record the actual listening result'),
        ('confirm-recovery', 'Offline statement: cold power-off done, native sound/shooting/playback normal'),
        ('install', 'Persist the exact owner-accepted sound; files before boot hook'),
        ('verify', 'Read loaded code/files/descriptor after cold boot'),
        ('restore-sound', 'Restore native sound; disable/read back boot hook before removing files'),
        ('status', 'Read local workspace state; no camera connection')):
        s = sub.add_parser(name, help=help_text)
        s.add_argument('--workspace', required=True, type=Path)
        if name in ('on', 'attach', 'import'):
            s.add_argument('--backup-copy', type=Path)
        if name in ('on', 'install'):
            power = s.add_mutually_exclusive_group(required=True)
            power.add_argument('--battery-percent', type=int)
            power.add_argument('--power-confirmed', action='store_true')
        if name in ('on', 'off', 'audition', 'install', 'restore-sound'):
            s.add_argument('--zig')
        if name == 'on':
            s.add_argument('--firmware', required=True, choices=('2.01',))
        if name == 'attach':
            s.add_argument('--native-job', required=True, type=Path)
            s.add_argument('--audio-job', type=Path)
        if name == 'import':
            s.add_argument('source', type=Path)
            s.add_argument('--start', type=float, default=0)
            s.add_argument('--duration', type=float)
            s.add_argument('--peak', type=float, default=0.4)
            s.add_argument('--ffmpeg', type=Path)
        if name == 'confirm':
            s.add_argument('--result', required=True,
                           choices=('correct', 'quiet', 'noise', 'wrong-speed', 'native', 'silent'))
        if name == 'verify':
            s.add_argument('--heard-correct', action='store_true')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'doctor':
            result = doctor()
        else:
            if sys.version_info < (3, 10) or struct.calcsize('P') != 8:
                raise ValueError('Use 64-bit Python 3.10 or newer')
            root, state = workspace(args.workspace, args.command in ('on', 'attach', 'import'),
                                    getattr(args, 'backup_copy', None))
            command = args.command
            if command == 'on': result = on(root, state, args.battery_percent, args.zig, power_confirmed=args.power_confirmed)
            elif command == 'off': result = off(root, state, args.zig)
            elif command == 'attach': result = attach(root, state, args.native_job, args.audio_job)
            elif command == 'import': result = import_audio(root, state, args.source, start=args.start,
                duration=args.duration, peak=args.peak, ffmpeg=args.ffmpeg)
            elif command == 'audition': result = audition(root, state, args.zig)
            elif command == 'confirm': result = confirm_audio(root, state, args.result)
            elif command == 'confirm-recovery': result = confirm_recovery(root, state)
            elif command == 'install': result = install(root, state, args.battery_percent, args.zig, power_confirmed=args.power_confirmed)
            elif command == 'restore-sound': result = restore_sound(root, state, args.zig)
            elif command == 'verify': result = verify(root, state, args.heard_correct)
            else: result = status(state)
        # Never print body identity, raw native buffers or the complete private journal.
        print(json.dumps({key: result[key] for key in ('phase', 'camera_io', 'camera_firmware_written',
            'complete_readback_and_settings_verified', 'owner_audio_correct', 'bytes', 'preview')
            if key in result} if args.command not in ('status', 'doctor') else result, indent=2))
        return 0
    except (ValueError, OSError, ImportError, RuntimeError, KeyError) as exc:
        print('Stopped: ' + str(exc) + '\nKeep the workspace and backup; do not repeat unknown writes.', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('Interrupted. Preserve the workspace; inspect status before further device operations.', file=sys.stderr)
        return 130
