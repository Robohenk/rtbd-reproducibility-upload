import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    rows=json.loads((ROOT/'ARTIFACT_MANIFEST.json').read_text())['files']
    failed=[r['path'] for r in rows if not (ROOT/r['path']).is_file() or hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256']]
    print(f'Manifest: {len(rows)} files; mismatches: {failed}');raise SystemExit(bool(failed))
if __name__=='__main__':main()
