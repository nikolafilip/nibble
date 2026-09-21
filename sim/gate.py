"""The machine gate (docs/plan.md): every reference program on a set of boards, at every corner, against the emulator.
    python3 gate.py --boards alu,hub,panel,reg [--corners TYP,LO,HI,MIX] [--seeds 1,2] [--programs fib,count] [-j 4] [--ticks 12] [--resume out/ledger.jsonl]
Writes out/gate_<boards>.md with one row per (program, corner) and exits 1 if anything mismatched.
--ticks N runs only the first N ticks of every program (the smoke gate: with the clock card a whole deck reports in about half an
hour instead of hours, and every harness fault so far showed within the first twelve ticks); its files carry a _tN suffix, and a row
that needed the ngspice retry ladder says so, since a deck that used to converge on the first rung and no longer does is a finding too.
--resume FILE keeps a ledger of finished runs (one JSON line each, keyed by program, boards, corner, seed, ticks and the CABLE_PF, VDD
and CROSS_PF of the environment): a gate that was cut short (a laptop switched off under a three-day queue) picks up at the first run
it has no passing row for, and the table it writes is still the whole gate. A queue starts a new ledger whenever the harness changes.
"""
import sys, os, glob, subprocess, time, json, threading
from concurrent.futures import ThreadPoolExecutor
HERE=os.path.dirname(os.path.abspath(__file__))

LOCK=threading.Lock()
def key(prog,boards,corner,seed,ticks): return json.dumps([os.path.basename(prog),boards,corner,seed if corner=='MIX' else 1,ticks]+[os.environ.get(k,'') for k in ('CABLE_PF','VDD','CROSS_PF')])

def one(prog,boards,corner,seed,ticks=None,ledger=None,done={}):
    k=key(prog,boards,corner,seed,ticks)
    if k in done:
        res=done[k]; print(f"  {res['prog']} @ {res['corner']}: {'pass' if res['ok'] else 'FAIL'}: {res['summary'].split(': ',1)[-1]} (from the ledger)",flush=True); return res
    t=time.time()
    r=subprocess.run([sys.executable,os.path.join(HERE,'machine.py'),prog,'--boards',boards,'--corner',corner,'--seed',str(seed)]+(['--ticks',str(ticks)] if ticks else []),capture_output=True,text=True,cwd=HERE)
    rung=1+r.stdout.count('retrying with')
    line=[l+(f" (ladder rung {rung})" if rung>1 else "") for l in r.stdout.splitlines() if ' ticks, ' in l]
    detail="\n".join(r.stdout.splitlines()[1:6])
    res=dict(prog=os.path.basename(prog),corner=corner+(str(seed) if corner=='MIX' else ''),ok=r.returncode==0,
             summary=line[0] if line else (r.stdout+r.stderr)[-300:].strip().replace("\n"," | "),detail=detail,secs=time.time()-t)
    print(f"  {res['prog']} @ {res['corner']}: {'pass' if res['ok'] else 'FAIL'}: {res['summary'].split(': ',1)[-1]} ({res['secs']:.0f} s)",flush=True)      # each run as it lands, so a queue's log shows progress
    if ledger:
        with LOCK: open(ledger,'a').write(json.dumps(dict(key=k,when=time.strftime('%Y-%m-%d %H:%M'),**res))+"\n")
    return res

def main():
    a=sys.argv; get=lambda k,d: a[a.index(k)+1] if k in a else d
    boards=get('--boards','alu,hub'); corners=get('--corners','TYP,LO,HI,MIX').split(','); seeds=[int(x) for x in get('--seeds','1').split(',')]
    progs=get('--programs','all'); jobs=int(get('-j','4')); ticks=int(get('--ticks',0)) or None
    progs=sorted(glob.glob(os.path.join(HERE,'programs','*.asm'))) if progs=='all' else [os.path.join(HERE,'programs',p+'.asm') for p in progs.split(',')]
    runs=[(p,boards,c,s) for p in progs for c in corners for s in (seeds if c=='MIX' else [1])]
    ledger=get('--resume',None); done={}
    if ledger and os.path.exists(ledger):
        for l in open(ledger):
            if l.strip():
                d=json.loads(l); k=d.pop('key')
                if d['ok']: done[k]=d      # only a pass is taken from the ledger: a failure is run again
    with ThreadPoolExecutor(jobs) as ex: res=list(ex.map(lambda r: one(*r,ticks=ticks,ledger=ledger,done=done),runs))
    tag=boards.replace(',','-').replace('@','')+(f'_t{ticks}' if ticks else '')
    out=os.path.join(HERE,'out',f'gate_{tag}.md')
    L=[f"# Machine gate: boards {boards}"+(f", first {ticks} ticks of every program (smoke)" if ticks else ""),f"Generated {time.strftime('%Y-%m-%d %H:%M')} by sim/gate.py. Corners: {', '.join(corners)}; MIX seeds {seeds}.","",
       "| program | corner | result | time |","|---|---|---|---|"]
    for r in res: L.append(f"| {r['prog']} | {r['corner']} | {'pass' if r['ok'] else 'FAIL'}: {r['summary'].split(': ',1)[-1]} | {r['secs']:.0f} s |")
    bad=[r for r in res if not r['ok']]
    if bad:
        L+=["","## Failures",""]
        for r in bad: L+=[f"### {r['prog']} @ {r['corner']}","```",r['detail'],"```"]
    open(out,'w').write("\n".join(L)+"\n"); print("\n".join(L[4:])); print("wrote",out)
    sys.exit(1 if bad else 0)

if __name__=='__main__': main()
