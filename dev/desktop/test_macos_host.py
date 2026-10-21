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


def test_unmounts_camera_media_only_and_retains_command_output(capsys):
    commands=[]
    def plist(*args):
        commands.append(args)
        if 'ioreg' in args[0]:return tree(['disk4','disk4s1'])
        return {'MountPoint':'/Volumes/CAMERA'} if args[-1].endswith('s1') else {}
    with patch.object(host,'plist_command',side_effect=plist),patch.object(host.subprocess,'run',
            return_value=Mock(returncode=0,stdout='unmounted',stderr='')) as run:
        assert host.unmount_camera()['unmounted']==['disk4s1']
    assert all('disk99' not in str(c) for c in commands)
    assert run.call_args.args[0]==['/usr/sbin/diskutil','unmount','/dev/disk4s1']
    assert 'unmounted' in capsys.readouterr().out


@pytest.mark.parametrize('disks',[[],['disk4']])
def test_no_card_and_already_unmounted_do_not_block_service(disks):
    with patch.object(host,'plist_command',side_effect=[tree(disks)]+[{} for _ in disks]), \
            patch.object(host.subprocess,'run') as run:
        assert host.unmount_camera()['unmounted']==[]
    run.assert_not_called()


def test_busy_volume_stops_before_capture_with_details(capsys):
    with patch.object(host,'plist_command',side_effect=[tree(['disk4s1']),{'MountPoint':'/Volumes/CAMERA'}]), \
            patch.object(host.subprocess,'run',return_value=Mock(returncode=1,stdout='',stderr='in use by Photos')):
        with pytest.raises(RuntimeError,match='照片'):host.unmount_camera()
    assert 'in use by Photos' in capsys.readouterr().err


def test_failed_claim_reattaches_detached_driver():
    device=Mock();device.is_kernel_driver_active.return_value=True
    with patch('usb.util.claim_interface',side_effect=RuntimeError('busy')),patch('usb.util.dispose_resources') as dispose:
        with pytest.raises(RuntimeError,match='busy'):host.claim_camera_interface(device)
    device.detach_kernel_driver.assert_called_once_with(0)
    device.attach_kernel_driver.assert_called_once_with(0)
    dispose.assert_called_once_with(device)
