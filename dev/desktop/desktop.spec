from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parents[1]
for slot in range(1, 7):
    path = root / 'desktop-assets/presets/default-six-v1' / ('slot%d.a7look' % slot)
    if not path.is_file():
        raise FileNotFoundError('Prepare the six-look distribution pack first: ' + str(path))
datas, binaries, hidden = [], [], ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
                                 'tarfile', 'lzma', 'bz2', 'zlib', 'urllib.request', 'wave']
for package in ('numpy', 'scipy', 'PIL', 'tifffile', 'yaml', 'elftools', 'usb',
                'libusb_package', 'Cryptodome', 'imageio_ffmpeg', 'ziglang', 'keystone', 'capstone', 'unicorn'):
    d, b, h = collect_all(package)
    datas.extend(d)
    binaries.extend(b)
    hidden.extend(h)

# Source keeps original __file__-relative native headers and asset paths.
for folder in ('src/desktopapp', 'src/camera_runtime', 'src/looks/looktool',
               'src/looks/assets', 'src/looks/native', 'src/fl23/native', 'src/fl23/assets',
               'src/vertical', 'dev/shutter_sound', 'plugins', 'desktop-assets'):
    for source in (root / folder).rglob('*'):
        relative = source.relative_to(root)
        if not source.is_file() or any(p in ('__pycache__', 'tests') for p in relative.parts):
            continue
        if '.private.' in source.name or source.suffix.lower() in ('.arw', '.hif', '.jpg', '.dcp', '.cube', '.pyc'):
            continue
        datas.append((str(source), str(relative.parent)))
for name in ('desktop.py', 'LICENSE', 'desktop-requirements.txt',
             'dev/desktop/offline_smoke.py', 'docs/en/desktop.md',
             'docs/zh-CN/desktop.md', 'docs/en/desktop-validation.md',
             'docs/zh-CN/desktop-validation.md', 'calibration/a7c2-2.01.virtual.npz'):
    datas.append((str(root / name), str(Path(name).parent)))

a = Analysis([str(root / 'dev/desktop/frozen_entry.py')], pathex=[],
             binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=['tkinter', 'matplotlib', 'pandas', 'IPython', 'pytest'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='A7C2Tools',
          console=False, disable_windowed_traceback=False)
collection = COLLECT(exe, a.binaries, a.datas, name='A7C2Tools')
if sys.platform == 'darwin':
    app = BUNDLE(collection, name='A7C2Tools.app', bundle_identifier='io.github.QAQLeonard.A7C2Tools',
                 info_plist={'CFBundleShortVersionString': '3.0.0',
                             'NSHighResolutionCapable': True,
                             'NSUSBUsageDescription': 'Access your Sony A7C II for requested camera operations.'})
