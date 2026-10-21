"""Read-only program-file soak test retains errors and never executes a worker."""
import json
from unittest.mock import Mock
import pytest
from desktopapp import usbcheck,jobs

AP=bytes(2*1024*1024)
CP=b'\1'*(1024*1024)


class Clock:
    """Each read advances fake time, so duration rules run without sleeping."""
    def __init__(self,step=1.0):self.now=0.0;self.step=step
    def __call__(self):return self.now


class Camera:
    def __init__(self,values,clock,cost=1.0):
        self.values=iter(values);self.calls=[];self.mark_unknown=Mock();self.clock=clock;self.cost=cost
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,path):
        self.calls.append(path);self.clock.now+=self.cost;value=next(self.values)
        if isinstance(value,Exception):raise value
        return value


def good(rounds):return [AP,CP]*rounds


def test_good_connection_reads_both_programs_until_minimum_time_and_rounds(tmp_path):
    clock=Clock();camera=Camera(good(100),clock,cost=5.0)
    report=usbcheck.run(tmp_path,factory=lambda:camera,clock=clock)
    # 10 s per round: 120 s minimum outweighs the 5-round minimum.
    assert report['phase']=='PASSED' and len(report['rounds'])==12
    assert camera.calls==list(usbcheck.PATHS)*12
    assert report['total_bytes']==12*(len(AP)+len(CP)) and report['seconds']>=120
    assert not report['camera_firmware_written'] and not report['camera_settings_written']
    assert not report['native_worker_executed']
    assert '不保证' in report['note']


def test_fast_connection_still_runs_minimum_rounds(tmp_path):
    clock=Clock();camera=Camera(good(100),clock,cost=0.0)
    report=usbcheck.run(tmp_path,factory=lambda:camera,clock=clock,min_seconds=0)
    assert len(report['rounds'])==usbcheck.MIN_ROUNDS


def test_round_cap_bounds_the_test(tmp_path):
    clock=Clock();camera=Camera(good(100),clock,cost=0.0)
    report=usbcheck.run(tmp_path,factory=lambda:camera,clock=clock,max_rounds=7)
    assert len(report['rounds'])==7


@pytest.mark.parametrize('failure',[TimeoutError('transfer timed out'),OSError('device disconnected'),AP[:-1]+b'X',AP[:1000]],
                         ids=['timeout','disconnect','bytes-differ','truncated'])
def test_bad_connection_stops_at_first_failure_with_original_error(tmp_path,failure):
    clock=Clock();camera=Camera([AP,CP,failure,CP],clock)
    with pytest.raises(RuntimeError,match='第 2 轮'):
        usbcheck.run(tmp_path,factory=lambda:camera,clock=clock)
    report=json.loads((tmp_path/'usb-stability.private.json').read_text(encoding='utf-8'))
    assert report['phase']=='FAILED' and report['failed_round']==2
    assert len(camera.calls)==3 and len(report['rounds'])==1
    camera.mark_unknown.assert_called_once()


def test_stalled_read_fails_even_when_bytes_match(tmp_path):
    clock=Clock();camera=Camera(good(10),clock,cost=usbcheck.STALL_SECONDS+1)
    with pytest.raises(RuntimeError,match='超过'):
        usbcheck.run(tmp_path,factory=lambda:camera,clock=clock)
    camera.mark_unknown.assert_called_once()


def test_test_is_an_explicit_camera_action_without_battery_or_flash_gate():
    assert 'usb_stability' in jobs.CAMERA_ACTIONS
    assert 'usb_stability' not in jobs.POWER_ACTIONS
