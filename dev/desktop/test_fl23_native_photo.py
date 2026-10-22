"""FL23 PR assets and real custom-look/FL23 installation order; no USB."""
import copy
import os
from pathlib import Path
import struct

import pytest

from desktopapp.worker import setup_runtime
setup_runtime()
from looktool import bundle, device_layout, direct, firmware, lookfile, nameworker
from looktool import photobasis, photobuild, photoformat, photoio
from looktool.devicesession import modules
from test_checkpoint import stock_names


def test_gui_uses_both_merged_pr_color_and_gamma_assets():
    core=modules()[1]
    legacy=core.BASE.parent/'fl23/assets'
    for name in ('patches.json','colors.json','fx2_fl23_donor.json'):
        assert core.read_json(core.BASE/'assets'/name)==core.read_json(legacy/name)
    for row in core.read_json(core.BASE/'assets/colors.json'):
        core.colour_record(row)
    block=next(new for at,old,new,legacy in device_layout.fl23_native_windows() if at==0x1100b80)
    assert struct.unpack_from('<II',block,0xe78+19*8)==(48,46)
    assert struct.unpack_from('<II',block,0xe78+20*8)==(49,47)
    helper=next(new for at,old,new,legacy in device_layout.fl23_native_windows() if at==0x138832)
    assert helper==bytes.fromhex('00bf'*7+'49f6f811c0f22011704700bf')


@pytest.fixture(scope='module')
def original_camera_inputs():
    root=os.environ.get('A7C2_FIRMWARE_ROOT')
    if not root:
        pytest.skip('Optional private original firmware; never reads a camera')
    core=modules()[1]
    folder=Path(root)/'a7c2-2.01/components'
    programs={name:(folder/name).read_bytes() for name in core.PROGRAMS}
    records=core.backup_records((folder/'CX89700_ALLLANG.bin').read_bytes())
    return programs,records


@pytest.fixture(scope='module')
def looks_first(original_camera_inputs,tmp_path_factory):
    programs,records=original_camera_inputs
    current=dict(programs,**{'resources/'+n:stock_names() for n in nameworker.filenames()})
    bootstrap=device_layout.replace(programs['appFw.so'],programs['cpapp-b.bin'],
        {1:bytes(1215)},hash_checks=False,transitions=False)[2]['cpapp-b.bin']
    bank=photoformat.extract_bank(bootstrap,records[1][0x02a40001].data,
        records[1][0x02a4000d].data,gamma_table_va=0x1209480,
        regular_row=0,still_row=10,color_parameter=0)[0]
    root=tmp_path_factory.mktemp('fl23-native-looks')
    selected=[]
    for slot in range(1,7):
        delta=photobasis.pack(bank,tone=[16+slot,0,0])[1]
        document=lookfile.write(root/f'{slot}.a7look',f'Look {slot}',bytes([slot])*1215,
            method='offline regression fixture',attribution='test',native_photo=delta)
        selected.append(dict(slot=slot,name=document['name'],document=document))
    target,wanted,_=bundle.plan(current,records,dict(fl23=False,sound=False),selected)
    working=copy.deepcopy(records)
    for chip in (0,1):
        for key,value in wanted[chip].items():
            working[chip][key]=working[chip][key]._replace(data=value)
    return current,records,target,working,selected


def assert_active_fl23(cp):
    original=0x1209480-photobuild.BASE
    for row in (46,47,48,49):
        assert cp[photobuild.TABLE_FILE+row*28:photobuild.TABLE_FILE+(row+1)*28]==cp[original+row*28:original+(row+1)*28]
    assert photoio.inspect(cp)['mask']==63


def test_enabling_fl23_after_six_looks_matches_fl23_first(looks_first):
    current,records,installed,working,selected=looks_first
    target,wanted,_=direct.plan(installed,working,'fl23_enable')
    combined,combined_wanted,_=bundle.plan(current,records,dict(fl23=True,sound=False),selected)
    assert target==combined
    for key,value in wanted[1].items():
        assert value==combined_wanted[1][key]
    assert_active_fl23(target['cpapp-b.bin'])
    assert device_layout.tables(target['cpapp-b.bin'])==device_layout.tables(installed['cpapp-b.bin'])
    for slot in range(1,7):
        assert photoio.slot_bytes(target['cpapp-b.bin'],slot)==photoio.slot_bytes(installed['cpapp-b.bin'],slot)


def test_reenable_repairs_current_pr_bytes_with_a_stale_active_table(looks_first):
    _,_,installed,working,_=looks_first
    target,_,_=direct.plan(installed,working,'fl23_enable')
    stale=bytearray(target['cpapp-b.bin'])
    start=photobuild.TABLE_FILE
    stale[start:start+50*28]=installed['cpapp-b.bin'][start:start+50*28]
    with pytest.raises(ValueError,match='runtime bytes conflict'):
        photoio.inspect(bytes(stale))
    source=dict(target,**{'cpapp-b.bin':bytes(stale)})
    repaired,_,_=direct.plan(source,working,'fl23_enable')
    assert repaired==target
    assert_active_fl23(repaired['cpapp-b.bin'])
    import compat
    programs={n:source[n] for n in modules()[1].PROGRAMS}
    _,enabled,after,forward,reverse=compat.plan(programs['appFw.so'],programs['cpapp-b.bin'])
    assert not enabled  # Native FL23 bytes match, but the active table needs repair.
    assert firmware.apply(programs,forward)==after
    assert firmware.apply(after,reverse)==programs
    assert compat.plan(after['appFw.so'],after['cpapp-b.bin'],transitions=False)[1]

