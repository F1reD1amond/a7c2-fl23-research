"""Backup-free project operations over fresh camera bytes.

Original firmware is a reference, not another body's backup. Only transaction
windows and target settings are retained; no complete body backup is created.
"""
import copy
import base64
from datetime import datetime
import json
from pathlib import Path
import struct
import uuid
import zlib
from . import checkpoint, checkpointworker, device_layout, devicesettings, nameworker, resources
from . import nativebuild, photoformat, photoio, six
from .checkpointjob import CheckpointCamera, Rollback
from .devicesession import invoke, modules
from .power import require_power
from .backupstore import write_json

MENU_FLAGS = (0x59892ca, 0x5989382)
ST_ADJUSTMENTS = (0, 0, 0, 0, 0, 4, 3, 1)


def recipe_defaults(ap, slots):
    result = {}
    def key(attribute):
        row = struct.unpack_from('<8I', ap, 0x57c6710 + (attribute - 0x14ea) * 32)
        if row[6] != attribute or row[1] >> 16 != 0x02cf:
            raise ValueError('Creative Look descriptor differs')
        return row[1]
    for slot in slots:
        if slot not in range(1, 7):
            raise ValueError('Select custom slots 1..6')
        selector = slot + 9
        result[key(0x14ea + selector)] = b'\0'
        for index, value in enumerate(ST_ADJUSTMENTS):
            result[key(0x1520 + index * 18 + selector)] = struct.pack('<I', value)
    return result


def color_regions():
    result = {checkpoint.CP_KEYS[0]: [], checkpoint.CP_KEYS[1]: []}
    for parameter, slot in ((55, 23), (56, 25)):
        result[checkpoint.CP_KEYS[0]] += [(0x1200 + parameter, 1), (0x1250 + slot * 64, 64)]
        result[checkpoint.CP_KEYS[1]] += [(0x196 + parameter, 1), (0x1e0 + slot * 768, 576)]
    return result


def plan(current, records, mode, *, factory=None, slot=None, look=None, name=None):
    """Pure planning: preserve every field outside the declared project scope."""
    _, core = modules()
    ap, cp = current['appFw.so'], current['cpapp-b.bin']
    target = dict(current)
    wanted = [{}, {}]
    rename = None
    if mode in ('factory_reset', 'fl23_enable'):
        for key, start, count in ((0x02a40001, 0x1200, 80), (0x02a4000d, 0x196, 74)):
            mapping = records[1][key].data[start:start + count]
            if len(mapping) != count or any(value in (23, 25) for index, value in enumerate(mapping) if index not in (55, 56)):
                raise ValueError('FL23 color positions are referenced by another native look; calibration was not changed')
    if mode == 'factory_reset':
        if factory is None:
            raise ValueError('Prepare the original Sony 2.01 reference first')
        regional = factory.get('schema') == 'a7c2-factory-regions/1'
        for program in checkpoint.PROGRAM_PATHS:
            if regional:
                spec = factory['programs'][program]
                if factory['model'] != 'ILCE-7CM2' or factory['version'] != '2.01' or len(current[program]) != spec['bytes']:
                    raise ValueError('Original reference model/version/program size differs')
                result = bytearray(current[program])
                for region in spec['regions']:
                    raw = zlib.decompress(base64.b64decode(region['zlib_base64']))
                    at, size = region['offset'], region['bytes']
                    if len(raw) != size or not 0 <= at <= at + size <= len(result):
                        raise ValueError('Invalid original reference region')
                    result[at:at + size] = raw
                target[program] = bytes(result)
            else:
                if len(current[program]) != len(factory[program]):
                    raise ValueError('Original and current program sizes differ')
                target[program] = factory[program]
        wanted[0] = recipe_defaults(target['appFw.so'], range(1, 7))
        wanted[0].update({key: b'\0' for key in checkpoint.AP_KEYS})
        original_records = None if regional else core.backup_records(factory['CX89700_ALLLANG.bin'])
        for key, spans in color_regions().items():
            value = bytearray(records[1][key].data)
            for start, size in spans:
                if regional:
                    region = next(r for r in factory['color_units'][str(key)] if r['offset'] == start and r['bytes'] == size)
                    raw = zlib.decompress(base64.b64decode(region['zlib_base64']))
                    if len(raw) != size:
                        raise ValueError('Original color-region length differs')
                    value[start:start + size] = raw
                else:
                    value[start:start + size] = original_records[1][key].data[start:start + size]
            wanted[1][key] = bytes(value)
        for filename in nameworker.filenames():
            key = 'resources/' + filename
            target[key] = resources.before_custom(current[key])
    elif mode == 'fl23_enable':
        import compat
        target.update(compat.plan(ap, cp, '2.01', transitions=False)[2])
        wanted[0] = dict(zip(checkpoint.AP_KEYS, (b'\x0a', b'\x0b')))
        units = {key: bytearray(records[1][key].data) for key in checkpoint.CP_KEYS}
        for row in core.read_json(core.BASE / 'assets/colors.json'):
            parameter, index = row['parameter'], row['slot']
            chroma, matrix = core.colour_record(row)
            a, b = units[checkpoint.CP_KEYS[0]], units[checkpoint.CP_KEYS[1]]
            if a[0x1200 + parameter] not in (0, index) or b[0x196 + parameter] not in (0, index):
                raise ValueError('FL23 parameter positions are used by another mapping')
            a[0x1200 + parameter] = b[0x196 + parameter] = index
            a[0x1250 + index * 64:0x1250 + (index + 1) * 64] = chroma
            b[0x1e0 + index * 768:0x1e0 + index * 768 + 576] = matrix
        wanted[1] = {key: bytes(value) for key, value in units.items()}
    elif mode == 'fl23_disable':
        result = bytearray(ap)
        for at in MENU_FLAGS:
            if ap[at:at + 2] not in (b'\0\0', b'\1\0'):
                raise ValueError('FL23 menu field conflicts at ' + hex(at))
            result[at:at + 2] = b'\0\0'
        target['appFw.so'] = bytes(result)
    elif mode in ('slot_default', 'look_import'):
        identity = device_layout.structural(ap, cp)
        wanted[0] = recipe_defaults(ap, [slot])
        bank = photoformat.extract_bank(cp, records[1][0x02a40001].data,
            records[1][0x02a4000d].data, gamma_table_va=0x1209480,
            regular_row=0, still_row=10, color_parameter=0)[0] if photoio.present(cp) else None
        if mode == 'slot_default':
            raw = bytes(six.TABLE_BYTES)
            if identity['kind'] != 'legacy-six' and not identity.get('first_install'):
                target.update(device_layout.deactivate(ap, cp, slot, raw, hash_checks=False, native_bank=bank, transitions=False)[2])
            elif identity['kind'] == 'legacy-six':
                target.update(device_layout.replace(ap, cp, {slot: raw}, hash_checks=False, native_bank=bank, transitions=False)[2])
                rename = ({slot: 'ST'}, identity['label_ids'])
        else:
            from . import lookfile
            raw = lookfile.writer_document(look)
            stage = look.get('native_photo')
            base_cp = device_layout.replace(ap, cp, {slot: raw}, hash_checks=False, transitions=False)[2]['cpapp-b.bin'] if identity.get('first_install') else cp
            bank = photoformat.extract_bank(base_cp, records[1][0x02a40001].data,
                records[1][0x02a4000d].data, gamma_table_va=0x1209480,
                regular_row=0, still_row=10, color_parameter=0)[0] if stage is not None or photoio.present(cp) else None
            target.update(device_layout.replace(ap, cp, {slot: raw}, hash_checks=False,
                native_photo={slot: stage}, native_bank=bank, transitions=False)[2])
            rename = ({slot: name or look['name']}, identity['label_ids'])
        if rename:
            for filename in nameworker.filenames():
                key = 'resources/' + filename
                target[key] = resources.rename(current[key], *rename)[0]
    else:
        raise ValueError('Unknown direct operation: ' + mode)
    return target, wanted, rename


class DirectJob(Rollback):
    def __init__(self, folder, *, factory=CheckpointCamera, zig=None):
        super().__init__(folder, factory=factory, zig=zig)
        self.state_path = self.root / 'direct.private.json'

    def save(self, phase, **values):
        self.state.update(values, phase=phase)
        write_json(self.state_path, self.state)
        labels = {'READING': '读取当前状态', 'PREFLIGHT_VERIFIED': '只校验完成',
                  'WRITING': '正在应用所选操作', 'AWAITING_RELOAD': '读回完成，等待断电重开',
                  'LOADED': '加载状态符合目标', 'COMPLETE': '完成', 'NEEDS_REVIEW': '已停止，请保留日志核对结果'}
        print(labels.get(phase, phase), flush=True)

    def settings(self, camera, before, wanted):
        ram, saved = [camera.records(before['settings-' + kind + '.bin']) for kind in ('ram', 'saved')]
        new_ram, new_saved = copy.deepcopy(ram), copy.deepcopy(saved)
        for chip in (0, 1):
            for key, value in wanted[chip].items():
                for records in (new_ram, new_saved):
                    if len(records[chip][key].data) != len(value):
                        raise ValueError('Default setting length differs')
                    records[chip][key] = records[chip][key]._replace(data=value)
                if chip == 1:
                    stored = bytearray(saved[1][key].data)
                    for at, size in color_regions()[key]:
                        stored[at:at + size] = value[at:at + size]
                    new_saved[1][key] = saved[1][key]._replace(data=bytes(stored))
        keys = list(wanted[0])
        if any(saved[0][key].data != value for key, value in wanted[0].items()):
            devicesettings.require_save_preserves_unsaved(ram, saved, set(keys))
        if any(saved[1][key].data != new_saved[1][key].data for key in wanted[1]):
            for key, value in ram[1].items():
                if key >> 16 == 0x02a4 and key not in wanted[1] and value != saved[1].get(key):
                    raise ValueError('Unrelated unsaved CP settings must be saved first')
        return keys, new_ram, new_saved, ram, saved

    def restore_settings(self, camera, prepared):
        # Reuse the reviewed group-save/preservation algorithm, restricted to
        # selected units; a menu-only operation never changes look settings.
        if not prepared[0] and prepared[1] == prepared[3] and prepared[2] == prepared[4]:
            return
        keys, ram, saved, old_ram, old_saved = prepared
        # Existing rollback always considers both CP units, so unchanged ones
        # must remain represented; no factory unit replaces calibration data.
        super().restore_settings(camera, (keys, ram, saved, old_ram, old_saved))

    def forward_names(self, camera, build, mode):
        if build.get('unchanged'):
            return
        return invoke(camera, Path(build['path']).read_bytes(), stage='lut-names-staged.so',
            request='a7c2.names.request', result='a7c2.names.result',
            contents=struct.pack('<8sII', b'A7NAM001', mode, 0), mode=mode,
            decode=lambda raw: nameworker.validate(raw, mode, build), record=self.record,
            save_raw=lambda raw: self.raw('names-forward-' + str(mode) + '.bin', raw))

    def run_direct(self, mode, *, version, power_confirmed, factory_values=None,
                   factory_path=None, slot=None, look_path=None, name=None):
        require_power(confirmed=power_confirmed)
        if version != '2.01':
            raise ValueError('Direct operations support ILCE-7CM2 2.01 only')
        if self.root.exists() and any(self.root.iterdir()):
            raise ValueError('Use a fresh transaction; preserve unknown outcomes')
        self.root.mkdir(parents=True, exist_ok=True)
        look = None
        if look_path:
            from . import lookfile
            look = lookfile.read(look_path)
            lookfile.writer_document(look)
            (self.root / 'reference.a7look').write_bytes(Path(look_path).read_bytes())
        self.state = dict(schema='a7c2-direct-job/1', mode=mode, slot=slot, name=name,
            factory_path=factory_path, job_id=uuid.uuid4().hex[:16], journal=[], backup_created=False,
            power_confirmation=require_power(confirmed=True))
        self.save('READING')
        try:
            with self.factory() as camera:
                self.state['identity'] = camera.identity
                current = self.capture(camera)
                target, wanted, rename = plan(current, camera.records(current['settings-ram.bin']), mode,
                    factory=factory_values, slot=slot, look=look, name=name)
                # Preserve the independent saved calibration when reconstructing
                # CP units; only the declared FL23 subranges use factory data.
                prepared = self.settings(camera, current, wanted)
                programs = checkpointworker.build_programs(current, target, self.root / 'worker', self.zig)
                inverse_names = None
                forward = None
                if rename:
                    sources = {n: current['resources/' + n] for n in nameworker.filenames()}
                    changed, forward = nameworker.prepare(sources, rename[0], current['appFw.so'],
                        self.state['job_id'], self.root / 'names', self.zig,
                        target_ap=target['appFw.so'], label_ids=rename[1], byte_only=True)
                    for n, value in changed.items():
                        target['resources/' + n] = value
                else:
                    inverse_names = checkpointworker.build_names(current, target,
                        self.root / 'worker', self.state['job_id'], self.zig)
                runtime = self.native(camera, 'runtime', 0)
                if runtime['image_mode'].strip() not in ('0', '2'):
                    raise ValueError('Unsupported retained image state')
                planned_change = bool(programs or inverse_names or (forward and not forward.get('unchanged'))
                    or prepared[1] != prepared[3] or prepared[2] != prepared[4])
                if planned_change and not runtime.get('boot_id', '').strip():
                    raise ValueError('Read-only boot identity is unavailable; no program/settings writes started')
                self.state['source_boot_id'] = runtime.get('boot_id', '').strip()
                for span in runtime['spans']:
                    expected = current['appFw.so'][span['offset']:span['offset'] + span['length']].hex()
                    if span['memory'] != expected or span['disk'] != expected:
                        raise ValueError('Finish the previous cold reload before changing another feature')
                for build in programs:
                    self.native(camera, 'program', 0, build)
                if inverse_names:
                    self.native(camera, 'names', 4, inverse_names)
                if forward:
                    self.forward_names(camera, forward, 0)
                self.save('PREFLIGHT_VERIFIED', program_builds=programs,
                          inverse_name_build=inverse_names, forward_name_build=forward)
                self.save('WRITING')
                for index, build in enumerate(programs):
                    print('正在写入程序窗口批次 %d/%d' % (index + 1, len(programs)), flush=True)
                    self.native(camera, 'program', 1, build)
                for program, path in checkpoint.PROGRAM_PATHS.items():
                    if camera.read(path) != target[program]:
                        raise ValueError('Complete program readback differs: ' + program)
                if inverse_names:
                    self.native(camera, 'names', 2, inverse_names)
                if forward:
                    self.forward_names(camera, forward, 1)
                self.readback(camera, target)
                self.restore_settings(camera, prepared)
                if forward:
                    self.forward_names(camera, forward, 3)
                changed = planned_change
                if changed and runtime['image_mode'].strip() == '2':
                    self.native(camera, 'wbi', 0)
                    self.native(camera, 'wbi', 1)
            self.save('AWAITING_RELOAD' if changed else 'LOADED', raw_profile_effective_since=datetime.now().isoformat(timespec='microseconds'))
            print('所有读写已结束。正常关机，拔掉所有外部供电，等存取灯熄灭后取出电池至少一分钟；重开后检查功能并核对。' if changed else '目标已经生效，没有重复写入或清除开机快照。', flush=True)
            return self.state
        except BaseException as exc:
            self.save('NEEDS_REVIEW', error=str(exc))
            raise

    def verify_direct(self, *, factory_values=None, accepted=False):
        self.state = json.loads(self.state_path.read_text(encoding='utf-8'))
        if self.state['phase'] not in ('AWAITING_RELOAD', 'LOADED', 'COMPLETE'):
            raise ValueError('Inspect the unfinished transaction before another write')
        look = None
        if (self.root / 'reference.a7look').exists():
            from . import lookfile
            look = lookfile.read(self.root / 'reference.a7look')
        with self.factory(self.state['identity']) as camera:
            current = self.capture(camera)
            target, wanted, _ = plan(current, camera.records(current['settings-ram.bin']), self.state['mode'],
                factory=factory_values, slot=self.state['slot'], look=look, name=self.state['name'])
            self.readback(camera, target)
            for memory in (False, True):
                records = camera.records(camera.snapshot(memory))
                for chip in (0, 1):
                    for key, value in wanted[chip].items():
                        actual = records[chip][key].data
                        differs = (any(actual[at:at + size] != value[at:at + size] for at, size in color_regions()[key])
                                   if chip == 1 else actual != value)
                        if differs:
                            raise ValueError('Reloaded default setting differs')
            runtime = self.native(camera, 'runtime', 0)
            if self.state['phase'] == 'AWAITING_RELOAD':
                before_boot = self.state.get('source_boot_id')
                current_boot = runtime.get('boot_id', '').strip()
                if not before_boot or not current_boot or before_boot == current_boot:
                    raise ValueError('尚未确认新的冷启动。完成断电重开后再核对，不要重复写入。')
            for span in runtime['spans']:
                expected = target['appFw.so'][span['offset']:span['offset'] + span['length']].hex()
                if span['memory'] != expected or span['disk'] != expected:
                    raise ValueError('Old application remains loaded; complete the cold restart')
        self.save('COMPLETE' if accepted else 'LOADED', physical_checks_accepted=accepted)
        if accepted and self.state['mode'] in ('look_import', 'slot_default', 'factory_reset'):
            from .rawidentity import after_verified
            slots = list(range(1, 7)) if self.state['mode'] == 'factory_reset' else [self.state['slot']]
            documents = [dict(name='ST', raw_profile=None) for _ in slots]
            if look:
                documents = [dict(name=self.state['name'] or look['name'], raw_profile=look.get('raw_profile'))]
            after_verified(self.state, self.save, self.state['job_id'], documents, slots)
        return self.state
