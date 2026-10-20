"""Download build-time driver/metadata helpers, without running either."""
import argparse
from pathlib import Path
import urllib.request
import zipfile
import io
import sys

ROOT = Path(__file__).resolve().parents[2]
DRIVER = 'https://github.com/Timocop/libwdi-wdi-releases/releases/download/v1.0/x64.zip'


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'A7C2Tools-Build'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exiftool-archive', type=Path,
                        help='Optional official Windows ExifTool ZIP to bundle')
    args = parser.parse_args()
    if sys.platform == 'win32':
        dest = ROOT / 'desktop-assets/windows'
        dest.mkdir(parents=True, exist_ok=True)
        exe = dest / 'wdi-simple.exe'
        if not exe.exists():
            with zipfile.ZipFile(io.BytesIO(fetch(DRIVER))) as archive:
                item = next(n for n in archive.namelist() if Path(n).name.lower() == 'wdi-simple.exe')
                exe.write_bytes(archive.read(item))
        (dest / 'SOURCE.txt').write_text(
            'libwdi wdi-simple driver helper, https://github.com/pbatard/libwdi\n'
            'Prebuilt distributor: ' + DRIVER + '\n'
            'GNU LGPL v3 or later; source and license: https://github.com/pbatard/libwdi/blob/master/COPYING\n', encoding='utf-8')
        license_file = dest / 'COPYING.txt'
        if not license_file.exists():
            license_file.write_bytes(fetch('https://raw.githubusercontent.com/pbatard/libwdi/master/COPYING'))
    if args.exiftool_archive:
        dest = ROOT / 'desktop-assets/exiftool'
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.exiftool_archive) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    continue
                relative = Path(item.filename)
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unexpected helper archive path')
                # Official bundles have a top-level exiftool-VERSION_64 folder.
                parts = relative.parts
                if len(parts) > 1 and parts[0].lower().startswith('exiftool-'):
                    parts = parts[1:]
                target = dest.joinpath(*parts)
                if target.name == 'exiftool(-k).exe':
                    target = target.with_name('exiftool.exe')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(item))
    print('Build helpers prepared. No driver installed; no camera connected.')


if __name__ == '__main__':
    main()
