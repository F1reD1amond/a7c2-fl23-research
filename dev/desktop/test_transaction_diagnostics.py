"""Support bundles include initial child errors without body-data snapshots."""
import json,zipfile
from desktopapp import jobs


def test_export_includes_failed_child_stage_and_excludes_calibration(tmp_path,monkeypatch):
    monkeypatch.setenv('A7C2_DESKTOP_DATA',str(tmp_path/'app'))
    root=tmp_path/'setup';child=root/'install';child.mkdir(parents=True)
    (root/'setup.private.json').write_text(json.dumps(dict(phase='NEEDS_REVIEW',install_workspace=str(child))))
    (child/'direct.private.json').write_text(json.dumps(dict(schema='a7c2-direct-job/1',mode='install_all',
        phase='NEEDS_REVIEW',failed_during='READING',error='cpapp-b.bin 0x138832',journal=[],
        identity=dict(serial='PRIVATE-BODY-SERIAL'),settings_snapshot='PRIVATE-CALIBRATION')))
    (child/'appFw.private.so').write_bytes(b'PRIVATE-PROGRAM')
    job=jobs.new_job('setup_all',dict(workspace=str(root)))
    output=tmp_path/'diagnostics.zip';jobs.export_support(job,output)
    with zipfile.ZipFile(output) as z:
        summary=json.loads(z.read('diagnostics/transactions/direct-summary-0.json'))
        assert summary['failed_during']=='READING' and summary['journal']==[]
        assert '0x138832' in summary['error']
        contents=b'\n'.join(z.read(n) for n in z.namelist() if n!='diagnostics/setupapi-tail.log')
        assert b'PRIVATE-BODY-SERIAL' not in contents and b'PRIVATE-CALIBRATION' not in contents
        assert b'PRIVATE-PROGRAM' not in contents


def test_vertical_export_selects_the_actual_persistent_child(tmp_path,monkeypatch):
    monkeypatch.setenv('A7C2_DESKTOP_DATA',str(tmp_path/'app'))
    root=tmp_path/'vertical';child=root/'persistent-actual';child.mkdir(parents=True)
    state=dict(mode='vertical_enable',phase='NEEDS_REVIEW',failed_during='WRITING',journal=[dict(
        event='vertical_alias_result',result=dict(status=-28,failure_step='写入临时图形',progress_bytes=4096,available_bytes=1024,required_bytes=10000))])
    (child/'direct.private.json').write_text(json.dumps(state))
    other=root/'persistent-newer';other.mkdir();(other/'direct.private.json').write_text(json.dumps(dict(error='UNRELATED-LATER-RUN')))
    job=jobs.new_job('vertical_enable',dict(workspace=str(root)))
    (job/'backend-workspace.private.json').write_text(json.dumps(dict(workspace=str(child))))
    summary=jobs.transaction_summaries(job)['direct-summary-0.json']
    assert summary['journal'][0]['result']['status']==-28
    assert summary['journal'][0]['result']['progress_bytes']==4096
    assert 'UNRELATED-LATER-RUN' not in json.dumps(summary)


def test_program_mismatch_export_keeps_offsets_without_program_bytes(tmp_path,monkeypatch):
    monkeypatch.setenv('A7C2_DESKTOP_DATA',str(tmp_path/'app'))
    root=tmp_path/'direct';root.mkdir()
    result=dict(program='appFw.so',expected_bytes=10000,actual_bytes=9999,
        first_difference='0x270f',raw_program='PRIVATE-PROGRAM',serial='PRIVATE-SERIAL')
    (root/'direct.private.json').write_text(json.dumps(dict(phase='LOADED',journal=[
        dict(event='verification_plan_diff',result=result),
        dict(event='program_readback_mismatch',result=result)])))
    job=jobs.new_job('direct_verify',dict(workspace=str(root)))
    summary=jobs.transaction_summaries(job)['direct-summary-0.json']
    for event in summary['journal']:
        assert event['result']=={k:v for k,v in result.items() if k not in ('raw_program','serial')}
    assert 'PRIVATE-' not in json.dumps(summary)
