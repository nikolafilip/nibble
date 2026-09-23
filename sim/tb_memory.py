"""Testbench for board 08 (data memory). A clocked script writes every slot and reads it back, three fills
(slot number, its complement, a scrambled pattern) plus interleaved single writes between reads, so every cell holds
both values, every address decodes, and a write never disturbs another slot.
Usage: python3 tb_memory.py <netlist.cir|dev|cards|cards@dev> <outdir> [--corner TYP|LO|HI|MIX] [--seed N] [--rescore] [--race]
  cards: the kicad-cli exports of cards/memctl and cards/memslot, the slot card eight times with its pair jumpers set (cards@dev: from the gate lists)
  --race: the machine's edge as the memory card sees it (D054): CLK rises over 35 us (the first clock card's edge into the machine's
  3 nF), the bus switches 10 us after the rise starts (the sequencer, at a low threshold, has stepped and a register drives the next
  tick's data) and the control lines only 100 us after it (they lag every edge by 60 to 170 us in the machine: MAI and MI are still
  high when the data changes). The memory gated by PH1 takes the next tick's data into its address latch and its cells at TYP, HI and mixed
  seeds 1 and 2 (121 to 170 of 217 pass; only LO passes); the mid-tick pulse passes at every corner.
The machine's timing: the address rides the bus during a MAI tick (the address latch is open while MPH, the mid-tick pulse, is high),
the data rides the bus during an MI tick, the board drives the bus during an MO tick.
"""
import sys, os, subprocess, random, json, numpy as np
import spicedat
import nmos, memory

T=1e-3; T0=2e-3; DELAY=20e-6; DELAY_CTL=20e-6; RISE=1e-6      # DELAY: the bus switches this long after a rising edge starts; DELAY_CTL: the control lines
CTL=['MAI','MI','MO']
HUB_PU='10k'

def script():
    """(controls, bus value driven by the bench or None)."""
    s=[]
    fills=[list(range(16)),[15-n for n in range(16)],[(n*7+3)%16 for n in range(16)]]
    for fill in fills:
        for n in range(16): s.append(({'MAI'},n)); s.append(({'MI'},fill[n]))
        for n in range(16): s.append(({'MAI'},n)); s.append(({'MO'},None))
    for n,v,m in ((5,9,10),(0,15,15),(15,0,0),(10,6,5)):        # write slot n, then read n and an untouched slot m
        s.append(({'MAI'},n)); s.append(({'MI'},v)); s.append(({'MO'},None)); s.append(({'MAI'},m)); s.append(({'MO'},None))
    s.append((set(),7)); s.append((set(),0)); s.append(({'MAI'},3)); s.append((set(),15)); s.append(({'MO'},None))   # bus noise while nothing loads
    return s

def expected(s):
    mem=[None]*16; mar=None; rows=[]
    for ctl,v in s:
        bus=0 if v is None else v
        if 'MO' in ctl and mar is not None: bus=mem[mar]
        if 'MAI' in ctl: mar=v          # the address latch is transparent during the MAI tick, so it already holds v at the tick's end
        rows.append(dict(mar=mar,bus=bus if not ('MO' in ctl and mar is not None and mem[mar] is None) else None))
        if 'MI' in ctl and mar is not None: mem[mar]=v
    return rows

def pwl(times,values):
    pts=[(0,values[0])]
    for t,v in zip(times,values): pts.append((t-1e-6,pts[-1][1])); pts.append((t+1e-6,v))
    return "PWL("+" ".join(f"{t:.7g} {5*v}" for t,v in pts)+")"

def deck(lines,s,corner,outfile,probes,kicad,seed):
    models={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}; rng=random.Random(seed)
    body=[]
    for l in lines:
        if l.lower().startswith(('.end','.tran','.include','.lib','.title','.ic','.option','.control')) and not l.lower().startswith('.ends'): continue
        if kicad and l[0] not in '.*+' and int(''.join(c for c in l.split()[0] if c.isdigit()) or 0)>=9000: continue
        if l[0] in 'Mm': l=l.replace(' 2N7000',' '+(models[rng.choice(['LO','TYP','HI'])] if corner=='MIX' else models[corner]))
        body.append(l)
    edges=[T0+k*T for k in range(len(s))]; starts=[e-T+DELAY for e in edges]; cstarts=[e-T+DELAY_CTL for e in edges]
    lib=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','lib','2N7000.lib')
    L=["* data memory testbench",f'.include "{lib}"',nmos.LED_MODEL,nmos.SW_MODEL,".global +5V","VDD +5V 0 5"]+[f"RHUB{i} +5V BUS{i}# {HUB_PU}" for i in range(4)]
    L.append(f"Vclk CLK 0 PULSE(0 5 {T0-T:.6g} {RISE:.6g} 1u {T/2-1e-6:.6g} {T:.6g})")      # the clock runs a cycle before the first case: every tick, the first included, has its falling edge (the mid-tick pulse, D054)
    if not any(' CLKD ' in ' '+l+' ' for l in body if l[0] in 'RrCc'): L+=["Rclkd CLK CLKD 100k","Cclkd CLKD 0 2.2n"]      # the pulse's RC is on the card's sheet; the gate list has it as an input
    for c in CTL: L.append(f"V{c} {c} 0 "+pwl(cstarts,[int(c in ctl) for ctl,v in s]))
    for i in range(4):
        L.append(f"Vd{i} d{i} 0 "+pwl(starts,[((v or 0)>>i)&1 for ctl,v in s]))
        L.append(f"Sd{i} BUS{i}# 0 d{i} 0 ODRV")
    L+=body
    tend=edges[-1]+T/2
    L.append(".save "+" ".join(f"v({p})" for p in probes))      # only the probed vectors stay in memory
    L+=[f".tran 1u {tend:.6g}",".option method=gear cshunt=1e-12 abstol=1e-10 chgtol=1e-12",".control","run","set wr_singlescale","set wr_vecnames",
        f"wrdata {outfile} "+" ".join(f"v({p})" for p in probes),"quit",".endc",".end"]
    return "\n".join(L)+"\n", edges

def run(lines,corner,outdir,tag,seed=1,rescore=False,cards=False):
    os.makedirs(outdir,exist_ok=True); s=script(); exp=expected(s)
    pre='xmemctl.' if cards else ''
    probes=[f'MAR{i}' for i in range(4)]+[f'BUS{i}#' for i in range(4)]+['CLK',f'{pre}MPH',f'{pre}CLKD']      # MAR is on the link ribbon, a port of the memctl card: a top-level node
    dat=os.path.join(outdir,f'{tag}.dat'); cir=os.path.join(outdir,f'{tag}.cir')
    text,edges=deck(lines,s,corner,dat,probes,tag.startswith('kicad'),seed); open(cir,'w').write(text)
    if not (rescore and os.path.exists(dat)):
        if os.path.exists(dat): os.remove(dat)
        r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
        if not os.path.exists(dat) or 'aborted' in r.stdout+r.stderr: print(r.stdout[-3000:],r.stderr[-3000:]); raise SystemExit('ngspice failed')
    names,a=spicedat.read(dat); t=a[:,0]; col={n.lower():a[:,k] for k,n in enumerate(names)}
    idx=np.searchsorted(t,np.array([e-5e-6 for e in edges]))-1
    val=lambda n,k: col[f'v({n.lower()})'][idx][k]
    num=lambda p,k,suf='': int(sum(int(val(f'{p}{i}{suf}',k)>2.5)<<i for i in range(4)))
    fails=[]; worst={'high':5.0,'low':0.0}
    for k,((ctl,v),w) in enumerate(zip(s,exp)):
        got=dict(mar=int(num("MAR",k)),bus=int(15-num("BUS",k,"#")))
        if 'MO' in ctl and w['bus'] is not None:
            for i in range(4):
                x=val(f'BUS{i}#',k); worst['high' if x>2.5 else 'low']=float(min(worst['high'],x) if x>2.5 else max(worst['low'],x))
        bad={f:(w[f],got[f]) for f in w if w[f] is not None and w[f]!=got[f]}
        if bad: fails.append(dict(case=k,ctl=sorted(ctl),val=v,bad=bad))
    res=dict(tag=tag,corner=corner,seed=seed,cases=len(s),fails=fails,worst=worst)
    json.dump(res,open(os.path.join(outdir,f'{tag}.json'),'w'),indent=1)
    print(f"{tag}: {len(s)-len(fails)}/{len(s)} pass, corner {corner}{' seed '+str(seed) if corner=='MIX' else ''}, bus during reads: worst high {worst['high']:.2f} V, worst low {worst['low']:.3f} V")
    for f_ in fails[:10]: print('  FAIL',f_)
    return res

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2]
    corner=sys.argv[sys.argv.index('--corner')+1] if '--corner' in sys.argv else 'TYP'
    seed=int(sys.argv[sys.argv.index('--seed')+1]) if '--seed' in sys.argv else 1
    if '--race' in sys.argv: RISE=35e-6; DELAY=10e-6; DELAY_CTL=100e-6
    cards=src.startswith('cards')
    if src=='dev':
        d=memory.build(); assert not d.check(), d.check(); lines=d.spice(vdd='+5V')
    elif cards:
        import machine; dev=src.endswith('@dev'); lines=[]
        ports,sub=machine.subckt('memctl',machine.export('memctl',dev),'TYP'); lines+=sub+["Xmemctl "+" ".join(ports)+" memctl"]
        for p in range(8):
            ports,sub=machine.subckt('memslot',machine.export('memslot',dev),'TYP')
            body=[f"Rj{k} {x} {m} 1m" for k,(x,m) in enumerate(memory.slot_jumpers(p).items())]
            ports=machine.ports_of(sub[1:-1]+body)      # the jumpers bring MAR1..3 (or their complements) onto the card: ports too, else they float inside
            lines+=[f".subckt memslot{p} "+" ".join(ports)]+sub[1:-1]+body+[sub[-1]]+[f"Xmemslot{p} "+" ".join(ports)+f" memslot{p}"]
    else: lines=[l.rstrip() for l in open(src) if l.strip() and not l.startswith('*')]
    tag={'dev':'dev','cards':'cards','cards@dev':'cardsdev'}.get(src,'kicad')+('_race' if '--race' in sys.argv else '')
    run(lines,corner,outdir,f"{tag}_{corner}{seed if corner=='MIX' else ''}",seed,rescore='--rescore' in sys.argv,cards=cards)
