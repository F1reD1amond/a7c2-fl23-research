"""Targeted macOS host preparation, simulated; never opens camera USB."""
import importlib.util
from pathlib import Path
from unittest.mock import Mock,patch
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('macos_host_test',ROOT/'src/camera_runtime/macos_host.py')
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)


def tree(disks):
    return [dict(IOObjectClass='IOUSBHostDevice',idVendor=0x054c,idProduct=0x0e8a,
                 IORegistryEntryChildren=[dict(IOObjectClass='IOMedia',**{'BSD Name':d}) for d in disks]),
            dict(IOObjectClass='IOUSBHostDevice',idVendor=0x1234,idProduct=1,
                 IORegistryEntryChildren=[dict(IOObjectClass='IOMedia',**{'BSD Name':'disk99s1'})])]


class Host:
    """Fake ioreg/diskutil; ``remounts`` re-mounts a volume after each unmount."""
    def __init__(self,disks,mounts,remounts=0,returncode=0,stderr=''):
        self.disks,self.mounts,self.remounts=disks,dict(mounts),remounts
        self.returncode,self.stderr=returncode,stderr
        self.commands,self.unmounts=[],[]
    def plist(self,*args):
        self.commands.append(args)
        if 'ioreg' in args[0]:return tree(self.disks)
        point=self.mounts.get(args[-1].removeprefix('/dev/'))
        return {'MountPoint':point} if point else {}
    def run(self,command,**kwargs):
        self.unmounts.append(command)
        disk=command[-1].removeprefix('/dev/')
        if not self.returncode:
            if self.remounts:self.remounts-=1
            else:self.mounts.pop(disk)
        return Mock(returncode=self.returncode,stdout='unmounted',stderr=self.stderr)
    def patches(self):
        return (patch.object(host,'plist_command',side_effect=self.plist),
                patch.object(host.subprocess,'run',side_effect=self.run),
                patch.object(host.time,'sleep'))


def test_unmounts_camera_media_only_and_retains_command_output(capsys):
    fake=Host(['disk4','disk4s1'],{'disk4s1':'/Volumes/CAMERA'})
    a,b,c=fake.patches()
    with a,b,c:assert host.unmount_camera()['unmounted']==['disk4s1']
    assert all('disk99' not in str(command) for command in fake.commands)
    assert fake.unmounts==[['/usr/sbin/diskutil','unmount','/dev/disk4s1']]
    assert 'unmounted' in capsys.readouterr().out


@pytest.mark.parametrize('disks',[[],['disk4']])
def test_no_card_and_already_unmounted_do_not_block_service(disks):
    fake=Host(disks,{})
    a,b,c=fake.patches()
    with a,b,c:assert host.unmount_camera()['unmounted']==[]
    assert fake.unmounts==[]


def test_busy_volume_stops_before_capture_with_details(capsys):
    fake=Host(['disk4s1'],{'disk4s1':'/Volumes/CAMERA'},returncode=1,stderr='in use by Photos')
    a,b,c=fake.patches()
    with a,b,c,pytest.raises(RuntimeError,match='照片'):host.unmount_camera()
    assert 'in use by Photos' in capsys.readouterr().err


def test_volume_remounted_by_macos_is_unmounted_again_before_capture():
    # Two camera disks (card and PMHOME), as in the field report; one remounts once.
    fake=Host(['disk9s1','disk10s1'],{'disk9s1':'/Volumes/Untitled','disk10s1':'/Volumes/PMHOME'},remounts=1)
    a,b,c=fake.patches()
    with a,b,c:result=host.unmount_camera()
    assert fake.mounts=={}
    assert result['unmounted'].count('disk10s1')==2


def test_persistent_remount_stops_before_claiming_usb():
    fake=Host(['disk4s1'],{'disk4s1':'/Volumes/CAMERA'},remounts=99)
    a,b,c=fake.patches()
    with a,b,c,pytest.raises(RuntimeError,match='重新挂载'):host.unmount_camera()
    assert len(fake.unmounts)==host.UNMOUNT_ROUNDS


def test_mount_state_must_settle_before_unmounting():
    states=iter([{},{'disk4s1':'/Volumes/CAMERA'},{'disk4s1':'/Volumes/CAMERA'},{},{}])
    with patch.object(host,'camera_media',side_effect=lambda:next(states)), \
            patch.object(host.subprocess,'run',return_value=Mock(returncode=0,stdout='',stderr='')) as run, \
            patch.object(host.time,'sleep'):
        assert host.unmount_camera()['unmounted']==['disk4s1']
    run.assert_called_once()


def test_failed_claim_reattaches_detached_driver():
    device=Mock();device.is_kernel_driver_active.return_value=True
    with patch('usb.util.claim_interface',side_effect=RuntimeError('busy')),patch('usb.util.dispose_resources') as dispose:
        with pytest.raises(RuntimeError,match='busy'):host.claim_camera_interface(device)
    device.detach_kernel_driver.assert_called_once_with(0)
    device.attach_kernel_driver.assert_called_once_with(0)
    dispose.assert_called_once_with(device)
