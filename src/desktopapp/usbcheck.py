"""Optional read-only USB bulk-transfer sample; never stages native workers."""
import time
from pathlib import Path
from .paths import write_json

PATH='/usr/share/app/image_00_32_IPSX.uxc'
NOTE='短时读取通过不保证刷写期间不会掉线；结果不代表线材认证或写入安全保证。'


def run(job,*,factory=None,rounds=3):
    if factory is None:
        from looktool.devicesession import Camera
        factory=Camera
    job=Path(job);job.mkdir(parents=True,exist_ok=True)
    report=dict(schema='a7c2-usb-stability/1',phase='READING',rounds=[],camera_firmware_written=False,
                camera_settings_written=False,native_worker_executed=False,note=NOTE)
    def save():write_json(job/'usb-stability.private.json',report)
    save();start=time.monotonic()
    try:
        with factory() as camera:
            baseline=None
            for number in range(1,rounds+1):
                print('USB 稳定性检测：只读传输 %d/%d，不写固件或设置。'%(number,rounds),flush=True)
                begin=time.monotonic()
                try:
                    raw=camera.read(PATH)
                    if raw is None or not 4096<=len(raw)<=32*1024*1024:
                        raise ValueError('固定测试资源未完整读回')
                    if baseline is not None and raw!=baseline:
                        raise ValueError('重复读回的字节不一致')
                except BaseException:
                    mark=getattr(camera,'mark_unknown',None)
                    if mark:mark()
                    raise
                baseline=raw
                report['rounds'].append(dict(round=number,bytes=len(raw),seconds=round(time.monotonic()-begin,3),passed=True))
                save()
        report.update(phase='PASSED',total_bytes=sum(r['bytes'] for r in report['rounds']),
                      seconds=round(time.monotonic()-start,3),camera_io_ended=True)
        save();print('三轮只读传输均完成且字节一致。'+NOTE,flush=True)
        return report
    except BaseException as exc:
        report.update(phase='FAILED',failed_round=len(report['rounds'])+1,error_type=type(exc).__name__,error=str(exc),
                      camera_io_ended=True,seconds=round(time.monotonic()-start,3))
        save()
        raise RuntimeError('USB 稳定性检测未通过（第 %d/%d 轮）：%s。请换线或直连电脑 USB 接口后重测；本次没有固件或设置写入。'%
                           (report['failed_round'],rounds,str(exc))) from exc
