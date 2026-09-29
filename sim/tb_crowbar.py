"""The hub's crowbar and reverse diode (D061) on the bench: what the five parts do when the bench supply is turned up, switched on
at the wrong voltage, plugged in live, or plugged in the wrong way round; and which values to fit.

    python3 tb_crowbar.py            (from sim/; ngspice; a minute; writes results/crowbar.md)
    python3 tb_crowbar.py --models   (the models of lib/power.lib against their datasheets, nothing else)

The circuit, after the polyfuse, across the machine's +5V and GND:
    a zener from the rail to the SCR's gate, a resistor RG and a capacitor CG from the gate to GND, the SCR across the rail,
    a 3 A diode across the rail the other way round.
Above the zener's voltage plus the gate's 0.6 V the zener feeds the gate, the SCR fires and holds the rail at about a volt; the
supply's current limit, or the polyfuse, carries the rest. With the leads reversed the diode holds the rail at minus a volt.

The bench: the supply is a set voltage behind a current limit (a current source held at the set voltage by a diode) with its
output capacitor (470 uF, and 2200 uF for the live plug: the supply's own is not known); two leads, 0.1 ohm and 1 uH; the
polyfuse as its resistance, 0.12 ohm new to 0.32 ohm after a trip (its tripping is heat, not in this deck: the table says what
the SCR carries until it does); the machine as the hub's 100 uF behind 0.3 ohm, the cards' 520 uF behind 0.15 ohm (their
own resistance and the ribbon's), and a load: 5 ohm (the machine running, 1 A) or 1 k (idle or unplugged). The idle machine
is the case that counts twice: the leads and the fuse then drop nothing, so the rail is at the supply's voltage when it
must not fire; and nothing but the crowbar stands between the supply and the rail when it must. With the machine running
and the supply's limit at 1.5 A the rail cannot pass 7.5 V whatever the knob says: 1.5 A into 5 ohm.
Swept: the zener (5.6, 6.2, 6.8 V, each at -5 %, nominal, +5 %, with the softest knee its datasheet allows), RG (100, 220 ohm),
the SCR (typical, the hardest to fire the datasheet allows, one that fires on a fifth of the typical current), the polyfuse's
resistance. CG is 100 nF: with RG it is 10 us, against the SCR's own microseconds.

What it must show: nothing conducts at 5.25 V, and not at 5.5 V (a supply's overshoot); every corner trips below 9 V (the
2N7000's gate stands 20 V); the rail never passes 9 V however the voltage arrives; reversed leads stay above -1.5 V."""
import os, re, subprocess, sys, itertools
HERE=os.path.dirname(os.path.abspath(__file__)); LIB=os.path.join(HERE,'..','lib','power.lib'); OUT=os.path.join(HERE,'out')
ZENERS={'1N4734A':(5.6,45e-3,5,600),'1N4735A':(6.2,41e-3,2,700),'1N4736A':(6.8,37e-3,3.5,700)}      # volts, test current, impedance there, impedance at 1 mA
SCRS={'typical':'BT151','hard':'BT151_HARD','easy':'BT151_EASY'}
RLOAD=5.0; RIDLE=1e3; RLEAD=0.1; LLEAD=1e-6

def ngspice(deck,tag):
    p=os.path.join(OUT,f'crowbar_{tag}.cir'); open(p,'w').write(deck)
    r=subprocess.run(['ngspice','-b',p],capture_output=True,text=True).stdout
    return {k.lower():float(v) for k,v in re.findall(r'^(\w+)\s*=\s*([-+.\deE]+)',r,re.M)},r

def bench(scene,zener='1N4735A',tol=1.0,rg=100,cg=100e-9,scr='typical',rfuse=0.12,ilim=1.5,cout=470e-6,crowbar=True,rload=RLOAD):
    """One run. scene: 'normal' (5.0 V, then 5.25, then 5.5), 'knob' (5 V turned up to 12 V in half a second), 'on30' (the output
    switched on with 30 V set: there in a millisecond), 'plug30' (the leads plugged in with the supply on at 30 V: its output
    capacitor into the machine), 'rev5' and 'revplug30' (the same with the leads crossed)."""
    vz,izt,zzt,zzk=ZENERS[zener]; rev=scene.startswith('rev'); P,N=('0','vbus') if rev else ('vbus','0')
    vset={'normal':'PWL(0 0 20m 5 100m 5 110m 5.25 200m 5.25 210m 5.5 300m 5.5)','knob':'PWL(0 0 20m 5 100m 5 600m 12 700m 12)',
          'on30':'PWL(0 0 20m 0 21m 30 300m 30)','plug30':'30','rev5':'PWL(0 0 20m 5 300m 5)','revplug30':'30'}[scene]
    plug='plug' in scene; tend={'normal':0.3,'knob':0.7,'on30':0.3,'plug30':0.1,'rev5':0.3,'revplug30':0.1}[scene]
    L=[f"* the hub's crowbar: {scene}",f".include {LIB}",
       f"Vset sv {N} {vset}",f"Ilim {N} so {ilim}","Dcv so sv DIDEAL",".model DIDEAL D(IS=1e-9 N=0.05 RS=1m)",f"Cout so {N} {cout}"+(" IC=30" if plug else ""),
       ("Splug so pl ctl 0 SPLUG\n.model SPLUG SW(VT=0.5 RON=1m ROFF=1e9)\nVctl ctl 0 PULSE(0 1 1m 10u 10u 1 2)" if plug else "Rplug so pl 1m"),f"Rlead pl ll {RLEAD}",f"Llead ll {P} {LLEAD}",
       f"Rfuse vbus rail {rfuse}","Chub rail ch 100u","Rhub ch 0 0.3","Ccards rail cc 520u","Rcards cc 0 0.15",f"Rload rail 0 {rload}"]
    if crowbar:
        L+=[f"XZ rail zg Z1N47 VZ={vz*tol:.4f} IZT={izt} ZZT={zzt} ZZK={zzk}","Vzm zg g 0",f"RG g 0 {rg}",f"CG g 0 {cg}","Vsa rail sa 0",f"XS sa g 0 {SCRS[scr]}","Vdm 0 da 0","DR da rail D1N5408"]
    else: L+=["Vzm zg g 0","Rz zg 0 1e9","Vsa rail sa 0","Rs sa 0 1e9","Vdm 0 da 0","Rd da rail 1e9"]
    L+=[".option method=gear reltol=2e-3 abstol=1e-9 vntol=1e-5 gmin=1e-10 rshunt=1e9 cshunt=1e-12",      # (trapezoidal integration rang on the leads' inductance and gave up on the live plug at 2200 uF)
        f".tran 2u {tend} uic",".control","run","let psc=v(sa)*i(Vsa)","let isq=i(Vsa)*i(Vsa)","let idq=i(Vdm)*i(Vdm)",
        "meas tran railmax MAX v(rail)","meas tran railmin MIN v(rail)",f"meas tran railend FIND v(rail) AT={tend*0.999}",
        "meas tran iscrmax MAX i(Vsa)","meas tran tfire WHEN i(Vsa)=0.1 RISE=1","meas tran vfire FIND v(rail) WHEN i(Vsa)=0.1 RISE=1",f"meas tran iscrend FIND i(Vsa) AT={tend*0.999}",f"meas tran pscrend FIND psc AT={tend*0.999}","meas tran i2tscr INTEG isq",
        "meas tran idmax MAX i(Vdm)",f"meas tran idend FIND i(Vdm) AT={tend*0.999}","meas tran i2td INTEG idq","meas tran gmax MAX v(g)"]
    if scene=='normal': L+=["meas tran iz50 FIND i(Vzm) AT=0.095","meas tran iz525 FIND i(Vzm) AT=0.195","meas tran iz55 FIND i(Vzm) AT=0.295","meas tran g55 FIND v(g) AT=0.295","meas tran rail525 FIND v(rail) AT=0.195"]
    L+=["quit",".endc",".end"]
    m,raw=ngspice('\n'.join(L)+'\n',scene)
    if 'railend' not in m or 'idend' not in m: raise SystemExit(f'{scene}: the run did not reach its end\n'+raw[-3000:])
    return m

def models():
    """The SCR's gate current and voltage to fire, its on-state voltage and holding current; the zeners' curves; the diode's forward voltage."""
    rows=[]
    for name,sub in SCRS.items():
        deck=f"""* SCR {sub}
.include {LIB}
V1 v1 0 PWL(0 0 1m 12)
R1 v1 a1 120
X1 a1 g1 0 {sub}
Ig 0 g1m PWL(0 0 2m 0 22m 20m)
Vm g1m g1 0
I2 0 a2 PWL(0 0 1m 0.2 2m 0.2 3m 1.5 4m 1.5 5m 3 6m 3 7m 10 8m 10 9m 23 22m 23)
X2 a2 g2 0 {sub}
Vg2 g2s 0 PULSE(0 5 1.1m 1u 1u 0.2m 1)
Rg2 g2s g2 100
I3 0 a3 PWL(0 0 1m 0.2 2m 0.2 22m 0)
X3 a3 g3 0 {sub}
Vg3 g3s 0 PULSE(0 5 1.1m 1u 1u 0.2m 1)
Rg3 g3s g3 100
D3 a3 cl DCL
Vcl cl 0 30
.model DCL D
.tran 5u 22m
.control
run
meas tran igt FIND i(Vm) WHEN v(a1)=6 FALL=1
meas tran vgt FIND v(g1) WHEN v(a1)=6 FALL=1
meas tran vt1p5 FIND v(a2) AT=3.9m
meas tran vt3 FIND v(a2) AT=5.9m
meas tran vt10 FIND v(a2) AT=7.9m
meas tran vt23 FIND v(a2) AT=9.9m
meas tran toff WHEN v(a3)=5 RISE=1 TD=2m
quit
.endc
.end
"""
        m,raw=ngspice(deck,'model_scr'); m['ih']=0.2*(22e-3-m['toff'])/20e-3; rows.append((name,m))
    z=[]
    for name,(vz,izt,zzt,zzk) in ZENERS.items():
        deck=f"""* zener {name}
.include {LIB}
V1 k 0 0
XZ k 0 Z1N47 VZ={vz} IZT={izt} ZZT={zzt} ZZK={zzk}
.dc V1 0 {vz+0.5} 0.005
.control
run
let iw=-i(V1)
meas dc i525 FIND iw AT=5.25
meas dc i55 FIND iw AT=5.5
meas dc v1m WHEN iw=1m
meas dc v8m WHEN iw=8m
meas dc vzt WHEN iw={izt}
quit
.endc
.end
"""
        m,raw=ngspice(deck,'model_z'); z.append((name,m))
    deck=f"""* 1N5408
.include {LIB}
I1 0 a 0
D1 a 0 D1N5408
.dc I1 0.1 10.5 0.1
.control
run
meas dc vf1p5 FIND v(a) AT=1.5
meas dc vf3 FIND v(a) AT=3
meas dc vf10 FIND v(a) AT=10
quit
.endc
.end
"""
    d,raw=ngspice(deck,'model_d')
    return rows,z,d

if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True); W=[]; P=W.append
    rows,z,d=models()
    P("# The hub's crowbar and reverse diode on the bench"); P("")
    P("Generated by `sim/tb_crowbar.py` (ngspice, the models of `lib/power.lib`). The five parts after the polyfuse (D061): a zener from the rail to an SCR's gate, a resistor and a capacitor from the gate to ground, the SCR across the rail, a 3 A diode across the rail the other way round."); P("")
    P("## The models against their datasheets"); P("")
    P("| SCR model | Gate current to fire | Gate voltage | On-state at 1.5 A | 3 A | 10 A | 23 A | Holding current |"); P("|---|---|---|---|---|---|---|---|")
    for name,m in rows: P(f"| {name} | {m['igt']*1e3:.1f} mA | {m['vgt']:.2f} V | {m['vt1p5']:.2f} V | {m['vt3']:.2f} V | {m['vt10']:.2f} V | {m['vt23']:.2f} V | {m['ih']*1e3:.0f} mA |")
    P("| BT151-500R datasheet, typical (maximum) | 2 (15) mA | 0.6 (1.5) V | | | | 1.4 (1.75) V | 7 (20) mA |"); P("")
    P("| Zener model, softest knee | At 5.25 V | At 5.5 V | 1 mA at | 8 mA at | Test current at |"); P("|---|---|---|---|---|---|")
    for name,m in z: P(f"| {name}, {ZENERS[name][0]} V | {m['i525']*1e3:.2f} mA | {m['i55']*1e3:.2f} mA | {m['v1m']:.2f} V | {m['v8m']:.2f} V | {m['vzt']:.2f} V |")
    P(""); P(f"1N5408 model: {d['vf1p5']:.2f} V at 1.5 A, {d['vf3']:.2f} V at 3 A (datasheet: 1.2 V maximum), {d['vf10']:.2f} V at 10 A."); P("")
    if '--models' in sys.argv: print('\n'.join(W)); sys.exit(0)
    # which zener and which gate resistor: every corner of each
    P("## Which zener, which gate resistor"); P("")
    P("The machine idle. The supply at 5.0, 5.25 and 5.5 V; then turned from 5 V to 12 V in half a second behind a 1.5 A limit. Every corner of zener tolerance (-5 %, nominal, +5 %), SCR (typical, hard, easy) and polyfuse resistance (0.12, 0.32 ohm): 18 runs a row. \"Fires at\" is the rail at the moment the SCR takes a tenth of an amp, the lowest and the highest of the corners."); P("")
    P("| Zener | RG | Zener current at 5.25 V | At 5.5 V | Gate at 5.5 V | Fires at | Verdict |"); P("|---|---|---|---|---|---|---|")
    pick=None; table={}
    for zen,rg in itertools.product(ZENERS,(100,220)):
        quiet=[bench('normal',zen,tol,rg,scr=s,rload=1e3) for tol in (0.95,1.0,1.05) for s in SCRS]
        fire=[bench('knob',zen,tol,rg,scr=s,rfuse=rf,rload=RIDLE).get('vfire',99.0) for tol in (0.95,1.0,1.05) for s in SCRS for rf in (0.12,0.32)]      # 99: it never fired
        iz525=max(m['iz525'] for m in quiet); iz55=max(m['iz55'] for m in quiet); g55=max(m['g55'] for m in quiet)
        stays=min(m['railend'] for m in quiet)>5.45 and min(m['rail525'] for m in quiet)>5.2 and max(m['iscrmax'] for m in quiet)<1e-3      # the rail is where the supply put it and the SCR carries nothing
        ok=stays and g55<0.3 and max(fire)<9.0 and min(fire)>5.8
        why=[] if ok else ([] if stays else ['fires at or below 5.5 V'])+([f'gate at {g55:.2f} V at 5.5 V: too near the 0.6 V that fires it'] if stays and g55>=0.3 else [])+(['a corner never fires'] if max(fire)>=99 else [f'a corner fires only at {max(fire):.1f} V'] if max(fire)>=9 else [])+([f'a corner fires at {min(fire):.2f} V'] if stays and min(fire)<=5.8 else [])
        table[(zen,rg)]=(iz525,iz55,g55,min(fire),max(fire),ok)
        P(f"| {zen}, {ZENERS[zen][0]} V | {rg} ohm | {iz525*1e3:.2f} mA | {iz55*1e3:.2f} mA | {g55:.2f} V | {min(fire):.2f} to {max(fire):.2f} V | {'fits' if ok else '; '.join(why)} |")
    fits=[k for k,v in table.items() if v[5]]
    if not fits: P(""); P("No combination fits."); open(os.path.join(HERE,'results','crowbar.md'),'w').write('\n'.join(W)+'\n'); print('\n'.join(W)); sys.exit(1)
    pick=min(fits,key=lambda k:(round(table[k][4],1),table[k][2]))      # the lowest highest firing point (to a tenth of a volt), then the quietest gate at 5.5 V
    zen,rg=pick; P(""); P(f"Chosen: **{zen} ({ZENERS[zen][0]} V) and {rg} ohm**: of the combinations that fit, the one whose worst corner fires lowest, and of those the one whose gate is farthest from firing at 5.5 V."); P("")
    # the chosen values, every way the voltage can arrive
    P("## The chosen values, every way the voltage can arrive"); P("")
    P("The worst corner of each line: the zener at +5 % and the hard SCR for the highest rail, the polyfuse new (0.12 ohm) for the highest currents. \"Without\" is the same bench with the five parts left out.")
    P(""); P("| What happens | Machine | Supply's limit | Rail without | Rail's peak with | Rail after | SCR or diode, peak | Steady | Heat in it, steady | I2t (rating) |"); P("|---|---|---|---|---|---|---|---|---|---|")
    heat={}
    for scene,what,cases in (('knob','5 V turned up to 12 V in half a second',((RLOAD,1.5,470e-6),(RIDLE,1.5,470e-6),(RIDLE,3.0,470e-6),(RIDLE,10.0,470e-6))),
                             ('on30','output switched on with 30 V set',((RLOAD,1.5,470e-6),(RIDLE,1.5,470e-6),(RIDLE,10.0,470e-6))),
                             ('plug30','leads plugged in live at 30 V',((RIDLE,1.5,470e-6),(RIDLE,10.0,470e-6),(RIDLE,10.0,2200e-6))),
                             ('rev5','leads crossed, 5 V',((RLOAD,1.5,470e-6),(RLOAD,10.0,470e-6))),
                             ('revplug30','leads crossed, plugged in live at 30 V',((RLOAD,1.5,470e-6),(RLOAD,10.0,2200e-6)))):
        for rl,ilim,cout in cases:
            kw=dict(scr='hard',rfuse=0.12,ilim=ilim,cout=cout,rload=rl); a=bench(scene,zen,1.05,rg,**kw); b=bench(scene,zen,1.05,rg,crowbar=False,**kw); rev=scene.startswith('rev')
            mach=('running' if rl==RLOAD else 'idle')+(f', supply {cout*1e6:.0f} uF' if 'plug' in scene else '')
            if rev:
                pd=a['idend']*abs(a['railend']); P(f"| {what} | {mach} | {ilim:g} A | {b['railmin']:.1f} V | {a['railmin']:.2f} V | {a['railend']:.2f} V | diode {a['idmax']:.0f} A | {a['idend']:.1f} A | {pd:.1f} W | {a['i2td']:.1f} A2s (166) |")
            else:
                fired=a['iscrmax']>0.1; P(f"| {what} | {mach} | {ilim:g} A | {b['railmax']:.1f} V | {a['railmax']:.2f} V | {a['railend']:.2f} V | "+(f"SCR {a['iscrmax']:.0f} A | {a['iscrend']:.1f} A | {a['pscrend']:.1f} W | {a['i2tscr']:.1f} A2s (72) |" if fired else "not fired: the limit holds the rail | | | |"))
                if fired: heat[ilim]=max(heat.get(ilim,0),a['pscrend'])
    P(""); P("The diode's I2t rating is its 200 A half-sine surge over 8.3 ms; the SCR's is the datasheet's, 10 ms. The SCR's peak is the machine's own capacitors emptying into it, over in a tenth of a millisecond; the datasheet's surge rating is 120 A for 10 ms.")
    P(""); P("## Heat: arithmetic on the datasheets, not simulation"); P("")
    P("The SCR stands in free air at 60 K/W (junction to ambient, datasheet), 125 degrees maximum. Room at 25 degrees. The polyfuse holds 1.5 A for ever, trips at 3 A in its own time, and at 7.5 A within 23 s (datasheet).")
    P(""); P("| Supply's limit | Heat in the SCR | Its junction in free air, left on | With a clip-on heatsink of 20 K/W | What ends it |"); P("|---|---|---|---|---|")
    for ilim,pd in sorted(heat.items()):
        P(f"| {ilim:g} A | {pd:.1f} W | {25+pd*60:.0f} degrees{'' if 25+pd*60<=125 else ' (over its 125)'} | {25+pd*(1.3+1.0+20):.0f} degrees{'' if 25+pd*22.3<=125 else ' (over its 125)'} | {'nothing: the supply holds its limit for as long as it is left on' if ilim<=1.5 else 'the polyfuse, if it trips: at 3 A it may hold for minutes' if ilim<=3 else 'the polyfuse, within seconds (23 s at 7.5 A at the longest); a TO-220 without a heatsink warms about 15 degrees a second at this power'} |")
    P(""); P("So: with the supply's limit at 1.5 A, as `docs/bring-up.md` sets it, the SCR holds a fault for as long as it takes to notice, without a heatsink. With the limit left at 3 A or more the SCR in free air overheats before the polyfuse is sure to have tripped; an SCR that dies of heat dies shorted as a rule, which still holds the rail down, but it is then a part to replace. A clip-on TO-220 heatsink covers the 3 A case and the seconds of the 10 A case.")
    os.makedirs(os.path.join(HERE,'results'),exist_ok=True); open(os.path.join(HERE,'results','crowbar.md'),'w').write('\n'.join(W)+'\n'); print('\n'.join(W))
