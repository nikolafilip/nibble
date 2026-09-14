"""Generate cards/coupon (KiCad project) from coupon.py: the gate coupon as a 100 x 100 card, powered from the bus header
(docs/cards.md). Run from sim/:  python3 build_coupon_card.py"""
import os, ksch, frame, coupon
G=ksch.G; OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','cards','coupon'); PROJECT='coupon'
def main():
    d=coupon.build(); pr=[p for p in d.check() if not p.startswith('TP_FO10')]; assert not pr, pr   # 10 loads on purpose
    os.makedirs(OUT,exist_ok=True); root=ksch.U(); tbu=ksch.U()
    w=ksch.DenseWriter(PROJECT,root); w.LIB_PREFIX='${KIPRJMOD}/../../lib'
    w.T("NIBBLE CARD COUPON: the 2N7000 + 47k cell in copper, measured before any card is trusted",10*G,6*G,3.5,True)
    w.T(f"{d.ntransistors()} transistors, 100 x 100 mm (docs/cards.md).  Power from the bus header (the hub, or 5 V on pins 1-2 and ground on 3-4; no other bus line is used).\n"
        "Drive IN, N1, N2, N3 from the 4-pin header (each has a 1Meg pull-down, so open = 0).\n"
        "Measure at the test loops: TP_RING period (gate delay = period / 10), TP_FO1 vs TP_FO10 rise time (fan-out 1 vs 10), TP_NAND / TP_NOR output low\n"
        "with all three inputs high, TP_BUS with the hub-style 10k pull-up, supply current with everything low.  Fill the numbers into docs/gate-cell.md.",10*G,14*G,1.6)
    x2=14*G; y2=36*G
    j2=w.pinheader(4,x2,y2,"IN N1 N2 N3"); w.at(j2,40.0,22.0,0); w.label("IN",35.0,21.5,0.8); w.label("N1",35.0,24.0,0.8); w.label("N2",35.0,26.6,0.8); w.label("N3",35.0,29.1,0.8)
    for k,n in enumerate(['IN','N1','N2','N3']):
        py=y2-G+k*G; w.W(x2-2*G,py,x2-5*G,py); w.L(n,x2-5*G,py,180,'input')
    for k,n in enumerate(['IN','N1','N2','N3']): w.at(frame.pulldown(w,n,x2+10*G+k*4*G,y2-2*G),46.0+k*5,36.0,270)
    frame.gnd_bar(w,46.0,61.0,41.08,join=(63.5,41.08)); w.vias.append(('GND',63.5,41.08)); w.label("1Meg PULL-DOWNS",44.0,33.0,0.8)
    x3=44*G
    for k,n in enumerate(['TP_RING','TP_FO1','TP_FO10','TP_NAND','TP_NOR','TP_BUS']):
        xx=x3+k*8*G; tp=w.testpoint(n,xx,y2); w.at(tp,40.0+k*8,56.0,0); w.label(n.replace('TP_',''),37.5+k*8,60.0,0.8); w.W(xx,y2,xx,y2+2*G); w.L(n,xx,y2+2*G,270,'input')
    w.label("TEST LOOPS",40.0,52.0,0.8)
    xx=x3+52*G; w.PW('+5V',xx,y2-4*G); w.W(xx,y2-4*G,xx,y2-3*G); w.at(w.R('10k',xx,y2-1.5*G),85.0,frame.Y0-2.0,270); w.W(xx,y2,xx,y2+2*G); w.L('TP_BUS',xx,y2+2*G,270,'input'); w.T("hub pull-up",xx+G,y2-2*G,1.0)
    w.label("10k",86.5,16.5,0.8)      # pad 1 on the +5V trunk, pad 2 to TP_BUS
    cols=3
    yend=w.layout(d.gates,coupon.GROUP_TITLES,10*G,48*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=3)
    extra=frame.card_frame(w,30*G,26*G,set(),"NIBBLE  GATE COUPON")
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    w.sheet("TESTBENCH",f"{PROJECT}-testbench.kicad_sch",10*G+cols*w.CELL_W+4*G,26*G,20*G,10*G,"2",tbu)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    t=ksch.Writer(PROJECT,root,tbu)
    for k in t.n: t.n[k]=9001
    t.T("TESTBENCH: IN toggles at 1 kHz, N1..N3 are stepped through 000,100,110,111.  Excluded from the board.",10*G,6*G,2.5,True)
    t.T(".tran 0.2u 4m",10*G,14*G,1.6); t.T(".ic v(RING0)=0",10*G,17*G,1.6)
    frame.supply(t,14*G,30*G)
    x=26*G; y=30*G
    t.vsource("PULSE","y1=0 y2=5 td=100u tr=1u tf=1u tw=500u per=1m",x,y); t.W(x,y-2*G,x,y-3*G); t.L('IN',x,y-3*G,90,'output'); t.PW('GND',x,y+2*G)
    for k,(n,pw) in enumerate([('N1','0 0 0.9995m 0 1.0005m 5 4m 5'),('N2','0 0 1.9995m 0 2.0005m 5 4m 5'),('N3','0 0 2.9995m 0 3.0005m 5 4m 5')]):
        xx=x+(k+1)*9*G; t.vsource("PWL",f'pwl=\\"{pw}\\"',xx,y); t.W(xx,y-2*G,xx,y-3*G); t.L(n,xx,y-3*G,90,'output'); t.PW('GND',xx,y+2*G)
    open(os.path.join(OUT,f'{PROJECT}-testbench.kicad_sch'),'w').write(t.file(80*G,50*G))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors())
if __name__=='__main__': main()
