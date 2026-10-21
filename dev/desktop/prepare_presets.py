"""Bundle six owner-supplied compiled looks, in NC/CC/NN/Astia/GR+/GR- order.

python dev/desktop/prepare_presets.py --look file1 ... --look file6
This never opens USB. Generated assets stay outside the source repository.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'src/looks')]
from desktopapp.presets import PACK, NAMES
from looktool import lookfile


def prepare(paths):
    if len(paths) != 6:
        raise ValueError('Provide exactly six compiled looks in NC/CC/NN/Astia/GR+/GR- order')
    sources = []
    for path, name in zip(map(Path, paths), NAMES):
        document = lookfile.read(path)
        lookfile.writer_document(document)
        if document['name'] != name or not document.get('native_photo'):
            raise ValueError('Expected native-photo look ' + name + ': ' + str(path))
        sources.append((path, document))
    output = ROOT / 'desktop-assets/presets' / PACK
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for slot, (path, doc) in enumerate(sources, 1):
        filename = 'slot%d.a7look' % slot
        shutil.copy2(path, output / filename)
        profile = doc.get('raw_profile', {})
        entries.append(dict(slot=slot, name=doc['name'], file=filename, method=doc['method'],
            attribution=doc['attribution'], source_profile=profile.get('source_profile'),
            source_filename=profile.get('source_filename'), copyright=profile.get('copyright')))
    (output / 'credits.json').write_text(json.dumps(dict(pack=PACK, looks=entries),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.copy2(ROOT / 'docs/profiles/CC-BY-NC-SA-4.0.txt', output / 'CC-BY-NC-SA-4.0.txt')
    (output / 'NOTICE.txt').write_text(
        'Bundled fitted looks and embedded original DCP profiles retain their original rights.\n'
        'They are not covered by the tool source MIT license. See credits.json for per-look attribution.\n'
        'Fuji film looks: abpy/FujifilmCameraProfiles (CC BY-NC-SA 4.0); A7C II adaptation: MTriton.\n'
        'GR source profiles retain the Adobe copyright recorded in credits.json and each A7Look.\n'
        'Camera rendering is an approximation; native-grid precision is not full DCP fidelity.\n', encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--look', action='append', required=True)
    print(prepare(parser.parse_args().look))
