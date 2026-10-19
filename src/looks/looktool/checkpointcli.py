"""Full original checkpoint operations shared by FL23 and LUT."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import uuid
from . import checkpoint

COMMANDS={'rollback','rollback-verify','upgrade-checkpoint','inspect-checkpoint'}

def main(argv):
    action=argv[0];p=argparse.ArgumentParser(prog='lut.py '+action)
    if action=='upgrade-checkpoint':
        p.add_argument('backup2',type=Path);p.add_argument('--fl23-workspace',required=True,type=Path)
        p.add_argument('--first-lut-job',required=True,type=Path);p.add_argument('--output',type=Path,required=True)
        a=p.parse_args(argv[1:]);manifest=checkpoint.upgrade_legacy(a.backup2,a.fl23_workspace,a.first_lut_job,a.output)
        print('Created:',a.output,'\nLimitations:',*manifest['limitations'],sep='\n');return 0
    if action=='inspect-checkpoint':
        p.add_argument('backup2',type=Path);a=p.parse_args(argv[1:]);manifest,_=checkpoint.read(a.backup2)
        # Do not print body IDs or private provenance paths to public logs.
        print(json.dumps({k:manifest[k] for k in ('schema','model','version','scope','limitations')},indent=2));return 0
    from .checkpointjob import Rollback
    if action=='rollback':
        p.add_argument('backup2',type=Path);p.add_argument('--battery-percent',type=int,required=True)
        p.add_argument('--firmware-version',required=True);p.add_argument('--work-dir',type=Path);p.add_argument('--zig')
        a=p.parse_args(argv[1:])
        folder=a.work_dir or Path.home()/'.a7c2-lut/rollbacks'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
        print('Rollback work:',folder,flush=True)
        state=Rollback(folder,zig=a.zig).run(a.backup2,a.battery_percent,a.firmware_version)
    else:
        p.add_argument('work',type=Path);p.add_argument('--accept-photos',action='store_true')
        a=p.parse_args(argv[1:]);state=Rollback(a.work).verify(a.accept_photos)
    print('Rollback:',state['phase']);return 0
