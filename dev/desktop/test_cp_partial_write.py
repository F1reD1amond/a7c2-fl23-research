"""Exercise actual CP write/read framing through a short-returning USB backend."""
from array import array
from collections import deque
from types import SimpleNamespace
import struct

import pytest
from looktool import devicesession

transport,_=devicesession.modules()


class CpEndpoint:
    idVendor=0x054c
    idProduct=0x0336
    _ctx=SimpleNamespace(dispose=lambda device:None)

    def __init__(self,counts=(),fault=None):
        self.counts=deque(counts)
        self.fault=fault
        self.calls=[]
        self.received=bytearray()
        self.replies=deque()
        self.commands=[]
        self.units={}
        self.default_timeout=0

    def get_active_configuration(self):
        return {(0,0):[SimpleNamespace(bmAttributes=2,bEndpointAddress=n) for n in (2,0x81)]}

    def write(self,ep,data,**kwargs):
        assert ep==2
        data=bytes(data);self.calls.append(data)
        if self.fault is not None and len(self.calls)==2:raise self.fault
        count=min(self.counts.popleft(),len(data)) if self.counts else len(data)
        self.received.extend(data[:count])
        header_type=transport.SonySenserDevice.SenserPacketHeader
        if len(self.received)>=header_type.size:
            header=header_type.unpack(bytes(self.received))
            expected=header_type.size+header.size
            if len(self.received)==expected:
                packet=bytes(self.received);self.commands.append(packet);self.received.clear()
                payload=packet[header_type.size:]
                category,command,key,chip=struct.unpack_from('<HHII',payload)
                assert (category,chip)==(0x603,1)
                if command==0x41:
                    self.units[key]=payload[12:];reply=b''
                else:
                    assert command==0x40;reply=self.units[key]
                self.replies.append(header_type.pack(size=len(reply),pFunc=header.pFunc,
                    sequence=header.sequence,version=0,miconType=0,offsetType=0,response=0))
                if reply:self.replies.append(reply)
            else:assert len(self.received)<expected
        return count

    def read(self,ep,size,timeout=None):
        assert ep==0x81 and self.replies,'No reply before the complete command was delivered'
        raw=self.replies.popleft()
        if len(raw)>size:self.replies.appendleft(raw[size:]);raw=raw[:size]
        return array('B',raw)


def session(device,budget=180):
    value=transport.Session()
    value.backend=transport.Bounded(device,budget)
    value.channel=transport.SonySenserDevice(transport.GenericUsbDriver(value.backend))
    value.camera=transport.SonySenserCamera(value.channel)
    return value


@pytest.mark.parametrize('size,key',[(8192,0x02a40001),(28672,0x02a4000d)])
@pytest.mark.parametrize('counts',[(512,),(512,512,13,1024,256)])
def test_cp_write_continues_only_unsent_tail_then_full_readback(size,key,counts):
    device=CpEndpoint(counts);value=session(device)
    payload=bytes(range(256))*(size//256)
    value.cp_write(key,payload)
    assert len(device.commands)==1
    expected=device.commands[0]
    assert len(expected)==size+24
    assert len(device.calls[0])==512
    sent=0
    for index,call in enumerate(device.calls):
        chunk_end=512 if sent<512 else min(len(expected),512+transport.SonySenserDevice.SenserChunkSize)
        assert call==expected[sent:chunk_end]
        sent+=min(counts[index],len(call)) if index<len(counts) else len(call)
    assert sent==len(expected) and not device.received
    assert device.units[key]==payload
    assert value.cp_read(key)==payload
    assert value.channel._sequence==3 and value.healthy


@pytest.mark.parametrize('size,key',[(8192,0x02a40001),(28672,0x02a4000d)])
def test_cp_control_transfer_finishes_before_long_data_phase(size,key,monkeypatch):
    # A receiver accepts the initial control block before arming its long-data
    # buffer. Submitting everything in one transfer consumes the whole budget
    # and reports only the first 512 bytes, as in the local failure.
    clock=[0.0];monkeypatch.setattr(transport.time,'monotonic',lambda:clock[0])
    device=CpEndpoint();write=device.write
    def phased(ep,data,**kwargs):
        if not device.calls and len(data)>512:
            clock[0]=180.0
            device.counts.appendleft(512)
        return write(ep,data,**kwargs)
    device.write=phased;value=session(device)
    payload=bytes([43])*(size)
    value.cp_write(key,payload)
    assert clock[0]==0.0 and value.cp_read(key)==payload


def test_partial_write_followed_by_usb_error_stops_without_replaying_command():
    fault=transport.usb.core.USBTimeoutError('write outcome unknown',-7,60)
    device=CpEndpoint([512],fault);value=session(device)
    with pytest.raises(transport.GenericUsbException):value.cp_write(0x02a40001,bytes(8192))
    assert len(device.calls)==2 and len(device.calls[1])==8216-512
    assert len(device.received)==512 and not device.commands
    assert not value.healthy and value.channel._failed and value.mutating
    with pytest.raises(RuntimeError):value.cp_write(0x02a40001,bytes(8192))
    assert len(device.calls)==2


def test_partial_write_then_zero_progress_stops_without_waiting_for_reply():
    device=CpEndpoint([512,0]);value=session(device)
    with pytest.raises(transport.GenericUsbException):value.cp_write(0x02a40001,bytes(8192))
    assert len(device.calls)==2 and len(device.received)==512
    assert not device.commands and not value.healthy


def test_lost_reply_after_completed_cp_write_is_never_replayed():
    device=CpEndpoint();value=session(device);payload=bytes(8192)
    def lost(*args,**kwargs):raise transport.usb.core.USBTimeoutError('lost reply',-7,60)
    device.read=lost
    with pytest.raises(transport.GenericUsbException):value.cp_write(0x02a40001,payload)
    assert device.units[0x02a40001]==payload and len(device.commands)==1
    assert not value.healthy
    with pytest.raises(RuntimeError):value.cp_write(0x02a40001,payload)
    assert len(device.commands)==1 and len(device.calls)==2


def test_large_unrelated_worker_upload_keeps_its_existing_framing():
    header=transport.SonySenserDevice.SenserPacketHeader
    class Driver:
        def __init__(self):self.calls=[]
        def reset(self):pass
        def getId(self):return 0x054c,0x0336
        def write(self,raw):self.calls.append(raw)
        def read(self,size):
            return header.pack(size=0,pFunc=0x40,sequence=1,version=0,miconType=0,offsetType=0,response=0)
    driver=Driver();value=transport.SonySenserDevice(driver)
    payload=b'worker'*9000
    assert value.sendSenserPacket(0x40,payload)==(0,b'')
    assert len(driver.calls)==1 and driver.calls[0][header.size:]==payload


def test_short_write_completion_shares_one_deadline(monkeypatch):
    clock=[0.0];monkeypatch.setattr(transport.time,'monotonic',lambda:clock[0])
    device=CpEndpoint([512]*20);write=device.write
    def slow(*args,**kwargs):
        result=write(*args,**kwargs);clock[0]+=.4;return result
    device.write=slow;value=session(device,budget=1)
    with pytest.raises(TimeoutError):value.cp_write(0x02a40001,bytes(8192))
    assert len(device.calls)==3 and not device.commands and not value.healthy


def test_initial_auth_write_also_finishes_only_unsent_tail():
    class Device:
        _ctx=SimpleNamespace(dispose=lambda device:None)
        def __init__(self):self.calls=[]
        def write(self,ep,data,**kwargs):
            self.calls.append(bytes(data));return min(512,len(data))
    device=Device();backend=transport._InitialBackend(device,None)
    raw=bytes(range(256))*2+b'end!'
    backend.write(2,raw)
    assert device.calls==[raw,b'end!']
