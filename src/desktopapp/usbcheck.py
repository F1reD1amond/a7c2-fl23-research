"""Read-only USB soak test over the camera's program files; never stages native workers.

The two program files are the same large reads a real write performs during its
full readback. Every round re-reads both and must match the first round byte for
byte. The test runs for a minimum duration and a minimum number of rounds, and a
read that stalls is treated as a failure, not just a slow pass.
"""
import time
from pathlib import Path
from .paths import write_json

PATHS=('/usr/lib/appFw.so','/cp/cpapp-b.bin')
MIN_SECONDS=120
MIN_ROUNDS=5
MAX_ROUNDS=60
STALL_SECONDS=20
MIN_BYTES,MAX_BYTES=1024*1024,256*1024*1024
NOTE='通过只说明这段时间内连续只读传输稳定；不保证刷写期间一定不掉线，也不代表线材认证。'


def run(job,*,factory=None,clock=time.monotonic,min_seconds=MIN_SECONDS,min_rounds=MIN_ROUNDS,max_rounds=MAX_ROUNDS):
    if factory is None:
        from looktool.devicesession import Camera
        factory=Camera
    job=Path(job);job.mkdir(parents=True,exist_ok=True)
    report=dict(schema='a7c2-usb-stability/2',phase='READING',paths=list(PATHS),rounds=[],
                minimum_seconds=min_seconds,minimum_rounds=min_rounds,stall_seconds=STALL_SECONDS,
                camera_firmware_written=False,camera_settings_written=False,native_worker_executed=False,note=NOTE)
    def save():write_json(job/'usb-stability.private.json',report)
    save();start=clock();number=0
    try:
        with factory() as camera:
            baseline={}
            while number<min_rounds or clock()-start<min_seconds:
                if number>=max_rounds:break
                number+=1
                print('USB 稳定性检测：第 %d 轮只读读取程序文件（至少 %d 轮、%d 秒），不写固件或设置。'%
                      (number,min_rounds,min_seconds),flush=True)
                reads=[]
                for path in PATHS:
                    begin=clock()
                    try:
                        raw=camera.read(path)
                        seconds=clock()-begin
                        if raw is None or not MIN_BYTES<=len(raw)<=MAX_BYTES:
                            raise ValueError('程序文件未完整读回：'+path)
                        if path in baseline and raw!=baseline[path]:
                            raise ValueError('重复读回的字节不一致：'+path)
                        if seconds>STALL_SECONDS:
                            raise TimeoutError('读取 %s 用时 %.1f 秒，超过 %d 秒，连接不稳定'%(path,seconds,STALL_SECONDS))
                    except BaseException:
                        mark=getattr(camera,'mark_unknown',None)
                        if mark:mark()
                        raise
                    baseline.setdefault(path,raw)
                    reads.append(dict(path=path,bytes=len(raw),seconds=round(seconds,3),
                                      mb_per_second=round(len(raw)/1048576/seconds,2) if seconds>0 else None))
                report['rounds'].append(dict(round=number,bytes=sum(r['bytes'] for r in reads),reads=reads,passed=True))
                save()
        speeds=[r['mb_per_second'] for row in report['rounds'] for r in row['reads'] if r['mb_per_second']]
        report.update(phase='PASSED',total_bytes=sum(r['bytes'] for r in report['rounds']),
                      seconds=round(clock()-start,3),camera_io_ended=True,
                      slowest_mb_per_second=min(speeds) if speeds else None,
                      fastest_mb_per_second=max(speeds) if speeds else None)
        save()
        print('%d 轮只读传输均完成，共 %.1f MB，用时 %.0f 秒，逐轮字节一致。%s'%
              (len(report['rounds']),report['total_bytes']/1048576,report['seconds'],NOTE),flush=True)
        return report
    except BaseException as exc:
        report.update(phase='FAILED',failed_round=number or 1,error_type=type(exc).__name__,error=str(exc),
                      camera_io_ended=True,seconds=round(clock()-start,3))
        save()
        raise RuntimeError('USB 稳定性检测未通过（第 %d 轮）：%s。请换线或直连电脑 USB 接口后重测；本次没有固件或设置写入。'%
                           (report['failed_round'],str(exc))) from exc
