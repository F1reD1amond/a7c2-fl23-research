"""Exercise packaged imports, assets and an actual native compile, without USB."""
import importlib
from pathlib import Path
import tempfile


def check_audio_conversion():
    """Convert generated mono/stereo/compressed audio using shipped dependencies.

    Importing sound_cli alone does not exercise its lazy media/codec imports.
    Keep this in the frozen self-test so omitted stdlib modules (such as wave)
    and a missing ffmpeg executable fail before a desktop build is distributed.
    """
    import math
    import struct
    import subprocess
    import wave
    import imageio_ffmpeg
    import media
    import native_codec
    import sound_cli
    import json

    executable = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve(strict=True)
    assert executable.is_file()
    results = {}
    with tempfile.TemporaryDirectory(prefix='a7c2-audio-smoke-') as temporary:
        root = Path(temporary)
        rate = 44100
        samples = [round(8000 * math.sin(2 * math.pi * 660 * i / rate))
                   for i in range(round(rate * .12))]
        mono = root / 'generated mono.wav'
        native_codec.write_wav(mono, samples, rate)
        stereo = root / 'generated stereo.wav'
        with wave.open(str(stereo), 'wb') as output:
            output.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
            output.writeframes(b''.join(struct.pack('<hh', x, round(x / 2)) for x in samples))
        compressed = root / 'generated stereo.mp3'
        encoded = subprocess.run([str(executable), '-nostdin', '-v', 'error', '-n',
            '-i', str(stereo), '-c:a', 'libmp3lame', str(compressed)],
            capture_output=True, timeout=60)
        assert encoded.returncode == 0, encoded.stderr.decode('utf-8', errors='replace')
        for label, source in (('mono_wav', mono), ('stereo_wav', stereo), ('stereo_mp3', compressed)):
            original = source.read_bytes()
            output = root / label
            report = media.convert(source, output, duration=.08, peak=.4,
                                   ffmpeg=str(executable))
            payload = (output / 'custom-native.private.bin').read_bytes()
            preview, preview_rate = native_codec.read_wav(output / 'preview.private.wav')
            assert 0 < len(payload) <= 51200 and len(payload) % 64 == 0
            assert len(payload) == report['encoded_bytes']
            assert preview_rate == 24000 and len(preview) == 1920 and any(preview)
            assert preview == native_codec.decode(payload)[:len(preview)]
            assert source.read_bytes() == original and report['camera_io'] is False
            results[label] = 'passed'
        workspace=root/'pending-camera-task';workspace.mkdir()
        state=dict(schema=sound_cli.SCHEMA,pending=dict(command='on',outcome='needs_review',job='synthetic-native-job'))
        sound_cli.save(workspace,state)
        original_state=(workspace/'sound.private.json').read_bytes()
        converted=sound_cli.import_audio(workspace,state,mono,duration=.08,peak=.4)
        assert converted['camera_io'] is False and converted['phase']=='converted_offline'
        assert (workspace/'sound.private.json').read_bytes()==original_state
        assert (workspace/'conversion.private.json').is_file()
        results['unresolved_camera_task_does_not_block_conversion']='passed'
        import trial
        failed=workspace/'failed-enable';failed.mkdir()
        events=[dict(event=event,stage='shutter.staged.so',mode=0) for event in (
            'native_stage_intent','native_intent','native_result_verified','native_cleanup_verified')]
        evidence=dict(schema='a7c2-shutter-job/1',phase='needs_review',
            camera_firmware_written=False,journal=events)
        trial.save(failed,evidence)
        before=(failed/'job.private.json').read_bytes()
        state.update(history=[],native_job=str(failed),pending=dict(command='on',job=str(failed)))
        assert sound_cli.retire_readonly_failure(workspace,state)
        assert state['pending'] is None and state['native_job'] is None
        assert (failed/'job.private.json').read_bytes()==before
        evidence['journal']=[dict(e,mode=1) for e in events]
        assert not trial.completed_readonly_failure(evidence)
        results['completed_readonly_failure_released_unknown_write_still_blocked']='passed'
        import buffer_trial
        old=root/'completed-audio';old.mkdir()
        raw=bytearray(208)
        struct.pack_into('<8sIIq',raw,0,b'A7PCM001',1,10,0)
        struct.pack_into('<6I',raw,88,0,0xffffffff,1,1,1,0)
        struct.pack_into('<8I',raw,112,0,0,0,0,1,3776,1,0)
        struct.pack_into('<4I',raw,192,0,0,0xffffffff,1)
        prior=dict(identity={'model':'ILCE-7CM2','serial_sha256':'offline-only'},
                   result=buffer_trial.parse(raw),lease_token_hex=bytes(range(16)).hex())
        trial.save(old,prior);(old/'report.private.bin').write_bytes(raw)
        class MarkerCamera:
            identity=prior['identity']
            marker=buffer_trial.initial_marker(prior)
            def read(self,*args):return self.marker
            def temp_read(self,*args):return None
            def temp_remove(self,name):
                assert name=='shutter.custom.lease'
                self.marker=None
        marker_camera=MarkerCamera()
        replacement=buffer_trial.replace_completed_marker(marker_camera,root,[old])
        assert replacement['completed_prior_marker_replaced'] and marker_camera.marker is None
        assert replacement['previous_cp_handle_released'] is False
        results['completed_sound_marker_replaced_before_next_registration']='passed'
    return dict(results, preview_rate_hz=24000, camera_io=False,
                bundled_ffmpeg='passed')


def run():
    from desktopapp.worker import setup_runtime
    from desktopapp.paths import ROOT
    setup_runtime()
    from desktopapp import reloadguide
    audition=dict(phase='temporary_pcm_registered_cold_reload_required_after_test')
    assert not reloadguide.required('sound_audition',audition)
    assert '保持相机开机' in reloadguide.sound_notice('sound_audition',audition)['text']
    assert '试听是可选步骤' in reloadguide.sound_notice('sound_install',dict(phase='sound_conversion_required'))['text']
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    instruction=bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm('bx lr')[0])
    assert next(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(instruction,0)).mnemonic=='bx'
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
    from unicorn.arm64_const import UC_ARM64_REG_X0
    cpu=Uc(UC_ARCH_ARM64,UC_MODE_ARM);cpu.mem_map(0x1000,4096)
    cpu.mem_write(0x1000,bytes.fromhex('200080d21f2003d5'))
    # Match the boot reader's code-hook stop path. The frozen Windows engine
    # aborts on count=1 termination; stopping through the hook avoids that path.
    def stop_emulator(engine,address,size,data):
        if address==0x1004:engine.emu_stop()
    cpu.hook_add(UC_HOOK_CODE,stop_emulator)
    cpu.emu_start(0x1000,0x1008,count=1000000)
    assert cpu.reg_read(UC_ARM64_REG_X0)==1
    del cpu
    importlib.import_module('desktopapp.allinone')
    from desktopapp import allinone, presets, lookbatch, reviewnames, completion
    from looktool import bundle
    packed, selected = bundle.documents(presets.resolve(dict(preset_pack=presets.PACK)))
    assert [row['name'] for row in selected] == list(presets.NAMES)
    defaults=lookbatch.options(presets.catalog())
    assert len(defaults['looks'])==6 and defaults['fl23'] is False and defaults['sound'] is False
    mixed=lookbatch.options([dict(slot=4,action='restore'),dict(presets.catalog()[1],action='write')])
    assert mixed['reset_slots']==[4] and [r['slot'] for r in mixed['looks']]==[2]
    assert not mixed['fl23'] and not mixed['sound'] and not mixed['vertical_persistent']
    importlib.import_module('desktopapp.lookeditor')
    from looktool import factoryrecover
    previous_pending=factoryrecover.pending
    try:
        factoryrecover.pending=lambda *args,**kwargs:None
        with tempfile.TemporaryDirectory() as temporary:
            calls=[]
            def simulated(action,args,folder):
                calls.append(action)
                if action == 'direct_install_all':
                    assert args['options']['vertical_persistent'] is True
                    _, rows = bundle.documents(args['options'])
                    assert [r['name'] for r in rows] == list(presets.NAMES)
                    assert all(Path(r['path']).parent == Path(temporary) / 'inputs' for r in rows)
                return {'phase':'LOADED','mode':'install_all','workspace':args.get('workspace',''),
                    'vertical_result':dict(persistent=True,loaded_verified=True,saved='ON',running='ON',alias_count=3)}
            result=allinone.run(dict(workspace=temporary,firmware='2.01',power_confirmed=True,
                options=dict(fl23=False,sound=False,vertical=True,plugin=False,preset_pack=presets.PACK)),dispatch=simulated)
            assert result['phase']=='COMPLETE' and not result['physical_checks_accepted']
            assert calls==['usb_prepare','direct_install_all']
            assert '电子快门声：本次未选择' in completion.text(result)
            assert completion.console_summary(result)['phase']=='COMPLETE'
            assert '无需每次连接电脑' in completion.text(result)
    finally:factoryrecover.pending=previous_pending
    from looktool import nativebuild, checkpointworker, device_layout, resources, nameworker
    from looktool.devicesession import modules
    transport, core = modules()
    assert nativebuild.ROOT == ROOT
    assert Path(core.__file__).resolve() == ROOT / 'src/camera_runtime/core.py'
    assert core.assets()
    core.merge_colors(bytes(8192), bytes(28672))
    assert device_layout.runtime()['schema'] == 'a7c2-lut-runtime/1'
    native_windows=device_layout.fl23_native_windows()
    gamma=next(new for at,old,new,legacy in native_windows if at==0x1100b80)
    import struct
    assert struct.unpack_from('<II',gamma,0xe78+19*8)==(48,46)
    assert struct.unpack_from('<II',gamma,0xe78+20*8)==(49,47)
    assert device_layout.fl23_previous_values(0x1100b80)
    assert (ROOT / 'src/looks/assets/native-photo-v2.json').is_file()
    for name in ('compilelook', 'lookfile', 'rawauto', 'rawprofiles', 'checkpointjob', 'devicejob', 'direct', 'directresume', 'factoryrecover', 'bundle','namespause','verticalpersist'):
        importlib.import_module('looktool.' + name)
    import sys
    sys.path.insert(0, str(ROOT / 'src/desktopapp/vendor'))
    from fwtool.sony import dat, fdat
    from fwtool.archive import ext2, fat
    from desktopapp.official import builtin
    assert builtin()['version'] == '2.01'
    sys.path[:0] = [str(ROOT / 'src/vertical'), str(ROOT / 'dev/shutter_sound')]
    importlib.import_module('verticaltool.device')
    assert (ROOT / 'src/vertical/assets/aliases_recovery.so').read_bytes()[:4] == b'\x7fELF'
    importlib.import_module('sound_cli')
    audio_conversion = check_audio_conversion()
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
        assert '#define CHECKPOINT_STREAM_RESTORE 1' in (Path(folder) / 'names.private.h').read_text()
        _,forward=nameworker.prepare({n:original for n in nameworker.filenames()},{1:'Smoke'},bytes(16),
            '0123456789abcdef',Path(folder)/'forward',byte_only=True)
        assert forward['stream_install'] and Path(forward['path']).read_bytes()[:4]==b'\x7fELF'
    return {'camera_io': False, 'project_imports': 'passed', 'assets': 'passed', 'builtin_factory_reference': 'passed',
            'native_cross_compile': 'passed', 'native_assembler_disassembler':'passed',
            'one_click_offline_sequence':'passed','look_batch_defaults':'passed','streaming_names_compile':'passed',
            'bundled_six_looks':list(presets.NAMES),'fl23_pr6_movie_routes':'passed',
            'completion_summary':'passed','persistent_vertical_plan':'passed',
            'audio_conversion':audio_conversion,'sound_install_emulator':'passed','numpy': np.__version__}
