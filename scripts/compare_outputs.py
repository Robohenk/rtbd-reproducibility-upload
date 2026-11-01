"""Compare regenerated scientific files against the shipped reference."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'verification.json','fresh_reproduction_comparison.json'}
def compare(reference,actual):
    files=sorted(p.relative_to(reference) for p in reference.rglob('*') if p.is_file() and p.name not in EXCLUDED)
    failures=[]
    for rel in files:
        if not (actual/rel).is_file(): failures.append({'file':str(rel),'error':'missing'})
        elif (reference/rel).read_bytes()!=(actual/rel).read_bytes(): failures.append({'file':str(rel),'error':'different'})
    if not files: failures.append({'error':'empty reference'})
    return {'compared':len(files),'failures':failures,'passed':not failures}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,default=ROOT/'outputs');ap.add_argument('--actual',type=Path,default=ROOT/'reproduced');a=ap.parse_args()
    if a.reference.resolve()==a.actual.resolve(): ap.error('Reference and actual must be different directories.')
    report=compare(a.reference,a.actual);print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
