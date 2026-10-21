"""Private job files, complete exception logs and support-bundle export."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import platform
import sys
import uuid
import zipfile
from .paths import data_root, write_json
from . import VERSION

CAMERA_ACTIONS = {'connect', 'usb_prepare', 'driver_uninstall', 'fl23_prepare', 'fl23_install', 'fl23_verify',
                  'restore', 'restore_auto', 'restore_verify', 'look_prepare', 'look_install',
                  'look_verify', 'look_restore', 'vertical_enable', 'vertical_disable',
                  'vertical_status', 'vertical_remove', 'sound_on', 'sound_off',
                  'sound_audition', 'sound_install', 'sound_verify', 'sound_restore_sound'}

POWER_ACTIONS = {'restore', 'restore_auto', 'fl23_install', 'look_install', 'look_restore',
                 'vertical_enable', 'vertical_disable', 'vertical_remove',
                 'sound_on', 'sound_off', 'sound_audition', 'sound_install', 'sound_restore_sound'}
DIRECT_ACTIONS = {'direct_fl23_enable', 'direct_fl23_disable', 'direct_vertical_enable', 'direct_vertical_disable', 'direct_slot_default',
                  'direct_look_import', 'direct_looks_import', 'direct_resume_looks', 'direct_factory_reset', 'direct_resume_factory', 'direct_install_all'}
POWER_ACTIONS |= DIRECT_ACTIONS
CAMERA_ACTIONS |= DIRECT_ACTIONS | {'direct_verify'}
POWER_ACTIONS.add('setup_all')
CAMERA_ACTIONS.add('setup_all')
CAMERA_ACTIONS.add('review_failed_names')


def new_job(action, arguments):
    root = data_root() / 'runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                                 + '-' + action + '-' + uuid.uuid4().hex[:6])
    root.mkdir(parents=True)
    request = {'schema': 'a7c2-desktop-job/1', 'action': action, 'arguments': arguments,
               'job_dir': str(root), 'version': VERSION}
    write_json(root / 'request.private.json', request)
    write_json(root / 'status.private.json', {'phase': 'QUEUED', 'action': action})
    return root


def worker_command(request):
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--worker', str(request)]
    from .paths import ROOT
    return [sys.executable, '-u', str(ROOT / 'desktop.py'), '--worker', str(request)]


def transaction_summaries(job):
    """Include original failure stages, never program/settings snapshots."""
    request_path=Path(job)/'request.private.json'
    if not request_path.is_file():return {}
    request=json.loads(request_path.read_text(encoding='utf-8'))
    folder=request.get('arguments',{}).get('workspace')
    if not folder:return {}
    root=Path(folder);result={};children=[root]
    fields=('schema','phase','mode','failed_during','error','error_type','completed_steps',
            'install_workspace','failed_install_workspaces','names_cleanup_pending',
            'readonly_after_reload_verified','physical_checks_accepted')
    setup=root/'setup.private.json'
    if setup.is_file():
        state=json.loads(setup.read_text(encoding='utf-8'))
        result['setup-summary.json']={k:state[k] for k in fields if k in state}
        children=[Path(state.get('install_workspace') or root/'install')]
        children.extend(Path(p) for p in state.get('failed_install_workspaces',[])[-5:])
    for i,child in enumerate(dict.fromkeys(children)):
        path=child/'direct.private.json'
        if not path.is_file():continue
        state=json.loads(path.read_text(encoding='utf-8'))
        summary={k:state[k] for k in fields if k in state}
        summary['journal']=[]
        for event in state.get('journal',[]):
            row={k:event[k] for k in ('event','stage','mode') if k in event}
            if isinstance(event.get('result'),dict):
                row['result']={k:event['result'][k] for k in ('phase','status','windows','mode',
                    'staged','linked','committed','restored','rollback','remount','readonly','cleanup') if k in event['result']}
            summary['journal'].append(row)
        result['direct-summary-%d.json'%i]=summary
    return result


def export_support(job, destination):
    """Export diagnostic text only; never programs, sensor calibration or photos."""
    job = Path(job)
    summary = {'app_version': VERSION, 'platform': platform.platform(),
               'python': sys.version, 'camera_binaries_included': False,
               'contains_local_paths': True}
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('environment.json', json.dumps(summary, indent=2))
        for name in ['request.private.json', 'status.private.json', 'worker.log',
                     'process.log', 'result.private.json', 'driver-report.private.json',
                     'authorization.private.json','authorization.stdout.log','authorization.stderr.log',
                     'privilege.private.json']:
            path = job / name
            if path.is_file():
                archive.write(path, 'diagnostics/' + name)
        try:
            for name,value in transaction_summaries(job).items():
                archive.writestr('diagnostics/transactions/'+name,json.dumps(value,ensure_ascii=False,indent=2))
        except (OSError,ValueError,TypeError) as exc:
            archive.writestr('diagnostics/transactions/read-error.txt',str(exc))
        # SetupAPI is particularly useful for driver installation failures.
        setupapi = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'INF/setupapi.dev.log'
        if sys.platform == 'win32' and setupapi.exists():
            with setupapi.open('rb') as stream:
                stream.seek(max(0, setupapi.stat().st_size - 512000))
                archive.writestr('diagnostics/setupapi-tail.log', stream.read())
    return str(destination)
