"""Generate review tables, claim checks, and figure inputs from verified outputs."""
import argparse, csv, json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'scripts'))
from reproduce import write_csv

def read(name):
    with (OUTPUT/f'{name}.csv').open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def mean(rows,key): return sum(float(r[key]) for r in rows)/len(rows)

def main():
    global OUTPUT
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'outputs')
    OUTPUT=ap.parse_args().output
    runs=read('run_summary'); manifest=read('input_manifest'); checks=read('conservation_checks')
    contrasts=read('matched_contrasts'); sensitivity=read('robustness_summary')
    factors=read('factorial_decomposition'); resources=read('resource_evidence')
    filtered=[r for r in runs if r['corpus']=='filtered']
    fleet=[]; regime_counts=[]; blocking=[]
    for corpus in ('filtered','raw','raw_retained'):
        selected=[r for r in runs if r['corpus']==corpus]
        for n in ('4','5','6'):
            group=[r for r in selected if r['fleet']==n]
            counts=Counter(r['regime'] for r in group)
            fleet.append(dict(corpus=corpus,fleet=int(n),throughput=mean(group,'throughput'),transport_queue=mean(group,'transport_queue'),production_utilization=mean(group,'production_utilization'),fleet_utilization=mean(group,'fleet_utilization')))
            regime_counts.append(dict(corpus=corpus,fleet=int(n),transport=counts['transport'],mixed=counts['mixed'],production=counts['production'],indeterminate=counts['indeterminate']))
            for direction in ('1','2','3'):
                subset=[r for r in group if r['direction']==direction]
                blocking.append(dict(corpus=corpus,fleet=int(n),direction=int(direction),blocking=mean(subset,'fleet_blocking')))
    for name,rows in [('fleet_summary',fleet),('regime_counts',regime_counts),('blocking_summary',blocking)]:
        write_csv(OUTPUT/f'{name}.csv',rows)
    # Explicitly reconstructed screening rules, not an invented historical ablation.
    screening=[]
    for r in contrasts:
        if r['from_run'][0]!='4': continue
        row=next(x for x in runs if x['corpus']==r['corpus'] and x['run']==r['from_run'])
        screening.append(dict(corpus=r['corpus'],run=r['from_run'],regime=row['regime'],gain_percent=r['gain_percent'],high_response=int(r['high_response']),utilization_unsaturated=int(float(row['production_utilization'])<.9),transport_persistent=int(float(row['transport_persistence'])>=.5),rtbd_transport_unsaturated=int(row['regime']=='transport')))
    write_csv(OUTPUT/'screening_predictions.csv',screening)
    score=[]
    for corpus in ('filtered','raw','raw_retained'):
        group=[r for r in screening if r['corpus']==corpus]
        for predictor in ('utilization_unsaturated','transport_persistent','rtbd_transport_unsaturated'):
            tp=sum(r[predictor] and r['high_response'] for r in group)
            fp=sum(r[predictor] and not r['high_response'] for r in group)
            fn=sum(not r[predictor] and r['high_response'] for r in group)
            tn=sum(not r[predictor] and not r['high_response'] for r in group)
            score.append(dict(corpus=corpus,predictor=predictor,true_positive=tp,false_positive=fp,false_negative=fn,true_negative=tn,accuracy=(tp+tn)/len(group)))
    write_csv(OUTPUT/'screening_scores.csv',score)
    claims=[]
    def claim(identifier,reported,observed,tolerance=0,note=''):
        numeric=isinstance(reported,(int,float)) and isinstance(observed,(int,float))
        matches=abs(reported-observed)<=tolerance if numeric else reported==observed
        claims.append(dict(claim=identifier,reported=reported,recomputed=observed,tolerance=tolerance,status='matches' if matches else 'discrepancy',note=note))
    for n,thr,queue,util in [(4,1288.1,55.76,88.6),(5,1420.2,4.57,97.7),(6,1424.9,2.46,98.0)]:
        r=next(r for r in fleet if r['corpus']=='filtered' and r['fleet']==n)
        claim(f'mean_throughput_{n}',thr,r['throughput'],.05)
        claim(f'mean_transport_queue_{n}',queue,r['transport_queue'],.005)
        claim(f'mean_max_production_utilization_percent_{n}',util,r['production_utilization']*100,.05)
    f=[r for r in fleet if r['corpus']=='filtered']
    claim('fleet_4_to_5_gain_percent',10.3,100*(f[1]['throughput']-f[0]['throughput'])/f[0]['throughput'],.05)
    claim('fleet_5_to_6_gain_percent',.3,100*(f[2]['throughput']-f[1]['throughput'])/f[1]['throughput'],.05)
    claim('transport_queue_reduction_4_to_5_percent',91.8,100*(f[0]['transport_queue']-f[1]['transport_queue'])/f[0]['transport_queue'],.05)
    for key,target in [('repairs',6557),('duplicates',402)]:
        claim(key,target,sum(int(r[key]) for r in manifest if r['corpus']=='filtered'))
    for level,target in [('service',405),('atomic',659)]:
        claim(f'{level}_conservation_count',target,sum(r['level']==level and r['corpus']=='filtered' for r in checks))
    claim('maximum_conservation_discrepancy_seconds_below_1.3e-9',True,max(abs(int(r['difference_us'])) for r in checks if r['corpus']=='filtered')/1e6<1.3e-9,note='Integer-microsecond reconstruction; this does not reproduce historical floating-point arithmetic.')
    for n,target in [(4,'5/2/2'),(5,'0/1/8'),(6,'0/0/9')]:
        r=next(r for r in regime_counts if r['corpus']=='filtered' and r['fleet']==n)
        claim(f'regimes_{n}',target,'/'.join(str(r[k]) for k in ('transport','mixed','production')))
    for n,target in [(4,7.08),(5,7.18),(6,6.25)]:
        r=next(r for r in blocking if r['corpus']=='filtered' and r['fleet']==n and r['direction']==3)
        claim(f'bidirectional_blocking_percent_{n}',target,100*r['blocking'],.005)
    for term,target in [('fleet',43.7),('fleet x dispatch',25.4),('dispatch',14.8),('fleet x direction',9.6)]:
        r=next(r for r in factors if r['corpus']=='filtered' and r['term']==term)
        claim(f'factorial_percent_{term}',target,float(r['percent']),.05)
    cc=[r for r in contrasts if r['corpus']=='filtered' and r['from_run'][0]=='4']
    claim('matched_4_to_5_min_products',2,min(int(r['difference']) for r in cc))
    claim('matched_4_to_5_max_products',409,max(int(r['difference']) for r in cc))
    for dispatch,target in [('1',67.0),('2',272.7),('3',56.7)]:
        claim('matched_dispatch_mean_'+dispatch,target,mean([r for r in cc if r['from_run'][2]==dispatch],'difference'),.05)
    claim('matched_5_to_6_mean_products',4.7,mean([r for r in contrasts if r['corpus']=='filtered' and r['from_run'][0]=='5'],'difference'),.05)
    for regime,lo,hi in [('production',.14,.21),('mixed',3.51,4.92),('transport',8.21,28.76)]:
        selected=[r for r in cc if r['regime']==regime]
        claim('response_min_percent_'+regime,lo,min(float(r['gain_percent']) for r in selected),.005,note='Approved baseline-relative percentage formula.')
        claim('response_max_percent_'+regime,hi,max(float(r['gain_percent']) for r in selected),.005,note='Approved baseline-relative percentage formula.')
    claim('high_response_count',5,sum(int(r['high_response']) for r in cc),note='6 under baseline-relative gains; legacy P5 denominator yields 5.')
    for run,key,target,tol in [('412','throughput',1013,0),('412','production_utilization',.70,.005),('421','throughput',1422,0),('421','production_utilization',.978,.0005),('633','throughput',1423,0),('633','production_utilization',.979,.0005),('633','fleet_utilization',.333,.0005),('633','fleet_blocking',.059,.0005),('633','transport_queue',2.33,.005)]:
        row=next(r for r in filtered if r['run']==run)
        claim(run+'_'+key,target,float(row[key]),tol)
    for variant,target in [('window_minutes=30',27),('window_minutes=120',27),('delay_threshold=0.5',27),('delay_threshold=2',27),('codominance_tolerance=0.01',26),('production_saturation=0.85',25),('production_saturation=0.95',25),('wp_persistence=0.7',22)]:
        row=next(r for r in sensitivity if r['corpus']=='filtered' and r['variant']==variant)
        claim('robustness_'+variant,target,int(row['agreement']))
    for row in sensitivity:
        if row['corpus']=='filtered' and row['variant'].startswith('hours='):
            note=('Agreement reproduced with full-horizon production saturation retained; other evidence is cropped.' if 'full_horizon_saturation' in row['variant'] else 'Alternative crop convention: production saturation is recomputed on the cropped horizon. Historical implementation unavailable.')
            claim('robustness_'+row['variant'],27,int(row['agreement']),note=note)
    write_csv(OUTPUT/'historical_claim_ledger.csv',claims)
    figure=OUTPUT/'figure_data'
    through=[]
    for n in ('4','5','6'):
        row={'fleet':int(n)}
        for z,name in [('1','random'),('2','lwt'),('3','nearest')]:
            row[name]=mean([r for r in filtered if r['fleet']==n and r['dispatch']==z],'throughput')
        through.append(row)
    write_csv(figure/'throughput_interaction.csv',through)
    landscape=[dict(run=r['run'],fleet=int(r['fleet']),production_utilization=float(r['production_utilization']),transport_persistence=float(r['transport_persistence']),wp_persistence=float(r['wp_persistence']),regime=r['regime'],congestion=int(r['congestion']),throughput=int(r['throughput'])) for r in filtered]
    write_csv(figure/'rtbd_landscape.csv',landscape)
    for regime in ('transport','mixed','production','indeterminate'):
        for fleet_n in (4,5,6):
            subset=[r for r in landscape if r['regime']==regime and r['fleet']==fleet_n]
            if subset: write_csv(figure/f'landscape_{regime}_{fleet_n}.csv',subset)
    write_csv(figure/'blocking_direction.csv',[dict(fleet=n,forward=next(r['blocking']*100 for r in blocking if r['corpus']=='filtered' and r['fleet']==n and r['direction']==1),backward=next(r['blocking']*100 for r in blocking if r['corpus']=='filtered' and r['fleet']==n and r['direction']==2),bidirectional=next(r['blocking']*100 for r in blocking if r['corpus']=='filtered' and r['fleet']==n and r['direction']==3)) for n in (4,5,6)])
    # Both candidate scientific baselines remain reviewable without rerunning data.
    raw=[r for r in runs if r['corpus']=='raw']
    write_csv(figure/'raw/throughput_interaction.csv',through)
    raw_landscape=[dict(run=r['run'],fleet=int(r['fleet']),production_utilization=float(r['production_utilization']),transport_persistence=float(r['transport_persistence']),wp_persistence=float(r['wp_persistence']),regime=r['regime'],congestion=int(r['congestion']),throughput=int(r['throughput'])) for r in raw]
    write_csv(figure/'raw/rtbd_landscape.csv',raw_landscape)
    for regime in ('transport','mixed','production','indeterminate'):
        for fleet_n in (4,5,6):
            subset=[r for r in raw_landscape if r['regime']==regime and r['fleet']==fleet_n]
            if subset: write_csv(figure/f'raw/landscape_{regime}_{fleet_n}.csv',subset)
    write_csv(figure/'raw/blocking_direction.csv',[dict(fleet=n,forward=next(r['blocking']*100 for r in blocking if r['corpus']=='raw' and r['fleet']==n and r['direction']==1),backward=next(r['blocking']*100 for r in blocking if r['corpus']=='raw' and r['fleet']==n and r['direction']==2),bidirectional=next(r['blocking']*100 for r in blocking if r['corpus']=='raw' and r['fleet']==n and r['direction']==3)) for n in (4,5,6)])
    # Selected data used by a reviewer; corpus comparisons remain separate.
    print(json.dumps(dict(claims=len(claims),matches=sum(r['status']=='matches' for r in claims),discrepancies=[r for r in claims if r['status']=='discrepancy']),indent=2))

if __name__=='__main__': main()
