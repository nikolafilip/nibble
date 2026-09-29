"""The reset-release sweep: the clock card's power-on reset lets go asynchronously to the clock, so on a real power-up the first
clock edge can land anywhere against the 45 us in which the cards release their resets (D053). This walks the release across a
clock period on the whole card deck and asks the emulator at each phase.

    python3 sweep_por.py [--corners TYP,MIX1,MIX2] [--offsets -40:80:10] [--early 20] [-j 2] [--resume out/sweep_por.jsonl]

For each corner: one calibration run with the release pulled to about --early ms (POR_V0 on the clock card's reset capacitor,
machine.py; the release times at POR_V0=0 are the gate25 files' 122.7 / 38.3 / 236.0 ms) tells where the nearest clock edge fell
(Y) and the period (P); a second one, asked for half a period earlier, tells how much of an asked shift arrives (k: the capacitor
is not a bare RC, the first TYP calibration released 2.6 % earlier than asked, which over a period is 40 us, the width of the window
being walked); then one run per wanted offset o, shifting the release by a further ((o - Y) mod P) / k so the nearest edge lands
o us after it (negative: before it). Every run is fib for 12 ticks; the scorer's own "reset: released at" line gives the offset
each run actually got, which is what the table records. Pulling the release to 20 ms changes nothing the machine sees (the
oscillator has run ten periods, every node has been at its rail for milliseconds) and makes a run minutes instead of most of an
hour of simulating a held reset. That holds where the release lands near what was asked: at TYP and MIX1 it came at 16 and
19 ms; at MIX2, whose release without help is at 236 ms, the formula was 7 % out over that distance and the release came at
3.8 ms, a period and a half after power-on: run MIX2 with --early 35. At most two decks at once (-j 2). A passing run's .dat is deleted; a failing run's stays.
Writes out/sweep_por.md; --resume keeps a ledger so a cut-short queue continues."""
import sys, os, math, glob, json, time, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'out')
BOARDS='aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc'; PROG=os.path.join(HERE,'programs','fib.asm'); TICKS=12
VDD=float(os.environ.get('VDD','5')); TAU=0.22                                   # the clock card's reset RC, 100k x 2.2 uF
REL0={'TYP':122.681e-3,'MIX1':38.327e-3,'MIX2':236.033e-3}                     # release at POR_V0=0, from the scorer on the gate25 files (commit 4f2b15d)
LOCK=threading.Lock()

def por_v0(shift): return VDD*(1-math.exp(-shift/TAU))                          # the capacitor voltage at t=0 that brings the release earlier by `shift` seconds

def run(corner,v0,reset_s,ledger=None,done={}):
    """One fib t12 deck at this POR_V0. Returns what the scorer reported: release time, the nearest edge's offset, the period, the score."""
    k=json.dumps([corner,round(v0,6),reset_s]);
    if k in done: return done[k]
    c,seed=(corner[:3],int(corner[3:])) if corner.startswith('MIX') else (corner,1)
    env=dict(os.environ,POR_V0=f'{v0:.6f}',RESET_S=f'{reset_s:g}'); t=time.time()
    r=subprocess.run([sys.executable,os.path.join(HERE,'machine.py'),PROG,'--boards',BOARDS,'--corner',c,'--seed',str(seed),'--ticks',str(TICKS)],capture_output=True,text=True,cwd=HERE,env=env)
    out=r.stdout; res=dict(corner=corner,v0=v0,reset_s=reset_s,ok=r.returncode==0,secs=time.time()-t,rung=1+out.count('retrying with'),
                           released_ms=None,edge_us=None,period_ms=None,summary='')
    for l in out.splitlines():
        if l.strip().startswith('reset: released at'):
            p=l.split(); res['released_ms']=float(p[3]); res['edge_us']=float(p[9]); res['period_ms']=float(p[-2])
        if ' ticks, ' in l: res['summary']=l.split(': ',1)[-1]
    if not res['summary']: res['summary']=(out+r.stderr)[-300:].strip().replace('\n',' | ')
    tag=f"machine_fib_{BOARDS.replace(',','-')}_{corner}_t{TICKS}_por{v0*1e6:.0f}uV"
    if res['ok']:
        for f in glob.glob(os.path.join(OUT,tag+'.dat')): os.remove(f)
    with LOCK:
        print(f"  {corner} POR_V0={v0:.4f} V: {'pass' if res['ok'] else 'FAIL'}: {res['summary']}; release {res['released_ms']} ms, edge {res['edge_us']} us, period {res['period_ms']} ms ({res['secs']:.0f} s{', rung '+str(res['rung']) if res['rung']>1 else ''})",flush=True)
        if ledger: open(ledger,'a').write(json.dumps(dict(key=k,when=time.strftime('%Y-%m-%d %H:%M'),**res))+'\n')
    return res

def main():
    a=sys.argv; get=lambda k,d: a[a.index(k)+1] if k in a else d
    corners=get('--corners','TYP,MIX1,MIX2').split(','); lo,hi,st=[int(x) for x in get('--offsets','-40:80:10').split(':')]
    offsets=list(range(lo,hi+1,st)); early=float(get('--early','20'))*1e-3; jobs=int(get('-j','2')); ledger=get('--resume',None); done={}
    if ledger and os.path.exists(ledger):
        for l in open(ledger):
            d=json.loads(l); done[d['key']]=d
    reset_s=round(early+0.01,3)                                              # the deck's allowance before the ticks: 10 ms past the release
    with ThreadPoolExecutor(jobs) as ex:
        cal={c:ex.submit(run,c,por_v0(REL0[c]-early),reset_s,ledger,done) for c in corners}
        cal={c:f.result() for c,f in cal.items()}
        cal2={c:ex.submit(run,c,por_v0(REL0[c]-early+cal[c]['period_ms']*0.5e-3),reset_s,ledger,done) for c in corners if cal[c]['period_ms']}
        cal2={c:f.result() for c,f in cal2.items()}
        plan=[]
        for c in corners:
            Y=cal[c]['edge_us']; P=cal[c]['period_ms']
            if Y is None or P is None or cal2[c]['edge_us'] is None: print(f'{c}: a calibration run gave no release line, skipped'); continue
            k=((cal2[c]['edge_us']-Y)%(P*1e3))/(P*0.5e3); cal[c]['k']=k       # the share of an asked shift that arrives (asked: half a period)
            if not 0.8<k<1.2: print(f'{c}: the second calibration moved the edge {k:.2f} of what was asked, skipped'); cal[c]['edge_us']=None; continue
            print(f'  {c}: an asked shift arrives x{k:.4f}',flush=True)
            for o in offsets:
                extra=((o-Y)%(P*1e3))*1e-6/k                                 # seconds of further shift so the nearest edge lands o us after the release
                plan.append((c,o,por_v0(REL0[c]-early+extra)))
        futs=[(c,o,ex.submit(run,c,v0,reset_s,ledger,done)) for c,o,v0 in plan]
        rows=[(c,o,f.result()) for c,o,f in futs]
    L=['# Reset-release sweep: fib, 12 ticks, the whole card deck','',f"Generated {time.strftime('%Y-%m-%d %H:%M')} by sim/sweep_por.py. Boards {BOARDS}. VDD {VDD:g} V.",
       'The release is pulled to about %d ms with POR_V0 (see the docstring); "edge" is where the nearest clock edge fell against the release as the scorer measured it,' % (early*1e3),
       'positive after. The cards let go of their resets over the 45 us after the release, so an edge at 0 to +45 us is the straddle.','']
    for c in corners:
        if c not in cal or cal[c]['edge_us'] is None: continue
        L+=[f"## {c}: calibration release {cal[c]['released_ms']} ms, edge {cal[c]['edge_us']:+.0f} us, period {cal[c]['period_ms']} ms ({'pass' if cal[c]['ok'] else 'FAIL'}); second calibration edge {cal2[c]['edge_us']:+.0f} us ({'pass' if cal2[c]['ok'] else 'FAIL'}), an asked shift arrives x{cal[c]['k']:.4f}",'',
            '| wanted us | POR_V0 V | release ms | edge us | period ms | result | time |','|---|---|---|---|---|---|---|']
        for cc,o,r in rows:
            if cc!=c: continue
            e=f"{r['edge_us']:+.0f}" if r['edge_us'] is not None else 'none'
            L.append(f"| {o:+d} | {r['v0']:.4f} | {r['released_ms']} | {e} | {r['period_ms']} | {'pass' if r['ok'] else 'FAIL'}: {r['summary']}{' (rung %d)'%r['rung'] if r['rung']>1 else ''} | {r['secs']:.0f} s |")
        L.append('')
    cals=list(cal.values())+list(cal2.values())
    n=sum(1 for _,_,r in rows if r['ok']); L.append(f"{n} of {len(rows)} sweep runs pass; calibrations {sum(1 for r in cals if r['ok'])} of {len(cals)}.")
    open(os.path.join(OUT,'sweep_por.md'),'w').write('\n'.join(L)+'\n'); print('\n'.join(L[-1:]))
    sys.exit(0 if rows and n==len(rows) and all(r['ok'] for r in cals) else 1)

if __name__=='__main__': main()
