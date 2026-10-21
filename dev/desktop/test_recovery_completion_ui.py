"""Recovery remains pending until loaded-state verification passes."""
import json,os
from pathlib import Path
from unittest.mock import Mock,patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from PySide6 import QtWidgets as W
from desktopapp import jobs,reloadguide
from desktopapp.window import Window


@pytest.fixture
def pending_window(tmp_path,monkeypatch):
    app=W.QApplication.instance() or W.QApplication([])
    monkeypatch.setenv('A7C2_DESKTOP_DATA',str(tmp_path/'app'))
    window=Window();window.timer.stop()
    work=tmp_path/'recovery';work.mkdir()
    state=dict(schema='a7c2-direct-job/1',mode='factory_reset',phase='AWAITING_RELOAD',
               readonly_after_reload_verified=False)
    (work/'direct.private.json').write_text(json.dumps(state))
    window.settings['factory_direct_work']=str(work)
    window.fields['factory_failed_work'].setText(str(work))
    yield window,work,state
    window.process=None;window.close()


def finish(window,work,phase,action='direct_factory_reset',success=True):
    window.current_job=jobs.new_job(action,{})
    (window.current_job/'status.private.json').write_text(json.dumps(dict(
        phase='SUCCEEDED' if success else 'FAILED',action=action,error='not loaded',
        result=dict(workspace=str(work),mode='factory_reset',phase=phase))))
    window.process=Mock()
    window.finished(0 if success else 2,None)


def test_written_recovery_is_70_percent_and_requires_reboot_verification(pending_window):
    window,work,state=pending_window
    with patch.object(window,'show_reload_guide') as popup:
        finish(window,work,'AWAITING_RELOAD')
    assert window.progress.value()==70
    assert '恢复尚未完成' in window.status.text()
    assert '重启后核对并完成恢复'==window.factory_button.text()
    assert '尚未完成' in window.factory_status.text()
    popup.assert_called_once_with(setup=False,mode='factory_reset')
    assert not window.factory_accept.isChecked()


def test_only_verified_recovery_reaches_100_percent(pending_window):
    window,work,state=pending_window
    state.update(phase='LOADED',readonly_after_reload_verified=True)
    (work/'direct.private.json').write_text(json.dumps(state))
    with patch.object(window,'show_reload_guide') as popup:
        finish(window,work,'LOADED','direct_verify')
    assert window.progress.value()==100
    assert '核对通过' in window.status.text()
    assert '核对已通过' in window.factory_status.text()
    assert not window.factory_accept.isChecked()
    popup.assert_not_called()


def test_failed_verify_keeps_pending_state(pending_window):
    window,work,state=pending_window
    finish(window,work,'AWAITING_RELOAD','direct_verify',False)
    assert window.progress.value()==0
    assert '尚未完成' in window.factory_status.text()
    assert window.factory_button.text()=='重启后核对并完成恢复'


def test_restart_dialog_explicitly_requires_followup_check():
    text=reloadguide.text(mode='factory_reset')
    for phrase in ('恢复尚未完成','必须重启后核对','至少等待 1 分钟','接回 USB','重启后核对并完成恢复','只有核对通过'):
        assert phrase in text
