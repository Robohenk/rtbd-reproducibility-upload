"""Package the reproducibility distribution, excluding Git history and caches."""
import argparse, hashlib, json, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def eligible(p):
    relative=p.relative_to(ROOT)
    return p.is_file() and not any(x in ('.git','__pycache__','.venv','reproduced','.downloads') for x in relative.parts) and p.suffix not in ('.pyc','.aux','.log')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--destination',type=Path,default=ROOT.parent/'rtbd-reproducibility-release.zip')
    ap.add_argument('--intervals',type=Path)
    args=ap.parse_args()
    files=sorted(p for p in ROOT.rglob('*') if eligible(p) and p.name!='ARTIFACT_MANIFEST.json')
    manifest={'status':'prepared_distribution','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]}
    (ROOT/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    files.append(ROOT/'ARTIFACT_MANIFEST.json')
    args.destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in sorted(files):
            info=zipfile.ZipInfo('rtbd-reproducibility/'+p.relative_to(ROOT).as_posix(),date_time=(2026,11,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,p.read_bytes())
    with zipfile.ZipFile(args.destination) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(files)
    print(f'{args.destination}: {len(files)} files, SHA256 {digest(args.destination)}')
    if args.intervals:
        interval_files=sorted(args.intervals.glob('*.csv.gz'))
        assert len(interval_files)==81
        interval_manifest=[{'file':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in interval_files]
        target=args.destination.parent/'rtbd-canonical-intervals.zip'
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as archive:
            for p in interval_files:
                archive.writestr(zipfile.ZipInfo(p.name,date_time=(2026,11,1,0,0,0)),p.read_bytes())
            archive.writestr('manifest.json',json.dumps(interval_manifest,indent=2)+'\n')
            archive.writestr('README.txt','81 canonical interval CSV.gz files: filtered, raw, and raw_retained corpora, 27 configurations each. See the review candidate docs/DATA_DICTIONARY.md and docs/REPRODUCIBILITY.md. Generated from the supplied data without altering inputs. Recreate with scripts/reproduce.py --data-root DATA --intervals PATH.\n')
        with zipfile.ZipFile(target) as archive:
            assert archive.testzip() is None
        print(f'{target}: {len(interval_files)} interval files, SHA256 {digest(target)}')

if __name__=='__main__': main()
