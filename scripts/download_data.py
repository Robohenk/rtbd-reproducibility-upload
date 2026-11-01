"""Download the pinned original dataset and validate all 54 file hashes."""
import argparse,hashlib,json,shutil,tempfile,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES={'RawData':'https://ndownloader.figshare.com/files/28325148','FilteredFiles':'https://ndownloader.figshare.com/files/28325151'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--destination',type=Path,default=ROOT/'data');a=ap.parse_args()
    hashes=json.loads((ROOT/'data/checksums.json').read_text(encoding='utf-8-sig'))
    with tempfile.TemporaryDirectory() as tmp:
        pending=[]
        for folder,url in SOURCES.items():
            archive=Path(tmp)/(folder+'.zip');print('Downloading '+url,flush=True)
            with urllib.request.urlopen(url,timeout=120) as response,archive.open('wb') as f:shutil.copyfileobj(response,f)
            with zipfile.ZipFile(archive) as z:
                for rel,expected in hashes.items():
                    if not rel.startswith(folder+'/'):continue
                    matches=[n for n in z.namelist() if n.replace('\\','/').split('/')[-1]==Path(rel).name]
                    if len(matches)!=1:raise ValueError('Missing or ambiguous archive member: '+rel)
                    data=z.read(matches[0])
                    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Checksum mismatch: '+rel)
                    staged=Path(tmp)/'verified'/rel;staged.parent.mkdir(parents=True,exist_ok=True);staged.write_bytes(data);pending.append((rel,staged))
        if len(pending)!=54:raise ValueError('Expected 54 verified source files')
        for rel,staged in pending:
            dest=a.destination/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=hashes[rel]:raise ValueError('Refusing to overwrite different local file: '+str(dest))
        for rel,staged in pending:shutil.copyfile(staged,a.destination/rel)
    print('PASS: downloaded and SHA256-verified all 54 original files.')
if __name__=='__main__':main()
