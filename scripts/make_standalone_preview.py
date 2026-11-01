"""Inline sources and exact CSV tables for a single-file LaTeX editor."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=(ROOT/'figures/preview.tex').read_text()
    for name in ('styles','fig_throughput','fig_landscape','fig_blocking','fig_pipeline'):
        source=source.replace('\\input{figures/'+name+'.tex}',(ROOT/f'figures/{name}.tex').read_text())
    # Resolve each data reference according to the active corpus macro.
    prefix='outputs/figure_data'; lines=[]; tables=[]; n=0
    for line in source.splitlines():
        match=re.search(r'\\renewcommand\{\\rtbddatadir\}\{([^}]+)\}',line)
        if match: prefix=match.group(1)
        match=re.search(r'\{\\rtbddatadir/([^}]+)\}',line)
        if match:
            n+=1
            # TeX control sequence names must contain letters only.
            macro='\\rtbdTable'+''.join(chr(97+int(d)) for d in str(n))
            data=(ROOT/prefix/match.group(1)).read_text().strip()
            tables.append('\\pgfplotstableread[col sep=comma]{\n'+data+'\n}'+macro)
            line=line.replace(match.group(0),'{'+macro+'}')
        lines.append(line)
    source='\n'.join(lines).replace('\\begin{document}','\n'.join(tables)+'\n\\begin{document}')+'\n'
    target=ROOT/'figures/preview_standalone.tex'
    target.write_text(source,encoding='utf-8')
    print(target)

if __name__=='__main__': main()
