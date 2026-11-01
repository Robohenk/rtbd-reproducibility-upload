"""Consistency checks of the full result snapshot; stdlib only."""
import argparse, csv, itertools, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'outputs'
def read(name):
    with (OUTPUT/f'{name}.csv').open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main():
    global OUTPUT
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'outputs')
    OUTPUT=ap.parse_args().output
    expected={''.join(c) for c in itertools.product('456','123','123')}
    runs=read('run_summary'); windows=read('window_evidence'); checks=read('conservation_checks'); manifest=read('input_manifest')
    for corpus in ('filtered','raw','raw_retained'):
        group=[r for r in runs if r['corpus']==corpus]
        assert {r['run'] for r in group}==expected and len(group)==27
        assert len([r for r in windows if r['corpus']==corpus])==27*24*5
        for row in group:
            wr=[r for r in windows if r['corpus']==corpus and r['run']==row['run'] and r['group']=='AGV']
            assert math.isclose(sum(float(r['queue_seconds']) for r in wr)/86400,float(row['transport_queue']),abs_tol=1e-10)
            assert math.isclose(sum(float(r['occupied_seconds']) for r in wr)/(86400*int(row['fleet'])),float(row['fleet_utilization']),abs_tol=1e-12)
            assert math.isclose(sum(float(r['blocked_seconds']) for r in wr)/(86400*int(row['fleet'])),float(row['fleet_blocking']),abs_tol=1e-12)
            for r in wr:
                assert math.isclose(float(r['active_seconds'])+float(r['blocked_seconds']),float(r['occupied_seconds']),abs_tol=1e-10)
                assert 0<=float(r['blocking'])<=float(r['utilization'])<=1
        cc=[r for r in checks if r['corpus']==corpus]
        assert len([r for r in cc if r['level']=='service'])==405
        assert len([r for r in cc if r['level']=='atomic'])==659
        assert all(int(r['difference_us'])==0 for r in cc)
        assert all(int(r['sweep_difference_us'])==0 for r in cc if r['sweep_difference_us'])
    # Independently counted in the initial corpus examination.
    m=[r for r in manifest if r['corpus']=='filtered']
    assert sum(int(r['repairs']) for r in m)==6557
    assert sum(int(r['duplicates']) for r in m)==402
    assert sum(int(r['throughput']) for r in m)==37199
    for run in expected:
        group=[r for r in runs if r['run']==run]
        assert len({r['throughput'] for r in group})==1
        assert next(r['regime'] for r in group if r['corpus']=='filtered')==next(r['regime'] for r in group if r['corpus']=='raw_retained')
    contrasts=read('matched_contrasts')
    for row in contrasts:
        assert math.isclose(float(row['gain_percent']),100*(int(row['to_products'])-int(row['from_products']))/int(row['from_products']),abs_tol=1e-12)
    assert sum(int(r['high_response']) for r in contrasts if r['corpus']=='filtered' and r['from_run'][0]=='4')==6
    for corpus in ('filtered','raw','raw_retained'):
        assert math.isclose(sum(float(r['percent']) for r in read('factorial_decomposition') if r['corpus']==corpus),100,abs_tol=1e-10)
    figures=OUTPUT/'figure_data'
    with (figures/'throughput_interaction.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            for z,name in [('1','random'),('2','lwt'),('3','nearest')]:
                expected_mean=sum(int(r['throughput']) for r in runs if r['corpus']=='filtered' and r['fleet']==row['fleet'] and r['dispatch']==z)/3
                assert math.isclose(float(row[name]),expected_mean,abs_tol=1e-12)
    with (figures/'rtbd_landscape.csv').open(newline='') as f:
        landscape=list(csv.DictReader(f))
    assert {r['run'] for r in landscape}==expected and len(landscape)==27
    for row in landscape:
        source=next(r for r in runs if r['corpus']=='filtered' and r['run']==row['run'])
        for key in ('production_utilization','transport_persistence','wp_persistence'):
            assert float(row[key])==float(source[key])
        assert row['regime']==source['regime']
    print('PASS: 81 run summaries, 9720 window/group rows, 3192 conservation checks, corpus controls, contrasts, factorial sums, and figure coordinates.')

if __name__=='__main__': main()
