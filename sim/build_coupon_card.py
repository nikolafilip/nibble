"""Generate cards/coupon (KiCad project) from coupon.py plus the parts drawn by hand: the Schmitt pair and RC of the oscillator,
the line driver's 100 ohm / diode / 10k, the program row's diode and 220k, the input and power headers, the test loops.
The gate coupon as a 100 x 100 card (docs/cards.md). Run from sim/:  python3 build_coupon_card.py"""
import os, ksch, frame, coupon
G=ksch.G; OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','cards','coupon'); PROJECT='coupon'
INPUTS=['IN','N1','N2','N3','RST']
LOOPS=[['TP_RING','RING0','TP_FO1','TP_FO10','TP_NAND','TP_NOR','TP_BUS','TP_VTO'],['X','TP_OSC','TP_Q','TP_DRV','TP_ROM','GND','+5V']]   # two rows on the board: the gates, then the clock
# RING0 is the ring node itself (a x10 probe's 15 pF is in the simulated band): with low-threshold transistors the ring swings only to about 3 V and a
# high-threshold buffer never switches, so TP_RING can show nothing while the ring runs (tb_coupon at MIX seeds 1 and 2)
def main():
    d=coupon.build()
    for n in INPUTS: d.pulldown(n,'1Meg')       # open = 0, as the panel's lines (PD tiles)
    pr=[p for p in d.check() if not p.startswith('TP_FO10')]; assert not pr, pr   # 10 loads on purpose
    os.makedirs(OUT,exist_ok=True); root=ksch.U(); tbu=ksch.U()
    w=ksch.DenseWriter(PROJECT,root); w.LIB_PREFIX='${KIPRJMOD}/../../lib'; w.HCOL=frame.HCOL
    w.T("NIBBLE CARD COUPON: every cell of the machine in copper, measured before any card is trusted",10*G,6*G,3.5,True)
    w.T(f"{d.ntransistors()+2} transistors, 100 x 100 mm (docs/cards.md).  Power: 5 V on the 2-pin header from the bench supply (limit 300 mA),\n"
        "or the bus header (the hub; no other bus line is used).\n"
        "Drive IN, N1, N2, N3, RST from the 6-pin header (each has a 1Meg pull-down, so open = 0; RST open lets the flip-flop run).\n"
        "Measure at the test loops: RING period (gate delay = period / 10; RING0 is the ring node itself, for when the buffer's threshold is above the ring's swing),\n"
        "FO1 vs FO10 rise time (fan-out 1 vs 10),\n"
        "NAND / NOR low with all three inputs high, BUS low with the hub's 10k, X (the Schmitt trip points) and OSC (the clock card's\n"
        "oscillator, 100k + 47n), Q (the toggle flip-flop, OSC / 2; RST high holds it at 0), DRV (the D053 line driver, clip 3.3 nF on it),\n"
        "VTO (about 0.1 V above one transistor's threshold), ROM (a program row through its diode into 220k), the supply current.\n"
        "The bands to expect at each loop: sim/results/coupon_expected.md; how to read them: docs/bring-up.md section 1.",10*G,17*G,1.6)
    # ---- inputs and power (left), test loops (right of the bus header) ----
    x2=14*G; y2=36*G
    def gnd_via(px,py,dx=0.0,dy=2.5):     # a ground pad away from the tiles: a stub to its own via, so the pour need not reach under a header or between tracks
        w.rails.append(('GND','F.Cu',px,py,px+dx,py+dy,0.5)); w.vias.append(('GND',px+dx,py+dy))
    j2=w.pinheader(6,x2,y2,"IN N1 N2 N3 RST GND"); w.at(j2,58.0,19.0,0); w.label("INPUTS",56.5,15.5,0.8)     # pins descend from (58,19) at 2.54
    for k,n in enumerate(INPUTS+['GND']):
        py=y2-2*G+k*G; w.W(x2-2*G,py,x2-5*G,py); w.label(n,60.3,18.5+k*2.54,0.8)
        if n=='GND': w.PW('GND',x2-5*G,py); gnd_via(58.0,19.0+k*2.54,-2.5,0.0)      # the stub goes left: the five signal tracks leave the header on the right
        else: w.L(n,x2-5*G,py,180,'input')
    y3=y2+8*G
    jp=w.pinheader(2,x2,y3,"+5V GND"); w.at(jp,68.0,19.0,0); w.label("POWER",66.5,15.5,0.8); w.label("+5V",70.3,18.5,0.8); w.label("GND",70.3,21.04,0.8); gnd_via(68.0,21.54,-2.5,0.0)
    w.W(x2-2*G,y3,x2-5*G,y3); w.PW('+5V',x2-5*G,y3); w.W(x2-2*G,y3+G,x2-5*G,y3+G); w.PW('GND',x2-5*G,y3+G)
    w.T("Bench supply in, 5.0 V, current limit 300 mA",x2-6*G,y3-3*G,1.0)
    x3=44*G
    for r,row in enumerate(LOOPS):
        for k,n in enumerate(row):
            xx=x3+k*5*G; yy=y2+r*10*G; tp=w.testpoint(n,xx,yy); bx=58.0+k*5.0; by=78.0+r*10.0
            w.at(tp,bx,by,0); w.label(n.replace('TP_','').replace('+5V','5V'),bx-2.2,by+4.0,0.8); w.W(xx,yy,xx,yy+2*G)
            if n in ('GND','+5V'): w.PW(n,xx,yy+2*G)
            else: w.L(n,xx,yy+2*G,270,'input')
    w.label("TEST LOOPS",58.0,74.5,0.8); w.T("TEST LOOPS",x3,y2-4*G,1.0)
    xx=x3+42*G; w.PW('+5V',xx,y2-4*G); w.W(xx,y2-4*G,xx,y2-3*G); w.at(w.R('10k',xx,y2-1.5*G),88.0,frame.Y0-2.0,270); w.W(xx,y2,xx,y2+2*G); w.L('TP_BUS',xx,y2+2*G,270,'input'); w.T("hub pull-up",xx+G,y2-2*G,1.0)
    w.label("10k",89.5,16.5,0.8)      # pad 1 on the +5V trunk, pad 2 to TP_BUS
    cols=3
    yend=w.layout(d.gates,coupon.GROUP_TITLES,10*G,58*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=6)
    extra=frame.card_frame(w,30*G,34*G,set(),"NIBBLE  GATE COUPON")
    # ---- the analogue parts, drawn by hand (the clock card's oscillator, D053's driver, a program row) ----
    y=yend+10*G; x=14*G
    w.T("SCHMITT TRIGGER (the clock card's, cards/clock): Q1 (gate X) and Q2 (gate = Q1's drain) share RS = 1k.  Q2 on: source at 0.45 V (RD2 10k); Q1 on: source at 0.1 V (RD1 47k).  VD2, Q2's drain, is the output: 0.5 V with X low, 5 V with X high.",x-4*G,y-8*G,1.6,True)
    q1=w.Q(x+8*G,y); w.at(q1,72,36,0); w.L('X',x+2*G,y,180,'input'); w.W(x+2*G,y,x+6*G,y)
    w.W(x+9*G,y-2*G,x+9*G,y-3*G); w.J(x+9*G,y-3*G); w.at(w.R("47k",x+9*G,y-4.5*G),76,24,270); w.W(x+9*G,y-6*G,x+9*G,y-7*G); w.PW('+5V',x+9*G,y-7*G)
    w.W(x+9*G,y+2*G,x+9*G,y+3*G); w.J(x+9*G,y+3*G)                                   # source node VS
    q2=w.Q(x+20*G,y); w.at(q2,82,36,0); w.W(x+9*G,y-3*G,x+14*G,y-3*G); w.W(x+14*G,y-3*G,x+14*G,y); w.W(x+14*G,y,x+18*G,y)
    w.W(x+21*G,y-2*G,x+21*G,y-3*G); w.J(x+21*G,y-3*G); w.at(w.R("10k",x+21*G,y-4.5*G),84,24,270); w.W(x+21*G,y-6*G,x+21*G,y-7*G); w.PW('+5V',x+21*G,y-7*G)
    w.W(x+21*G,y-3*G,x+24*G,y-3*G); w.L('VD2',x+24*G,y-3*G,0,'output')
    w.W(x+21*G,y+2*G,x+21*G,y+3*G); w.W(x+9*G,y+3*G,x+21*G,y+3*G); w.W(x+21*G,y+3*G,x+24*G,y+3*G); w.L('VS',x+24*G,y+3*G,0,'output')
    w.W(x+9*G,y+3*G,x+9*G,y+4*G); w.at(w.R('1k',x+9*G,y+5.5*G),77,42,270); w.W(x+9*G,y+7*G,x+9*G,y+8*G); w.PW('GND',x+9*G,y+8*G); gnd_via(77,47.08,2.5,0)
    w.label("Q1",71.5,32.2,0.8); w.label("Q2",81.5,32.2,0.8); w.label("47k",77.5,26.5,0.8); w.label("10k",85.5,26.5,0.8); w.label("1k",78.5,44.5,0.8); w.label("SCHMITT",76.5,21.0,0.8)
    y+=18*G
    w.T("TIMING: SA -> 100k -> X, 47n from X to GND: the clock card at its fastest setting (its pot at zero), about 500 Hz.  X swings only between the two trip points, about half a volt around Vth.",x-4*G,y-6*G,1.6,True)
    w.L('SA',x,y,180,'input'); w.W(x,y,x+G,y); w.at(w.R('100k',x+2.5*G,y,90),58,42,0); w.W(x+4*G,y,x+6*G,y); w.J(x+6*G,y); w.L('X',x+6*G,y,0,'output')
    w.W(x+6*G,y,x+6*G,y+G); w.at(w.C('47n',x+6*G,y+2.5*G),66,42,270); w.W(x+6*G,y+4*G,x+6*G,y+5*G); w.PW('GND',x+6*G,y+5*G); gnd_via(66,44.5,0,2.5)
    w.label("100k",58.5,39.5,0.8); w.label("47n",68.7,45.8,0.8)
    y+=14*G
    w.T("LINE DRIVER (D053): DRVN (1k pull-up) through 100 ohm and a diode into TP_DRV with a 10k pull-down, as the clock card drives CLK and RST and the panel its buttons.  Clip 3.3 nF from TP_DRV to GND: the ribbon and the cards' gates.",x-4*G,y-6*G,1.6,True)
    w.L('DRVN',x,y,180,'input'); w.W(x,y,x+G,y); w.at(w.R('100',x+2.5*G,y,90),58,54,0); w.W(x+4*G,y,x+5*G,y)
    w.at(w.diode(x+6.5*G,y,180),73,54,180); w.W(x+8*G,y,x+10*G,y); w.J(x+10*G,y); w.L('TP_DRV',x+10*G,y,0,'output')
    w.W(x+10*G,y,x+10*G,y+G); w.at(w.R('10k',x+10*G,y+2.5*G),77,54,270); w.W(x+10*G,y+4*G,x+10*G,y+5*G); w.PW('GND',x+10*G,y+5*G); gnd_via(77,59.08,2.5,0)
    w.label("DRIVER",58.0,50.5,0.8); w.label("100",58.5,56.5,0.8); w.label("10k",78.5,56.5,0.8)
    y+=14*G
    w.T("PROGRAM ROW: ROW (3.3k pull-up) through a 1N4148 into TP_ROM with the hub's 220k pull-down (D048): the M line's high is 5 V less a diode drop.",x-4*G,y-6*G,1.6,True)
    w.L('ROW',x,y,180,'input'); w.W(x,y,x+5*G,y)
    w.at(w.diode(x+6.5*G,y,180),73,64,180); w.W(x+8*G,y,x+10*G,y); w.J(x+10*G,y); w.L('TP_ROM',x+10*G,y,0,'output')
    w.W(x+10*G,y,x+10*G,y+G); w.at(w.R('220k',x+10*G,y+2.5*G),77,64,270); w.W(x+10*G,y+4*G,x+10*G,y+5*G); w.PW('GND',x+10*G,y+5*G); gnd_via(77,69.08,2.5,0)
    w.label("ROM",58.0,62.5,0.8); w.label("220k",78.5,66.5,0.8)
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    w.sheet("TESTBENCH",f"{PROJECT}-testbench.kicad_sch",84*G,4*G,10*G,6*G,"2",tbu)
    W=10*G+cols*w.CELL_W+40*G; H=y+14*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    t=ksch.Writer(PROJECT,root,tbu)
    for k in t.n: t.n[k]=9001
    t.T("TESTBENCH: IN toggles at 1 kHz, N1..N3 are stepped through 000,100,110,111, RST is high for the first millisecond.  Excluded from the board; sim/tb_coupon.py is the measured bench.",10*G,6*G,2.5,True)
    t.T(".tran 0.5u 12m",10*G,14*G,1.6); t.T(".ic v(RING0)=0 v(X)=0",10*G,17*G,1.6)
    frame.supply(t,14*G,30*G)
    x=26*G; y=30*G
    t.vsource("PULSE","y1=0 y2=5 td=100u tr=1u tf=1u tw=500u per=1m",x,y); t.W(x,y-2*G,x,y-3*G); t.L('IN',x,y-3*G,90,'output'); t.PW('GND',x,y+2*G)
    for k,(n,pw) in enumerate([('N1','0 0 0.9995m 0 1.0005m 5 12m 5'),('N2','0 0 1.9995m 0 2.0005m 5 12m 5'),('N3','0 0 2.9995m 0 3.0005m 5 12m 5'),('RST','0 5 0.9995m 5 1.0005m 0 12m 0')]):
        xx=x+(k+1)*9*G; t.vsource("PWL",f'pwl=\\"{pw}\\"',xx,y); t.W(xx,y-2*G,xx,y-3*G); t.L(n,xx,y-3*G,90,'output'); t.PW('GND',xx,y+2*G)
    open(os.path.join(OUT,f'{PROJECT}-testbench.kicad_sch'),'w').write(t.file(80*G,50*G))
    ksch.write_project(OUT,PROJECT)
    print("wrote",OUT,"transistors",d.ntransistors()+2,"tiles",w.pcb_extent)
if __name__=='__main__': main()
