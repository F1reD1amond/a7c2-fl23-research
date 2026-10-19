"""Self-contained initial project checkpoints. No firmware fingerprint admission.

Archives are private: they contain the owner's programs and body settings.
ZIP CRC detects damaged storage; firmware verification uses direct bytes.
"""
import json
import os
from pathlib import Path
import shutil
import struct
from zipfile import ZipFile, ZIP_DEFLATED
from . import nameworker, resources

PROGRAM_PATHS={'appFw.so':'/usr/lib/appFw.so','cpapp-b.bin':'/cp/cpapp-b.bin'}
CP_KEYS=(0x02a40001,0x02a4000d)
AP_KEYS=(0x02cf1287,0x02cf1289)
SCHEMA='a7c2-initial-checkpoint/1'

def inventory():
    return set(PROGRAM_PATHS)|{'settings-ram.bin','settings-saved.bin'}|{'resources/'+n for n in nameworker.filenames()}

def same_body(a,b):
    if a.get('model')!='ILCE-7CM2' or b.get('model')!='ILCE-7CM2':
        raise ValueError('Checkpoint is only for ILCE-7CM2')
    common=[k for k in ('serial_sha256','usb_serial_sha256') if a.get(k) and b.get(k)]
    if not common or any(a[k]!=b[k] for k in common):
        raise ValueError('Checkpoint belongs to a different body, or body identity is missing')

def archive_path(path):
    path=Path(path)
    return path/'checkpoint.private.zip' if path.is_dir() else path

def write(path,values,identity,*,provenance,limitations=()):
    path=Path(path)
    if path.exists():raise ValueError('Preserve the existing initial checkpoint: '+str(path))
    if set(values)!=inventory():raise ValueError('Checkpoint needs both programs, saved/live settings and all 68 resources')
    same_body(identity,identity)
    manifest={'schema':SCHEMA,'model':'ILCE-7CM2','version':'2.01','identity':identity,
        'provenance':provenance,'limitations':list(limitations),
        'scope':'AP/CP programs, 68 name resources, FL23 bindings/color units, six custom-look recipes; not a full camera filesystem or calibration reset',
        'files':sorted(values)}
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.new')
    with temporary.open('xb') as stream:
        with ZipFile(stream,'w',compression=ZIP_DEFLATED,compresslevel=6) as archive:
            archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
            for name in sorted(values):archive.writestr(name,values[name])
        stream.flush();os.fsync(stream.fileno())
    # Read compressed data once before publishing the original point.
    _,actual=read(temporary)
    if actual!=values:raise ValueError('Checkpoint storage readback differs')
    os.replace(temporary,path)
    return manifest

def read(path):
    path=archive_path(path)
    with ZipFile(path) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('schema')!=SCHEMA or manifest.get('version')!='2.01':raise ValueError('Unsupported checkpoint format/version')
        expected=inventory()
        if set(manifest['files'])!=expected or set(archive.namelist())!=expected|{'manifest.json'}:
            raise ValueError('Incomplete checkpoint; legacy backup2 needs upgrade-checkpoint first')
        same_body(manifest['identity'],manifest['identity'])
        values={name:archive.read(name) for name in expected}
    return manifest,values

def copy(path,destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Preserve the existing checkpoint copy')
    shutil.copyfile(path,destination)
    # The ZIP reader checks storage CRC, without a separate SHA inventory.
    read(destination)

def capture(session,programs,ram,saved):
    values=dict(programs,**{'settings-ram.bin':ram,'settings-saved.bin':saved})
    for filename in nameworker.filenames():
        values['resources/'+filename]=session.read('/tmp/jiritsu/../../usr/share/app/'+filename)
    return values

def upgrade_legacy(backup2,workspace,first_lut,output):
    """Supplement old FL23 backup2; never overwrite the originals."""
    from .devicejob import Job
    from .devicesession import modules
    _,core=modules()
    backup2,workspace=Path(backup2),Path(workspace)
    state=json.loads((workspace/'state.json').read_text(encoding='utf-8'))
    if state.get('version')!='2.01':raise ValueError('Legacy workspace version differs')
    job=Job(first_lut)
    job.state=json.loads(job.state_path.read_text(encoding='utf-8'))
    same_body(state['identity'],job.state['identity'])
    values={}
    for name in PROGRAM_PATHS:
        raw=(backup2/(name+'.bin')).read_bytes()
        if raw!=(workspace/'original'/(name+'.bin')).read_bytes():raise ValueError('Selected backup2 and FL23 workspace differ: '+name)
        values[name]=raw
    ram=(backup2/'backup.private.bin').read_bytes()
    if ram!=(workspace/'original/backup.private.bin').read_bytes():raise ValueError('Selected backup2 settings and workspace differ')
    # FL23 never changes name resources. Require a pre-custom source to avoid
    # silently taking titles from a later LUT task.
    for name in nameworker.filenames():
        raw=job.source('resources/'+name)
        if resources.decode(raw)['count']!=2860:raise ValueError('Use the earliest pre-custom LUT job for original name resources')
        values['resources/'+name]=raw
    core.backup_records(ram)
    values.update({'settings-ram.bin':ram,'settings-saved.bin':ram})
    limitations=['Legacy FL23 did not save a separate flash settings snapshot. Look recipes use the original RAM snapshot; original unsaved/flash differences cannot be recovered.']
    identity=dict(state['identity'])
    if job.state['identity'].get('usb_serial_sha256'):identity['usb_serial_sha256']=job.state['identity']['usb_serial_sha256']
    return write(output,values,identity,provenance={'type':'legacy-backup2-plus-pre-custom-names',
        'backup2':str(backup2.resolve()),'workspace':str(workspace.resolve()),'names_job':str(Path(first_lut).resolve())},limitations=limitations)

def recipe_keys(ap):
    keys=list(AP_KEYS)
    for slot in range(1,7):
        selector=slot+9
        for attribute in [0x14ea+selector]+[0x1520+i*18+selector for i in range(8)]:
            row=struct.unpack_from('<8I',ap,0x57c6710+(attribute-0x14ea)*32)
            if row[6]!=attribute or row[1]>>16!=0x02cf:raise ValueError('Archived custom-look descriptor differs')
            keys.append(row[1])
    if len(set(keys))!=56:raise ValueError('Overlapping look descriptors')
    return keys

def name_inverse(before,after):
    """Plan current append-only project resources back to the archive."""
    old,new=resources.decode(before),resources.decode(after)
    plan={'before_bytes':len(before),'after_bytes':len(after),'before_count':old['count'],'changes':[
        {'index_offset':16+2*((rid&0xffffff)-0xa000),
         'before_pointer':old['entries'].get(rid,{}).get('pointer',65535),
         'after_pointer':new['entries'].get(rid,{}).get('pointer',65535)} for rid in resources.LABEL_IDS]}
    if resources.inverse(after,plan)!=before:
        raise ValueError('Names cannot be reconstructed to this checkpoint; no camera write performed')
    return plan
