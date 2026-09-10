"""Generate boards/05-clock (KiCad project) from clock.py plus the RC parts, pot, switch and jumper. Run from sim/."""
import os
import ksch, clock, bus, frame
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','05-clock')
PROJECT='clock'
R_FIX='100k'; C_FAST='47n'; C_SLOW='2.2u'; R_POT='1M'

def board_frame(w,used):
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",26,14,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G); w.at(c1,118,6,270); w.at(c2,124,6,270); frame.cap_gnd(w,118,6,2.5); frame.cap_gnd(w,124,6,2.0)
    frame.holes(w,x+46*G,y-8*G,4)

def main():
    d=clock.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True); root_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid); w.n['RV']=1
    w.T("NIBBLE BOARD 05 - CLOCK: RC oscillator with a speed knob, RUN/STEP switch, halt, power-on reset",10*G,6*G,3.5,True)
    w.T(f"{d.ntransistors()+2} transistors, {d.nresistors()+9} resistors, {d.nleds()} LEDs, one pot, one switch, one jumper.\n"
        "RUN: the switch puts 10k from +5V on CLK and the oscillator pulls CLK low for half of each cycle, or for as long as HLT is high.\n"
        "STEP: the switch is open and the pull-down transistor is held off; the front panel's CLK button owns the line, one edge per press.\n"
        f"Speed: a Schmitt-trigger RC oscillator, {R_FIX} + the pot from SA to X, {C_FAST} on X: about 500 Hz down to 40 Hz; the SLOW jumper adds {C_SLOW} for 10 Hz down to 0.8 Hz.\n"
        "Power-on reset: 2.2 uF charging through 100k into a Schmitt trigger holds RST high for a tenth of a second after power-up, so the machine starts at address 0 without touching the panel.",10*G,16*G,1.6)
    used={'HLT','CLK','RST'}
    board_frame(w,used)
    cols=14; w.PCB_COL=12.7
    yend=w.layout(d.gates,clock.GROUP_TITLES,10*G,60*G,cols,pcb_origin=(8.0,22.0),pcb_cols=6)
    # ---- the analogue parts, drawn by hand ----
    y=yend+10*G; x=14*G
    w.T("SCHMITT TRIGGER: Q1 (gate X) and Q2 (gate = Q1's drain) share RS = 1k.  Q2 on: source at 0.45 V (RD2 10k); Q1 on: source at 0.1 V (RD1 47k).  VD2, Q2's drain, is the output: 0.5 V with X low, 5 V with X high.",x-4*G,y-8*G,1.6,True)
    # Q1
    q1=w.Q(x+8*G,y); w.at(q1,90,80,0); w.L('X',x+2*G,y,180,'input'); w.W(x+2*G,y,x+6*G,y)
    w.W(x+9*G,y-2*G,x+9*G,y-3*G); w.J(x+9*G,y-3*G); w.at(w.R("47k",x+9*G,y-4.5*G),96,68,270); w.W(x+9*G,y-6*G,x+9*G,y-7*G); w.PW('+5V',x+9*G,y-7*G)
    w.W(x+9*G,y+2*G,x+9*G,y+3*G); w.J(x+9*G,y+3*G)                                   # source node VS
    # Q2, gate from Q1's drain
    q2=w.Q(x+20*G,y); w.at(q2,102,80,0); w.W(x+9*G,y-3*G,x+14*G,y-3*G); w.W(x+14*G,y-3*G,x+14*G,y); w.W(x+14*G,y,x+18*G,y)
    w.W(x+21*G,y-2*G,x+21*G,y-3*G); w.J(x+21*G,y-3*G); w.at(w.R("10k",x+21*G,y-4.5*G),108,68,270); w.W(x+21*G,y-6*G,x+21*G,y-7*G); w.PW('+5V',x+21*G,y-7*G)
    w.W(x+21*G,y-3*G,x+24*G,y-3*G); w.L('VD2',x+24*G,y-3*G,0,'output')
    w.W(x+21*G,y+2*G,x+21*G,y+3*G); w.W(x+9*G,y+3*G,x+21*G,y+3*G); w.W(x+21*G,y+3*G,x+24*G,y+3*G); w.L('VS',x+24*G,y+3*G,0,'output')
    # RS from VS to GND
    w.W(x+9*G,y+3*G,x+9*G,y+4*G); w.at(w.R('1k',x+9*G,y+5.5*G),90,98,270); w.W(x+9*G,y+7*G,x+9*G,y+8*G); w.PW('GND',x+9*G,y+8*G)
    # timing: SA -> R_FIX -> RT -> pot -> X; C on X; SLOW jumper adds C_SLOW
    y+=14*G
    w.T(f"TIMING: SA -> {R_FIX} + pot -> X, {C_FAST} from X to GND; the SLOW jumper adds {C_SLOW}.  X swings only between the two trip points, about half a volt around Vth.",x-4*G,y-6*G,1.6,True)
    w.L('SA',x,y,180,'input'); w.W(x,y,x+G,y); w.at(w.R(R_FIX,x+2.5*G,y,90),90,110,270); w.W(x+4*G,y,x+5*G,y); w.L('RT',x+5*G,y,0,'output')
    xp=x+10*G; w.L('RT',xp,y-3*G,90,'input'); w.W(xp,y-3*G,xp,y-1.5*G)
    pv=w.symbol("Device","R_Potentiometer",w.ref('RV'),R_POT,xp,y,0,('1','2','3'),"Potentiometer_THT:Potentiometer_Alpha_RD901F-40-00D_Single_Vertical",[("Description","Potentiometer",True)],sim=False)
    w.at(pv,112,100,0); w.label("SPEED",108,95,1.5)
    w.W(xp+1.5*G,y,xp+2*G,y); w.W(xp+2*G,y,xp+2*G,y+2*G); w.W(xp,y+1.5*G,xp,y+2*G); w.W(xp,y+2*G,xp+2*G,y+2*G); w.J(xp,y+2*G)   # wiper tied to the low end: a two-terminal variable resistor
    w.W(xp,y+2*G,xp,y+3*G); w.L('X',xp,y+3*G,270,'output')
    w.T("In the simulation the pot is shorted (RT to X): the fastest setting, about 500 Hz.",x-4*G,y+6*G,1.27)
    xc=x+18*G; w.L('X',xc,y-3*G,90,'input'); w.W(xc,y-3*G,xc,y-1.5*G); w.at(w.C(C_FAST,xc,y),96,110,270); w.W(xc,y+1.5*G,xc,y+3*G); w.PW('GND',xc,y+3*G)
    xj=xc+8*G; jp=w.pinheader(2,xj,y-4*G,"SLOW"); w.at(jp,102,110,0); w.label("SLOW",99,106,1.0)     # Conn_01x02: pin 1 at (xj-2G, y-4G), pin 2 at (xj-2G, y-3G)
    w.W(xj-2*G,y-4*G,xj-4*G,y-4*G); w.L('X',xj-4*G,y-4*G,180,'input')
    w.W(xj-2*G,y-3*G,xj-3*G,y-3*G); w.W(xj-3*G,y-3*G,xj-3*G,y-1.5*G); w.at(w.C(C_SLOW,xj-3*G,y,True),108,110,270); w.W(xj-3*G,y+1.5*G,xj-3*G,y+3*G); w.PW('GND',xj-3*G,y+3*G)
    # RUN switch and the CLK pull-up
    y2=y+12*G
    w.T("RUN / STEP: the switch closes +5V onto RUNSW (1 Meg pull-down); a diode and 10k from RUNSW to CLK are the clock's pull-up, present only in RUN",x-4*G,y2-4*G,1.6,True)
    sw=w.dipswitch(1,x+3*G,y2,"RUN"); w.at(sw,96,124,0); w.label("RUN",93,120,1.0)
    w.W(x,y2,x-2*G,y2); w.PW('+5V',x-2*G,y2); w.W(x+6*G,y2,x+8*G,y2); w.J(x+8*G,y2); w.L('RUNSW',x+8*G,y2,0,'output')
    w.W(x+8*G,y2,x+8*G,y2+G); w.at(w.R('1Meg',x+8*G,y2+2.5*G),90,132,270); w.W(x+8*G,y2+4*G,x+8*G,y2+5*G); w.PW('GND',x+8*G,y2+5*G)
    w.W(x+8*G,y2,x+9*G,y2); w.at(w.diode(x+10.5*G,y2,180),108,124,0); w.W(x+12*G,y2,x+13*G,y2)          # diode: in STEP the 10k must not pull CLK down against the panel's button
    w.at(w.R('10k',x+14.5*G,y2,90),96,132,270); w.W(x+16*G,y2,x+17*G,y2); w.L('CLK',x+17*G,y2,0,'bidirectional')
    # power-on reset
    y3=y2+10*G
    w.T("POWER-ON RESET: POR charges through 100k into 2.2 uF; 100k into PN with 1 Meg from PB (hysteresis); PA (high while the capacitor is still low) drives RST through 10k and a diode",x-4*G,y3-6*G,1.6,True)
    w.PW('+5V',x,y3-3*G); w.W(x,y3-3*G,x,y3-2.5*G); w.at(w.R('100k',x,y3-G),102,132,270); w.W(x,y3+0.5*G,x,y3+G); w.J(x,y3+G); w.L('POR',x,y3+G,0,'output')
    w.W(x,y3+G,x,y3+2*G); w.at(w.C('2.2u',x,y3+3.5*G,True),108,132,270); w.W(x,y3+5*G,x,y3+6*G); w.PW('GND',x,y3+6*G)
    xs=x+16*G; w.L('POR',xs,y3,180,'input'); w.W(xs,y3,xs+G,y3); w.at(w.R('100k',xs+2.5*G,y3,90),120,132,270); w.W(xs+4*G,y3,xs+6*G,y3); w.J(xs+6*G,y3); w.L('PN',xs+6*G,y3,0,'output')
    w.W(xs+6*G,y3,xs+6*G,y3-G); w.at(w.R('1Meg',xs+6*G,y3-2.5*G),126,132,270); w.W(xs+6*G,y3-4*G,xs+6*G,y3-5*G); w.L('PB',xs+6*G,y3-5*G,90,'input')
    xr=x+30*G; w.L('PA',xr,y3,180,'input'); w.W(xr,y3,xr+G,y3); w.at(w.R('10k',xr+2.5*G,y3,90),114,132,270); w.W(xr+4*G,y3,xr+5*G,y3)
    w.at(w.diode(xr+6.5*G,y3,180),102,116,0); w.W(xr+8*G,y3,xr+9*G,y3); w.L('RST',xr+9*G,y3,0,'output')
    BW,BH=136,160
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE CLOCK",10,BH-8,1.8)],hide_refs=['Q','R']))
    W=10*G+cols*w.CELL_W+30*G; H=y3+14*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"tiles",w.pcb_extent)

if __name__=='__main__': main()
