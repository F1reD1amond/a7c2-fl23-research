"""Version-only source admission, LUT preservation and conflict tests. No USB."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core,app,compat

class Guards(unittest.TestCase):
    def test_unknown_pair_rejected(self):
        with self.assertRaises(ValueError):compat.plan(b'unknown',b'unknown')
    def test_wrong_version_stops_before_program_inspection(self):
        with self.assertRaisesRegex(ValueError,'2.01'):compat.plan(b'anything',b'anything','3.00')
    def test_wrong_version_stops_prepare_before_usb(self):
        job=app.Job('unused-workspace')
        with patch('transport.Session',side_effect=AssertionError('No USB')):
            with self.assertRaisesRegex(ValueError,'2.01'):job.prepare('unused-backup','3.00')
    def test_existing_enabled_colors_must_be_complete(self):
        a,b=bytes(8192),bytes(28672)
        with self.assertRaises(ValueError):compat.validate_enabled_colors(a,b)
        merged=core.merge_colors(a,b);compat.validate_enabled_colors(*merged)
        wrong=bytearray(merged[0]);wrong[0x1250+23*64]^=1
        with self.assertRaises(ValueError):compat.validate_enabled_colors(bytes(wrong),merged[1])
    def test_already_enabled_install_never_opens_camera(self):
        job=app.Job('.')
        def load():job.state={'phase':'prepared','compatibility':{'already_enabled':True}}
        with patch.object(job,'load',side_effect=load),patch('transport.Session',side_effect=AssertionError('No USB')):
            job.install(100)
    def test_identification_only_job_cannot_restore_an_existing_install(self):
        job=app.Job('.')
        def load():job.state={'compatibility':{'already_enabled':True}}
        with patch.object(job,'load',side_effect=load),patch('transport.Session',side_effect=AssertionError('No USB')):
            with self.assertRaises(ValueError):job.restore(100)


@unittest.skipUnless(os.environ.get('A7C2_FIRMWARE_ROOT'),'Requires private original firmware')
class OriginalFirmware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout,cls.firmware,cls.build,_=compat.modules()
        folder=Path(os.environ['A7C2_FIRMWARE_ROOT'])/'a7c2-2.01/components'
        cls.ap=(folder/'appFw.so').read_bytes();cls.cp=(folder/'cpapp-b.bin').read_bytes()
        if [core.sha(cls.ap),core.sha(cls.cp)]!=core.ORIGINAL:raise AssertionError('Original source required')
        cls.flap=core.patch_program(cls.ap,0)
        spec=next(s for s in cls.layout.runtime()['cp_sources'] if s['kind']=='stock')
        result=bytearray(cls.cp)
        for w in spec['windows']:
            at=w['offset'];old,new=bytes.fromhex(w['before']),bytes.fromhex(w['after'])
            if len(old)!=len(new) or result[at:at+len(old)]!=old:raise AssertionError('Source window differs')
            result[at:at+len(new)]=new
        cls.lutcp=bytes(result)
        if core.sha(cls.lutcp)!=cls.layout.runtime()['cp_zero_tables_sha256']:raise AssertionError('Canonical LUT runtime differs')
    def test_stock_lut_becomes_fl23_lut_without_changing_any_cp_byte(self):
        for mask in [1,32,63]:
            with self.subTest(mask=mask):
                source=self.layout._ap_target(self.ap,mask)
                identity,enabled,after,f,r=compat.plan(source,self.lutcp)
                self.assertFalse(enabled);self.assertFalse(identity['provenance_checked']);self.assertEqual(identity['kind'],'lut')
                self.assertEqual(after['appFw.so'],self.layout._ap_target(self.flap,mask))
                self.assertEqual(after['cpapp-b.bin'],self.lutcp)
                self.assertEqual(self.firmware.apply(after,r),{'appFw.so':source,'cpapp-b.bin':self.lutcp})
                self.assertEqual(self.firmware.apply(self.firmware.apply(after,r),f),after)
    def test_fl23_lut_is_recognized_without_reinstallation(self):
        source=self.layout._ap_target(self.flap,63)
        identity,enabled,after,f,r=compat.plan(source,self.lutcp)
        self.assertTrue(enabled);self.assertEqual(after['appFw.so'],source);self.assertIsNone(f)
    def test_changes_outside_patched_positions_are_accepted_and_preserved(self):
        source=self.layout._ap_target(self.ap,1)
        changed_ap=bytearray(source);changed_ap[0x70000]^=1
        changed_cp=bytearray(self.lutcp);changed_cp[0x70000]^=1
        with patch.object(self.layout,'identify',side_effect=AssertionError('No source whitelist')):
            identity,enabled,after,f,r=compat.plan(bytes(changed_ap),bytes(changed_cp))
        self.assertFalse(identity['provenance_checked'])
        self.assertEqual(after['appFw.so'][0x70000],changed_ap[0x70000])
        self.assertEqual(after['cpapp-b.bin'],bytes(changed_cp))
        self.assertEqual(self.firmware.apply(after,r),{'appFw.so':bytes(changed_ap),'cpapp-b.bin':bytes(changed_cp)})
    def test_actual_patch_position_conflict_is_not_overwritten(self):
        source=self.layout._ap_target(self.ap,1)
        wrong=bytearray(source);wrong[0x4b2ed19]=0x77
        with self.assertRaisesRegex(ValueError,'衝突'):compat.plan(bytes(wrong),self.lutcp)
        wrong=bytearray(self.lutcp);wrong[0x138814]^=1
        with self.assertRaisesRegex(ValueError,'衝突'):compat.plan(source,bytes(wrong))
    def test_modified_stock_programs_also_do_not_require_source_hashes(self):
        changed_ap=bytearray(self.ap);changed_ap[0x70000]^=1
        changed_cp=bytearray(self.cp);changed_cp[0x70000]^=1
        _,enabled,after,f,r=compat.plan(bytes(changed_ap),bytes(changed_cp))
        self.assertFalse(enabled)
        self.assertEqual(after['appFw.so'][0x70000],changed_ap[0x70000])
        self.assertEqual(after['cpapp-b.bin'][0x70000],changed_cp[0x70000])
        self.assertEqual(self.firmware.apply(after,r),{'appFw.so':bytes(changed_ap),'cpapp-b.bin':bytes(changed_cp)})
    def test_job_worker_compiles_with_exact_forward_and_inverse_hashes(self):
        source=self.layout._ap_target(self.ap,1)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'candidate').mkdir();(root/'original').mkdir()
            # Supply Zig explicitly for local verification without installation.
            original_build=self.build.build_program
            zig=os.environ.get('A7C2_ZIG')
            def build(*args,**kwargs):return original_build(*args,**dict(kwargs,zig=zig))
            with patch.object(self.build,'build_program',side_effect=build):spec=compat.prepare(root,source,self.lutcp)
            for name,data in [('appFw.so',source),('cpapp-b.bin',self.lutcp)]:
                (root/'original'/(name+'.bin')).write_bytes(data)
            compat.validate(root,{'compatibility':spec})
            contract=spec['build']['contract']
            self.assertEqual(contract['before']['cpapp-b.bin'],contract['after']['cpapp-b.bin'])
            self.assertNotEqual(contract['before']['appFw.so'],contract['after']['appFw.so'])
            blob=root/'compat-worker/program.so';blob.write_bytes(blob.read_bytes()+b'x')
            with self.assertRaises(ValueError):compat.validate(root,{'compatibility':spec})

if __name__=='__main__':unittest.main()
