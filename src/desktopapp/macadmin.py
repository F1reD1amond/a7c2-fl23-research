"""macOS system authorization for explicit camera workers.

Like MDHan's sudo adapter, only camera commands receive root privileges.
The GUI remains the login user. Passwords belong to the macOS dialog only.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import traceback
from .paths import data_root,write_json


def required(action):
    if sys.platform!='darwin' or os.geteuid()==0:return False
    from .jobs import CAMERA_ACTIONS
    return action in CAMERA_ACTIONS


def applescript_string(value):
    # AppleScript quoting and POSIX shell quoting are separate layers.
    return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('\r','\\r').replace('\n','\\n')+'"'


def shell_command(request,uid,gid,environment):
    from .jobs import worker_command
    argv=worker_command(request)
    argv[argv.index('--worker')]='--privileged-worker'
    argv.extend([str(uid),str(gid)])
    assignments={key:environment[key] for key in ('HOME','USER','LOGNAME','PATH','TMPDIR',
        'A7C2_ZIG_CACHE','A7LOOK_AUTO_SETTINGS') if environment.get(key)}
    assignments.update(A7C2_DESKTOP_DATA=str(data_root()),PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    assignments.setdefault('A7C2_ZIG_CACHE',str(data_root()/'compiler-cache'))
    shell=shlex.join(['/usr/bin/env']+[key+'='+value for key,value in assignments.items()]+argv)
    parent=Path(request).parent
    shell+=' > '+shlex.quote(str(parent/'authorization.stdout.log'))
    shell+=' 2> '+shlex.quote(str(parent/'authorization.stderr.log'))
    return shell


def command(request,uid,gid,environment):
    shell=shell_command(request,uid,gid,environment)
    script='do shell script '+applescript_string(shell)+' with prompt '+applescript_string(
        'A7C II Tools 需要接管相机 USB 进行本次操作。请输入 Mac 管理员密码；程序不会保存密码。')+' with administrator privileges'
    return ['/usr/bin/osascript','-e',script]


def execute(path):
    path=Path(path).resolve();request=json.loads(path.read_text(encoding='utf-8'))
    job=Path(request['job_dir']);job.mkdir(parents=True,exist_ok=True)
    status=job/'status.private.json'
    write_json(status,dict(phase='WAITING_AUTHORIZATION',action=request['action'],camera_io=False))
    with (job/'worker.log').open('a',encoding='utf-8') as log:
        log.write('等待 macOS 系统管理员授权；尚未接管 USB 或开始相机操作。取消不会刷写相机。\n')
    print('等待 macOS 管理员授权，请在系统弹窗中确认。',flush=True)
    try:
        result=subprocess.run(command(path,os.getuid(),os.getgid(),os.environ),
                              capture_output=True,text=True,encoding='utf-8',errors='replace')
    except Exception as exc:
        result=None;detail=repr(exc)
    else:detail=(result.stdout+'\n'+result.stderr).strip()
    current=json.loads(status.read_text(encoding='utf-8'))
    write_json(job/'authorization.private.json',dict(system_dialog=True,
        exit_code=result.returncode if result else None,detail=detail,password_stored=False))
    if current.get('phase') in ('SUCCEEDED','FAILED'):
        # The privileged worker owns the actual outcome; never replay it.
        return 0 if current['phase']=='SUCCEEDED' else 2
    extra=job/'authorization.stderr.log'
    if extra.is_file():detail+='\n'+extra.read_text(encoding='utf-8',errors='replace')
    cancelled='-128' in detail or 'canceled' in detail.lower() or 'cancelled' in detail.lower()
    error=('已取消 macOS 管理员授权；本次相机操作尚未开始，可重新点击原按钮。' if cancelled else
           'macOS 授权进程未完成，相机操作未报告开始。请保留日志；系统详情：'+detail)
    with (job/'worker.log').open('a',encoding='utf-8') as log:log.write(error+'\n'+detail+'\n')
    write_json(status,dict(phase='FAILED',action=request['action'],error=error,
        error_type='MacAuthorizationCancelled' if cancelled else 'MacAuthorizationError',
        camera_io=False,authorization_denied=True))
    return 2


def return_ownership(request,uid,gid):
    """Return app-created root files to the login user, as in the sudo adapter."""
    args=request.get('arguments',{})
    roots=[data_root(),Path(request['job_dir'])]
    roots.extend(Path(args[key]).expanduser() for key in ('workspace','backup') if args.get(key))
    home=Path.home().resolve();seen=set()
    roots.extend([home/'Library/Application Support/Adobe/Lightroom/Modules/A7LookAuto.lrplugin',
                  home/'Library/Application Support/Adobe/CameraRaw/CameraProfiles/A7Look-Imported'])
    for value in roots:
        if value.is_symlink():continue
        root=value.resolve()
        if root in seen or root==home or len(root.parts)<3:continue
        if root.parts[1] in ('System','Library','usr','bin','sbin','etc','dev') and not root.is_relative_to(home):continue
        if root.parts[1]=='Volumes' and len(root.parts)<=3:continue
        seen.add(root)
        if not root.exists():continue
        for directory,folders,files in os.walk(root,followlinks=False):
            folders[:]=[name for name in folders if not (Path(directory)/name).is_symlink()]
            for path in [Path(directory)]+[Path(directory)/name for name in files]:
                if not path.is_symlink() and path.stat().st_uid==0:
                    os.chown(path,uid,gid,follow_symlinks=False)


def privileged(path,uid,gid):
    if sys.platform!='darwin' or os.geteuid()!=0 or uid<=0 or gid<0:
        raise RuntimeError('相机授权 worker 必须由 macOS 系统授权启动。')
    import pwd
    owner=pwd.getpwuid(uid)
    if gid!=owner.pw_gid:raise ValueError('Authorization owner group differs from login user')
    os.umask(0o022)  # Let the login-user GUI read live status/logs before ownership is returned.
    os.environ['HOME']=owner.pw_dir
    os.environ['USER']=os.environ['LOGNAME']=owner.pw_name
    path=Path(path);request=json.loads(path.read_text(encoding='utf-8'))
    try:
        from .worker import execute_request
        return execute_request(path)
    finally:
        try:return_ownership(request,uid,gid)
        except Exception:
            with (Path(request['job_dir'])/'worker.log').open('a',encoding='utf-8') as log:
                log.write('相机任务已结束，但文件所有权交还失败；请保留此日志。\n'+traceback.format_exc())
