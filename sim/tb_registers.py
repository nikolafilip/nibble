"""Testbench for board 02 (registers). A clocked script of operations covers every reachable path:
every value through A and B from the bus, A and B driven back onto the bus, MOV (BA), XCH (AB+BA), OUT (OI), holds.
Usage: python3 tb_registers.py <netlist.cir|dev> <outdir> [--corner TYP|LO|HI|MIX] [--seed N]
"""
import sys, os, subprocess, random, json, numpy as np
import spicedat
import nmos, registers

T=1e-3; T0=2e-3; DELAY=20e-6
CTL=['AI','AO','BI','BO','BA','AB','OI']
HUB_PU='10k'

def script():
    """(controls, bus value driven by the bench or None). The bench drives the bus like the sequencer's operand register."""
    s=[]
    for v in range(16): s.append(({'AI'},v)); s.append(({'AO'},None))          # A <- v, then A drives the bus
    for v in range(16): s.append(({'BI'},v)); s.append(({'BO'},None))          # B <- v, then B drives the bus
    for v in (5,10,15,0): s.append(({'AI'},v)); s.append(({'BA'},None)); s.append(({'BO'},None))     # MOV B,A
    for a,b in ((3,12),(15,0),(6,9)):
        s.append(({'AI'},a)); s.append(({'BI'},b)); s.append(({'AB','BA'},None)); s.append(({'AO'},None)); s.append(({'BO'},None))   # XCH
    for v in range(16): s.append(({'OI'},v))
    s.append((set(),7)); s.append((set(),0)); s.append((set(),15))              # holds: bus changes, nothing loads
    s.append(({'AI'},9)); s.append(({'AB'},None)); s.append(({'AO'},None))     # A <- B
    return s

def expected(s):
    a=b=out=None; rows=[]
    for ctl,v in s:
        bus=0 if v is None else v
        if 'AO' in ctl and a is not None: bus|=a
        if 'BO' in ctl and b is not None: bus|=b
        rows.append(dict(a=a,b=b,out=out,bus=bus))
        na,nb,no=a,b,out
        if 'AI' in ctl: na=v
        elif 'AB' in ctl: na=b
        if 'BI' in ctl: nb=v
        elif 'BA' in ctl: nb=a
        if 'OI' in ctl: no=v
        a,b,out=na,nb,no
    return rows

def pwl(times,values):
    pts=[(0,values[0])]
    for t,v in zip(times,values): pts.append((t-1e-6,pts[-1][1])); pts.append((t+1e-6,v))
    return "PWL("+" ".join(f"{t:.7g} {5*v}" for t,v in pts)+")"

def deck(lines,s,corner,outfile,probes,kicad,seed):
    models={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}; rng=random.Random(seed)
    body=[]
    for l in lines:
        if l.lower().startswith(('.end','.tran','.include','.lib','.title','.ic','.option','.control')): continue
        if kicad and l[0] not in '.*+' and int(''.join(c for c in l.split()[0] if c.isdigit()) or 0)>=9000: continue   # testbench sheet parts: replaced by the sources below
        if l[0] in 'Mm': l=l.replace(' 2N7000',' '+(models[rng.choice(['LO','TYP','HI'])] if corner=='MIX' else models[corner]))
        body.append(l)
    edges=[T0+k*T for k in range(len(s))]; starts=[e-T+DELAY for e in edges]
    lib=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib','2N7000.lib')
    L=["* registers testbench",f'.include "{lib}"',nmos.LED_MODEL,nmos.SW_MODEL,"VDD +5V 0 5"]+[f"RHUB{i} +5V BUS{i}# {HUB_PU}" for i in range(4)]
    L.append(f"Vclk CLK 0 PULSE(0 5 {T0:.6g} 1u 1u {T/2-1e-6:.6g} {T:.6g})")
    for c in CTL: L.append(f"V{c} {c} 0 "+pwl(starts,[int(c in ctl) for ctl,v in s]))
    for i in range(4):
        L.append(f"Vd{i} d{i} 0 "+pwl(starts,[((v or 0)>>i)&1 for ctl,v in s]))
        L.append(f"Sd{i} BUS{i}# 0 d{i} 0 ODRV")      # ideal open-drain driver: a switch to ground
    L+=body
    tend=edges[-1]+T/2
    L+=[f".tran 1u {tend:.6g}",".option method=gear cshunt=1e-12 abstol=1e-10 chgtol=1e-12",".control","run","set wr_singlescale","set wr_vecnames",
        f"wrdata {outfile} "+" ".join(f"v({p})" for p in probes),"quit",".endc",".end"]
    return "\n".join(L)+"\n", edges

def run(lines,corner,outdir,tag,seed=1,rescore=False):
    tb_T,tb_T0=T,T0
    os.makedirs(outdir,exist_ok=True); s=script(); exp=expected(s)
    probes=[f'A{i}' for i in range(4)]+[f'B{i}' for i in range(4)]+[f'OUT{i}' for i in range(4)]+[f'BUS{i}#' for i in range(4)]+['CLK','PH1','PH2']
    dat=os.path.join(outdir,f'{tag}.dat'); cir=os.path.join(outdir,f'{tag}.cir')
    text,edges=deck(lines,s,corner,dat,probes,tag.startswith('kicad'),seed); open(cir,'w').write(text)
    if not (rescore and os.path.exists(dat)):
        if os.path.exists(dat): os.remove(dat)
        r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
        if not os.path.exists(dat) or 'aborted' in r.stdout+r.stderr: print(r.stdout[-3000:],r.stderr[-3000:]); raise SystemExit('ngspice failed')
    names,a=spicedat.read(dat); t=a[:,0]; col={n.lower():a[:,k] for k,n in enumerate(names)}
    ts_all=np.array([e-5e-6 for e in edges]); idx=np.searchsorted(t,ts_all)-1
    cache={}
    def v(n,tt):
        n=n.lower()
        if n not in cache: cache[n]=col[f'v({n})'][idx]
        return cache[n][int(round((tt+5e-6-tb_T0)/tb_T))]
    num=lambda pre,tt,suf='': sum((v(f'{pre}{i}{suf}',tt)>2.5)<<i for i in range(4))
    fails=[]; worst={'high':5.0,'low':0.0}
    for k,(e,(ctl,val),w) in enumerate(zip(edges,s,exp)):
        ts=e-5e-6
        got=dict(a=num('A',ts),b=num('B',ts),out=num('OUT',ts),bus=15-num('BUS',ts,'#'))   # BUSi# low = bit set
        for reg,pre in (('a','A'),('b','B'),('out','OUT')):
            if w[reg] is None: continue      # not written yet: the power-on state is not a logic level
            for i in range(4):
                x=v(f'{pre}{i}',ts); worst['high' if x>2.5 else 'low']=min(worst['high'],x) if x>2.5 else max(worst['low'],x)
        bad={f:(w[f],got[f]) for f in w if w[f] is not None and w[f]!=got[f]}
        if bad: fails.append(dict(case=k,ctl=sorted(ctl),val=val,bad=bad))
    res=dict(tag=tag,corner=corner,seed=seed,cases=len(s),fails=fails,worst=worst)
    json.dump(res,open(os.path.join(outdir,f'{tag}.json'),'w'),indent=1)
    print(f"{tag}: {len(s)-len(fails)}/{len(s)} pass, corner {corner}{' seed '+str(seed) if corner=='MIX' else ''}, worst high {worst['high']:.2f} V, worst low {worst['low']:.3f} V")
    for f_ in fails[:10]: print('  FAIL',f_)
    return res

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2]
    corner=sys.argv[sys.argv.index('--corner')+1] if '--corner' in sys.argv else 'TYP'
    seed=int(sys.argv[sys.argv.index('--seed')+1]) if '--seed' in sys.argv else 1
    if src=='dev':
        d=registers.build(); assert not d.check(), d.check(); lines=d.spice(vdd='+5V')
    else: lines=[l.rstrip() for l in open(src) if l.strip() and not l.startswith('*')]
    run(lines,corner,outdir,f"{'dev' if src=='dev' else 'kicad'}_{corner}{seed if corner=='MIX' else ''}",seed,rescore='--rescore' in sys.argv)
