"""Execute the actual portrait file worker under ARM64 syscall emulation."""
from pathlib import Path
import struct
import sys

import pytest
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_INTR
from unicorn.arm64_const import *

sys.path.insert(0,str(Path(__file__).parent))
from test_portrait import fixtures
from verticaltool import portrait

SRC=[f'/usr/share/app/image_{i:02d}_32_IPSX.uxc' for i in range(3)]
DST=[f'/usr/share/app/image_{i:02d}_23_IPSX.uxc' for i in range(3)]
BASE=0x7f00000000


@pytest.fixture(scope='module')
def compiled(tmp_path_factory):
    originals=fixtures();targets,path=portrait.build(originals,tmp_path_factory.mktemp('portrait-native'))
    return originals,targets,path


def execute(compiled,mode,existing='none',fault=None):
    originals,targets,path=compiled
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x10000000,0x400000)
    with path.open('rb') as stream:
        elf=ELFFile(stream)
        for s in elf.iter_segments():
            if s['p_type']=='PT_LOAD':u.mem_write(0x10000000+s['p_vaddr'],s.data())
        for r in elf.get_section_by_name('.rela.dyn').iter_relocations():
            assert r['r_info_type']==1027
            u.mem_write(0x10000000+r['r_offset'],struct.pack('<Q',0x10000000+r['r_addend']))
        init=next(t.entry.d_val for t in elf.get_section_by_name('.dynamic').iter_tags() if t.entry.d_tag=='DT_INIT')
    u.mem_map(0x60000000,0x100000);u.mem_map(0x70000000,4096)
    u.reg_write(UC_ARM64_REG_SP,0x600f0000);u.reg_write(UC_ARM64_REG_X30,0x70000000)
    u.reg_write(UC_ARM64_REG_CPACR_EL1,0x300000)
    files={p:bytearray(v) for p,v in zip(SRC,originals)}
    files.update({'/proc/self/maps':(f'{BASE:x}-{BASE+0x51a7000:x} r-xp 00000000 00:01 12 /usr/lib/appFw.so\n'+
        f'{BASE+0x51b7000:x}-{BASE+0x9900000:x} rw-p 051a7000 00:01 12 /usr/lib/appFw.so\n').encode(),
        '/proc/self/cmdline':b'/usr/bin/app\0','/tmp/jiritsu/libJit.so':b'own',
        '/tmp/jiritsu/a7c2.names.request':struct.pack('<8sII',b'A7VRS001',mode,0)})
    links={}
    if existing=='legacy':links={p:Path(SRC[i]).name for i,p in enumerate(DST)}
    if existing=='correct':
        files.update({p:bytearray(targets[i]) for i,p in enumerate(DST[:2])});links[DST[2]]=Path(SRC[2]).name
    if existing=='foreign':files[DST[0]]=bytearray(b'foreign')
    if existing=='partial_temp':files['/usr/share/app/.a7c2-portrait-00.tmp']=bytearray(targets[0][:5000])
    before={p:bytes(v) for p,v in files.items() if p in SRC or p in DST};before_links=dict(links)
    handles={};state={'ro':True,'interrupted':False};audit=[]
    def text(addr):
        result=bytearray()
        while True:
            c=bytes(u.mem_read(addr+len(result),1))
            if c==b'\0':return result.decode()
            result+=c
    def canonical(p):return '/usr/share/app/'+links[p] if p in links else p
    def syscall(cpu,_num,_user):
        no=cpu.reg_read(UC_ARM64_REG_X8)
        a=[cpu.reg_read(x) for x in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4)]
        r=0
        if no in (172,175):r=47 if no==172 else 0
        elif no==56:
            p=text(a[1]);flags=a[2]
            if flags&0x20000 and p in links:r=-40
            elif flags&0x40:
                if flags&0x80 and p in files:r=-17
                else:files[p]=bytearray()
            elif p not in files and p not in links and p not in ('/usr/share/app','/proc/self/mem','/proc/mounts'):r=-2
            if not r:r=max([9,*handles])+1;handles[r]=[p,canonical(p),0]
        elif no==57:pass
        elif no==35:
            p=text(a[1]);audit.append(('unlink',p))
            if p in links:del links[p]
            elif p in files:del files[p]
            else:r=-2
        elif no==36:
            p=text(a[2]);audit.append(('link',p))
            if p in files or p in links:r=-17
            else:links[p]=text(a[0])
        elif no==38:
            old,new=text(a[1]),text(a[3]);audit.append(('rename',new))
            if fault=='rename' and new==DST[1]:r=-5
            else:files[new]=files.pop(old);links.pop(new,None)
        elif no==78:
            p=text(a[1])
            if p in links:
                raw=links[p].encode();cpu.mem_write(a[2],raw);r=len(raw)
            else:r=-22 if p in files else -2
        elif no==40:state['ro']=bool(a[3]&1);audit.append(('mount',state['ro']))
        elif no==43:
            free=1 if fault=='capacity' else 50000
            raw=struct.pack('<qq5Q2I7q',0xef53,4096,100000,free,free,1000,999,0,0,255,4096,0,0,0,0,0)
            cpu.mem_write(a[1],raw)
        elif no in (63,67):
            p,actual,at=handles[a[0]]
            if no==67:at=a[3]
            if actual=='/proc/self/mem':raw=struct.pack('<I',16)
            elif actual=='/proc/mounts':raw=('/dev/nflasha15 /usr ext2 '+('ro' if state['ro'] else 'rw')+',nosuid,nodev 0 0\n').encode()[at:at+a[2]]
            else:raw=bytes(files[actual][at:at+a[2]])
            if fault=='shortread' and len(raw)>128:raw=raw[:len(raw)//2]
            if fault=='eintr_read' and actual in SRC and a[2]>128 and not state['interrupted']:
                state['interrupted']=True;cpu.reg_write(UC_ARM64_REG_X0,(-4)&((1<<64)-1));return
            if raw:cpu.mem_write(a[1],raw)
            r=len(raw)
            if no==63:handles[a[0]][2]+=r
        elif no==80:
            p,actual,_=handles[a[0]];size=len(files[actual]);ino=SRC.index(actual)+100 if actual in SRC else 200
            cpu.mem_write(a[1],struct.pack('<QQIIIIQQqIIQ7Q',99,ino,0o100644,1,57285,1000,0,0,size,4096,0,1,*([0]*7)))
        elif no==64:
            p=handles[a[0]][1]
            if fault=='space' and p.endswith('.tmp'):r=-28
            elif fault=='eintr_write' and p.endswith('.tmp') and not state['interrupted']:
                state['interrupted']=True;r=-4
            else:
                count=max(1,a[2]//2) if fault=='shortwrite' and p.endswith('.tmp') else a[2]
                files[p].extend(cpu.mem_read(a[1],count));r=count
        elif no in (52,55):pass
        elif no==82:
            p=handles[a[0]][0]
            if fault=='sync' and p.endswith('.tmp'):r=-5
        else:raise AssertionError('Unexpected syscall '+str(no))
        cpu.reg_write(UC_ARM64_REG_X0,r&((1<<64)-1))
    u.hook_add(UC_HOOK_INTR,syscall)
    u.emu_start(0x10000000+init,0x70000000,count=15000000)
    assert u.reg_read(UC_ARM64_REG_PC)==0x70000000
    report=bytes(files['/tmp/jiritsu/a7c2.names.result'])
    result=struct.unpack_from('<8sIIIIqqqIIII3II3Q',report)
    assert result[1]==2 and len(report)==128
    assert all(bytes(files[p])==v for p,v in zip(SRC,originals))
    assert state['ro']
    if fault not in (None,'shortread','shortwrite','eintr_read','eintr_write') or existing=='foreign':
        assert result[5]!=0
        if fault in ('space','capacity'):assert result[5]==-28
        assert {p:bytes(v) for p,v in files.items() if p in SRC or p in DST}==before
        assert links==before_links
        assert not any(p.endswith('.tmp') for p in files)
    elif mode==1:
        assert result[5]==0
        assert all(bytes(files[canonical(p)])==v for p,v in zip(DST,targets))
    elif mode==2:
        assert result[5]==0 and not any(p in files or p in links for p in DST)
    else:
        assert result[5]==0 and not any(a[0] in ('rename','unlink','mount') and
            not (a[0]=='unlink' and a[1]=='/tmp/jiritsu/libJit.so') for a in audit)


@pytest.mark.parametrize('mode,existing',[(0,'none'),(0,'legacy'),(0,'correct'),(1,'none'),(1,'legacy'),
    (1,'correct'),(1,'partial_temp'),(2,'legacy'),(2,'correct'),(2,'none'),(0,'foreign'),(1,'foreign'),(2,'foreign')])
def test_native_resource_transactions(compiled,mode,existing):execute(compiled,mode,existing)


@pytest.mark.parametrize('existing',['none','legacy'])
@pytest.mark.parametrize('fault',['space','sync','rename'])
def test_native_failure_rolls_back_without_touching_landscape(compiled,existing,fault):execute(compiled,1,existing,fault)


@pytest.mark.parametrize('fault',['shortread','shortwrite','eintr_read','eintr_write'])
def test_short_or_interrupted_syscalls_complete_instead_of_becoming_eio(compiled,fault):execute(compiled,1,'legacy',fault)


def test_capacity_error_is_reported_before_bulk_copy(compiled):execute(compiled,1,'legacy','capacity')
