"""Bounded wait for senser chunk end packets, with a simulated USB driver."""
import pytest
from looktool import devicesession

transport, _ = devicesession.modules()
usb = transport.usb
GenericUsbException = transport.GenericUsbException


def wrapped(error):
    # pmca re-raises every pyusb error as an empty GenericUsbException.
    try:raise error
    except usb.core.USBError:raise GenericUsbException()


class Driver:
    """Serves one senser response as header, chunks and end packets."""
    def __init__(self, chunks, end_packets):
        self.reads, self.end_packets = [], list(end_packets)
        header = transport.SonySenserDevice.SenserPacketHeader.pack(
            size=sum(chunks), pFunc=0x40, sequence=1, version=0, miconType=0, offsetType=0, response=0)
        self.queue = [header] + [b'x' * n for n in chunks]
    def reset(self):pass
    def getId(self):return (0x054c, 0x0336)
    def write(self, data, ep=0):pass
    def read(self, length, ep=0, timeout=None):
        self.reads.append((length, timeout))
        if timeout is not None:  # an end-packet read
            outcome = self.end_packets.pop(0)
            if isinstance(outcome, Exception):wrapped(outcome)
            return outcome
        return self.queue.pop(0)


def test_missing_end_packet_after_final_512_multiple_chunk_does_not_block():
    # Field log 31: 32768 + 20992 bytes; no end packet followed the 20992-byte chunk.
    timeout = usb.core.USBTimeoutError('Operation timed out', -7, 60)
    driver = Driver([32768, 20992], [b'', timeout])
    response, data = transport.SonySenserDevice(driver).sendSenserPacket(0x40, b'request')
    assert response == 0 and len(data) == 32768 + 20992
    assert [t for _, t in driver.reads if t is not None] == [1000, 1000]


def test_present_end_packets_are_consumed_as_before():
    driver = Driver([32768, 20992], [b'', b''])
    _, data = transport.SonySenserDevice(driver).sendSenserPacket(0x40, b'request')
    assert len(data) == 53760 and driver.end_packets == []


def test_final_chunk_that_is_not_a_512_multiple_needs_no_end_read():
    driver = Driver([32768, 30968], [b''])
    _, data = transport.SonySenserDevice(driver).sendSenserPacket(0x40, b'request')
    assert len(data) == 32768 + 30968
    assert sum(1 for _, t in driver.reads if t is not None) == 1


def test_other_usb_errors_on_the_end_read_still_stop_the_session():
    driver = Driver([20992], [usb.core.USBError('Pipe error', -9, 32)])
    with pytest.raises(GenericUsbException):
        transport.SonySenserDevice(driver).sendSenserPacket(0x40, b'request')
