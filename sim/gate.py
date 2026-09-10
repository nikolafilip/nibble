"""The machine gate (docs/plan.md): every reference program on a set of boards, at every corner, against the emulator.
    python3 gate.py --boards alu,hub,panel,reg [--corners TYP,LO,HI,MIX] [--seeds 1,2] [--programs fib,count] [-j 4]
Writes out/gate_<boards>.md with one row per (program, corner) and exits 1 if anything mismatched.
"""
import sys, os, glob, subprocess, time
from concurrent.futures import ThreadPoolExecutor
HERE=os.path.dirname(os.path.abspath(__file__))

def one(prog,boards,corner,seed):
    t=time.time()
    r=subprocess.run([sys.executable,os.path.join(HERE,'machine.py'),prog,'--boards',boards,'--corner',corner,'--seed',str(seed)],capture_output=True,text=True,cwd=HERE)
    line=[l for l in r.stdout.splitlines() if ' ticks, ' in l]
    detail="\n".join(r.stdout.splitlines()[1:6])
    return dict(prog=os.path.basename(prog),corner=corner+(str(seed) if corner=='MIX' else ''),ok=r.returncode==0,
                summary=line[0] if line else (r.stdout+r.stderr)[-300:].strip().replace("\n"," | "),detail=detail,secs=time.time()-t)

def main():
    a=sys.argv; get=lambda k,d: a[a.index(k)+1] if k in a else d
    boards=get('--boards','alu,hub'); corners=get('--corners','TYP,LO,HI,MIX').split(','); seeds=[int(x) for x in get('--seeds','1').split(',')]
    progs=get('--programs','all'); jobs=int(get('-j','4'))
    progs=sorted(glob.glob(os.path.join(HERE,'programs','*.asm'))) if progs=='all' else [os.path.join(HERE,'programs',p+'.asm') for p in progs.split(',')]
    runs=[(p,boards,c,s) for p in progs for c in corners for s in (seeds if c=='MIX' else [1])]
    with ThreadPoolExecutor(jobs) as ex: res=list(ex.map(lambda r: one(*r),runs))
    tag=boards.replace(',','-').replace('@','')
    out=os.path.join(HERE,'out',f'gate_{tag}.md')
    L=[f"# Machine gate: boards {boards}",f"Generated {time.strftime('%Y-%m-%d %H:%M')} by sim/gate.py. Corners: {', '.join(corners)}; MIX seeds {seeds}.","",
       "| program | corner | result | time |","|---|---|---|---|"]
    for r in res: L.append(f"| {r['prog']} | {r['corner']} | {'pass' if r['ok'] else 'FAIL'}: {r['summary'].split(': ',1)[-1]} | {r['secs']:.0f} s |")
    bad=[r for r in res if not r['ok']]
    if bad:
        L+=["","## Failures",""]
        for r in bad: L+=[f"### {r['prog']} @ {r['corner']}","```",r['detail'],"```"]
    open(out,'w').write("\n".join(L)+"\n"); print("\n".join(L[4:])); print("wrote",out)
    sys.exit(1 if bad else 0)

if __name__=='__main__': main()
