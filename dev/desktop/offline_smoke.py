"""Exercise packaged imports, assets and an actual native compile, without USB."""
import importlib
from pathlib import Path
import tempfile


def run():
    from desktopapp.worker import setup_runtime
    from desktopapp.paths import ROOT
    setup_runtime()
    from looktool import nativebuild, checkpointworker, device_layout, resources, nameworker
    from looktool.devicesession import modules
    transport, core = modules()
    assert nativebuild.ROOT == ROOT
    assert Path(core.__file__).resolve() == ROOT / 'src/camera_runtime/core.py'
    assert core.assets()
    core.merge_colors(bytes(8192), bytes(28672))
    assert device_layout.runtime()['schema'] == 'a7c2-lut-runtime/1'
    assert (ROOT / 'src/looks/assets/native-photo-v2.json').is_file()
    for name in ('compilelook', 'lookfile', 'rawauto', 'rawprofiles', 'checkpointjob', 'devicejob'):
        importlib.import_module('looktool.' + name)
    import sys
    sys.path[:0] = [str(ROOT / 'src/vertical'), str(ROOT / 'dev/shutter_sound')]
    importlib.import_module('verticaltool.device')
    importlib.import_module('sound_cli')
    import numpy as np
    import scipy.optimize
    from looktool.measuredmodel import Response
    model = Response(ROOT / 'calibration/a7c2-2.01.virtual.npz')
    with tempfile.TemporaryDirectory() as folder:
        before = {'appFw.so': bytes(40000), 'cpapp-b.bin': bytes(40000)}
        after = dict(before, **{'appFw.so': b'\x01' + bytes(39999)})
        builds = checkpointworker.build_programs(before, after, Path(folder))
        assert builds and Path(builds[0]['path']).read_bytes()[:4] == b'\x7fELF'
        import struct
        count = 2860
        raw = bytearray(b'uxc\x07\0\0\0\0' + struct.pack('<HHI', 8, 5, count | (count << 12)) + b'\xff\xff' * count)
        struct.pack_into('<H', raw, 16, 0)
        raw.extend(struct.pack('<I', 0x1e00a000) + b'Native\0\0')
        original = bytes(raw)
        renamed = resources.rename(original, {1: 'Smoke'})[0]
        current = {'resources/' + name: renamed for name in nameworker.filenames()}
        target = {'resources/' + name: original for name in nameworker.filenames()}
        names = checkpointworker.build_names(current, target, Path(folder), 'smoke')
        assert Path(names['path']).read_bytes()[:4] == b'\x7fELF'
    return {'camera_io': False, 'project_imports': 'passed', 'assets': 'passed',
            'native_cross_compile': 'passed', 'numpy': np.__version__}
