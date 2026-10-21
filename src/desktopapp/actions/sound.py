"""Shared sound CLI adapter; conversion/volume remain host-only actions."""
import sys
from ..paths import ROOT

def run(action,args):
    sys.path.insert(0, str(ROOT / 'src/shutter_sound'))
    from sound_cli import main
    command = action.removeprefix('sound_').replace('_', '-')
    argv = [command]
    if command == 'import':
        argv += [args['source'], '--start', str(args.get('start', 0)),
                 '--duration', str(args.get('duration', .15)),
                 '--peak', str(args.get('peak', .4))]
    elif command == 'volume':
        argv += ['--reset'] if args.get('reset') else ['--decibels',str(args['decibels'])]
    elif command=='compile-install':
        argv += ['--ap',args['ap'],'--cp',args['cp'],'--native-bin',args['native_bin']]
    argv += ['--workspace', args['workspace']]
    if command in ('on','install','audition') and args.get('backup'):
        argv += ['--backup-copy',args['backup']]
    if command == 'on':
        argv += ['--firmware', args['firmware']]
    if command in ('on', 'install'):
        argv += ['--power-confirmed'] if args.get('power_confirmed') else ['--battery-percent', str(args['battery'])]
    elif command == 'confirm':
        argv += ['--result', args.get('result', 'correct')]
    elif command == 'verify' and args.get('accepted'):
        argv += ['--heard-correct']
    outcome = {}
    code = main(argv, report=outcome.update)
    if code:
        raise RuntimeError('Sound operation stopped; see the complete backend log above.')
    return dict(outcome, workspace=args['workspace'], command=command, exit_code=code)
