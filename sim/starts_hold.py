"""The machine's starts with the hold-off (D064): fib for 12 ticks on the whole card deck, the two parts in the deck (HOLD=1).

    python3 starts_hold.py [-j 2] [--resume out/starts_hold.jsonl] [--only sweep,corners,press]

sweep     every start of the reset sweep again, at the POR_V0 it had: the 45 runs of out/sweep_por.jsonl (39 of the sweep, 6
          calibrations; two of them failed) and the start of out/sweep_por_mix2.jsonl that failed. Same corner, same release.
corners   a start at LO, HI, MIX3 and MIX4, the reset left to run its own length (the run ends itself after the release).
press     the panel's RST button pressed while the machine runs, at TYP, MIX1 and MIX2: the finger comes down at four places
          a quarter of a clock period apart, stays 20 ms, and the run is scored from the release the button's debounce makes.
A run passes when the emulator agrees on all 12 ticks and the first clock edge came 1 ms or more after the release.
Writes results/starts_hold.md. At most two decks at once. A passing run's .dat is deleted; a failing run's stays."""
import sys, os, glob, json, time, subprocess, threading
from concurrent.futures import ThreadPoolExecutor
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'out'); DOC=os.path.join(HERE,'results','starts_hold.md')
BOARDS='aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc'; PROG=os.path.join(HERE,'programs','fib.asm'); TICKS=12; EDGE_MIN=1000
LOCK=threading.Lock()

def plan(only):
    P=[]
    if 'sweep' in only:
        for f,pick in (('sweep_por.jsonl',lambda r:True),('sweep_por_mix2.jsonl',lambda r:not r['ok'])):
            for l in open(os.path.join(OUT,f)):
                if not l.strip(): continue
                r=json.loads(l)
                if pick(r): P.append(dict(group='sweep',corner=r['corner'],env=dict(POR_V0=f"{r['v0']:.6f}",RESET_S=f"{r['reset_s']:g}"),
                                          before=f"{'pass' if r['ok'] else 'FAIL'}, edge {r['edge_us']:+.0f} us" if r['edge_us'] is not None else ('pass' if r['ok'] else 'FAIL')))
    if 'corners' in only:
        for c in ('LO','HI','MIX3','MIX4'): P.append(dict(group='corners',corner=c,env=dict(RESET_S='0.6',END_AFTER_RELEASE='1'),before=''))
    if 'press' in only:
        for c,v0,per in (('TYP','1.864759',1.64e-3),('MIX1','0.399645',2.48e-3),('MIX2','3.127134',2.476e-3)):      # the release of each corner's first sweep run (17, 20 and 5 ms), its period
            for k in range(4):
                dn=35e-3+k*per/4; P.append(dict(group='press',corner=c,env=dict(POR_V0=v0,RESET_S='1.0',RST_PRESS=f'{dn:.6f},{dn+20e-3:.6f}'),before=''))
    return P

def run(p,ledger=None,done={}):
    k=json.dumps([p['group'],p['corner'],sorted(p['env'].items())])
    if k in done: res=done[k]
    else:
        c,seed=(p['corner'][:3],int(p['corner'][3:])) if p['corner'].startswith('MIX') else (p['corner'],1)
        env=dict(os.environ,HOLD='1',**p['env']); t=time.time()
        r=subprocess.run([sys.executable,os.path.join(HERE,'machine.py'),PROG,'--boards',BOARDS,'--corner',c,'--seed',str(seed),'--ticks',str(TICKS)],capture_output=True,text=True,cwd=HERE,env=env)
        out=r.stdout; res=dict(p,scored=r.returncode==0,secs=time.time()-t,rung=1+out.count('retrying with'),released_ms=None,edge_us=None,period_ms=None,summary='')
        for l in out.splitlines():
            if l.strip().startswith('reset: released at'):
                w=l.split(); res['released_ms']=float(w[3]); res['edge_us']=float(w[9]); res['period_ms']=float(w[-2])
            if ' ticks, ' in l: res['summary']=l.split(': ',1)[-1]
        if not res['summary']: res['summary']=(out+r.stderr)[-300:].strip().replace('\n',' | ')
        res['ok']=bool(res['scored'] and res['edge_us'] is not None and res['edge_us']>=EDGE_MIN)
        e=p['env']; tag=(f"machine_fib_{BOARDS.replace(',','-')}_{p['corner']}_t{TICKS}"+(f"_por{float(e['POR_V0'])*1e6:.0f}uV" if 'POR_V0' in e else '')+'_hold'
                       +(f"_press{float(e['RST_PRESS'].split(',')[0])*1e6:.0f}us" if 'RST_PRESS' in e else '')+('_ear' if 'END_AFTER_RELEASE' in e else ''))
        res['tag']=tag
        if res['ok']:
            for f in glob.glob(os.path.join(OUT,tag+'.dat')): os.remove(f)
        if ledger:
            with LOCK: open(ledger,'a').write(json.dumps(dict(key=k,when=time.strftime('%Y-%m-%d %H:%M'),**res))+'\n')
    with LOCK: print(f"  {res['group']} {res['corner']} {' '.join(f'{a}={b}' for a,b in sorted(res['env'].items()))}: {'pass' if res['ok'] else 'FAIL'}: {res['summary']}; release {res['released_ms']} ms, first edge {res['edge_us']} us after it ({res['secs']:.0f} s)",flush=True)
    return res

def main():
    a=sys.argv; get=lambda k,d: a[a.index(k)+1] if k in a else d
    jobs=int(get('-j','2')); ledger=get('--resume',None); only=get('--only','sweep,corners,press').split(','); done={}
    if ledger and os.path.exists(ledger):
        for l in open(ledger):
            if l.strip():
                d=json.loads(l)
                if d['ok']: done[d.pop('key')]=d      # a failure is run again
    with ThreadPoolExecutor(jobs) as ex: rows=list(ex.map(lambda p: run(p,ledger,done),plan(only)))
    n=sum(1 for r in rows if r['ok'])
    L=['# The machine\'s starts with the hold-off: fib, 12 ticks, the whole card deck','',f"Generated {time.strftime('%Y-%m-%d %H:%M')} by sim/starts_hold.py. Boards {BOARDS}. The two parts of D064 are in the deck (`HOLD=1`), not on the card.",
       f'A run passes when the emulator agrees on all 12 ticks and the first clock edge came {EDGE_MIN/1000:g} ms or more after RST fell under 0.7 VDD.','']
    for g,title in (('sweep','The starts of the reset sweep again, each at the POR_V0 it had'),('corners','Other corners, the reset left to its own length'),('press','The panel\'s RST button pressed while the machine runs')):
        R=[r for r in rows if r['group']==g]
        if not R: continue
        L+=[f"## {title}: {sum(1 for r in R if r['ok'])} of {len(R)}",'','| corner | '+('finger down, up s' if g=='press' else 'POR_V0 V')+' | release ms | first edge after it us | period ms | result |'+(' without the hold-off |' if g=='sweep' else '')+' time |','|---|---|---|---|---|---|---|'+('---|' if g=='sweep' else '')]
        for r in R:
            L.append(f"| {r['corner']} | {r['env'].get('RST_PRESS','').replace(',',', ') if g=='press' else r['env'].get('POR_V0','0')} | {r['released_ms']} | {r['edge_us'] if r['edge_us'] is None else format(r['edge_us'],'+.0f')} | {r['period_ms']} | "
                     f"{'pass' if r['ok'] else 'FAIL'}: {r['summary']}{' (rung %d)'%r['rung'] if r['rung']>1 else ''} |"+(f" {r['before']} |" if g=='sweep' else '')+f" {r['secs']:.0f} s |")
        L.append('')
    L.append(f"{n} of {len(rows)} starts pass.")
    open(DOC,'w').write('\n'.join(L)+'\n'); print(L[-1]); sys.exit(0 if rows and n==len(rows) else 1)

if __name__=='__main__': main()
