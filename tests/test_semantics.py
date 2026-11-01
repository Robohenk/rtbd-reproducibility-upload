import json, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rtbd.core import Event, Interval, US, HORIZON, adapter, reconstruct, validate, window_exposure, evidence, ratio, classify, PRODUCTION, GROUPS, elapsed

def ev(eid,activity,status,t,resource,case='job'):
    return Event(case,str(eid),activity,status,resource,int(t*US))

def service(activity='Transport',start=0,end=10,case='job',resource='.MUs.AGV:1'):
    return [ev(1,activity,'Start',start,resource,case),ev(2,activity,'Waiting',start,resource,case),ev(3,activity,'In progress',start+2,resource,case),ev(4,activity,'Complete',end,resource,case)]

class Semantics(unittest.TestCase):
    def test_queue_occupied_and_independent_sweep(self):
        ints=reconstruct(service())
        self.assertEqual({i.kind:(i.end-i.start)//US for i in ints},{'queue':2,'occupied':8})
        checks=validate(ints,4)
        self.assertTrue(all(c['difference_us']==0 for c in checks))

    def test_blocked_inside_occupied(self):
        e=service(end=12)
        e[3:3]=[ev(5,'Transport','Blocked',4,'.MUs.AGV:1'),ev(6,'Transport','In progress',7,'.MUs.AGV:1'),ev(7,'Transport','Blocked',8,'.MUs.AGV:1'),ev(8,'Transport','In progress',9,'.MUs.AGV:1')]
        ints=reconstruct(e); validate(ints,4)
        occupied=sum(i.end-i.start for i in ints if i.kind=='occupied')
        blocked=sum(i.end-i.start for i in ints if i.kind=='blocked')
        self.assertEqual(occupied,10*US); self.assertEqual(blocked,4*US)
        self.assertEqual(occupied-blocked,6*US)

    def test_repeated_occurrences_do_not_merge(self):
        ints=reconstruct(service()+service(start=20,end=30))
        self.assertEqual({i.occurrence for i in ints},{1,2})
        self.assertEqual(sum(i.end-i.start for i in ints if i.kind=='occupied'),16*US)

    def test_narrow_repair_reorders_only_equal_time(self):
        e=service('Welding',0,10,resource='.Models.JobShop.Welding.Machine')
        e += [ev(5,'Welding','In progress',10,'.MUs.AGV:1'),ev(6,'Transport','Start',10,'.MUs.AGV:1'),ev(7,'Transport','Waiting',10,'.MUs.AGV:1'),ev(8,'Transport','Complete',20,'.MUs.AGV:1')]
        adapted,audit=adapter(e)
        self.assertEqual([x.eid for x in adapted[-4:]],['6','7','5','8'])
        self.assertEqual(len(audit),1)
        ints=reconstruct(adapted)
        self.assertEqual(sum(i.end-i.start for i in ints if i.kind=='occupied' and i.group=='AGV'),10*US)
        self.assertEqual({x.eid:x.time for x in e},{x.eid:x.time for x in adapted})
        e[5]=ev(6,'Transport','Start',11,'.MUs.AGV:1')
        with self.assertRaises(ValueError): adapter(e)

    def test_consecutive_duplicate_only(self):
        e=service(); e.insert(3,ev(5,'Transport','In progress',2,'.MUs.AGV:1'))
        clean,audit=adapter(e)
        self.assertEqual(len(clean),4); self.assertEqual(len(audit),1)
        e=service(); e[3:3]=[ev(5,'Transport','Blocked',2,'.MUs.AGV:1'),ev(6,'Transport','In progress',2,'.MUs.AGV:1')]
        clean,audit=adapter(e)
        self.assertEqual(len(clean),6); self.assertEqual(len(audit),0)
        self.assertEqual(sum(i.end-i.start for i in reconstruct(clean) if i.kind=='blocked'),0)

    def test_right_censoring(self):
        ints=reconstruct(service()[:2],horizon=10*US)
        self.assertEqual(len(ints),1); self.assertTrue(ints[0].censored)
        self.assertEqual(ints[0].end,10*US)
        e=service()[:3]+[ev(4,'Transport','Blocked',5,'.MUs.AGV:1')]
        ints=reconstruct(e,horizon=10*US)
        self.assertEqual({i.kind:(i.end-i.start)//US for i in ints},{'queue':2,'occupied':8,'blocked':5})

    def test_window_boundary_and_crop(self):
        i=Interval('c',1,'Transport','queue','buffer','AGV',5*US,25*US,'1','2')
        t=window_exposure([i],10*US,10*US,30*US)
        self.assertEqual(t['AGV',0,'queue'],10*US)
        self.assertEqual(t['AGV',1,'queue'],5*US)
        self.assertEqual(sum(t.values()),15*US)

    def test_physical_queue_and_service_group_are_distinct(self):
        e=service(); e[1]=ev(2,'Transport','Waiting',0,'.Models.JobShop.Welding.Output')
        q=next(i for i in reconstruct(e) if i.kind=='queue')
        self.assertEqual(q.resource,'.Models.JobShop.Welding.Output'); self.assertEqual(q.group,'AGV')

    def test_atomic_overlap_rejected(self):
        ints=reconstruct(service(case='a'))+reconstruct(service(case='b'))
        with self.assertRaisesRegex(ValueError,'Concurrent occupancy'): validate(ints,4)

    def test_orphan_and_bad_resume_rejected(self):
        with self.assertRaises(ValueError): reconstruct(service()[1:])
        e=service(); e.insert(3,ev(5,'Transport','In progress',3,'.MUs.AGV:1'))
        with self.assertRaisesRegex(ValueError,'repeated'): reconstruct(e)

    def test_zero_service_ratios(self):
        self.assertEqual(ratio(0,0),0)
        self.assertEqual(ratio(1,0),float('inf'))
        self.assertEqual(ratio(6,2),3)

    def test_fixed_pool_multiplicity_and_near_ties(self):
        cfg=json.loads((Path(__file__).resolve().parents[1]/'config/baseline.json').read_text())
        cfg['end_hour']=1
        width=3600*US
        totals={(g,0,k):0 for g in GROUPS for k in ('queue','occupied','blocked')}
        for g,seconds in [('Welding',3600),('Painting',3528),('AGV',3600)]:
            totals[g,0,'occupied']=seconds*US
            totals[g,0,'queue']=seconds*US
        summary,rows=evidence(totals,4,cfg)
        self.assertEqual(summary['fleet_utilization'],.25)
        self.assertEqual(summary['wp_persistence'],1)
        totals['Painting',0,'occupied']-=1
        summary,_=evidence(totals,4,cfg)
        self.assertEqual(summary['wp_persistence'],0)

    def test_regime_boundaries_and_indeterminate(self):
        c={'transport_persistence':.5,'production_saturation':.9,'wp_persistence':.5}
        self.assertEqual(classify(.5,.9,0,c),'mixed')
        self.assertEqual(classify(.5,.899,0,c),'transport')
        self.assertEqual(classify(.49,.99,.5,c),'production')
        self.assertEqual(classify(.49,.99,.49,c),'indeterminate')

    def test_source_precision(self):
        self.assertEqual(elapsed('2019/04/18 00:00:04.0005'),4_000_500)
        self.assertEqual(elapsed('2019-04-18T00:00:04.000+02:00'),4_000_000)

if __name__=='__main__': unittest.main()
