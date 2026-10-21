"""Self-contained small image-bank additions and recovery over current bytes."""
import json
import struct
from . import imagebank,portraitlayout,portraitlines

MAGIC=b'A7PFBK01'


def compatible(current,before,after):
    return len(current)==len(before)==len(after) and all(c in (a,b) for c,a,b in zip(current,before,after))


def seal(target,plan):
    receipt={key:value for key,value in plan.items() if key not in ('append_hex','camera_io')}
    payload=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode('ascii')
    payload+=b' '*((-len(payload))%4)
    result=target+payload+struct.pack('<I8s',len(payload),MAGIC)
    plan=dict(plan,target_bytes=len(result),append_hex=result[plan['source_bytes']:].hex())
    return result,plan


def baseline(source,group):
    """Reconstruct old metadata from our on-camera footer, without old jobs."""
    if source.endswith(MAGIC):
        size=struct.unpack_from('<I',source,len(source)-12)[0]
        if size>65536 or size+12>len(source):raise ValueError('Portrait resource footer is incomplete')
        saved=json.loads(source[-12-size:-12])
        if saved.get('schema')!='a7c2-image-bank-additions/1' or saved.get('group')!=group:
            raise ValueError('Portrait resource footer identifies a different bank')
        original_size=saved['source_bytes']
        if not original_size<=saved['target_bytes']<=len(source)-12-size:
            raise ValueError('Portrait resource footer sizes differ')
        original=bytearray(source[:original_size])
        for window in saved['windows']:
            at=window['offset'];before=bytes.fromhex(window['before_hex']);after=bytes.fromhex(window['after_hex'])
            if not 0<=at<=at+len(before)<=original_size or not compatible(source[at:at+len(before)],before,after):
                raise ValueError('Portrait resource edit conflicts at '+hex(at))
            original[at:at+len(before)]=before
        imagebank.inspect(original,group)
        return bytes(original)
    parsed=imagebank.inspect(source,group)
    end=max(max(row['at']+row['field']+8,row['start']+row['size']) for row in parsed['records'].values())
    return source[:(end+3)&~3]


def prepare(source,group):
    original=baseline(source,group)
    selected=[]
    for row in portraitlines.specs():
        old=0x02000000+row['group']*8192+row['index']
        if row['group']!=group or old not in portraitlayout.IMAGES:continue
        new=portraitlayout.IMAGES[old]
        selected.append(dict(index=(new-0x02000000)%8192,width=row['portrait'][0],height=row['portrait'][1],
                             payload=portraitlines.compress(portraitlines.raster(row))))
    target,plan=imagebank.add(original,group,selected)
    target,plan=seal(target,plan)
    if len(source)<len(original) or len(source)>len(target):raise ValueError('Portrait resource size is outside this operation')
    tail=source[len(original):]
    if tail!=target[len(original):len(source)]:
        raise ValueError('Unrecognized data after the original image bank; no bytes were removed')
    for window in plan['windows']:
        at=window['offset'];before=bytes.fromhex(window['before_hex']);after=bytes.fromhex(window['after_hex'])
        if not compatible(source[at:at+len(before)],before,after):
            raise ValueError('Portrait resource edit conflicts at '+hex(at))
    return original,target,plan
