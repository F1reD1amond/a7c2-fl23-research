"""All automated development tests are offline, including Windows USB hosts."""
import pytest


@pytest.fixture(autouse=True)
def no_physical_usb(monkeypatch):
    import usb.core
    def forbidden(*args,**kwargs):
        raise AssertionError('Physical USB enumeration is forbidden in offline tests; supply a fake camera')
    monkeypatch.setattr(usb.core,'find',forbidden)
