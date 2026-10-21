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
