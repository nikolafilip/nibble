"""Testbench for board 05 (clock). RUN switch closed and the pot at minimum (about 860 Hz), then HLT for 30 ms,
then STEP mode with the panel button pressed once. Measures the period and duty at each corner, that CLK stops
within one cycle of HLT, that the power-on reset pulse lasts long enough, and that STEP releases the line.
Usage: python3 tb_clock.py <netlist.cir|dev> <outdir> [--corner TYP|LO|HI|MIX] [--seed N]
"""
import sys, os, subprocess, random, json, numpy as np
import spicedat, nmos, clock

T_HLT=60e-3; T_STEP=90e-3; T_BTN=100e-3; TEND=400e-3

def deck(lines,corner,outfile,kicad,seed):
    models={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}; rng=random.Random(seed); body=[]
    for l in lines:
        if l.lower().startswith(('.end','.tran','.include','.lib','.title','.ic','.option','.control')): continue
        if l[0] in 'Mm': l=l.replace(' 2N7000',' '+(models[rng.choice(['LO','TYP','HI'])] if corner=='MIX' else models[corner]))
        body.append(l)
    lib=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib','2N7000.lib'); led=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib','led.lib')
    L=["* clock testbench",f'.include "{lib}"',f'.include "{led}"',nmos.SW_MODEL,"VDD +5V 0 5"]
    L.append("Rpot RT X 1m")                                                     # the speed pot at minimum
    L.append("Rj2 Net-_J2-Pin_2_ 0 1G")                                         # the open SLOW jumper's cap: not floating for the DC solution
    L.append(".ic V(POR)=0 V(X)=0")                                             # power-up: the reset and timing capacitors are empty (the DC solution would sit exactly on the trip point)
    L.append(f"Brun runsw 0 V = time<{T_STEP} ? 5 : 0"); L.append("Srun +5V RUNSW runsw 0 ODRV")    # RUN switch closed until T_STEP
    L.append(f"Vhlt HLT 0 PWL(0 0 {T_HLT} 0 {T_HLT+2e-6} 5 {T_STEP} 5 {T_STEP+2e-6} 0)")
    L.append("Rpd CLK 0 1Meg"); L.append("Cline CLK 0 100p"); L.append("Rrpd RST 0 1Meg")      # the panel's pull-downs and the ribbon
    L.append(f"Vbtn btn 0 PWL(0 0 {T_BTN} 0 {T_BTN+1e-3} 5 {T_BTN+5e-3} 5 {T_BTN+6e-3} 0)"); L.append("Rbtn btn btna 10k"); L.append("Dbtn btna CLK D1N4148")   # the panel button in STEP mode
    L+=body
    L+=[f".tran 2u {TEND:.6g}",".option method=gear cshunt=1e-12 abstol=1e-10 chgtol=1e-12",".control","run","set wr_singlescale","set wr_vecnames",
        f"wrdata {outfile} v(CLK) v(RST) v(HLT) v(X) v(VD2) v(VS) v(POR) v(RUNSW)","quit",".endc",".end"]
    return "\n".join(L)+"\n"

def run(lines,corner,outdir,tag,seed=1):
    os.makedirs(outdir,exist_ok=True); dat=os.path.join(outdir,f'{tag}.dat'); cir=os.path.join(outdir,f'{tag}.cir')
    open(cir,'w').write(deck(lines,corner,dat,tag.startswith('kicad'),seed))
    if os.path.exists(dat): os.remove(dat)
    r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
    if not os.path.exists(dat) or 'aborted' in r.stdout+r.stderr: print(r.stdout[-3000:],r.stderr[-3000:]); raise SystemExit('ngspice failed')
    names,a=spicedat.read(dat); t=a[:,0]; col={n.lower():a[:,k] for k,n in enumerate(names)}
    clk=col['v(clk)']; hi=clk>3.5; lo=clk<1.5; st=0; rises=[]; falls=[]
    for k in range(len(t)):
        if st==0 and hi[k]: st=1; rises.append(t[k])
        elif st==1 and lo[k]: st=0; falls.append(t[k])
    run_r=[x for x in rises if 5e-3<x<T_HLT]; run_f=[x for x in falls if 5e-3<x<T_HLT]
    period=np.mean(np.diff(run_r)) if len(run_r)>2 else float('nan')
    highs=[min([f for f in run_f if f>r],default=r)-r for r in run_r[:-1]]
    duty=np.mean(highs)/period if len(run_r)>2 else float('nan')
    last_before_hlt=max([x for x in rises if x<T_HLT],default=0); after_hlt=[x for x in rises if T_HLT<x<T_STEP]
    rst=col['v(rst)']>2.5; rst_end=t[np.argmax(~rst)] if rst[0] else 0.0
    step_rises=[x for x in rises if x>T_STEP]
    clk_low_in_step=float(np.max(clk[(t>T_STEP+1e-3)&(t<T_BTN)]))
    res=dict(tag=tag,corner=corner,seed=seed,period_ms=period*1e3,freq_hz=1/period,duty=duty,rises_in_run=len(run_r),
             rises_after_hlt=len(after_hlt),rst_pulse_ms=rst_end*1e3,step_rises=len(step_rises),clk_max_in_step_idle=clk_low_in_step)
    ok=(len(run_r)>=8 and len(after_hlt)==0 and 20e-3<rst_end<TEND and len(step_rises)==1 and clk_low_in_step<0.5 and 0.1<duty<0.9)
    res['ok']=bool(ok)
    json.dump(res,open(os.path.join(outdir,f'{tag}.json'),'w'),indent=1)
    print(f"{tag}: {'PASS' if ok else 'FAIL'} period {period*1e3:.2f} ms ({1/period:.0f} Hz) duty {duty:.2f}, {len(run_r)} edges in RUN, {len(after_hlt)} after HLT, RST pulse {rst_end*1e3:.0f} ms, STEP: {len(step_rises)} edge from the button, idle CLK max {clk_low_in_step:.2f} V")
    return res

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2]
    corner=sys.argv[sys.argv.index('--corner')+1] if '--corner' in sys.argv else 'TYP'
    seed=int(sys.argv[sys.argv.index('--seed')+1]) if '--seed' in sys.argv else 1
    if src=='dev': raise SystemExit('the clock needs its RC parts: use the kicad export')
    lines=[l.rstrip() for l in open(src) if l.strip() and not l.startswith('*')]
    run(lines,corner,outdir,f"kicad_{corner}{seed if corner=='MIX' else ''}",seed)
