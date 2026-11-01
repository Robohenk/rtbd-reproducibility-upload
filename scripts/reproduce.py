"""Reconstruct RTBD results from the supplied original repository data directory."""
import argparse, csv, gzip, hashlib, itertools, json, platform, sys, time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rtbd.core import read_events, adapter, reconstruct, validate, window_exposure, evidence, classify, US, HORIZON

def write_csv(path, rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        return
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)

def factorial(runs):
    values={r['run']:r['throughput'] for r in runs}
    grand=sum(values.values())/len(values)
    total=sum((y-grand)**2 for y in values.values())
    effects={}; rows=[]
    names=['fleet','direction','dispatch']
    for size in (1,2,3):
        for dims in itertools.combinations(range(3),size):
            vals={}
            for key in itertools.product(*[('456' if d==0 else '123') for d in dims]):
                mean=sum(y for k,y in values.items() if all(k[d]==c for d,c in zip(dims,key)))/(3**(3-size))
                effect=mean-grand
                for sub,ev in effects.items():
                    if set(sub)<set(dims):
                        effect-=ev[tuple(key[dims.index(d)] for d in sub)]
                vals[key]=effect
            effects[dims]=vals
            ss=sum(e*e for e in vals.values())*3**(3-size)
            rows.append(dict(term=' x '.join(names[d] for d in dims),sum_squares=ss,percent=100*ss/total))
    if abs(sum(r['sum_squares'] for r in rows)-total)>1e-6:
        raise ValueError('Factorial decomposition does not conserve variation')
    return rows

def variants(baseline):
    variants={'baseline':baseline}
    for key,values in [('window_minutes',[30,120]),('capacity_threshold',[.85,.95]),('codominance_tolerance',[.01,.05]),('delay_threshold',[.5,2]),('production_saturation',[.85,.95]),('wp_persistence',[.7])]:
        for value in values:
            variants[f'{key}={value}']={**baseline,key:value}
    for lo,hi in [(1,23),(2,22),(0,22),(2,24)]:
        variants[f'hours={lo}-{hi}']={**baseline,'start_hour':lo,'end_hour':hi}
        variants[f'hours={lo}-{hi};full_horizon_saturation']={**baseline,'start_hour':lo,'end_hour':hi,'production_utilization_reference':'full_horizon'}
    return variants

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data-root',required=True,type=Path,help='Directory containing FilteredFiles and RawData')
    ap.add_argument('--output',type=Path,default=ROOT/'reproduced')
    ap.add_argument('--intervals',type=Path,help='Optional directory for compressed canonical intervals')
    ap.add_argument('--corpora',nargs='+',choices=['filtered','raw','raw_retained'],default=['filtered','raw','raw_retained'])
    ap.add_argument('--runs',nargs='+',help='Diagnostic subset; full verification requires all 27')
    args=ap.parse_args()
    if args.output.resolve()==(ROOT/'outputs').resolve():
        ap.error('outputs/ is the frozen reference; use a separate --output directory.')
    started=time.perf_counter()
    expected=[''.join(x) for x in itertools.product('456','123','123')]
    runs=args.runs or expected
    baseline=json.loads((ROOT/'config/baseline.json').read_text())
    configs=variants(baseline)
    checksum_path=ROOT/'data/checksums.json'
    expected_hashes=json.loads(checksum_path.read_text())
    summaries=[]; all_windows=[]; audits=[]; checks=[]; inventory=[]; sensitivity=[]; resources=[]
    for run in runs:
        raw_traces=filtered_traces=None
        for corpus in args.corpora:
            source_raw=corpus!='filtered'
            path=args.data_root/('RawData' if source_raw else 'FilteredFiles')/(f'Experiment{run}.txt' if source_raw else f'{run}.xes')
            relative=str(path.relative_to(args.data_root)).replace('\\','/')
            checksum=hashlib.sha256(path.read_bytes()).hexdigest()
            if expected_hashes and expected_hashes.get(relative)!=checksum:
                raise ValueError(f'Input hash mismatch: {relative}')
            if source_raw:
                if raw_traces is None: raw_traces=read_events(path,True)
                traces=raw_traces
            else:
                if filtered_traces is None: filtered_traces=read_events(path)
                traces=filtered_traces
            if corpus=='raw_retained':
                if filtered_traces is None: filtered_traces=read_events(args.data_root/'FilteredFiles'/f'{run}.xes')
                traces={c:e for c,e in traces.items() if c in filtered_traces}
            intervals=[]; count=Counter(); throughput=0
            for case,events in sorted(traces.items()):
                count['source_events']+=len(events)
                throughput+=sum(e.activity=='Drain' and e.status=='Complete' for e in events)
                adapted,audit=adapter(events)
                audits.extend(dict(corpus=corpus,run=run,**a) for a in audit)
                count.update(a['action'] for a in audit)
                intervals.extend(reconstruct(adapted))
            for v in validate(intervals,int(run[0])):
                checks.append(dict(corpus=corpus,run=run,**v))
            if args.intervals:
                args.intervals.mkdir(parents=True,exist_ok=True)
                dest=args.intervals/f'{corpus}_{run}.csv.gz'
                with dest.open('wb') as file:
                    with gzip.GzipFile(filename='',mode='wb',fileobj=file,mtime=0) as gz:
                        import io
                        with io.TextIOWrapper(gz,encoding='utf-8',newline='') as f:
                            writer=csv.DictWriter(f,fieldnames=list(asdict(intervals[0])),lineterminator='\n')
                            writer.writeheader(); writer.writerows(asdict(it) for it in intervals)
            cache={}
            for name,cfg in configs.items():
                key=(cfg['window_minutes'],cfg['start_hour'],cfg['end_hour'])
                if key not in cache:
                    cache[key]=window_exposure(intervals,cfg['window_minutes']*60*US,cfg['start_hour']*3600*US,cfg['end_hour']*3600*US)
                summary,windows=evidence(cache[key],int(run[0]),cfg)
                if cfg.get('production_utilization_reference')=='full_horizon':
                    summary['production_utilization']=full_horizon_production
                    summary['regime']=classify(summary['transport_persistence'],summary['production_utilization'],summary['wp_persistence'],cfg)
                sensitivity.append(dict(corpus=corpus,run=run,variant=name,**summary))
                if name=='baseline':
                    full_horizon_production=summary['production_utilization']
                    summaries.append(dict(corpus=corpus,run=run,fleet=int(run[0]),direction=int(run[1]),dispatch=int(run[2]),throughput=throughput,cases=len(traces),**summary))
                    all_windows.extend(dict(corpus=corpus,run=run,**w) for w in windows)
                    for group in ('Sawing','Drilling','Welding','Painting','AGV'):
                        wr=[w for w in windows if w['group']==group]
                        resources.append(dict(corpus=corpus,run=run,group=group,occupied_seconds=sum(w['occupied_seconds'] for w in wr),queue_seconds=sum(w['queue_seconds'] for w in wr),blocked_seconds=sum(w['blocked_seconds'] for w in wr),utilization=sum(w['utilization'] for w in wr)/24,mean_queue=sum(w['mean_queue'] for w in wr)/24,joint_persistence=sum(w['joint_dominant'] for w in wr)/24))
            inventory.append(dict(corpus=corpus,run=run,filename=relative,sha256=checksum,cases=len(traces),source_events=count['source_events'],throughput=throughput,repairs=count['repair_label_and_same_time_order'],duplicates=count['ignore_consecutive_duplicate_ip'],censored_intervals=sum(i.censored for i in intervals),intervals=len(intervals)))
            print(f'{corpus} {run}: {throughput} products; {count["repair_label_and_same_time_order"]} repairs; {summaries[-1]["regime"]}',flush=True)
    out=args.output
    for filename,table in [('run_summary',summaries),('window_evidence',all_windows),('resource_evidence',resources),('repair_audit',audits),('conservation_checks',checks),('input_manifest',inventory),('sensitivity_runs',sensitivity)]:
        write_csv(out/f'{filename}.csv',table)
    comparisons=[]; robustness=[]; contrasts=[]; factors=[]
    for corpus in args.corpora:
        base={r['run']:r for r in summaries if r['corpus']==corpus}
        for name in configs:
            selected=[r for r in sensitivity if r['corpus']==corpus and r['variant']==name]
            robustness.append(dict(corpus=corpus,variant=name,agreement=sum(r['regime']==base[r['run']]['regime'] for r in selected),total=len(selected),changed_runs=','.join(r['run'] for r in selected if r['regime']!=base[r['run']]['regime'])))
        for a in base:
            if a[0] not in '45': continue
            b=str(int(a[0])+1)+a[1:]
            if b not in base: continue
            p,q=base[a]['throughput'],base[b]['throughput']
            contrasts.append(dict(corpus=corpus,from_run=a,to_run=b,regime=base[a]['regime'],from_products=p,to_products=q,difference=q-p,gain_percent=100*(q-p)/p,legacy_percent=100*(q-p)/q,high_response=int((q-p)/p>=.05)))
        if sorted(base)==expected:
            factors.extend(dict(corpus=corpus,**r) for r in factorial(list(base.values())))
    base={r['run']:r for r in summaries if r['corpus']=='filtered'}
    for row in summaries:
        if row['corpus']=='filtered' or row['run'] not in base: continue
        ref=base[row['run']]
        comparisons.append(dict(corpus=row['corpus'],run=row['run'],filtered_regime=ref['regime'],comparison_regime=row['regime'],regime_changed=int(row['regime']!=ref['regime']),throughput_delta=row['throughput']-ref['throughput'],queue_delta=row['transport_queue']-ref['transport_queue'],production_utilization_delta=row['production_utilization']-ref['production_utilization'],transport_persistence_delta=row['transport_persistence']-ref['transport_persistence'],wp_persistence_delta=row['wp_persistence']-ref['wp_persistence']))
    for filename,table in [('corpus_comparison',comparisons),('robustness_summary',robustness),('matched_contrasts',contrasts),('factorial_decomposition',factors)]:
        write_csv(out/f'{filename}.csv',table)
    (out/'analysis_configs.json').write_text(json.dumps(configs,indent=2)+'\n')
    report=dict(status='measurement_checks_passed',full_corpus=(runs==expected),corpora=args.corpora,runs_per_corpus=len(runs),service_checks=sum(r['level']=='service' for r in checks),atomic_checks=sum(r['level']=='atomic' for r in checks),max_conservation_difference_us=max(abs(r['difference_us']) for r in checks),python=platform.python_version(),runtime_seconds=round(time.perf_counter()-started,3),note='Measurement validation does not resolve manuscript discrepancies; inspect claim ledger and corpus comparison.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
