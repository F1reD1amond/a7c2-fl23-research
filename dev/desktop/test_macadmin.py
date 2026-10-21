"""Authorization dispatch, cancellation and outcome forwarding; no USB writes."""
import json
import os
from pathlib import Path
import shlex
from types import SimpleNamespace
from unittest.mock import Mock,patch
import pytest
from desktopapp import macadmin,worker
from desktopapp.paths import write_json


@pytest.mark.parametrize('action',['setup_all','direct_factory_reset','direct_verify','sound_install','connect'])
def test_camera_actions_need_mac_authorization(action):
    with patch.object(macadmin.sys,'platform','darwin'),patch.object(macadmin.os,'geteuid',return_value=501,create=True):
        assert macadmin.required(action)
    with patch.object(macadmin.sys,'platform','darwin'),patch.object(macadmin.os,'geteuid',return_value=0,create=True):
        assert not macadmin.required(action)


@pytest.mark.parametrize('action',['sound_import','compile_look','plugin_install','driver_scan'])
def test_offline_actions_do_not_request_privileges(action):
    with patch.object(macadmin.sys,'platform','darwin'),patch.object(macadmin.os,'geteuid',return_value=501,create=True):
        assert not macadmin.required(action)


def test_shell_and_applescript_quoting_preserve_spaces_quotes_and_metacharacters(tmp_path,monkeypatch):
    monkeypatch.setenv('A7C2_DESKTOP_DATA',str(tmp_path/'用户 data'))
    request=tmp_path/'quote "+$(touch should-not-run)'/'request.private.json'
    prefix=['/Applications/A7 C2 "+$ app/Contents/MacOS/A7C2Tools','--worker',str(request)]
    with patch('desktopapp.jobs.worker_command',return_value=prefix):
        cmd=macadmin.command(request,501,20,{'HOME':'/Users/user name','PATH':'/usr/bin:/bin'})
    assert cmd[:2]==['/usr/bin/osascript','-e']
    script=cmd[-1]
    assert 'with administrator privileges' in script
    assert '--privileged-worker' in script
    assert 'A7C2_DESKTOP_DATA=' in script and 'HOME=' in script
    assert '\\"' in script and 'password ' not in script


def make_request(tmp_path,monkeypatch):
    monkeypatch.setenv('A7C2_DESKTOP_DATA',str(tmp_path/'app'))
    request=tmp_path/'job/request.private.json'
    write_json(request,dict(action='direct_factory_reset',arguments={},job_dir=str(request.parent)))
    return request


def test_cancelled_authorization_never_starts_worker(tmp_path,monkeypatch):
    request=make_request(tmp_path,monkeypatch)
    with patch.object(macadmin.os,'getuid',return_value=501,create=True), \
         patch.object(macadmin.os,'getgid',return_value=20,create=True), \
         patch.object(macadmin.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='',stderr='User canceled. (-128)')):
        assert macadmin.execute(request)==2
    state=json.loads((request.parent/'status.private.json').read_text(encoding='utf-8'))
    assert state['error_type']=='MacAuthorizationCancelled'
    assert state['camera_io'] is False
    assert '尚未开始' in state['error']


@pytest.mark.parametrize('phase,code',[('SUCCEEDED',0),('FAILED',2)])
def test_native_worker_outcome_is_preserved_without_replay(tmp_path,monkeypatch,phase,code):
    request=make_request(tmp_path,monkeypatch)
    def run(*args,**kwargs):
        write_json(request.parent/'status.private.json',dict(phase=phase,action='direct_factory_reset',error='original camera error'))
        return SimpleNamespace(returncode=code,stdout='',stderr='')
    with patch.object(macadmin.os,'getuid',return_value=501,create=True), \
         patch.object(macadmin.os,'getgid',return_value=20,create=True), \
         patch.object(macadmin.subprocess,'run',side_effect=run) as execute:
        assert macadmin.execute(request)==code
    execute.assert_called_once()
    assert json.loads((request.parent/'status.private.json').read_text())['error']=='original camera error'


def test_dispatch_requests_authorization_before_loading_camera_backend(tmp_path,monkeypatch):
    request=make_request(tmp_path,monkeypatch)
    with patch.object(macadmin,'required',return_value=True),patch.object(macadmin,'execute',return_value=2) as authorized, \
            patch.object(worker,'run',side_effect=AssertionError('Camera must not run before authorization')):
        assert worker.execute_request(request)==2
    authorized.assert_called_once_with(request)
