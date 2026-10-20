"""Developer install/restore controller for the original native boot sound path.

Install requires an owner-confirmed format0 RAM trial for the identical payload.
Files are installed and read back before the AP hook. Restore removes the AP
hook and reads it back before deleting the private files. No automatic retries
or restoration after unknown outcomes. Not a released/public camera feature.
"""
import argparse
import json
from pathlib import Path
import struct

import boot_sound
import candidate
import files_worker
import trial


PATHS = ('/usr/share/avsystemsound/custom-shutter.bin',
         '/usr/share/avsystemsound/custom.txt')


def prepare(ap, cp, payload, output, zig=None):
    from looktool import nativebuild
    candidate.guard(ap, cp, installed=True)
    target, csv, edits, report = boot_sound.verify(ap, payload)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    (root / 'custom-shutter.bin').write_bytes(payload)
    (root / 'custom.txt').write_bytes(csv)
    (root / 'offline.private.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    lines = []
    for name, at in (('audio_getter', 0x286cde8), ('table_getter', 0x2885488)):
        lines.append('static const u8 ' + name + '[]={' + ','.join(map(str, ap[at:at + 20])) + '};')
    header = root / 'probe.private.h'
    header.write_text('\n'.join(lines) + '\n', encoding='ascii')
    nativebuild.compile_worker(Path(__file__).with_name('sound_probe.c'), header, root / 'probe.so', zig, fingerprints=False)
    nativebuild.compile_worker(candidate.ROOT / 'src/fl23/native/wbi.c', header, root / 'wbi.so', zig, fingerprints=False)
    program = program_worker(ap, cp, edits, root / 'program', zig)
    post = list(lines) + ['#define CHECK_EXTRA_GUARDS 1',
        'struct ExtraGuard {u64 offset;u32 length;const u8 *bytes;};']
    rows = []
    for index, (at, old, new) in enumerate(edits):
        post.append('static const u8 guard_' + str(index) + '[]={' + ','.join(map(str, new)) + '};')
        rows.append('{' + str(at) + 'UL,' + str(len(new)) + ',guard_' + str(index) + '}')
    post += ['static const struct ExtraGuard extra_guards[]={' + ','.join(rows) + '};',
             'static const u32 extra_guard_count=' + str(len(rows)) + ';']
    post_header = root / 'post-probe.private.h'
    post_header.write_text('\n'.join(post) + '\n', encoding='ascii')
    nativebuild.compile_worker(Path(__file__).with_name('sound_probe.c'), post_header,
                               root / 'post-probe.so', zig, fingerprints=False)
    files = files_worker.build(payload, csv, root / 'files', zig)
    return {'appFw.so': target, 'cpapp-b.bin': cp}, {
        'windows': [{'offset': at, 'before_hex': old.hex(), 'after_hex': new.hex()} for at, old, new in edits],
        'program': program, 'files': str(files), 'probe': str(root / 'probe.so'),
        'post_probe': str(root / 'post-probe.so'),
        'wbi': str(root / 'wbi.so'), 'csv': str(root / 'custom.txt'),
        'audio': str(root / 'custom-shutter.bin')}


def program_worker(ap, cp, edits, output, zig=None):
    from looktool import nativebuild
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    lines, rows = ['#define BYTE_WINDOWS_ONLY 1'], []
    for index, (at, old, new) in enumerate(edits):
        if len(old) != len(new) or not old or ap[at:at + len(old)] != old:
            raise ValueError('Boot sound program window conflicts')
        for label, value in (('old', old), ('new', new)):
            lines.append('static const u8 ' + label + '_' + str(index) + '[]={' + ','.join(map(str, value)) + '};')
        rows.append('{' + str(at) + 'UL,' + str(len(old)) + ',0,old_' + str(index) + ',new_' + str(index) + '}')
    lines += ['static const struct Window windows[]={' + ','.join(rows) + '};',
              'static const u32 window_count=' + str(len(rows)) + ';',
              'static const u64 file_sizes[]={' + str(len(ap)) + 'UL,' + str(len(cp)) + 'UL};']
    header = root / 'program.private.h'
    header.write_text('\n'.join(lines) + '\n', encoding='ascii')
    worker = root / 'program.so'
    nativebuild.compile_worker(candidate.ROOT / 'src/fl23/native/installer.c', header, worker, zig, fingerprints=False)
    return {'path': str(worker), 'windows': len(rows), 'sizes': [len(ap), len(cp)]}


def invoke_files(camera, root, state, worker, mode):
    from looktool import devicesession
    def record(event, **fields):
        state['journal'].append({'event': event, **fields})
        trial.save(root, state)
    def capture(raw):
        folder = root / 'evidence'
        folder.mkdir(exist_ok=True)
        (folder / ('files-' + str(len(state['journal'])) + '.bin')).write_bytes(raw)
    result = devicesession.invoke(camera, Path(worker).read_bytes(),
        stage='shutter.staged.so', request='a7c2.install.request',
        result='shutter.probe.result', contents=struct.pack('<8sII', b'A7SFQ001', mode, 0),
        mode=mode, decode=files_worker.parse, record=record, save_raw=capture,
        extras=('a7c2.probe.result',))
    if not result['native_success'] or result['mode'] != mode:
        raise ValueError('Sound-file transaction failed; preserve evidence and do not repeat')
    return result


def probe(camera, root, state, components):
    result = trial.run_native(camera, root, state, components['probe'], 'probe')
    candidate.require_registry(result)
    if result['image_mode'] == '2':
        trial.run_native(camera, root, state, components['wbi'], 'wbi', 0)
    return result


def check_settings(camera, before):
    from looktool import devicesettings
    for name, ram in (('settings-ram.bin', True), ('settings-saved.bin', False)):
        devicesettings.compare(camera.records(before[name]), camera.records(camera.snapshot(ram)), {}, camera.core)


def install(root, backup_copy, native_job, audio_job, payload, battery, zig=None, camera_factory=trial.factory, *, power_confirmed=False):
    from looktool.power import require_power
    power = require_power(battery, confirmed=power_confirmed)
    original = json.loads((Path(native_job) / 'job.private.json').read_text(encoding='utf-8'))
    evidence = json.loads((Path(audio_job) / 'job.private.json').read_text(encoding='utf-8'))
    if not evidence.get('owner_audio_correct') or evidence.get('wire_format') != 0:
        raise ValueError('First confirm correct format0 RAM playback, pitch and speed on the body')
    if evidence.get('identity') != original['identity'] or (Path(audio_job) / 'payload.private.bin').read_bytes() != payload:
        raise ValueError('The confirmed audio trial belongs to another body or payload')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    state = {'schema': 'a7c2-native-boot-sound-job/1', 'phase': 'preparing',
             'identity': original['identity'], 'camera_firmware_written': False,
             'battery_percent_reported': power['battery_percent'], 'power_confirmation': power, 'journal': [],
             'owner_audio_job': str(Path(audio_job).resolve()),
             'original_file_absence_required': list(PATHS)}
    trial.save(root, state)
    try:
        with camera_factory(original['identity']) as camera:
            before = trial.capture(camera)
            target, components = prepare(before['appFw.so'], before['cpapp-b.bin'], payload, root / 'build', zig)
            state['components'] = components
            state['backup_copy'] = trial.backup(root, backup_copy, before)
            trial.save(root, state)
            camera.programs_pinned = True
            runtime = probe(camera, root, state, components)
            invoke_files(camera, root, state, components['files'], 0)
            plan = components['program']
            trial.run_native(camera, root, state, plan['path'], 'program', 0, plan)
            state['phase'] = 'creating_audio_before_boot_hook'
            trial.save(root, state)
            invoke_files(camera, root, state, components['files'], 1)
            for path, local in zip(PATHS, (components['audio'], components['csv'])):
                if camera.read(path) != Path(local).read_bytes():
                    raise ValueError('Sound-file complete readback differs; AP hook was not invoked')
            state['phase'] = 'audio_verified_installing_boot_hook'
            trial.save(root, state)
            trial.run_native(camera, root, state, plan['path'], 'program', 1, plan)
            state['camera_firmware_written'] = True
            trial.save(root, state)
            for name, path in (('appFw.so', '/usr/lib/appFw.so'), ('cpapp-b.bin', '/cp/cpapp-b.bin')):
                if camera.read(path) != target[name]:
                    raise ValueError('Complete program readback differs; keep both audio files for recovery')
            check_settings(camera, before)
            state['complete_readback_and_settings_verified'] = True
            state['phase'] = 'installed_reload_pending'
            trial.save(root, state)
            if runtime['image_mode'] == '2':
                trial.run_native(camera, root, state, components['wbi'], 'wbi', 1)
            state['phase'] = 'installed_cold_test_pending'
            trial.save(root, state)
    except BaseException:
        state['phase'] = 'needs_review'
        trial.save(root, state)
        raise
    return state


def restore(root, zig=None, camera_factory=trial.factory):
    root = Path(root)
    state = json.loads((root / 'job.private.json').read_text(encoding='utf-8'))
    if state['phase'] not in ('installed_cold_test_pending', 'loaded_owner_confirmation_pending', 'owner_confirmed_working'):
        raise ValueError('Inspect the original job before restoration; unknown operations are not repeated')
    components = state['components']
    state['phase'] = 'restoring_boot_hook_first'
    trial.save(root, state)
    try:
        with camera_factory(state['identity']) as camera:
            before = trial.capture(camera)
            camera.programs_pinned = True
            runtime = probe(camera, root, state, components)
            reverse = [(w['offset'], bytes.fromhex(w['after_hex']), bytes.fromhex(w['before_hex']))
                       for w in reversed(components['windows'])]
            plan = program_worker(before['appFw.so'], before['cpapp-b.bin'], reverse, root / 'restore-build', zig)
            expected = boot_sound.patch(before['appFw.so'], reverse)
            trial.run_native(camera, root, state, plan['path'], 'program', 0, plan)
            trial.run_native(camera, root, state, plan['path'], 'program', 1, plan)
            if camera.read('/usr/lib/appFw.so') != expected or camera.read('/cp/cpapp-b.bin') != before['cpapp-b.bin']:
                raise ValueError('Restored AP readback differs; audio files must remain in place')
            state['phase'] = 'boot_hook_restored_removing_audio_files'
            trial.save(root, state)
            invoke_files(camera, root, state, components['files'], 2)
            if any(camera.read(path, True) is not None for path in PATHS):
                raise ValueError('Audio file removal not confirmed')
            check_settings(camera, before)
            if runtime['image_mode'] == '2':
                trial.run_native(camera, root, state, components['wbi'], 'wbi', 1)
            state['phase'] = 'restored_cold_test_pending'
            trial.save(root, state)
    except BaseException:
        state['phase'] = 'needs_review'
        trial.save(root, state)
        raise
    return state


def verify_loaded(root, heard_correct=False, camera_factory=trial.factory):
    root = Path(root)
    state = json.loads((root / 'job.private.json').read_text(encoding='utf-8'))
    if state['phase'] not in ('installed_cold_test_pending', 'loaded_owner_confirmation_pending', 'owner_confirmed_working'):
        raise ValueError('Use a completed installation job after a cold power cycle')
    components = state['components']
    with camera_factory(state['identity']) as camera:
        camera.programs_pinned = True
        loaded = trial.run_native(camera, root, state, components['post_probe'], 'probe')
        candidate.require_registry(loaded)
        selected = loaded['entries'][2]
        if (selected['kind'] != 3 or selected['length'] != Path(components['audio']).stat().st_size
                or selected['filename_prefix'] != '/usr' or not selected['native_handle'] & 0x8000):
            raise ValueError('Loaded kind3 does not show the original file-loader CP lease')
        for path, local in zip(PATHS, (components['audio'], components['csv'])):
            if camera.read(path) != Path(local).read_bytes():
                raise ValueError('Installed private audio files differ')
        state['loaded_code_and_owned_custom_descriptor_verified'] = True
        state['loaded_sound'] = selected
        state['owner_persistent_audio_correct'] = bool(heard_correct)
        state['phase'] = 'owner_confirmed_working' if heard_correct else 'loaded_owner_confirmation_pending'
        trial.save(root, state)
    return state


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('install')
    a.add_argument('--job', type=Path, required=True)
    a.add_argument('--backup-copy', type=Path, required=True)
    a.add_argument('--native-sound-job', type=Path, required=True)
    a.add_argument('--confirmed-audio-job', type=Path, required=True)
    a.add_argument('--native-bin', type=Path, required=True)
    a.add_argument('--battery-percent', type=int, required=True)
    a.add_argument('--zig')
    r = sub.add_parser('restore')
    r.add_argument('--job', type=Path, required=True)
    r.add_argument('--zig')
    s = sub.add_parser('status')
    s.add_argument('--job', type=Path, required=True)
    v = sub.add_parser('verify')
    v.add_argument('--job', type=Path, required=True)
    v.add_argument('--heard-correct', action='store_true', help='Owner confirms correct content, pitch/speed and normal shooting/playback after cold boot')
    args = p.parse_args(argv)
    if args.command == 'install':
        result = install(args.job, args.backup_copy, args.native_sound_job,
            args.confirmed_audio_job, args.native_bin.read_bytes(), args.battery_percent, args.zig)
    elif args.command == 'restore':
        result = restore(args.job, args.zig)
    elif args.command == 'verify':
        result = verify_loaded(args.job, args.heard_correct)
    else:
        result = json.loads((args.job / 'job.private.json').read_text(encoding='utf-8'))
    print(json.dumps({key: result.get(key) for key in
        ('phase', 'camera_firmware_written', 'complete_readback_and_settings_verified')}, indent=2))


if __name__ == '__main__':
    main()
