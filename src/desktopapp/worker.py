"""One job per child process. Full tracebacks stay in the GUI's private log."""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
import uuid
from .paths import ROOT, data_root, write_json


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def setup_runtime():
    sys.path[:0] = [str(ROOT / 'src/looks'), str(ROOT / 'src/camera_runtime'),
                   str(ROOT / 'src/camera_runtime/vendor')]
    os.environ['A7C2_VERBOSE_ERRORS'] = '1'
    os.environ.setdefault('A7LOOK_AUTO_SETTINGS', str(data_root() / 'raw-profiles/settings.json'))
    if getattr(sys, 'frozen', False):
        os.environ['A7C2_DESKTOP_EXECUTABLE'] = sys.executable


def register_backup(path):
    # Backup indexing is a convenience. If its disk is full, preserve the
    # successfully completed camera job and show the indexing error separately.
    try:
        from .recovery import register
        register(path)
    except Exception:
        print('Backup completed, but automatic recovery indexing failed. Select the backup manually.', flush=True)
        traceback.print_exc()


def run(action, args, job):
    setup_runtime()
    from .jobs import POWER_ACTIONS
    if action in POWER_ACTIONS:
        from looktool.power import require_power
        power = require_power(args.get('battery'), confirmed=args.get('power_confirmed', False))
        write_json(job / 'power-confirmation.private.json', power)
        print('Power:', json.dumps(power), flush=True)
    if action in ('driver_scan', 'driver_install', 'driver_uninstall', 'usb_prepare', 'mac_unmount'):
        from . import drivers
        if action == 'driver_scan':
            result = drivers.scan()
            write_json(job / 'driver-report.private.json', result)
            return result
        if action == 'driver_install':
            return drivers.install(args, job)
        if action == 'driver_uninstall':
            return drivers.uninstall(args, job)
        if action == 'usb_prepare':
            return drivers.prepare(job)
        return drivers.unmount_camera_volume(args['volume'])
    if action == 'connect':
        from looktool.devicesession import Camera
        with Camera() as camera:
            return {'model': camera.identity['model'], 'service_connected': True,
                    'firmware_programs_written': False}
    if action.startswith('fl23_'):
        # The tested flexible planner, with PR #5's revised color/curve assets.
        # The PR's original standalone GUI/CLI remains untouched in src/fl23.
        from looktool.devicelock import DeviceLock
        app = module('desktop_fl23', ROOT / 'src/camera_runtime/app.py')
        work = Path(args['workspace'])
        with DeviceLock():
            obj = app.Job(work)
            if action == 'fl23_prepare':
                obj.prepare(Path(args['backup']), args['firmware'])
                register_backup(Path(args['backup']) / 'checkpoint.private.zip')
            elif action == 'fl23_install':
                obj.load()
                obj.install(args.get('battery'), power_confirmed=args.get('power_confirmed', False))
            else:
                obj.verify()
        return {'workspace': str(work), 'phase': obj.state.get('phase')}
    if action == 'backup_inspect':
        from looktool import checkpoint
        manifest, target = checkpoint.load_target(args['backup'])
        return {'model': manifest['model'], 'firmware': manifest['version'],
                'files': len(target), 'legacy_backup': manifest.get('legacy_raw', False),
                'limitations': manifest.get('limitations', []), 'camera_io': False}
    if action == 'restore_auto':
        from .recovery import restore_auto
        return restore_auto(args, job)
    if action in ('restore', 'restore_verify'):
        from looktool.checkpointjob import Rollback
        obj = Rollback(Path(args['workspace']))
        if action == 'restore':
            result = obj.run(args['backup'], args.get('battery'), args['firmware'],
                             power_confirmed=args.get('power_confirmed', False))
        else:
            result = obj.verify(accept_photos=bool(args.get('accepted')))
        return {'workspace': str(obj.root), 'phase': result.get('phase')}
    if action.startswith('look_'):
        from looktool.devicecli import main
        work = str(args['workspace'])
        if action == 'look_prepare':
            argv = ['import', args['look'], '--slot', str(args['slot']),
                    '--name', args['name'], '--work-dir', work,
                    '--backup-dir', args['backup']]
        elif action == 'look_install':
            argv = ['install', work]
            argv += ['--power-confirmed'] if args.get('power_confirmed') else ['--battery-percent', str(args['battery'])]
        elif action == 'look_restore':
            restored_work = str(data_root() / 'work' / ('slot-restore-' + uuid.uuid4().hex[:12]))
            argv = ['restore-slot', work, '--work-dir', restored_work, '--backup-dir', args['backup']]
            argv += ['--power-confirmed'] if args.get('power_confirmed') else ['--battery-percent', str(args['battery'])]
            work = restored_work
        else:
            argv = ['verify', work] + (['--accept-photos'] if args.get('accepted') else [])
        code = main(argv)
        if code:
            raise RuntimeError('A7Look operation stopped; see the complete backend log above.')
        state = json.loads((Path(work) / 'job.private.json').read_text(encoding='utf-8'))
        if action == 'look_prepare' and state.get('initial_checkpoint'):
            register_backup(state['initial_checkpoint'])
        return {'workspace': work, 'phase': state['phase']}
    if action == 'compile_look':
        from looktool.compilelook import main
        argv = [args['source'], '--name', args['name'], '--output', args['output'],
                '--calibration', args['model'], '--passes', str(args.get('passes', 3))]
        if Path(args['source']).suffix.lower() == '.cube':
            argv += ['--input-space', args.get('input_space', 'sony-st-srgb')]
            if args.get('bridge'):
                argv += ['--bridge', args['bridge']]
        elif args.get('renderer_config'):
            argv += ['--config', args['renderer_config']]
        code = main(argv)
        if code:
            raise RuntimeError('A7Look conversion did not complete')
        return {'output': args['output'], 'exit_code': code}
    if action == 'plugin_install':
        from .plugins import install
        return install(args)
    if action.startswith('vertical_'):
        sys.path.insert(0, str(ROOT / 'src/vertical'))
        from verticaltool.device import execute
        return execute(action.removeprefix('vertical_'), Path(args['workspace']))
    if action.startswith('sound_'):
        sys.path.insert(0, str(ROOT / 'dev/shutter_sound'))
        from sound_cli import main
        command = action.removeprefix('sound_').replace('_', '-')
        argv = [command]
        if command == 'import':
            argv += [args['source'], '--start', str(args.get('start', 0)),
                     '--duration', str(args.get('duration', .15)),
                     '--peak', str(args.get('peak', .4))]
        argv += ['--workspace', args['workspace']]
        if command == 'on':
            argv += ['--backup-copy', args['backup'], '--firmware', args['firmware']]
        if command in ('on', 'install'):
            argv += ['--power-confirmed'] if args.get('power_confirmed') else ['--battery-percent', str(args['battery'])]
        elif command == 'confirm':
            argv += ['--result', args.get('result', 'correct')]
        elif command == 'verify' and args.get('accepted'):
            argv += ['--heard-correct']
        code = main(argv)
        if code:
            raise RuntimeError('Sound operation stopped; see the complete backend log above.')
        return {'workspace': args['workspace'], 'command': command, 'exit_code': code}
    raise ValueError('Unknown desktop action: ' + action)


def execute_request(path):
    request = json.loads(Path(path).read_text(encoding='utf-8'))
    job = Path(request['job_dir'])
    status = job / 'status.private.json'
    write_json(status, {'phase': 'RUNNING', 'action': request['action'], 'pid': os.getpid()})
    with (job / 'worker.log').open('a', encoding='utf-8', buffering=1) as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            print('Action:', request['action'], flush=True)
            try:
                result = run(request['action'], request['arguments'], job)
                write_json(job / 'result.private.json', result)
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str), flush=True)
                write_json(status, {'phase': 'SUCCEEDED', 'action': request['action'], 'result': result})
                return 0
            except BaseException as exc:
                traceback.print_exc()
                write_json(status, {'phase': 'FAILED', 'action': request['action'],
                                    'error_type': type(exc).__name__, 'error': str(exc),
                                    'log': str(job / 'worker.log')})
                return 2
