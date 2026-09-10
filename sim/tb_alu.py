"""Testbench for board 01 (ALU). Builds stimuli, runs ngspice on a netlist, checks every case.
Usage: python3 tb_alu.py <netlist.cir|dev> <outdir> [--corner TYP|LO|HI|MIX] [--seed N] [--cases exhaustive|demo] [--rescore]
The netlist is either the dev netlist (built from alu.py) or a kicad-cli export of boards/01-alu.
A case is (A, B, controls, EO) with controls a subset of SUB ONE F0 F1. Exhaustive = every A, B, SUB and function
(2048 cases) plus every A with ONE for both SUB values and all four functions with B = 0 and 15 (256 cases).
"""
import sys, os, subprocess, random, json, numpy as np
import spicedat
import nmos, alu

T=400e-6          # per case
TR=1e-6
HUB_PU='10k'
INPUTS=['A0','A1','A2','A3','B0','B1','B2','B3','SUB','ONE','F0','F1','EO']
FN={'add':(),'and':('F0',),'or':('F1',),'xor':('F0','F1')}

def demo_cases():
    c=[]
    for a,b,s in [(3,4,0),(7,5,1),(6,6,1),(2,5,1),(9,7,0),(15,1,0),(0,0,1),(8,8,0),(5,3,1),(12,4,1),(1,15,0),(7,1,1)]:
        c.append((a,b,('SUB',) if s else (),1))
    c+=[(5,0,('ONE',),1),(15,9,('ONE',),1),(0,3,('ONE','SUB'),1),(9,2,('ONE','SUB'),1)]          # INC 5, INC 15 (carry), DEC 0 (borrow), DEC 9
    c+=[(12,10,('F0',),1),(12,10,('F1',),1),(12,10,('F0','F1'),1),(15,15,('F0','F1'),1)]            # 12 and/or/xor 10, 15 xor 15 (zero)
    c.append((5,3,(),0))   # EO low: bus must float high
    return c
def exhaustive_cases():
    c=[(a,b,tuple(s)+f,1) for f in FN.values() for s in ((),('SUB',)) for a in range(16) for b in range(16)]
    c+=[(a,b,('ONE',)+tuple(s)+f,1) for f in FN.values() for s in ((),('SUB',)) for a in range(16) for b in (0,15)]
    return c

def expected(a,b,ctl):
    """What the hardware computes. Logic functions see XB (= B xor SUB); the sequencer never sets SUB with them."""
    if 'ONE' in ctl: b=1
    xb=(~b)&15 if 'SUB' in ctl else b
    f=(2 if 'F1' in ctl else 0)+(1 if 'F0' in ctl else 0)
    if f==0:
        r=a+xb+(1 if 'SUB' in ctl else 0); cf=(r>>4)&1; S=r&15
    else:
        S=[0,a&xb,a|xb,a^xb][f]; cf=0
    return S,cf,int(S==0)

def pwl(bits):
    """bits: list of 0/1 per case -> PWL string"""
    pts=[(0,bits[0]*5)]; t=0
    for k in range(1,len(bits)):
        t=k*T; pts.append((t-TR/2,bits[k-1]*5)); pts.append((t+TR/2,bits[k]*5))
    pts.append((len(bits)*T,bits[-1]*5))
    return 'PWL('+' '.join(f'{x:.7g} {y:g}' for x,y in pts)+')'

def bitof(name,case):
    a,b,ctl,eo=case
    if name[0]=='A' and name[1:].isdigit(): return (a>>int(name[1]))&1
    if name[0]=='B' and name[1:].isdigit(): return (b>>int(name[1]))&1
    if name=='EO': return eo
    return int(name in ctl)

def sources(cases):
    return [f"V{name} {name} 0 {pwl([bitof(name,c) for c in cases])}" for name in INPUTS]

def deck(netlist_lines, cases, corner, outfile, probes, kicad=False, seed=1):
    models={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}; rng=random.Random(seed)
    body=[]
    for l in netlist_lines:
        if l.lower().startswith(('.end','.tran','.include','.lib','.title','.ic','.option','.control')): continue
        if kicad and l[0] not in '.*+' and int(''.join(c for c in l.split()[0] if c.isdigit()) or 0)>=9000: continue   # testbench sheet parts
        if l[0] in 'Mm': l=l.replace(' 2N7000',' '+(models[rng.choice(['LO','TYP','HI'])] if corner=='MIX' else models[corner]))
        body.append(l)
    supply=["VDD +5V 0 5"]+[f"RHUB{i} +5V BUS{i}# {HUB_PU}" for i in range(4)]
    tend=len(cases)*T
    lib=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib','2N7000.lib')
    return "\n".join(["* ALU testbench", f'.include "{lib}"', nmos.LED_MODEL]+supply+sources(cases)+body+
        [f".tran 2u {tend:.6g}", ".option method=gear", ".control","run","set wr_singlescale","set wr_vecnames",
         f"wrdata {outfile} "+" ".join(f"v({p.lower()})" for p in probes),"quit",".endc",".end"])

def dev_netlist():
    d=alu.build(); assert not d.check(), d.check()
    return d.spice(vdd='+5V')

OUTS=['R0','R1','R2','R3','CF','ZF','BUS0#','BUS1#','BUS2#','BUS3#']

def run(netlist_lines, cases, corner, outdir, tag, seed=1, rescore=False):
    os.makedirs(outdir,exist_ok=True)
    probes=INPUTS+OUTS
    dat=os.path.join(outdir,f'{tag}.dat'); cir=os.path.join(outdir,f'{tag}.cir')
    if not (rescore and os.path.exists(dat)):
        open(cir,'w').write(deck(netlist_lines,cases,corner,dat,probes,kicad=tag.startswith('kicad'),seed=seed))
        if os.path.exists(dat): os.remove(dat)
        r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
        if not os.path.exists(dat) or 'aborted' in r.stdout+r.stderr: print(r.stdout[-3000:],r.stderr[-3000:]); raise SystemExit('ngspice failed')
    names,a=spicedat.read(dat); t=a[:,0]; col={n.lower():a[:,k] for k,n in enumerate(names)}
    ts_all=np.array([(k+1)*T-5e-6 for k in range(len(cases))]); idx=np.searchsorted(t,ts_all)-1     # one sample per case, just before its end
    cache={}
    def v(n,tt):
        n=n.lower()
        if n not in cache: cache[n]=col[f'v({n})'][idx]
        return cache[n][int(round((tt+5e-6)/T))-1]
    fails=[]; worst={'high':5.0,'low':0.0,'settle':0.0}
    for n in OUTS:
        y=col[f'v({n.lower()})']>2.5
        cross=t[1:][y[1:]!=y[:-1]]
        for tc in cross:
            k=int(tc//T); worst['settle']=max(worst['settle'],tc-k*T)
    for k,(A,B,ctl,eo) in enumerate(cases):
        ts=(k+1)*T-5e-6
        S,cf,zf=expected(A,B,ctl)
        got_s=sum((v(f'R{i}',ts)>2.5)<<i for i in range(4)); got_cf=v('CF',ts)>2.5; got_zf=v('ZF',ts)>2.5
        bus=[v(f'BUS{i}#',ts) for i in range(4)]
        want_bus=[ (0 if (eo and (S>>i)&1) else 5) for i in range(4)]
        ok=(got_s==S and got_cf==cf and got_zf==zf and all(abs(bus[i]-want_bus[i])<1.0 for i in range(4)))
        for n in [f'R{i}' for i in range(4)]+['CF','ZF']:
            x=v(n,ts)
            if x>2.5: worst['high']=min(worst['high'],x)
            else: worst['low']=max(worst['low'],x)
        if not ok: fails.append(dict(case=k,A=A,B=B,ctl=list(ctl),EO=eo,want=(S,cf,zf,want_bus),got=(got_s,int(got_cf),int(got_zf),[round(x,2) for x in bus])))
    res=dict(tag=tag,corner=corner,seed=seed,cases=len(cases),fails=fails,worst=worst)
    json.dump(res,open(os.path.join(outdir,f'{tag}.json'),'w'),indent=1)
    print(f"{tag}: {len(cases)-len(fails)}/{len(cases)} pass, corner {corner}{' seed '+str(seed) if corner=='MIX' else ''}, worst high {worst['high']:.2f} V, worst low {worst['low']:.3f} V, worst settle {worst['settle']*1e6:.0f} us")
    for f_ in fails[:10]: print('  FAIL',f_)
    return res

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2]
    corner='TYP'; which='demo'
    if '--corner' in sys.argv: corner=sys.argv[sys.argv.index('--corner')+1]
    if '--cases' in sys.argv: which=sys.argv[sys.argv.index('--cases')+1]
    seed=int(sys.argv[sys.argv.index('--seed')+1]) if '--seed' in sys.argv else 1
    lines=dev_netlist() if src=='dev' else [l.rstrip() for l in open(src) if l.strip() and not l.startswith('*')]
    cases=exhaustive_cases() if which=='exhaustive' else demo_cases()
    run(lines,cases,corner,outdir,f"{'dev' if src=='dev' else 'kicad'}_{which}_{corner}{seed if corner=='MIX' else ''}",seed,'--rescore' in sys.argv)
