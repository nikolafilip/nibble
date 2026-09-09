"""Shared testbench: key/op stimulus, expected results, ngspice run, pass/fail, plot data."""
import subprocess, numpy as np, os
T=100e-6            # clock period
EDGE=50e-6          # first rising edge offset inside a period
def clock_line(): return f"VCLK CLOCK GND PULSE(0 5 {EDGE-25e-6} 1u 1u 49u {T})"   # rises at 50us+k*100us

OPS={'ADD':(0,0),'SUB':(0,1),'MUL':(1,0),'DIV':(1,1)}
def expected(op,a,b):
    if op=='ADD': return dict(sign=0,mag=a+b)
    if op=='SUB': return dict(sign=int(a<b),mag=abs(a-b))
    if op=='MUL': return dict(sign=0,mag=a*b)
    if op=='DIV':
        if b==0: return dict(sign=0,mag=None,div0=1)
        return dict(sign=0,mag=(a//b)|((a%b)<<3),q=a//b,r=a%b)

def sequence():
    return [('ADD',3,4),('ADD',7,7),('SUB',7,5),('SUB',2,5),('ADD',0,6),
            ('MUL',3,5),('MUL',7,7),('MUL',6,0),('MUL',1,7),
            ('DIV',7,2),('DIV',6,3),('DIV',5,7),('DIV',7,1),('DIV',4,0),
            ('SUB',6,6),('MUL',5,5)]

def build_stimulus(seq):
    """returns (source lines, checks[(t, op,a,b,expected)], t_end, windows)"""
    t=0.4e-3    # settle
    keysY={k:[] for k in range(1,8)}; keysX={k:[] for k in range(1,8)}
    op0=[];op1=[];start=[]
    checks=[]; windows=[]
    def step(lst,t0,v):
        lst.append((t0,v))
    for op,a,b in seq:
        t0=t+10e-6
        dur=0.3e-3 if op in('ADD','SUB') else 0.7e-3
        for k in range(1,8):
            step(keysY[k],t0,5 if a==k else 0); step(keysX[k],t0,5 if b==k else 0)
        o1,o0=OPS[op]; step(op0,t0,5*o0); step(op1,t0,5*o1)
        if op in('MUL','DIV'):
            step(start,t0,5); step(start,t0+T,0)
        else: step(start,t0,0)
        checks.append((t+dur-20e-6,op,a,b,expected(op,a,b)))
        windows.append((t,t+dur,op,a,b))
        t+=dur
    def pwl(name,net,pts):
        s=f"0 0"; last=0
        for (tt,v) in pts:
            s+=f" {tt-1e-6:.7g} {last} {tt+1e-6:.7g} {v}"; last=v
        return f"{name} {net} GND PWL({s})"
    lines=[clock_line()]
    for k in range(1,8): lines.append(pwl(f"VY{k}",f"Y{k}",keysY[k])); lines.append(pwl(f"VX{k}",f"X{k}",keysX[k]))
    lines.append(pwl("VOP0","OP0",op0)); lines.append(pwl("VOP1","OP1",op1)); lines.append(pwl("VSTART","START",start))
    return lines,checks,t+0.1e-3,windows

PROBE="OUT_SIGN OUT_B5 OUT_B4 OUT_B3 OUT_B2 OUT_B1 OUT_B0 DIV0 CLOCK MEMCLK START OP0 OP1 L T1 T2 T3 DN P5 P4 P3 P2 P1 P0 A0 A1 A2 EB0 EB1 EB2 S3 S2 S1 S0 SIG SUB".split()
IC="L T1 T2 T3 DN P0 P1 P2 P3 P4 P5 OUT_B4 OUT_B5 OUT_SIGN OUT_B3 OUT_B2 OUT_B1 OUT_B0".split()

def run(root_lines, tag, workdir, extra_probe=(), step='0.5u'):
    src,checks,tend,windows=build_stimulus(sequence())
    probes=list(PROBE)+list(extra_probe)
    cir=[".title muldiv e2e", '.include "../../lib/2N3904.lib"']+root_lines+src
    cir.append(f".tran {step} {tend:.6g}")
    cir.append(".ic "+" ".join(f"v({n})=0" for n in IC))
    cir.append(".option method=gear")
    cir+=[".control","set filetype=ascii","run",f"wrdata {tag}.txt "+" ".join(f"v({n})" for n in probes),"quit",".endc",".end"]
    path=os.path.join(workdir,f"{tag}.cir"); open(path,'w').write("\n".join(cir)+"\n")
    r=subprocess.run(["ngspice","-b",path],capture_output=True,text=True,cwd=workdir)
    open(os.path.join(workdir,f"{tag}.log"),'w').write(r.stdout+r.stderr)
    d=np.loadtxt(os.path.join(workdir,f"{tag}.txt"))
    t=d[:,0]; sig={n:d[:,2*k+1] for k,n in enumerate(probes)}
    return t,sig,checks,windows

def bit(v): return 1 if v>1.1 else 0
def evaluate(t,sig,checks):
    rows=[]; ok=True
    for (tc,op,a,b,exp) in checks:
        i=np.searchsorted(t,tc)
        mag=sum(bit(sig[f"OUT_B{k}"][i])<<k for k in range(6)); sign=bit(sig["OUT_SIGN"][i]); div0=bit(sig["DIV0"][i])
        if exp.get('div0'):
            passed=(div0==1)
            got=f"DIV0 flag={div0}"; want="DIV0 flag=1"
        else:
            passed=(mag==exp['mag'] and sign==exp['sign'] and div0==0)
            if op=='DIV': got=f"q={mag&7} r={mag>>3} sign={sign}"; want=f"q={exp['q']} r={exp['r']} sign=0"
            else: got=f"{'-' if sign else ''}{mag}"; want=f"{'-' if exp['sign'] else ''}{exp['mag']}"
        ok&=passed
        rows.append((op,a,b,want,got,passed,tc))
    return ok,rows

def levels(t,sig,names,t0):
    """logic-level health: worst high and worst low seen after t0 (sampled just before each rising clock edge)"""
    edges=np.arange(EDGE,t[-1],T); res={}
    for n in names:
        v=sig[n]; hi=[];lo=[]
        for e in edges:
            if e<t0: continue
            i=np.searchsorted(t,e-3e-6); x=v[i]
            (hi if x>1.25 else lo).append(x)
        res[n]=(min(hi) if hi else None, max(lo) if lo else None)
    return res
