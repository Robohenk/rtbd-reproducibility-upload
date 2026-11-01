"""Reproduce, derive, validate and compare results without replacing references."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-root',type=Path,default=ROOT/'data');ap.add_argument('--output',type=Path,default=ROOT/'reproduced');a=ap.parse_args()
    if a.output.exists() and any(a.output.iterdir()):ap.error('Choose an empty output directory to prevent stale results.')
    def run(script,*args):subprocess.run([sys.executable,'-B',str(ROOT/'scripts'/script),*map(str,args)],check=True)
    run('reproduce.py','--data-root',a.data_root,'--output',a.output)
    run('build_review.py','--output',a.output)
    run('check_outputs.py','--output',a.output)
    run('compare_outputs.py','--actual',a.output)
if __name__=='__main__':main()
