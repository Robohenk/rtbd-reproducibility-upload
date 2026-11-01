"""Exact integer-microsecond interval reconstruction and window exposure.

Only Python's standard library is required. Source inputs are never modified.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from fractions import Fraction
from pathlib import Path
import csv
import xml.etree.ElementTree as ET

US = 1_000_000
HORIZON = 24 * 3600 * US
PRODUCTION = ('Sawing', 'Drilling', 'Welding', 'Painting')
GROUPS = PRODUCTION + ('AGV',)

@dataclass(frozen=True)
class Event:
    case: str
    eid: str
    activity: str
    status: str
    resource: str
    time: int

@dataclass(frozen=True)
class Interval:
    case: str
    occurrence: int
    activity: str
    kind: str
    resource: str
    group: str
    start: int
    end: int
    open_id: str
    close_id: str
    censored: bool = False

def elapsed(value, raw=False):
    dt = datetime.fromisoformat(value.replace('/', '-').replace(' ', 'T'))
    # Simulation origin: midnight of the timestamp's local simulation date.
    return ((dt.hour * 60 + dt.minute) * 60 + dt.second) * US + dt.microsecond

def read_events(path, raw=False):
    traces = defaultdict(list)
    dates = set()
    if raw:
        with Path(path).open(encoding='utf-8-sig', newline='') as f:
            for e in csv.DictReader(f, delimiter='\t'):
                dates.add(e['Timestamp'][:10])
                traces[e['Product']].append(Event(e['Product'], e['ID'], e['Event'], e['Status'], e['Resource'], elapsed(e['Timestamp'], True)))
    else:
        # iterparse keeps memory bounded by a log, and supports namespaced XES.
        for _, tr in ET.iterparse(path, events=('end',)):
            if tr.tag.rsplit('}', 1)[-1] != 'trace':
                continue
            case = next(x.attrib['value'] for x in tr if x.attrib.get('key') == 'concept:name')
            for node in tr:
                if node.tag.rsplit('}', 1)[-1] != 'event':
                    continue
                e = {x.attrib['key']: x.attrib['value'] for x in node}
                dates.add(e['time:timestamp'][:10])
                traces[case].append(Event(case, e['ID'], e['concept:name'], e['lifecycle:transition'], e['org:resource'], elapsed(e['time:timestamp'])))
            tr.clear()
    if len(dates) != 1:
        raise ValueError(f'Expected a single simulation date, got {dates}')
    for case, evs in traces.items():
        if any(b.time < a.time for a, b in zip(evs, evs[1:])):
            raise ValueError(f'Non-monotonic source trace {case}')
        if any(e.time < 0 or e.time >= HORIZON for e in evs):
            raise ValueError(f'Event outside [0,24h): {case}')
    return dict(traces)

def adapter(events):
    """Repair a narrowly specified same-time production-to-transport pattern.

    Candidate must immediately follow production Complete and precede Transport
    Start, Waiting; all four transitions share a timestamp and the last three
    share the same AGV. Emit Start, Waiting, repaired In progress, recording IDs.
    Remove only consecutive identical In progress transitions (ID excluded).
    """
    repaired, audit = [], []
    i = 0
    while i < len(events):
        e = events[i]
        if e.status == 'In progress' and 'AGV:' in e.resource and e.activity != 'Transport':
            prev = events[i-1] if i else None
            nxt = events[i+1:i+3]
            valid = (prev is not None and e.activity in PRODUCTION and
                     prev.activity == e.activity and prev.status == 'Complete' and
                     prev.time == e.time and len(nxt) == 2 and
                     [x.status for x in nxt] == ['Start', 'Waiting'] and
                     all(x.activity == 'Transport' and x.resource == e.resource and x.time == e.time for x in nxt))
            if not valid:
                raise ValueError(f'Unresolved label repair candidate {e}')
            repaired.extend([*nxt, replace(e, activity='Transport')])
            audit.append(dict(case=e.case, event_id=e.eid, action='repair_label_and_same_time_order', original_activity=e.activity, activity='Transport', time_us=e.time, related_ids=','.join(x.eid for x in nxt)))
            i += 3
        else:
            repaired.append(e)
            i += 1
    result = []
    for e in repaired:
        prev = result[-1] if result else None
        if (prev is not None and e.status == 'In progress' and
            (e.activity, e.status, e.resource, e.time) == (prev.activity, prev.status, prev.resource, prev.time)):
            audit.append(dict(case=e.case, event_id=e.eid, action='ignore_consecutive_duplicate_ip', original_activity=e.activity, activity=e.activity, time_us=e.time, related_ids=prev.eid))
        else:
            result.append(e)
    return result, audit

def reconstruct(events, horizon=HORIZON):
    out, active = [], {}
    occurrence = 0
    def emit(st, kind, opening, closing, resource, censored=False):
        end, eid = (horizon, '') if closing is None else (closing.time, closing.eid)
        if end < opening.time:
            raise ValueError('Negative interval')
        group = 'AGV' if st['activity'] == 'Transport' else st['activity']
        out.append(Interval(opening.case, st['occurrence'], st['activity'], kind, resource, group,
                            opening.time, end, opening.eid, eid, censored))
    for e in events:
        if e.activity not in PRODUCTION + ('Transport',):
            if e.activity not in ('Arrival', 'Drain'):
                raise ValueError(f'Unknown activity: {e.activity}')
            continue
        if e.status == 'Start':
            if e.activity in active:
                raise ValueError(f'Overlapping occurrence {e}')
            occurrence += 1
            active[e.activity] = dict(activity=e.activity, occurrence=occurrence, start=e, waiting=None, ip=None, block=None)
            continue
        if e.activity not in active:
            raise ValueError(f'Orphan transition {e}')
        st = active[e.activity]
        if e.status == 'Waiting':
            if st['waiting'] is not None or st['ip'] is not None:
                raise ValueError(f'Unexpected Waiting {e}')
            st['waiting'] = e
        elif e.status == 'In progress':
            if st['ip'] is None:
                if st['waiting'] is None:
                    raise ValueError(f'Service before Waiting {e}')
                expected = 'AGV:' if e.activity == 'Transport' else e.activity + '.Machine'
                if expected not in e.resource:
                    raise ValueError(f'Unexpected service resource {e}')
                emit(st, 'queue', st['waiting'], e, st['waiting'].resource)
                st['ip'] = e
            elif st['block'] is not None:
                if e.resource != st['ip'].resource:
                    raise ValueError('Resource changed within service')
                emit(st, 'blocked', st['block'], e, st['block'].resource)
                st['block'] = None
            else:
                raise ValueError(f'Unexplained repeated In progress {e}')
        elif e.status == 'Blocked':
            if st['ip'] is None or st['block'] is not None or e.resource != st['ip'].resource or e.activity != 'Transport':
                raise ValueError(f'Invalid blocking transition {e}')
            st['block'] = e
        elif e.status == 'Complete':
            if st['ip'] is None or e.resource != st['ip'].resource:
                raise ValueError(f'Completion without matching service {e}')
            if st['block'] is not None:
                emit(st, 'blocked', st['block'], e, st['block'].resource)
            emit(st, 'occupied', st['ip'], e, st['ip'].resource)
            del active[e.activity]
        else:
            raise ValueError(f'Unknown transition {e}')
    for st in active.values():
        if st['ip'] is not None:
            emit(st, 'occupied', st['ip'], None, st['ip'].resource, True)
            if st['block'] is not None:
                emit(st, 'blocked', st['block'], None, st['block'].resource, True)
        elif st['waiting'] is not None:
            emit(st, 'queue', st['waiting'], None, st['waiting'].resource, True)
        else:
            raise ValueError(f'Unfinished Start without Waiting {st}')
    return out

def overlap(s, e, lo, hi):
    return max(0, min(e, hi) - max(s, lo))

def window_exposure(intervals, width, lo=0, hi=HORIZON):
    if hi <= lo or (hi-lo) % width:
        raise ValueError('Horizon must contain whole windows')
    totals = {(g, k, kind): 0 for g in GROUPS for k in range((hi-lo)//width) for kind in ('queue','occupied','blocked')}
    for it in intervals:
        a, b = max(it.start, lo), min(it.end, hi)
        if b <= a:
            continue
        for k in range((a-lo)//width, (b-1-lo)//width+1):
            totals[it.group, k, it.kind] += overlap(a, b, lo+k*width, lo+(k+1)*width)
    return totals

def sweep_exposure(intervals, kind, group, lo, hi):
    # Independent endpoint integration, for queue/occupied/blocked conservation.
    changes = Counter()
    for it in intervals:
        if it.kind == kind and it.group == group:
            a,b=max(it.start,lo),min(it.end,hi)
            if b>a:
                changes[a]+=1; changes[b]-=1
    count=area=0; previous=lo
    for t, delta in sorted(changes.items()):
        area += (t-previous)*count
        count += delta
        if count<0:
            raise ValueError('Negative endpoint count')
        previous=t
    if count:
        raise ValueError('Unclosed sweep')
    return area

def validate(intervals, fleet):
    by_occ=defaultdict(list); by_resource=defaultdict(list)
    for it in intervals:
        if it.end < it.start or it.start < 0 or it.end > HORIZON:
            raise ValueError(f'Invalid interval {it}')
        by_occ[it.case,it.occurrence].append(it)
        if it.kind=='occupied' and it.end>it.start:
            by_resource[it.resource].append(it)
    for key, items in by_occ.items():
        occupied=[i for i in items if i.kind=='occupied']
        blocked=sorted((i for i in items if i.kind=='blocked'),key=lambda i:i.start)
        if blocked:
            if len(occupied)!=1:
                raise ValueError(f'Blocking without occupied service: {key}')
            occ=occupied[0]
            if any(i.start<occ.start or i.end>occ.end or i.resource!=occ.resource for i in blocked):
                raise ValueError('Blocking outside occupied service')
            if any(a.end>b.start for a,b in zip(blocked,blocked[1:])):
                raise ValueError('Overlapping blocked intervals')
            if sum(i.end-i.start for i in blocked)>occ.end-occ.start:
                raise ValueError('Negative active time')
    for resource, items in by_resource.items():
        items.sort(key=lambda i:(i.start,i.end))
        if any(a.end>b.start for a,b in zip(items,items[1:])):
            raise ValueError(f'Concurrent occupancy on unit resource {resource}')
    agvs={r for r in by_resource if 'AGV:' in r}
    if len(agvs)>fleet:
        raise ValueError('Observed fleet exceeds configured multiplicity')
    totals=window_exposure(intervals,3600*US)
    checks=[]
    for group in GROUPS:
        for kind in ('queue','occupied','blocked'):
            whole=sum(i.end-i.start for i in intervals if i.group==group and i.kind==kind)
            window=sum(totals[group,k,kind] for k in range(24))
            sweep=sweep_exposure(intervals,kind,group,0,HORIZON)
            if whole!=window or whole!=sweep:
                raise ValueError('Service conservation failed')
            checks.append(dict(level='service', key=group, kind=kind, total_us=whole, difference_us=whole-window, sweep_difference_us=whole-sweep))
    atomic=defaultdict(list)
    for it in intervals:
        atomic[it.resource,it.kind].append(it)
    for (resource,kind),items in sorted(atomic.items()):
        whole=sum(i.end-i.start for i in items)
        # Compute independently over explicit window edges.
        window=sum(overlap(i.start,i.end,k*3600*US,(k+1)*3600*US) for i in items for k in range(24))
        if whole!=window:
            raise ValueError('Atomic conservation failed')
        checks.append(dict(level='atomic',key=resource,kind=kind,total_us=whole,difference_us=whole-window,sweep_difference_us=''))
    return checks

def ratio(q,b):
    return q/b if b else (float('inf') if q else 0.0)

def classify(transport_persistence, production_utilization, wp_persistence, config):
    if transport_persistence >= config['transport_persistence']:
        return 'mixed' if production_utilization >= config['production_saturation'] else 'transport'
    if wp_persistence >= config['wp_persistence']:
        return 'production'
    return 'indeterminate'

def evidence(totals, fleet, config):
    width=config['window_minutes']*60*US
    n=(config['end_hour']-config['start_hour'])*3600*US//width
    rows=[]; wp=tr=0
    theta=Fraction(str(config['capacity_threshold']))
    epsilon=Fraction(str(config['codominance_tolerance']))
    delay=Fraction(str(config['delay_threshold']))
    trtheta=Fraction(str(config['transport_pressure_threshold']))
    for k in range(n):
        b={g:totals[g,k,'occupied'] for g in GROUPS}
        q={g:totals[g,k,'queue'] for g in GROUPS}
        maxb=max(b[g] for g in PRODUCTION)
        capacity={g for g in PRODUCTION if b[g]>=theta*width and maxb-b[g]<=epsilon*width}
        delayed={g for g in PRODUCTION if (b[g]>0 and q[g]>=delay*b[g]) or (b[g]==0 and q[g]>0)}
        joint=capacity & delayed
        wp+= {'Welding','Painting'}<=joint
        transport=(b['AGV']>0 and q['AGV']>=trtheta*b['AGV']) or (b['AGV']==0 and q['AGV']>0)
        tr+=transport
        for g in GROUPS:
            z=totals[g,k,'blocked']; m=fleet if g=='AGV' else 1
            rows.append(dict(window=k, start_hour=config['start_hour']+k*width/(3600*US), group=g,
                occupied_seconds=b[g]/US,queue_seconds=q[g]/US,blocked_seconds=z/US,active_seconds=(b[g]-z)/US,
                utilization=b[g]/(m*width),mean_queue=q[g]/width,delay_ratio=ratio(q[g],b[g]),blocking=z/(m*width),
                capacity_dominant=int(g in capacity),delay_dominant=int(g in delayed),joint_dominant=int(g in joint),
                transport_pressure=int(transport) if g=='AGV' else 0))
    duration=width*n
    summary=dict(transport_persistence=tr/n, wp_persistence=wp/n,
        production_utilization=max(sum(totals[g,k,'occupied'] for k in range(n))/duration for g in PRODUCTION),
        fleet_utilization=sum(totals['AGV',k,'occupied'] for k in range(n))/(fleet*duration),
        transport_queue=sum(totals['AGV',k,'queue'] for k in range(n))/duration,
        fleet_blocking=sum(totals['AGV',k,'blocked'] for k in range(n))/(fleet*duration))
    summary['regime']=classify(summary['transport_persistence'],summary['production_utilization'],summary['wp_persistence'],config)
    summary['congestion']=int(summary['fleet_blocking']>=config['blocking_modifier'])
    return summary,rows
