"""Legacy reports remain readable; new reports retain real syscall failures."""
from pathlib import Path
import struct
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src/vertical'))
from verticaltool.device import parse_aliases,require_aliases


def report(version=2,status=-28,step=3):
    diagnostic=(1<<8)|step if version==2 else 0
    raw=struct.pack('<8sIIIIqqqIIII3II3Q',b'A7VRS001',version,1,2,3,status,0,0,7,7,0,0,7844,7880,3709,diagnostic,9949936,9695356,9392312)
    return raw+(struct.pack('<3Q',4096,1024*1024,10*1024*1024) if version==2 else b'')


def test_old_eio_report_does_not_invent_a_failure_stage():
    value=parse_aliases(report(version=1,status=-5),1)
    assert value['status']==-5 and 'failure_step' not in value


def test_enospc_report_includes_source_group_operation_and_required_space():
    value=parse_aliases(report(),1)
    assert value['failure_group']==0 and value['failure_step']=='检查可用空间'
    with pytest.raises(ValueError,match='-28（ENOSPC）') as error:require_aliases(value)
    assert '1.00 MB' in str(error.value) and '10.00 MB' in str(error.value)


def test_negative_io_error_is_not_replaced_with_eio():
    value=parse_aliases(report(status=-13,step=5),1)
    with pytest.raises(ValueError,match='-13（EACCES）'):require_aliases(value)


@pytest.mark.parametrize('raw',[report()[:-1],report(version=1)+bytes(24)])
def test_truncated_or_mixed_abi_is_rejected(raw):
    with pytest.raises(ValueError):parse_aliases(raw,1)
