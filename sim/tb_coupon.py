"""Testbench for the gate coupon (cards/coupon): what the bench should read at each test loop, from the routed card's own
netlist, at every transistor corner. The numbers it prints are the bands in sim/results/coupon_expected.md and the table
in docs/bring-up.md section 1: a measurement outside its band means the cell in copper is not the cell the whole machine
was simulated with, and the second order waits.

Stimulus (all inputs come from the card's own 6-pin header): RST high for the first millisecond and again from 26 to
27.5 ms; IN a 1 kHz square from 2 ms; N1, N2, N3 stepped on at 6, 7, 8 ms. 3.3 nF clipped on TP_DRV (the ribbon and
seventeen cards' gates), 15 pF on every other loop (a x10 scope probe). The supply is 5.00 V.

Usage: python3 tb_coupon.py <kicad|dev> <outdir> [--corner TYP|LO|HI|MIX] [--seed N] [--all]
  kicad: export cards/coupon/coupon.kicad_sch with kicad-cli (the card as routed); dev: the gate list plus the sheet-drawn parts
  --all: TYP, LO, HI and MIX seeds 1..3, then the table out/<outdir>/coupon_expected.md
"""
import sys, os, subprocess, random, json, numpy as np
import spicedat, nmos, coupon

HERE=os.path.dirname(os.path.abspath(__file__)); KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
SCH=os.path.join(HERE,'..','cards','coupon','coupon.kicad_sch')
TEND=30e-3; VDD=5.0; PROBE_PF=15; DRV_NF=3.3
LOOPS=['TP_RING','RING0','TP_FO1','TP_FO10','TP_NAND','TP_NOR','TP_BUS','TP_VTO','X','TP_OSC','TP_Q','TP_DRV','TP_ROM']

def export():
    cir=os.path.join(HERE,'out','coupon_kicad.cir'); os.makedirs(os.path.dirname(cir),exist_ok=True)
    r=subprocess.run([KICAD_CLI,'sch','export','netlist','--format','spice','-o',cir,SCH],capture_output=True,text=True)
    if not os.path.exists(cir): raise SystemExit(r.stdout+r.stderr)
    lines=[l.rstrip() for l in open(cir) if l.strip() and not l.startswith('*')]
    assert any(l[0] in 'MRCD' for l in lines), "empty export"
    return lines

def dev_lines():
    """The gate list's flat netlist plus everything build_coupon_card.py draws by hand (the same parts, so a difference
    between dev and kicad results is a sheet fault)."""
    d=coupon.build()
    for n in ['IN','N1','N2','N3','RST']: d.pulldown(n,'1Meg')
    L=d.spice(vdd='+5V')
    L+=["MQ1 VD1 X VS 2N7000","MQ2 VD2 VD1 VS 2N7000","RD1 +5V VD1 47k","RD2 +5V VD2 10k","RS VS 0 1k",      # the Schmitt pair
        "RT SA X 100k","CX X 0 47n",                                                                       # the RC at the fastest setting
        "RDRV DRVN DRVA 100","DDRV DRVA TP_DRV D1N4148","RDPD TP_DRV 0 10k",                                 # D053's driver
        "DROM ROW TP_ROM D1N4148","RROM TP_ROM 0 220k",                                                    # the program row
        "RBUS +5V TP_BUS 10k"]                                                                             # the hub's pull-up
    return L

def deck(lines,corner,seed,outfile):
    models={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}; rng=random.Random(seed); body=[]
    for l in lines:
        if l.lower().startswith(('.end','.tran','.include','.lib','.title','.ic','.option','.control')): continue
        ref=l.split()[0]; num=''.join(c for c in ref if c.isdigit())
        if num and int(num)>=9000: continue                          # the testbench sheet's sources
        if l[0] in 'Mm': l=l.replace(' 2N7000',' '+(models[rng.choice(['LO','TYP','HI'])] if corner=='MIX' else models[corner]))
        body.append(l)
    lib=os.path.join(HERE,'..','lib','2N7000.lib'); led=os.path.join(HERE,'..','lib','led.lib')
    L=["* coupon testbench",f'.include "{lib}"',f'.include "{led}"',f"VDD +5V 0 {VDD}"]
    L.append("Vrst RST 0 PWL(0 5 1m 5 1.001m 0 26m 0 26.001m 5 27.5m 5 27.501m 0)")
    L.append("Vin IN 0 PULSE(0 5 2m 1u 1u 0.5m 1m)")
    for k,n in enumerate(['N1','N2','N3']): L.append(f"V{n.lower()} {n} 0 PWL(0 0 {6+k}m 0 {6+k}.001m 5)")
    L.append(f"Cdrv TP_DRV 0 {DRV_NF}n")
    for n in LOOPS:
        if n!='TP_DRV': L.append(f"Cp_{n} {n} 0 {PROBE_PF}p")
    L.append(".ic V(RING0)=0 V(X)=0")                          # the ring must not start on its symmetric point; the timing capacitor empty
    L+=body
    L+=[f".tran 0.1u {TEND:.6g}",".option method=gear cshunt=1e-12 abstol=1e-10 chgtol=1e-12",".control","run","set wr_singlescale","set wr_vecnames",
        f"wrdata {outfile} "+" ".join(f"v({n})" for n in LOOPS+['IN','RST','VD2'])+" i(vdd)","quit",".endc",".end"]
    return "\n".join(L)+"\n"

def cross(t,v,level,rising,t0,t1=None):
    """First time after t0 (and before t1) that v crosses level in that direction, interpolated; nan if never."""
    m=(t[1:]>t0)&(((v[:-1]<level)&(v[1:]>=level)) if rising else ((v[:-1]>level)&(v[1:]<=level)))
    if t1 is not None: m&=t[1:]<t1
    i=np.argmax(m)
    if not m[i]: return float('nan')
    return t[i]+(t[i+1]-t[i])*(level-v[i])/(v[i+1]-v[i])
def crossings(t,v,level,rising,t0,t1):
    m=(t[1:]>t0)&(t[1:]<t1)&(((v[:-1]<level)&(v[1:]>=level)) if rising else ((v[:-1]>level)&(v[1:]<=level)))
    i=np.nonzero(m)[0]; return t[i]+(t[i+1]-t[i])*(level-v[i])/(v[i+1]-v[i])
def within(t,t0,t1): return (t>=t0)&(t<=t1)

def measure(dat):
    names,a=spicedat.read(dat); t=a[:,0]; c={n.lower():a[:,k] for k,n in enumerate(names)}
    V=lambda n:c[f'v({n.lower()})']; half=VDD/2
    r={}
    w=within(t,10e-3,25e-3); ring=crossings(t,V('TP_RING'),half,True,10e-3,25e-3); r['ring_us']=float(np.median(np.diff(ring)))*1e6 if len(ring)>10 else float('nan')
    r['ring_low']=float(V('TP_RING')[w].min()); r['ring_high']=float(V('TP_RING')[w].max())
    r0=V('RING0'); r['ring0_low']=float(r0[w].min()); r['ring0_high']=float(r0[w].max()); mid=(r['ring0_low']+r['ring0_high'])/2       # the ring node: its swing shrinks as the threshold drops
    ring0=crossings(t,r0,mid,True,10e-3,25e-3); r['ring0_us']=float(np.median(np.diff(ring0)))*1e6 if len(ring0)>10 else float('nan')
    # fan-out: IN falls at 2.5 ms -> TP_FO1 rises; IN rises at 3.0 ms -> TP_FO1 falls -> TP_FO10 rises
    def rise(n,t0): a_=cross(t,V(n),0.1*VDD,True,t0); b_=cross(t,V(n),0.9*VDD,True,a_); return (b_-a_)*1e6
    def fall(n,t0): a_=cross(t,V(n),0.9*VDD,False,t0); b_=cross(t,V(n),0.1*VDD,False,a_); return (b_-a_)*1e6
    r['fo1_rise_us']=rise('TP_FO1',2.5e-3-1e-6); r['fo1_fall_us']=fall('TP_FO1',3.0e-3-1e-6)
    r['fo10_rise_us']=rise('TP_FO10',3.0e-3-1e-6); r['fo10_fall_us']=fall('TP_FO10',2.5e-3-1e-6)
    r['fo1_delay_us']=(cross(t,V('TP_FO1'),half,True,2.5e-3-1e-6)-2.5e-3)*1e6; r['fo10_delay_us']=(cross(t,V('TP_FO10'),half,True,3.0e-3-1e-6)-3.0e-3)*1e6
    # the stacks: N = 111 from 8 ms; IN high 2.0-2.5 ms (bus low, ROM low, ROW low) and low 2.5-3.0 (bus high, ROM high)
    w=within(t,9.0e-3,9.9e-3); r['nand_low']=float(V('TP_NAND')[w].max()); r['nor_low']=float(V('TP_NOR')[w].max())
    w=within(t,5.0e-3,5.9e-3); r['nand_high']=float(V('TP_NAND')[w].min()); r['nor_high']=float(V('TP_NOR')[w].min())
    w=within(t,2.3e-3,2.49e-3); r['bus_low']=float(V('TP_BUS')[w].max()); r['rom_low']=float(V('TP_ROM')[w].max())
    w=within(t,2.8e-3,2.99e-3); r['bus_high']=float(V('TP_BUS')[w].min()); r['rom_high']=float(V('TP_ROM')[w].min())
    # the oscillator: X between the trip points, OSC period and duty, Q at half the rate, held by RST
    w=within(t,5e-3,26e-3); r['x_low']=float(V('X')[w].min()); r['x_high']=float(V('X')[w].max())
    osc_r=crossings(t,V('TP_OSC'),half,True,5e-3,26e-3); osc_f=crossings(t,V('TP_OSC'),half,False,5e-3,26e-3)
    r['osc_ms']=float(np.median(np.diff(osc_r)))*1e3 if len(osc_r)>2 else float('nan')
    highs=[min([f for f in osc_f if f>x],default=x)-x for x in osc_r[:-1]]; r['osc_duty']=float(np.mean(highs)/np.median(np.diff(osc_r))) if len(osc_r)>2 else float('nan')
    q_r=crossings(t,V('TP_Q'),half,True,5e-3,26e-3); q_f=crossings(t,V('TP_Q'),half,False,5e-3,26e-3)
    r['q_ms']=float(np.median(np.diff(q_r)))*1e3 if len(q_r)>1 else float('nan')
    if len(osc_r)>1:      # every OSC rising edge toggles Q within a few microseconds: the Q edges between the first and the last OSC edge (plus that margin) are one per OSC edge
        qe=[x for x in list(q_r)+list(q_f) if osc_r[0]-1e-6<x<osc_r[-1]+200e-6]; r['q_edges_per_osc_edge']=len(qe)/len(osc_r)
    else: r['q_edges_per_osc_edge']=float('nan')
    # Q while RST holds it: 0 between clock edges. At a rising clock edge a pulse of up to 4 V and ten microseconds can appear when the
    # master's release (ckn down, m1 up, mq down: two rising 47k edges) loses the race against the slave's copy (ckb up, sa down: one),
    # which the threshold spread decides (MIX seed 2 on the export); the machine's masters are closed at that moment, so nothing captures it
    w=within(t,26.3e-3,27.5e-3); tw=t[w]; qh=V('TP_Q')[w]
    edges=[x for x in list(crossings(t,V('TP_OSC'),half,True,26.3e-3,27.5e-3))+list(crossings(t,V('TP_OSC'),half,False,26.3e-3,27.5e-3))]
    away=np.ones(len(tw),bool)
    for e in edges: away&=~((tw>e-5e-6)&(tw<e+60e-6))
    r['q_held_max']=float(qh[away].max()) if away.any() else float('nan'); r['q_held_runt']=float(qh.max())
    hi=(qh>1.0).astype(int); d_=np.diff(np.concatenate(([0],hi,[0]))); starts=np.nonzero(d_==1)[0]; ends=np.nonzero(d_==-1)[0]
    r['q_held_pulse_us']=float(max([(tw[min(e_,len(tw)-1)]-tw[s_]) for s_,e_ in zip(starts,ends)],default=0))*1e6
    w=within(t,0.2e-3,1.0e-3); r['q_at_powerup_max']=float(V('TP_Q')[w].max())
    # the line driver into 3.3 nF: rise 0.5 to 3.5 V as tb_clock measures CLK, release 0.7 VDD to 0.8 V as it measures RST
    w=within(t,5e-3,26e-3); r['drv_high']=float(V('TP_DRV')[w].max()); r['drv_low']=float(V('TP_DRV')[w].min())
    t0=osc_f[2] if len(osc_f)>3 else 5e-3                       # OSC falls -> DRVN rises -> TP_DRV rises
    a_=cross(t,V('TP_DRV'),0.5,True,t0-5e-6); b_=cross(t,V('TP_DRV'),3.5,True,a_); r['drv_rise_us']=(b_-a_)*1e6
    t0=osc_r[3] if len(osc_r)>4 else 6e-3
    a_=cross(t,V('TP_DRV'),0.7*VDD,False,t0-5e-6); b_=cross(t,V('TP_DRV'),0.8,False,a_); r['drv_fall_us']=(b_-a_)*1e6
    r['vto']=float(V('TP_VTO')[-1])
    idd=-c['i(vdd)']; w=within(t,10e-3,26e-3); vin=V('IN')      # what a meter averages with IN held low or high (the oscillator and the 1k driver always run; N = 111)
    r['idd_ma_in_low']=float(idd[w&(vin<half)].mean())*1e3; r['idd_ma_in_high']=float(idd[w&(vin>half)].mean())*1e3; r['idd_ma_max']=float(idd[w].max())*1e3
    return r

FIELDS=[('ring_us','Ring period at RING (buffered)','us','{:.1f}'),('ring0_us','Ring period at RING0 (the ring node)','us','{:.1f}'),('ring0_high','RING0 peak (the ring\'s swing)','V','{:.1f}'),('fo1_rise_us','Rise 10-90 %, fan-out 1 (FO1)','us','{:.2f}'),('fo10_rise_us','Rise 10-90 %, fan-out 10 (FO10)','us','{:.2f}'),
        ('fo1_fall_us','Fall 90-10 %, fan-out 1 (FO1)','us','{:.2f}'),('fo10_fall_us','Fall 90-10 %, fan-out 10 (FO10)','us','{:.2f}'),
        ('fo1_delay_us','Delay IN edge to FO1 half way (rising)','us','{:.2f}'),('fo10_delay_us','Delay IN edge to FO10 half way (rising)','us','{:.2f}'),
        ('nand_low','NAND low, N1 N2 N3 = 111','V','{:.3f}'),('nor_low','NOR low, N1 N2 N3 = 111','V','{:.3f}'),('bus_low','BUS low, IN high (10k pull-up)','V','{:.3f}'),
        ('x_low','X lower trip point','V','{:.2f}'),('x_high','X upper trip point','V','{:.2f}'),('osc_ms','OSC period','ms','{:.2f}'),('osc_duty','OSC duty (high fraction)','','{:.2f}'),
        ('q_ms','Q period','ms','{:.2f}'),('q_edges_per_osc_edge','Q edges per OSC rising edge','','{:.2f}'),('q_held_max','Q while RST is high, away from clock edges','V','{:.2f}'),('q_held_runt','Q pulse at a clock edge while RST is high: peak','V','{:.2f}'),('q_held_pulse_us','That pulse: width above 1 V','us','{:.0f}'),
        ('drv_high','DRV high (3.3 nF, 10k)','V','{:.2f}'),('drv_rise_us','DRV rise 0.5 to 3.5 V','us','{:.1f}'),('drv_fall_us','DRV fall 3.5 to 0.8 V','us','{:.0f}'),
        ('vto','VTO','V','{:.2f}'),('rom_high','ROM high, IN low','V','{:.2f}'),('rom_low','ROM low, IN high','V','{:.3f}'),
        ('idd_ma_in_low','Supply current, IN low (meter average)','mA','{:.1f}'),('idd_ma_in_high','Supply current, IN high (the LED, the row)','mA','{:.1f}'),('idd_ma_max','Supply current, peak','mA','{:.1f}')]

def run(src,corner,seed,outdir):
    os.makedirs(outdir,exist_ok=True); tag=f"{src}_{corner}{seed if corner=='MIX' else ''}"
    dat=os.path.join(outdir,f'{tag}.dat'); cir=os.path.join(outdir,f'{tag}.cir')
    lines=export() if src=='kicad' else dev_lines()
    open(cir,'w').write(deck(lines,corner,seed,dat))
    if os.path.exists(dat): os.remove(dat)
    r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
    if not os.path.exists(dat) or 'aborted' in r.stdout+r.stderr: print(r.stdout[-3000:],r.stderr[-3000:]); raise SystemExit('ngspice failed')
    res=measure(dat); res['tag']=tag; res['corner']=corner; res['seed']=seed
    json.dump(res,open(os.path.join(outdir,f'{tag}.json'),'w'),indent=1)
    print(tag+": "+", ".join(f"{k}={F(fmt,res[k])}{u}" for k,_,u,fmt in FIELDS if isinstance(res.get(k),(int,float))))
    return res

def F(fmt,v): return 'none' if v!=v else fmt.format(v)      # nan: the loop showed no signal in that run

def table(results,path,src):
    cols=[r['tag'].replace(src+'_','') for r in results]
    out=["# Coupon: what the bench should read","",f"From `sim/tb_coupon.py {src}` on the card's netlist, 5.00 V, a x10 probe (15 pF) on the loop being read and 3.3 nF clipped on DRV;",
         "LO, TYP, HI are the transistor model's threshold corners (0.8, 2.0, 3.0 V, `lib/2N7000.lib`), MIX gives every transistor its own.",
         "The band is the lowest to the highest value over all the runs; a bench reading outside it means the cell in copper is not the modelled one (docs/bring-up.md section 1).","",
         "| Measurement | Unit | "+" | ".join(cols)+" | Band |","|---|---|"+"---|"*len(cols)+"---|"]
    for k,name,u,fmt in FIELDS:
        vals=[r[k] for r in results]; ok=[v for v in vals if v==v]; band=f"{fmt.format(min(ok))} to {fmt.format(max(ok))}" if ok else 'none'
        out.append(f"| {name} | {u} | "+" | ".join(F(fmt,v) for v in vals)+f" | {band} |")
    open(path,'w').write("\n".join(out)+"\n"); print("table",path)

if __name__=='__main__':
    src=sys.argv[1]; outdir=sys.argv[2]
    corner=sys.argv[sys.argv.index('--corner')+1] if '--corner' in sys.argv else 'TYP'
    seed=int(sys.argv[sys.argv.index('--seed')+1]) if '--seed' in sys.argv else 1
    if '--all' in sys.argv:
        res=[run(src,'TYP',1,outdir),run(src,'LO',1,outdir),run(src,'HI',1,outdir)]+[run(src,'MIX',s,outdir) for s in (1,2,3)]
        table(res,os.path.join(outdir,'coupon_expected.md'),src)
    else: run(src,corner,seed,outdir)
