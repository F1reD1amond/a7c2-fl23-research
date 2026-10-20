"""Build native desktop artifacts; run separately on Windows and macOS."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                    '--distpath', str(output), '--workpath', str(ROOT / 'build/desktop'),
                    str(ROOT / 'dev/desktop/desktop.spec')], cwd=ROOT, check=True)
    if sys.platform == 'darwin':
        staging = output / 'dmg-contents'
        staging.mkdir(exist_ok=True)
        app = output / 'A7C2Tools.app'
        shutil.copytree(app, staging / app.name, symlinks=True, dirs_exist_ok=True)
        applications = staging / 'Applications'
        if not applications.exists():
            applications.symlink_to('/Applications', target_is_directory=True)
        target = output / ('A7C2Tools-macOS-' + __import__('platform').machine() + '.dmg')
        subprocess.run(['hdiutil', 'create', '-ov', '-format', 'UDZO', '-volname',
                        'A7C II Tools', '-srcfolder', str(staging), str(target)], check=True)
    elif sys.platform == 'win32':
        target = output / 'A7C2Tools-Windows-x64.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
            for source in (output / 'A7C2Tools').rglob('*'):
                if source.is_file():
                    stream.write(source, source.relative_to(output))
    else:
        raise RuntimeError('Build on native Windows or macOS')
    print(json.dumps({'artifact': str(target), 'bytes': target.stat().st_size, 'camera_io': False}))


if __name__ == '__main__':
    main()
