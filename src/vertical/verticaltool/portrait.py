"""Derive portrait line banks from this body's landscape files, offline.

Only existing frame/scale records are redirected to generated portrait pixels.
The original image bank and every resource index stay unchanged.
"""
import json
from pathlib import Path
import struct

ASSETS=Path(__file__).resolve().parents[1]/'assets'


def compress(raw):
    """Sony LZ77 blocks, with at most 16 KiB decoded per block."""
    result=bytearray();lengths=list(range(3,17))+[32,64]
    for base in range(0,len(raw),16384):
        data=raw[base:base+16384];out=bytearray(b'\xf0');history={};at=0;tokens=[]
        while at<len(data):
            key=data[at:at+3];prior=history.get(key);size=0
            if len(key)==3 and prior is not None and at-prior<=4095:
                limit=min(64,len(data)-at);matched=0
                while matched<limit and data[prior+matched]==data[at+matched]:matched+=1
                candidates=[n for n in lengths if n<=matched]
                if candidates:size=candidates[-1]
            if size:
                distance=at-prior
                tokens.append((1,bytes([(lengths.index(size)<<4)|(distance>>8),distance&255])))
            else:size=1;tokens.append((0,data[at:at+1]))
            for k in range(at,at+size):history[data[k:k+3]]=k
            at+=size
        tokens.append((1,b'\0\0'))
        for start in range(0,len(tokens),8):
            group=tokens[start:start+8];out.append(sum(flag<<i for i,(flag,_) in enumerate(group)))
            for _,payload in group:out.extend(payload)
        result.extend(out)
    return bytes(result)


def raster(spec):
    w,h=spec['portrait'];stride=(w+15)&~15
    if not 1<=w<=640 or not 1<=h<=640:raise ValueError('Invalid portrait geometry')
    pixels=bytearray(stride*h*2)
    for x,y,width,height,color in spec['rectangles']:
        if not (0<=x<x+width<=w and 0<=y<y+height<=h and 0<=color<=65535):
            raise ValueError('Portrait rectangle outside its image')
        row=struct.pack('<H',color)*width
        for line in range(y,y+height):pixels[(line*stride+x)*2:(line*stride+x+width)*2]=row
    return bytes(pixels)


def bank(source,group,specs=None):
    if specs is None:specs=json.loads((ASSETS/'portrait-lines-v1.json').read_text())['assets']
    if len(source)<20 or source[:8]!=b'uxd\x07\0\0\0\0':raise ValueError('Unsupported image bank')
    version,actual,descriptor=struct.unpack_from('<HHI',source,8);count=descriptor&8191
    if version!=8 or actual!=group or descriptor!=(count|(((count+1)&~1)<<12)):
        raise ValueError('Unsupported image bank layout')
    base=16+((descriptor>>11)&0x7ffc);target=bytearray(source);edits=[]
    for spec in specs:
        if spec['group']!=group:continue
        index=spec['index']
        if index>=count:raise ValueError('Missing portrait line resource')
        pointer=struct.unpack_from('<H',source,16+2*index)[0]
        if pointer==65535:raise ValueError('Missing portrait line resource')
        at=base+4*pointer
        if at+20>len(source):raise ValueError('Image record outside bank')
        rid,flags,w,h,length,offset=struct.unpack_from('<IIHHII',source,at)
        if rid!=0x1a000000+group*8192+index or flags!=0xc0000000 or [w,h]!=spec['landscape']:
            raise ValueError('Portrait line source geometry differs: '+hex(rid))
        if not 0<=at+4+offset<=at+4+offset+length<=len(source):raise ValueError('Image payload outside bank')
        payload=compress(raster(spec))
        target.extend(bytes((-len(target))%4));payload_at=len(target);target.extend(payload)
        new=struct.pack('<HHII',*spec['portrait'],len(payload),payload_at-at-4)
        old=source[at+8:at+20];target[at+8:at+20]=new
        edits.append((at+8,old,new))
    return bytes(target),edits


def build(originals,folder):
    from looktool.nativebuild import compile_worker,ROOT
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    targets=[];lines=['#define PORTRAIT_GEOMETRY 1',
        'struct PortraitEdit {u64 at;const u8 *old,*value;};']
    for group,source in enumerate(originals):
        target,edits=bank(source,group);targets.append(target)
        for n,(at,old,new) in enumerate(edits):
            for label,raw in [('old',old),('new',new)]:
                lines.append(f'static const u8 {label}_{group}_{n}[]='+cbytes(raw)+';')
        rows=[f'{{{at}UL,old_{group}_{n},new_{group}_{n}}}' for n,(at,_,_) in enumerate(edits)]
        lines.append(f'static const struct PortraitEdit edits_{group}[]='+'{'+(','.join(rows) or '{0,0,0}')+'};')
        lines.append(f'static const u8 tail_{group}[]='+cbytes(target[len(source):] or b'\0')+';')
    lines.extend([
        'static const u64 portrait_source_sizes[]={'+','.join(str(len(x))+'UL' for x in originals)+'};',
        'static const u64 portrait_tail_sizes[]={'+','.join(str(len(b)-len(a))+'UL' for a,b in zip(originals,targets))+'};',
        'static const u32 portrait_edit_counts[]={'+','.join(str(len(bank(x,i)[1])) for i,x in enumerate(originals))+'};',
        'static const struct PortraitEdit *portrait_edits[]={edits_0,edits_1,edits_2};',
        'static const u8 *portrait_tails[]={tail_0,tail_1,tail_2};'])
    header=folder/'portrait.private.h';header.write_text('\n'.join(lines),encoding='ascii')
    path=folder/'portrait.so'
    compile_worker(ROOT/'src/vertical/native/portrait_aliases.c',header,path,fingerprints=False)
    return targets,path


def cbytes(raw):return '{'+','.join(map(str,raw))+'}'
