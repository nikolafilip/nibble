"""Testbench for board 01 (ALU). Builds stimuli, runs ngspice on a netlist, checks every case.
Usage: python3 tb_alu.py <netlist.cir|dev> <outdir> [--corner TYP|LO|HI] [--cases exhaustive|demo]
The netlist is either the dev netlist (built from alu.py) or a kicad-cli export of boards/01-alu.
"""
import sys, os, subprocess, itertools, json, numpy as np
import nmos, alu

T=400e-6          # per case
TR=1e-6
HUB_PU='10k'
INPUTS=['A0','A1','A2','A3','B0','B1','B2','B3','SUB','EO']

def demo_cases():
    c=[]
    for a,b,s in [(3,4,0),(7,5,1),(6,6,1),(2,5,1),(9,7,0),(15,1,0),(0,0,1),(8,8,0),(5,3,1),(12,4,1),(1,15,0),(7,1,1)]:
        c.append((a,b,s,1))
    c.append((5,3,0,0))   # EO low: bus must float high
    return c
def exhaustive_cases():
    return [(a,b,s,1) for s in (0,1) for a in range(16) for b in range(16)]

def expected(a,b,s):
    if s: r=(a+(~b&15)+1)
    else: r=a+b
    cf=(r>>4)&1; S=r&15
    return S,cf,int(S==0)

def pwl(bits):
    """bits: list of 0/1 per case -> PWL string"""
    pts=[(0,bits[0]*5)]; t=0
    for k in range(1,len(bits)):
        t=k*T; pts.append((t-TR/2,bits[k-1]*5)); pts.append((t+TR/2,bits[k]*5))
    pts.append((len(bits)*T,bits[-1]*5))
    return 'PWL('+' '.join(f'{x:.7g} {y:g}' for x,y in pts)+')'

def sources(cases):
    L=[]
    for j,name in enumerate(INPUTS):
        bits=[]
        for a,b,s,eo in cases:
            v={'A':(a>>j)&1 if j<4 else 0}
            if name.startswith('A'): bit=(a>>int(name[1]))&1
            elif name.startswith('B'): bit=(b>>int(name[1]))&1
            elif name=='SUB': bit=s
            else: bit=eo
            bits.append(bit)
        L.append(f"V{name} {name} 0 {pwl(bits)}")
    return L

def deck(netlist_lines, cases, corner, outfile, probes, kicad=False):
    model={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}[corner]
    body=[l for l in netlist_lines if not l.lower().startswith(('.end','.tran','.include','.lib','.title','.ic'))]
    if kicad:   # drop the sheet's demo stimulus (replaced below); keep its supply and hub pull-ups
        body=[l for l in body if not (l[0] in 'Vv' and l.split()[1] in INPUTS)]
        supply=[]
    else:
        supply=["VDD VDD 0 5"]+[f"RHUB{i} VDD BUS{i}# {HUB_PU}" for i in range(4)]
    if corner!='TYP': body=[l.replace(' 2N7000',' '+model) if l[0] in 'Mm' else l for l in body]
    tend=len(cases)*T
    return "\n".join(["* ALU testbench", '.include "../../lib/2N7000.lib"', nmos.LED_MODEL]+supply+sources(cases)+body+
        [f".tran 2u {tend:.6g}", ".option method=gear", ".control","run","set wr_singlescale","set wr_vecnames",
         f"wrdata {outfile} "+" ".join(f"v({p.lower()})" for p in probes),"quit",".endc",".end"])

def dev_netlist():
    d=alu.build(); assert not d.check(), d.check()
    return d.spice()

def run(netlist_lines, cases, corner, outdir, tag):
    os.makedirs(outdir,exist_ok=True)
    probes=INPUTS+['S0','S1','S2','S3','CF','ZF','BUS0#','BUS1#','BUS2#','BUS3#']
    dat=os.path.join(outdir,f'{tag}.dat'); cir=os.path.join(outdir,f'{tag}.cir')
    open(cir,'w').write(deck(netlist_lines,cases,corner,dat,probes,kicad=tag.startswith('kicad')))
    r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
    if not os.path.exists(dat): print(r.stdout[-3000:],r.stderr[-3000:]); raise SystemExit('ngspice failed')
    with open(dat) as f: names=f.readline().split()
    a=np.loadtxt(dat,skiprows=1); t=a[:,0]; col={n:a[:,k] for k,n in enumerate(names)}
    v=lambda n,tt: np.interp(tt,t,col[f'v({n.lower()})'])
    fails=[]; worst={'high':5.0,'low':0.0,'settle':0.0}
    outs=['S0','S1','S2','S3','CF','ZF','BUS0#','BUS1#','BUS2#','BUS3#']
    for n in outs:
        y=col[f'v({n.lower()})']>2.5
        cross=t[1:][y[1:]!=y[:-1]]
        for tc in cross:
            k=int(tc//T); worst['settle']=max(worst['settle'],tc-k*T)
    for k,(A,B,s,eo) in enumerate(cases):
        ts=(k+1)*T-5e-6
        S,cf,zf=expected(A,B,s)
        got_s=sum((v(f'S{i}',ts)>2.5)<<i for i in range(4)); got_cf=v('CF',ts)>2.5; got_zf=v('ZF',ts)>2.5
        bus=[v(f'BUS{i}#',ts) for i in range(4)]
        want_bus=[ (0 if (eo and (S>>i)&1) else 5) for i in range(4)]
        ok=(got_s==S and got_cf==cf and got_zf==zf and all(abs(bus[i]-want_bus[i])<1.0 for i in range(4)))
        for n in [f'S{i}' for i in range(4)]+['CF','ZF']:
            x=v(n,ts); 
            if x>2.5: worst['high']=min(worst['high'],x)
            else: worst['low']=max(worst['low'],x)
        if not ok: fails.append(dict(case=k,A=A,B=B,SUB=s,EO=eo,want=(S,cf,zf,want_bus),got=(got_s,int(got_cf),int(got_zf),[round(x,2) for x in bus])))
    res=dict(tag=tag,corner=corner,cases=len(cases),fails=fails,worst=worst)
    json.dump(res,open(os.path.join(outdir,f'{tag}.json'),'w'),indent=1)
    print(f"{tag}: {len(cases)-len(fails)}/{len(cases)} pass, corner {corner}, worst high {worst['high']:.2f} V, worst low {worst['low']:.3f} V, worst settle {worst['settle']*1e6:.0f} us")
    for f_ in fails[:10]: print('  FAIL',f_)
    return res

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2]
    corner='TYP'; which='demo'
    if '--corner' in sys.argv: corner=sys.argv[sys.argv.index('--corner')+1]
    if '--cases' in sys.argv: which=sys.argv[sys.argv.index('--cases')+1]
    lines=dev_netlist() if src=='dev' else [l.rstrip() for l in open(src) if l.strip() and not l.startswith('*')]
    cases=exhaustive_cases() if which=='exhaustive' else demo_cases()
    run(lines,cases,corner,outdir,f"{'dev' if src=='dev' else 'kicad'}_{which}_{corner}")
