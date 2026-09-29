"""The reset release against the clock, on the clock card alone: the bench of the hold-off (one transistor and one resistor).

    python3 tb_reset_release.py [--corners TYP,LO,HI,MIX1,MIX2,MIX3] [--speeds fast,potmax,slow,slowpotmax] [--phases 20]

The fault (sim/results/sweep_por.md): RST lets go whenever its capacitor, or a finger, lets it, and the oscillator runs through
the reset. A clock edge in the 45 us in which the cards leave their resets starts the machine wrong: 2 of 39 starts.

The part on trial: a transistor from the oscillator's timing node X to ground through 100 ohm, its gate on the RST line.
While RST is high X is held empty, the Schmitt trigger reads "low", and the card's own gate holds CLK low. When RST lets
go X charges from 0 V, not from the lower trip point, so the first clock edge comes later than a half period after the
release, whoever released RST: the card's power-on reset or the panel's button (the card reads the line, not its own reset).

The deck is the card's schematic export with the machine's load on CLK and RST (3 nF and the panel's 10k, as tb_clock.py),
the RUN switch closed, and the two parts added in the deck: the card is not changed until this and the machine's sweep pass.
The panel's RST button is its Schmitt's output as the card sees it: 1k and 100 ohm from +5V through a diode onto RST.

Each case is three runs. CALIBRATION: power-on and one press, with the hold-off: the period P, the first edge's delay, the
release's lag behind the button. TRIAL: power-on, then --phases presses of the button (8 ms each), press k timed to fall
(k + 1/2) / phases of a period after a clock edge, so the presses walk across the period. REFERENCE: the same presses
without the two parts, which has to show the fault, or the bench could not have seen it.

What has to hold at every release of the trial (power-on and each press):
  held      CLK under 0.5 V from 1 ms after RST rose until RST lets go, and on until the first edge
  delay     the first rising edge of CLK (0.5 V) comes 1 ms or more after RST fell under 0.8 V, the lowest threshold on the line
  whole     the first high time is 0.9 or more of the high time of the edges after it; the first period is within a tenth of P
and of the case:
  walked    the presses fell in 18 or more of the 20 twentieths of the period (the bench did what it says)
  same      P with the two parts is within 1 % of P without them (the transistor, off, is not a load on the oscillator)
  seen      the reference has a release with a clock edge nearer than a twentieth of a period (the first bench asked for an
            edge inside 1 ms, which 21 releases seldom hit in a period of 17 ms to 1.3 s: the slow cases failed on the
            reference alone)
Writes out/reset_release/<case>.json and results/reset_release.md. One ngspice at a time."""
import sys, os, subprocess, random, json, time, numpy as np
import spicedat, nmos, machine
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'out','reset_release'); DOC=os.path.join(HERE,'results','reset_release.md')
MODELS={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}
SPEEDS={'fast':('the pot at its least, 47 nF',1e-3,False,2e-3),'potmax':('the pot at 1 M, 47 nF',1e6,False,30e-3),
        'slow':('the pot at its least, SLOW jumper on (2.2 uF more)',1e-3,True,0.12),'slowpotmax':('the pot at 1 M, SLOW jumper on',1e6,True,1.4)}      # (what, pot ohms, jumper, a period to plan the first run by)
R_HOLD=100; PRESS=8e-3; VLO=0.5; VREL=0.8; VHI=3.5; DELAY_MIN=1e-3

def deck(lines,corner,speed,hold,presses,tend,tmax,outfile):
    c,seed=(corner[:3],int(corner[3:])) if corner.startswith('MIX') else (corner,1); rng=random.Random(seed); body=[]
    for l in lines:
        if l.startswith(('.','*')): continue
        if l[0]=='M': l=l.replace(' 2N7000',' '+(MODELS[rng.choice(['LO','TYP','HI'])] if c=='MIX' else MODELS[c]))
        body.append(l)
    what,pot,jumper,_=SPEEDS[speed]; lib=os.path.join(HERE,'..','lib')
    L=[f"* reset release, {corner}, {speed}, {'with' if hold else 'without'} the hold-off",f'.include "{lib}/2N7000.lib"',f'.include "{lib}/led.lib"',nmos.SW_MODEL,"VDD +5V 0 5",
       "Rrun +5V RUNSW 1m",f"Rpot RT X {pot:g}","Rj2 X Net-_J2-Pin_2_ 1m" if jumper else "Rj2 Net-_J2-Pin_2_ 0 1G","Vhlt HLT 0 0",
       "Rpd CLK 0 10k","Cline CLK 0 3n","Rrpd RST 0 10k","Crst RST 0 3n",".ic V(POR)=0 V(X)=0"]
    pw=[(0,0)]
    for p in presses: pw+=[(p,0),(p+2e-6,5),(p+PRESS,5),(p+PRESS+2e-6,0)]
    L+=["Vbs BS 0 PWL("+" ".join(f"{t:.9g} {v}" for t,v in pw)+")" if presses else "Vbs BS 0 0","Rbs BS BS1 1.1k","Dbs BS1 RST D1N4148"]
    if hold:
        m=MODELS[random.Random(seed+1000).choice(['LO','TYP','HI'])] if c=='MIX' else MODELS[c]      # (a draw of its own: the card's transistors keep the models they have in every other deck of this corner)
        L+=[f"Rhold X XH {R_HOLD}",f"Mhold XH RST GND {m}"]
    L+=body+[".save v(CLK) v(RST) v(X) v(BS)",f".tran 2u {tend:.6g} 0 {tmax:.3g}",".option method=gear cshunt=1e-12 abstol=1e-10 chgtol=1e-12",".control","run","set wr_singlescale","set wr_vecnames",
             f"wrdata {outfile} v(CLK) v(RST) v(X) v(BS)","quit",".endc",".end"]
    return "\n".join(L)+"\n"

def run(lines,corner,speed,hold,presses,tend,tmax,tag):
    os.makedirs(OUT,exist_ok=True); dat=os.path.join(OUT,tag+'.dat'); cir=os.path.join(OUT,tag+'.cir'); open(cir,'w').write(deck(lines,corner,speed,hold,presses,tend,tmax,dat))
    if os.path.exists(dat): os.remove(dat)
    r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True)
    if not os.path.exists(dat) or 'aborted' in r.stdout+r.stderr: print(r.stdout[-2000:],r.stderr[-2000:]); raise SystemExit(f'ngspice failed: {tag}')
    names,a=spicedat.read(dat); os.remove(dat); col={n.lower():a[:,k] for k,n in enumerate(names)}
    return a[:,0],col['v(clk)'],col['v(rst)'],col['v(bs)']

def crossings(t,v,level,rising):
    m=((v[:-1]<level)&(v[1:]>=level)) if rising else ((v[:-1]>level)&(v[1:]<=level)); i=np.nonzero(m)[0]
    return t[i]+(level-v[i])*(t[i+1]-t[i])/(v[i+1]-v[i])
after=lambda xs,t0: next((x for x in xs if x>t0),None)
before=lambda xs,t0: next((x for x in reversed(xs) if x<=t0),None)

def releases(t,clk,rst):
    """Every release of RST in the run: where RST rose, where it fell under VHI and under VREL, the clock's edges after it."""
    up=crossings(t,clk,VLO,True); dn=crossings(t,clk,VLO,False); mu=crossings(t,clk,2.5,True); md=crossings(t,clk,2.5,False)
    rr=list(crossings(t,rst,VHI,True)); f35=crossings(t,rst,VHI,False); f08=crossings(t,rst,VREL,False); out=[]
    if rst[0]>VHI: rr=[0.0]+rr
    for k,r in enumerate(rr):
        a=after(f35,r); b=after(f08,r); nxt=rr[k+1] if k+1<len(rr) else t[-1]
        if a is None or b is None: continue
        e=[x for x in up if b<x<nxt]; m1=[x for x in mu if b<x<nxt]; m0=[x for x in md if b<x<nxt]
        highs=[after(m0,x)-x for x in m1 if after(m0,x) is not None]
        d=dict(rose=r,fell35=a,fell08=b,edges=len(e),first=e[0]-b if e else None,period1=e[1]-e[0] if len(e)>1 else None,periods=list(np.diff(e)[1:]),high1=highs[0] if highs else None,highs=highs[1:],
               phase_edge=before(up,r),                                           # the clock edge the press came after
               stop=(lambda x: 0.0 if x is None else max(0.0,x-r))(before(dn,a) if before(dn,a) is not None and before(dn,a)>r else None),      # RST up to CLK down, 0 if CLK was low already
               held=float(np.max(clk[(t>min(r+1e-3,a))&(t<(e[0] if e else nxt)-2e-6)],initial=0.0)),
               nearest=min([abs(x-a) for x in list(up)+list(dn)] or [None]),next_edge=(lambda x: None if x is None else x-a)(after(up,a)))
        out.append(d)
    return out

def case(lines,corner,speed,phases):
    what,pot,jumper,pnom=SPEEDS[speed]; tag=f'{corner}_{speed}'; t0=time.time(); tmax=min(max(pnom/500,2e-6),200e-6)
    # calibration: power-on and one press, with the hold-off, and the same without it for the period
    por=0.5; t,clk,rst,bs=run(lines,corner,speed,True,[],por+8*pnom,tmax,tag+'_cal0'); R=releases(t,clk,rst)
    assert R and R[0]['edges']>=4, f'{tag}: the power-on reset had not let go, or the clock had not run four periods, after {por+8*pnom:g} s'
    rel0=R[0]['fell08']; d1=R[0]['first']; P=float(np.mean(R[0]['periods'])); press=rel0+d1+3.5*P
    t,clk,rst,bs=run(lines,corner,speed,True,[press],press+PRESS+d1+5*P,tmax,tag+'_cal1'); R=releases(t,clk,rst); assert len(R)==2, f'{tag}: calibration press not found'
    lag=R[1]['fell08']-(press+PRESS); d1b=R[1]['first']
    t,clk,rst,bs=run(lines,corner,speed,False,[],rel0+8*P,tmax,tag+'_cal2'); up=[x for x in crossings(t,clk,VLO,True) if x>rel0]; P0=float(np.mean(np.diff(up)[1:]))
    # the schedule: press k comes (k+1/2)/phases of a period after the third edge that follows the release before it
    presses=[]; rel=rel0; d=d1
    for k in range(phases):
        p=rel+d+3*P+(k+0.5)/phases*P; presses.append(p); rel=p+PRESS+lag; d=d1b
    tend=rel+d1b+5*P
    t,clk,rst,bs=run(lines,corner,speed,True,presses,tend,tmax,tag+'_trial'); T=releases(t,clk,rst)
    t,clk,rst,bs=run(lines,corner,speed,False,presses,tend,tmax,tag+'_ref'); F=releases(t,clk,rst)
    assert len(T)==phases+1, f'{tag}: {len(T)} releases found in the trial, {phases+1} made'
    hs=float(np.median([h for r in T for h in r['highs']])); bins=sorted({int(((r['rose']-r['phase_edge'])/P%1)*20) for r in T[1:] if r['phase_edge'] is not None})
    res=dict(corner=corner,speed=speed,what=what,phases=phases,period_ms=P*1e3,period_without_ms=P0*1e3,high_ms=hs*1e3,por_release_ms=rel0*1e3,
             first_ms=[r['first']*1e3 if r['first'] is not None else None for r in T],held_v=max(r['held'] for r in T),stop_us=max(r['stop'] for r in T[1:])*1e6,
             high1=[r['high1']/hs if r['high1'] else None for r in T],period1=[r['period1']/P if r['period1'] else None for r in T],bins=bins,
             ref_next_ms=[r['next_edge']*1e3 if r['next_edge'] is not None else None for r in F],ref_nearest_us=[r['nearest']*1e6 for r in F],secs=time.time()-t0)
    ok=dict(held=res['held_v']<VLO,delay=all(x is not None and x>=DELAY_MIN*1e3 for x in res['first_ms']),
            whole=all(x is not None and x>=0.9 for x in res['high1']) and all(x is not None and 0.9<=x<=1.1 for x in res['period1']),
            walked=len(bins)>=18,same=abs(P/P0-1)<0.01,seen=min(res['ref_nearest_us'])<P*1e6/20); ok={k:bool(v) for k,v in ok.items()}
    res['checks']=ok; res['ok']=all(ok.values()); json.dump(res,open(os.path.join(OUT,tag+'.json'),'w'),indent=1)
    print(f"{tag}: {'PASS' if res['ok'] else 'FAIL '+','.join(k for k,v in ok.items() if not v)}: P {P*1e3:.3g} ms, first edge {min(res['first_ms']):.3g} to {max(res['first_ms']):.3g} ms after the release over {len(T)} releases, "
          f"CLK held under {res['held_v']:.2f} V, first high {min(res['high1']):.2f} of the usual, {len(bins)} of 20 phases; without: nearest edge {min(res['ref_nearest_us']):.0f} us, "
          f"{sum(1 for x in res['ref_next_ms'] if x is not None and x<1)} of {len(F)} releases with an edge inside 1 ms ({res['secs']:.0f} s)",flush=True)
    return res

def write(rows,corners,speeds,phases):
    n=sum(1 for r in rows if r['ok']); rel=sum(len(r['first_ms']) for r in rows)
    L=['# The reset release against the clock: the hold-off on the clock card alone','',f"Generated {time.strftime('%Y-%m-%d %H:%M')} by sim/tb_reset_release.py. {len(rows)} cases, {rel} releases.",'',
       f"The two parts on trial: {R_HOLD} ohm and a 2N7000 from the timing node X to ground, gate on RST. They are in the deck, not on the card yet.",
       f"Each case: power-on, then {phases} presses of the panel's RST button ({PRESS*1e3:g} ms each), walked across the clock period; the same without the two parts.",'',
       '| corner | speed | period ms | first edge after the release ms | CLK while held V | RST up to CLK down us | first high / usual | first period / usual | phases of 20 | period without ms | without: nearest edge us | without: releases with an edge inside 1 ms | result |','|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        f=[x for x in r['first_ms'] if x is not None]; h=[x for x in r['high1'] if x is not None]; p=[x for x in r['period1'] if x is not None]
        L.append(f"| {r['corner']} | {r['what']} | {r['period_ms']:.4g} | {min(f):.4g} to {max(f):.4g} | {r['held_v']:.2f} | {r['stop_us']:.0f} | {min(h):.2f} to {max(h):.2f} | {min(p):.2f} to {max(p):.2f} | {len(r['bins'])} | {r['period_without_ms']:.4g} | "
                 f"{min(r['ref_nearest_us']):.0f} | {sum(1 for x in r['ref_next_ms'] if x is not None and x<1)} of {len(r['ref_next_ms'])} | {'pass' if r['ok'] else 'FAIL: '+', '.join(k for k,v in r['checks'].items() if not v)} |")
    L+=['',f"{n} of {len(rows)} cases pass."]
    open(DOC,'w').write('\n'.join(L)+'\n'); print(L[-1]); return n==len(rows)

if __name__=='__main__':
    a=sys.argv; get=lambda k,d: a[a.index(k)+1] if k in a else d
    corners=get('--corners','TYP,LO,HI,MIX1,MIX2,MIX3').split(','); speeds=get('--speeds','fast,potmax,slow,slowpotmax').split(','); phases=int(get('--phases','20'))
    lines=machine.export('clkc'); rows=[]
    for s in speeds:
        for c in corners: rows.append(case(lines,c,s,phases))
    sys.exit(0 if write(rows,corners,speeds,phases) else 1)
