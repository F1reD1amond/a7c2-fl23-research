"""Native archive composition without PyInstaller, signing tools or USB."""
import importlib.util
import io
from pathlib import Path
from unittest.mock import patch
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[2]


def module(name):
    spec=importlib.util.spec_from_file_location('desktop_'+name,ROOT/('dev/desktop/'+name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


assets=module('prepare_assets')
build=module('build')


def test_pack_export_import_preserves_six_files_and_notices(tmp_path):
    before=tmp_path/'before';folder=before/'desktop-assets/presets/default-six-v1';folder.mkdir(parents=True)
    for name in assets.PRESET_NAMES:(folder/name).write_bytes(name.encode())
    (folder/'private-photo.ARW').write_bytes(b'not-distributable')
    archive=assets.export_presets(tmp_path/'presets.zip',before)
    after=assets.import_presets(archive,tmp_path/'after')
    assert sorted(p.name for p in after.iterdir())==sorted(assets.PRESET_NAMES)
    for name in assets.PRESET_NAMES:assert (after/name).read_bytes()==(folder/name).read_bytes()


def test_existing_windows_zip_extracts_data_only(tmp_path):
    source=io.BytesIO()
    with zipfile.ZipFile(source,'w') as z:
        for name in assets.PRESET_NAMES:z.writestr('A7C2Tools/_internal/desktop-assets/presets/default-six-v1/'+name,b'asset')
        z.writestr('A7C2Tools/A7C2Tools.exe',b'windows-executable')
        z.writestr('../../outside',b'not-data')
    source.seek(0)
    target=assets.import_presets(source,tmp_path)
    assert len(list(target.iterdir()))==len(assets.PRESET_NAMES)
    assert not list(tmp_path.rglob('*.exe'))


def test_missing_pack_notice_does_not_replace_existing_assets(tmp_path):
    target=tmp_path/'desktop-assets/presets/default-six-v1';target.mkdir(parents=True)
    (target/'slot1.a7look').write_bytes(b'existing')
    source=io.BytesIO()
    with zipfile.ZipFile(source,'w') as z:z.writestr('default-six-v1/slot1.a7look',b'incomplete')
    source.seek(0)
    with pytest.raises(KeyError):assets.import_presets(source,tmp_path)
    assert (target/'slot1.a7look').read_bytes()==b'existing'


def test_windows_output_path_unchanged(tmp_path):
    exe=tmp_path/'A7C2Tools/A7C2Tools.exe';exe.parent.mkdir();exe.write_bytes(b'test')
    result=build.make_windows_zip(tmp_path)
    assert result.name=='A7C2Tools-Windows-x64.zip'
    with zipfile.ZipFile(result) as z:assert z.read('A7C2Tools/A7C2Tools.exe')==b'test'


def test_dmg_has_fresh_staging_and_arch_specific_filename(tmp_path):
    app=tmp_path/'A7C2Tools.app';app.mkdir();(app/'file').write_bytes(b'app')
    old=tmp_path/'dmg-contents';old.mkdir();(old/'stale').write_bytes(b'stale')
    def command(args,**kwargs):
        if args[:2]==['hdiutil','create']:
            stage=Path(args[args.index('-srcfolder')+1])
            assert sorted(p.name for p in stage.iterdir())==['A7C2Tools.app','Applications']
            Path(args[-1]).write_bytes(b'dmg')
    def symlink(path,target,**kwargs):path.write_text(str(target))
    with patch.object(build.platform,'machine',return_value='arm64'), \
            patch.object(build.subprocess,'run',side_effect=command) as run, \
            patch.object(Path,'symlink_to',symlink):
        result=build.make_dmg(tmp_path)
    assert result.name=='A7C2Tools-macOS-arm64.dmg'
    assert not list(tmp_path.glob('a7c2-dmg-*'))
    assert run.call_args.args[0]==['hdiutil','verify',str(result)]
