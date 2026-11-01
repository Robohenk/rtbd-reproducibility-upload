import importlib.util,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'scripts/compare_outputs.py'
s=importlib.util.spec_from_file_location('comparison',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Comparison(unittest.TestCase):
    def test_missing_changed_and_equal(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'ref',Path(t)/'actual';a.mkdir();b.mkdir();(a/'result.csv').write_text('x\n1\n')
            self.assertFalse(m.compare(a,b)['passed'])
            (b/'result.csv').write_text('x\n2\n');self.assertFalse(m.compare(a,b)['passed'])
            (b/'result.csv').write_text('x\n1\n');self.assertTrue(m.compare(a,b)['passed'])
    def test_metadata_is_excluded(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'ref',Path(t)/'actual';a.mkdir();b.mkdir()
            for d in (a,b):(d/'result.csv').write_text('x\n1\n')
            (a/'verification.json').write_text('1');(b/'verification.json').write_text('2')
            self.assertTrue(m.compare(a,b)['passed'])
if __name__=='__main__':unittest.main()
