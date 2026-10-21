"""Release only this Sony camera's mounted media before libusb capture.

Inspired by MDHan/a7c2-fl23-macos at 1491f734df07f02fb77da6ea7062828bce0e30e7.
No forced unmount, driver installation, service authentication or firmware I/O.
"""
import plistlib
import re
import subprocess
import sys


def registry_nodes(tree):
    if isinstance(tree,list):
        for item in tree:yield from registry_nodes(item)
    elif isinstance(tree,dict):
        yield tree
        yield from registry_nodes(tree.get('IORegistryEntryChildren',[]))


def plist_command(*command):
    result=subprocess.run(command,capture_output=True,timeout=30)
    if result.returncode:
        print(result.stdout.decode('utf-8',errors='replace'),flush=True)
        print(result.stderr.decode('utf-8',errors='replace'),file=sys.stderr,flush=True)
        raise RuntimeError('macOS command failed (%s): %s'%(result.returncode,' '.join(command)))
    return plistlib.loads(result.stdout)


def unmount_camera():
    tree=plist_command('/usr/sbin/ioreg','-p','IOService','-l','-a')
    cameras=[node for node in registry_nodes(tree)
             if node.get('idVendor')==0x054c and node.get('idProduct')==0x0e8a
             and node.get('IOObjectClass')=='IOUSBHostDevice']
    if len(cameras)!=1:raise RuntimeError('请只连接一台海量存储模式的 A7C II，再准备 USB 连接。')
    # Disk identifiers come only from the selected USB device's registry
    # subtree, never from all external disks or every mounted /Volumes path.
    media={node['BSD Name'] for node in registry_nodes(cameras[0])
           if node.get('IOObjectClass')=='IOMedia' and node.get('BSD Name')}
    unmounted=[]
    for disk in sorted(media):
        if not re.fullmatch(r'disk[0-9]+(?:s[0-9]+)*',disk):
            raise RuntimeError('Unexpected camera disk identifier: '+disk)
        info=plist_command('/usr/sbin/diskutil','info','-plist','/dev/'+disk)
        if not info.get('MountPoint'):continue
        print('正在卸载相机存储卷（不拔线）：'+info['MountPoint'],flush=True)
        result=subprocess.run(['/usr/sbin/diskutil','unmount','/dev/'+disk],
                              capture_output=True,text=True,timeout=30)
        print(result.stdout,flush=True)
        if result.stderr:print(result.stderr,file=sys.stderr,flush=True)
        if result.returncode:
            raise RuntimeError('无法卸载相机存储卷。请关闭照片、图像捕捉及使用存储卡的程序后重试。')
        unmounted.append(disk)
    # An empty SD slot or already-unmounted camera is valid for service access.
    return dict(unmounted=unmounted,camera_firmware_written=False)


def claim_camera_interface(device):
    """libusb ownership after storage has unmounted; no authentication retry."""
    import usb.util
    detached=False
    try:
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0);detached=True
        usb.util.claim_interface(device,0)
    except BaseException:
        try:
            if detached:device.attach_kernel_driver(0)
        finally:usb.util.dispose_resources(device)
        raise
