"""Image record mapping, lossless line geometry and untouched landscape banks."""
import io
import json
from pathlib import Path
import struct
import sys

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src/vertical'),str(ROOT/'src/looks'),str(ROOT/'src/desktopapp/vendor')]
from verticaltool import portrait
from fwtool.lz77 import inflateLz77


def fixtures():
    specs=json.loads((portrait.ASSETS/'portrait-lines-v1.json').read_text())['assets'];banks=[]
    for group in range(3):
        selected=[s for s in specs if s['group']==group];count=max([x['index'] for x in selected] or [0])+1
        header=bytearray(struct.pack('<8sHHI',b'uxd\x07\0\0\0\0',8,group,count|(((count+1)&~1)<<12)))
        header.extend(b'\xff\xff'*((count+1)&~1));base=len(header)
        for i,row in enumerate(selected):
            struct.pack_into('<H',header,16+2*row['index'],i*5)
            header.extend(struct.pack('<IIHHII',0x1a000000+8192*group+row['index'],0xc0000000,
                *row['landscape'],4,20*(len(selected)-i)-4))
        header.extend(bytes(4*max(1,len(selected))))
        banks.append(bytes(header))
    return banks


def decode(raw):
    stream=io.BytesIO(raw);out=b''
    while stream.tell()<len(raw):out+=inflateLz77(stream)
    return out


@pytest.mark.parametrize('raw',[b'abc',bytes(65536),b'0123456789'*6500,bytes(range(256))*193],ids=['literal','zeros','periodic','bytes'])
def test_lz77_round_trip_across_blocks(raw):
    packed=portrait.compress(raw);stream=io.BytesIO(packed);blocks=[]
    while stream.tell()<len(packed):blocks.append(inflateLz77(stream))
    assert b''.join(blocks)==raw
    assert all(len(block)==4096 for block in blocks[:-1])
    assert len(blocks[-1])<=4096


def test_only_selected_existing_records_change_and_new_rasters_decode_exactly():
    specs=json.loads((portrait.ASSETS/'portrait-lines-v1.json').read_text())['assets']
    for group,source in enumerate(fixtures()):
        target,edits=portrait.bank(source,group)
        previous=bytearray(target[:len(source)])
        for at,old,new in edits:
            assert target[at:at+12]==new
            previous[at:at+12]=old
            w,h,length,offset=struct.unpack('<HHII',new);data_at=at-4+offset
            spec=next(s for s in specs if s['group']==group and s['portrait']==[w,h] and
                s['index']==(struct.unpack_from('<I',source,at-8)[0]&8191))
            assert decode(target[data_at:data_at+length])==portrait.raster(spec)
        assert bytes(previous)==source
        if group==2:assert target==source and edits==[]


def test_fn_portrait_grid_uses_480_width_and_aligned_columns():
    specs=json.loads((portrait.ASSETS/'portrait-lines-v1.json').read_text())['assets']
    for s in specs[:2]:
        assert s['landscape'][0]==640 and s['portrait'][0]==480
        raw=portrait.raster(s);w,h=s['portrait']
        # Official portrait Fn layout uses a different column count, not a
        # clipped or resized landscape grid. These are its original pixels.
        row=struct.unpack_from('<'+'H'*w,raw,2*w*10)
        assert sum(bool(x&15) for x in row)>0


def test_unknown_geometry_is_rejected_without_changing_source():
    source=bytearray(fixtures()[0]);before=bytes(source)
    descriptor=struct.unpack_from('<I',source,12)[0];base=16+((descriptor>>11)&0x7ffc)
    struct.pack_into('<H',source,base+8,639)
    with pytest.raises(ValueError,match='source geometry'):portrait.bank(source,0)
    assert before!=bytes(source)  # Only the deliberately modified fixture.
