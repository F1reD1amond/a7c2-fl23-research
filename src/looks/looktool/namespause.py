"""A completed name transaction may need a cold boot before program writes.

No broad EBUSY bypass: verify all names and original program windows first.
The program installer retains its read-only mount prerequisite.
"""
import json,re,struct
from pathlib import Path
from . import bundle,checkpoint,nameworker,resources,lookfile

WAIT='AWAITING_RESOURCE_RELOAD'


def source(folder):
    root=Path(folder).resolve();state=json.loads((root/'direct.private.json').read_text(encoding='utf-8'))
    if state.get('mode') not in ('install_all','look_import') or state.get('phase') not in ('NEEDS_REVIEW',WAIT,'RESOURCE_RELOAD_VERIFIED'):
        raise ValueError('Not a completed-name reload checkpoint')
    build=state.get('forward_name_build')
    if not build or state.get('inverse_name_build'):raise ValueError('No completed forward name transaction')
    if {s['file'] for s in build['files']}!=set(nameworker.filenames()):raise ValueError('Name inventory differs')
    if any(e.get('event')=='native_intent' and e.get('result')=='checkpoint.program.result' and e.get('mode')==1 for e in state['journal']):
        raise ValueError('Program writes have started; not a name-only checkpoint')
    paths=list((root/'evidence').glob('*-names-forward-1.bin'))
    if len(paths)!=1 or not nameworker.completed_mount_busy(paths[0].read_bytes(),1,build):
        raise ValueError('Names/cleanup/mount outcome is not fully accounted for')
    if state['phase']=='NEEDS_REVIEW':
        if not state['journal']:raise ValueError('No completed operation report to continue')
        last=state['journal'][-1]
        if last.get('event')!='native_intent' or last.get('result')!='a7c2.names.result' or last.get('mode')!=1:
            raise ValueError('Unknown operation after name commit')
    return root,state,paths[0].read_bytes()


def verify_files(camera,root,state):
    print('正在读取原程序，核对尚未写入的程序窗口。',flush=True)
    images={n:camera.read(p) for n,p in checkpoint.PROGRAM_PATHS.items()}
    anchor=Path(state.get('program_source_workspace') or root).resolve()
    for build in state['program_builds']:
        path=Path(build['path'])
        if path.parent.resolve()!=anchor/'worker':raise ValueError('Program evidence outside checkpoint')
        text=path.with_suffix('.private.h').read_text(encoding='ascii')
        arrays={int(i):bytes(map(int,v.split(','))) for i,v in re.findall(r'static const u8 old_(\d+)\[\]=\{([\d,]+)\};',text)}
        rows=re.findall(r'\{(\d+)UL,(\d+),([01]),old_(\d+),new_(\d+)\}',text)
        if len(rows)!=build['windows']:raise ValueError('Incomplete original program evidence')
        for at,size,chip,old,new in rows:
            expected=arrays[int(old)];raw=images['cpapp-b.bin' if chip=='1' else 'appFw.so']
            if len(expected)!=int(size) or raw[int(at):int(at)+int(size)]!=expected:
                raise ValueError('Current program differs; no automatic replay')
    if state['mode']=='install_all':
        _,rows=bundle.documents(state['bundle_options']);titles={r['slot']:r['name'] for r in rows}
    else:
        doc=lookfile.read(root/'reference.a7look');titles={state['slot']:state.get('name') or doc['name']}
    build=state['forward_name_build']
    header=Path(build['path']).with_name('names.private.h').read_text(encoding='ascii')
    match=re.search(r'static const u32 label_ids\[\]=\{([^}]+)\};',header)
    if not match:raise ValueError('Missing name layout evidence')
    ids=tuple(int(v.strip().rstrip('U')) for v in match[1].split(','))
    for index,spec in enumerate(build['files'],1):
        raw=camera.read('/usr/share/app/'+spec['file'])
        original=resources.inverse(raw,spec['inverse'])
        expected,_=resources.rename(original,titles,ids)
        if raw!=expected:raise ValueError('Complete name readback differs: '+spec['file'])
        if index%16==0 or index==len(build['files']):print('名称完整读回：%d/%d'%(index,len(build['files'])),flush=True)
    camera.programs_pinned=True
    return images


def cleanup(camera,state,raw):
    build=state['forward_name_build']
    expected={'lut-names-staged.so':Path(build['path']).read_bytes(),
              'a7c2.names.request':struct.pack('<8sII',b'A7NAM001',1,0),'a7c2.names.result':raw}
    for name in ('libJit.so','checkpoint.staged.so','checkpoint.program.request','checkpoint.program.result',
                 'a7c2.wbi.request','a7c2.wbi.result'):
        if camera.temp_read(name,True) is not None:raise ValueError('Unaccounted temporary state: '+name)
    for name,data in expected.items():
        value=camera.temp_read(name,True)
        if value is not None and value!=data:raise ValueError('Unexpected temporary bytes: '+name)
    for name in expected:
        if camera.temp_read(name,True) is not None:camera.temp_remove(name)
        if camera.temp_read(name,True) is not None:raise ValueError('Temporary cleanup incomplete: '+name)
