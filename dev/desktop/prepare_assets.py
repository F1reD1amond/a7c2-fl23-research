"""Download build-time driver/metadata helpers, without running either."""
import argparse
from pathlib import Path
import urllib.request
import zipfile
import io
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
DRIVER = 'https://github.com/Timocop/libwdi-wdi-releases/releases/download/v1.0/x64.zip'


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'A7C2Tools-Build'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


PRESET_NAMES = tuple('slot%d.a7look' % slot for slot in range(1,7)) + (
    'credits.json','NOTICE.txt','CC-BY-NC-SA-4.0.txt')


def import_presets(archive, root=ROOT):
    """Accept the exported pack or a desktop ZIP; extract only six-look data."""
    target=Path(root)/'desktop-assets/presets/default-six-v1'
    with zipfile.ZipFile(archive) as source:
        candidates=[n for n in source.namelist() if n.endswith('/default-six-v1/slot1.a7look')
                    or n=='slot1.a7look' or n=='default-six-v1/slot1.a7look']
        if len(candidates)!=1:raise ValueError('Archive must contain one default-six-v1 pack')
        prefix=candidates[0][:-len('slot1.a7look')]
        # Read all required files before replacing an existing local pack.
        values={name:source.read(prefix+name) for name in PRESET_NAMES}
    target.mkdir(parents=True,exist_ok=True)
    for name,value in values.items():(target/name).write_bytes(value)
    return target


def export_presets(destination, root=ROOT):
    folder=Path(root)/'desktop-assets/presets/default-six-v1'
    values={name:(folder/name).read_bytes() for name in PRESET_NAMES}
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as output:
        for name,value in values.items():output.writestr('default-six-v1/'+name,value)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exiftool-archive', type=Path,
                        help='Optional official Windows ExifTool ZIP to bundle')
    parser.add_argument('--preset-archive',type=Path,help='Six-look ZIP or existing desktop ZIP')
    parser.add_argument('--presets-url',default=os.environ.get('A7C2_PRESET_ARCHIVE_URL'),
                        help='Download the same six-look pack for native CI builds')
    parser.add_argument('--export-presets',type=Path,help='Export only six-look distribution data for CI')
    args = parser.parse_args()
    if args.export_presets:
        print(export_presets(args.export_presets));return
    if args.preset_archive:import_presets(args.preset_archive)
    elif args.presets_url:import_presets(io.BytesIO(fetch(args.presets_url)))
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
