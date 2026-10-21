"""Read-only transfer sampling retains errors and never executes a worker."""
import json
from unittest.mock import Mock
import pytest
from desktopapp import usbcheck,jobs


class Camera:
    def __init__(self,values):self.values=iter(values);self.calls=[];self.mark_unknown=Mock()
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,path):
        self.calls.append(path);value=next(self.values)
        if isinstance(value,Exception):raise value
        return value


def test_good_connection_only_reads_fixed_resource_and_compares_bytes(tmp_path):
    camera=Camera([bytes(8192)]*3)
    report=usbcheck.run(tmp_path,factory=lambda:camera)
    assert report['phase']=='PASSED' and report['total_bytes']==24576
    assert camera.calls==[usbcheck.PATH]*3
    assert not report['camera_firmware_written'] and not report['camera_settings_written']
    assert not report['native_worker_executed']
    assert '不保证' in report['note']


@pytest.mark.parametrize('failure',[TimeoutError('transfer timed out'),OSError('device disconnected'),bytes(8191)+b'X'],ids=['timeout','disconnect','bytes-differ'])
def test_bad_connection_stops_at_first_failure_with_original_error(tmp_path,failure):
    camera=Camera([bytes(8192),failure,bytes(8192)])
    with pytest.raises(RuntimeError,match='第 2/3 轮'):
        usbcheck.run(tmp_path,factory=lambda:camera)
    report=json.loads((tmp_path/'usb-stability.private.json').read_text(encoding='utf-8'))
    assert report['phase']=='FAILED' and report['failed_round']==2
    assert len(camera.calls)==2 and len(report['rounds'])==1
    camera.mark_unknown.assert_called_once()


def test_test_is_an_explicit_camera_action_without_battery_or_flash_gate():
    assert 'usb_stability' in jobs.CAMERA_ACTIONS
    assert 'usb_stability' not in jobs.POWER_ACTIONS
