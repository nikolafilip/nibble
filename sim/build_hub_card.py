"""Generate cards/hub (KiCad project): the bus hub card (docs/cards.md, D043). Power entry (two 4 mm banana sockets, a polyfuse, a crowbar and a
reverse diode), the four bus pull-ups, the eight M-line pull-downs, test loops, and two bus headers, one per column face's ribbon, wired pin for pin. No logic.
The 64 lines are routed; ground is wired on the front as a ring and bars instead of a pour, which the lines cut to islands. Run from sim/:  python3 build_hub_card.py"""
import os, ksch, frame, bus
G=ksch.G; OUT=os.path.join(ksch.CARDS,'hub'); PROJECT='hub'
HY2=93.0                    # the second bus header along the bottom edge (rot 90 like the top one: pin 1 left, pin 2 above it)
YV1,YV2=14.0,86.0           # the +5V trunks (front) below the top header and above the bottom one
XT=90.0; XV=92.2            # the trunks end at XT; a back-side link at XV joins them and feeds the bottom header's pin 64
XG=91.0; YG1,YG2=2.0,97.5   # the ground ring on the front: a bar above the top header's pads, one below the bottom's, joined down the right edge
YB1,YB2=22.0,45.08          # ground bars: the LED and capacitors; the M pull-downs

def crowbar(w,R,bx,by,WIDE,YK):
    """D061, values from sim/tb_crowbar.py (sim/results/crowbar.md): behind the polyfuse, across +5V and GND, a 6.2 V zener into the gate of an SCR that
    shorts the rail, 100 ohm and 100 nF from the gate to ground, and a 3 A diode the other way round for crossed leads. Fires between 6.3 and 7.8 V.
    None of it is in the machine's SPICE export (sim=False), like the rest of the power entry (D052).
    Board: the SCR below the fuse's +5V pad with its tab toward the fuse (room for a clip-on heatsink above it), the loop in 2 mm copper on the front:
    fuse -> anode, cathode -> the black socket; the diode left of it between the same two tracks; the gate's three small parts right of the SCR, on
    the side of its gate pin (left of it they stood behind the cathode's track, and the router could not bring the gate across: one net open)."""
    P=lambda name,val,xx,yy,rot,foot,desc: w.symbol("Device",name,w.ref('Q' if name.startswith('Q') else 'D' if name.startswith('D') else 'R' if name=='R' else 'C'),val,xx,yy,rot,
                                                     ('1','2','3') if name.startswith('Q') else ('1','2'),foot,[("Description",desc,True)],sim=False)
    yv,yg,yq=by-6*G,by+8*G,by+G; sx=bx+14*G; xd=bx+20*G; xr,xc=bx+4*G,bx+8*G
    w.T("CROWBAR (D061): above about 6.3 to 7.8 V the zener fires the SCR, which holds the rail near 1 V until the supply is switched off; the diode takes crossed leads.\n"
        "Run the supply with its limit at 1.5 A: the SCR then holds a fault for as long as it takes to notice. At 3 A or more it wants a clip-on heatsink.",bx-4*G,by-11*G,1.4)
    w.PW('+5V',bx,yv-2*G); w.W(bx,yv-2*G,bx,yv); w.W(bx,yv,xd,yv); w.J(bx,yv); w.J(sx,yv)
    w.PW('GND',xd,yg+2*G); w.W(xd,yg,xd,yg+2*G); w.W(bx+4*G,yg,xd,yg); w.J(xd,yg); w.J(xc,yg); w.J(sx,yg)
    dz=P("D_Zener","1N4735A",bx,by-2*G,270,"Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal","zener diode 6.2 V 1.3 W")      # rot 270: K at the top, A at the bottom
    w.W(bx,by-3.5*G,bx,yv); w.W(bx,by-0.5*G,bx,yq); w.W(bx,yq,sx-1.5*G,yq); w.J(xr,yq); w.J(xc,yq)
    rg=P("R","100",xr,by+3.5*G,0,w.R_FOOT,"Resistor"); w.W(xr,yq,xr,by+2*G); w.W(xr,by+5*G,xr,yg)
    cg=P("C","100n",xc,by+3.5*G,0,w.C_FOOT,"Capacitor"); w.W(xc,yq,xc,by+2*G); w.W(xc,by+5*G,xc,yg)
    q=P("Q_SCR_KAG","BT151-500R",sx,by,0,"Package_TO_SOT_THT:TO-220-3_Vertical","SCR 12 A, TO-220: pin 1 cathode, 2 anode (and the tab), 3 gate")      # A at the top, K at the bottom, G at the left
    w.W(sx,by-1.5*G,sx,yv); w.W(sx,by+1.5*G,sx,yg)
    dr=P("D","1N5408",xd,by+G,270,"Diode_THT:D_DO-201AD_P15.24mm_Horizontal","rectifier diode 3 A, across the rail the other way round"); w.W(xd,by-0.5*G,xd,yv); w.W(xd,by+2.5*G,xd,yg)
    XA,YQ,YT=36.2,34.0,29.81          # the SCR's anode pin stands under the fuse's +5V pad (36.2, 17.9); the +5V tee at YT
    w.at(q,XA-2.54,YQ,0); w.at(dr,27.5,YT,270); w.at(dz,46.3,YT,270); w.at(rg,42.0,YK-5.08,270); w.at(cg,38.2,YK-2.5,270)
    R('+5V',XA,17.9,XA,YQ,WIDE); R('+5V',XA,YT,27.5,YT,WIDE); R('+5V',XA,YT,46.3,YT,0.8)
    R('GND',14.0+2.38,YK,42.0,YK,WIDE); R('GND',XA-2.54,YQ,XA-2.54,YK,WIDE)
    w.label("CROWBAR",28.5,50.0,1.0)

def main():
    os.makedirs(OUT,exist_ok=True); root=ksch.U()
    w=ksch.Writer(PROJECT,root)
    R=lambda net,x1,y1,x2,y2,wd=0.5,layer='F.Cu': w.rails.append((net,layer,x1,y1,x2,y2,wd))
    w.T("NIBBLE CARD HUB - BUS HUB: power entry, the four bus pull-ups, the eight M-line pull-downs, and a header for each face's ribbon",10*G,6*G,3.5,True)
    w.T("No logic on this card.  Two 64-pin headers wired pin for pin: the top one takes one column face's ribbon, the bottom one the other's (docs/cards.md, D043).\n"
        "Power: 5 V from the bench supply, its banana leads into the two 4 mm sockets (D058; no USB, D057), through a 1.5 A polyfuse (D052: the machine draws up to about 1.2 A with every LED lit).  The BUS0#..BUS3# pull-ups (10k) live here and nowhere else.\n"
        "The M0..M7 pull-downs (220k) also live here: the program cards diode-OR onto the M lines, so an unselected card leaves them floating and the hub reads them as 0 (D019, D021); 220k, not 1 Meg, so a line falls within the fetch tick against the ribbon and the cards' diodes (D048).\n"
        "Bulk capacitance for the whole machine, a power LED, and test loops on the bus lines and the clock for a logic analyser.\n"
        "Board: ground is a wired ring and bars, not a pour (the 64 lines through the card cut a pour to islands).",10*G,14*G,1.6)
    # power entry (D052, D057, D058, D063): the bench supply's banana leads into two 4 mm sockets standing on the front face, 19.05 mm apart
    # (a dual banana plug fits too), red +5V above black GND at the left edge -> polyfuse -> +5V. No USB, no terminal: the machine is bench-powered.
    x,y=16*G,30*G
    BAN="nibble:Banana_CalTest_CT3151V1_Vertical"     # Cal Test CT3151V1-2 (red), -0 (black): soldered to the board on four pins, 1.6 mm of pin behind it (the frame's rail is 12 mm
                                                      # behind the card: a panel socket's bushing, nut and tag did not clear it). lib/nibble.pretty, drawn from the maker's drawing
    red=w.symbol("Connector_Generic","Conn_01x01",w.ref('J'),"BENCH +5V",x,y,0,('1',),BAN,[("Description","4 mm banana socket, red: bench supply +5 V",True)],sim=False)
    blk=w.symbol("Connector_Generic","Conn_01x01",w.ref('J'),"BENCH GND",x,y+6*G,0,('1',),BAN,[("Description","4 mm banana socket, black: bench supply ground",True)],sim=False)
    XS,YR,YK=14.0,26.0,45.05
    w.at(red,XS,YR,0); w.at(blk,XS,YK,0)
    WIDE=2.0                  # the entry's loop carries what the supply is limited to once the crowbar has fired, until the polyfuse trips: 2 mm of copper, not 0.8
    for net,cy in (('VBUS',YR),('GND',YK)):      # a socket's four pins stand on a 4.76 mm diamond: joined round it on both faces
        P4=[(XS-2.38,cy),(XS,cy-2.38),(XS+2.38,cy),(XS,cy+2.38)]
        for k in range(4):
            for layer in ('F.Cu','B.Cu'): R(net,*P4[k],*P4[(k+1)%4],1.2,layer)
    w.W(x-2*G,y,x-5*G,y); w.L('VBUS',x-5*G,y,180,'output')
    w.W(x-2*G,y+6*G,x-5*G,y+6*G); w.PW('GND',x-5*G,y+6*G); w.W(x-5*G,y+6*G,x-5*G,y+8*G); w.pwr_flag(x-5*G,y+8*G)     # flagged as the machine's source of ground
    R('VBUS',XS+2.38,YR,20.0,YR,WIDE); R('VBUS',20.0,YR,20.0,16.0,WIDE); R('VBUS',20.0,16.0,26.0,16.0,WIDE)     # red socket to the fuse
    R('GND',XS-2.38,YK,3.0,YK,0.8); R('GND',3.0,YK,3.0,YG1,0.8)                                                  # black socket along the left edge up to the ring (nothing else lives there)
    w.label("BENCH IN",8.0,35.5,1.0); w.label("+5V",21.8,28.6,1.0); w.label("GND",21.8,48.2,1.0)
    fx=x+12*G
    w.L('VBUS',fx,y-4*G,180,'input'); w.W(fx,y-4*G,fx,y-3*G)
    fuse=w.symbol("Device","Polyfuse",w.ref('F'),"1.5A",fx,y-1.5*G,0,('1','2'),"Fuse:Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm",[("Description","resettable fuse, 1.5 A hold",True)],sim=False)
    w.at(fuse,26.0,16.0,0); w.label("1.5A",30.0,21.5,1.0)     # pad 1 (VBUS) at (26,16), pad 2 (+5V) at (36.2,17.9); the body runs 19.4 to 42.8
    w.W(fx,y,fx,y+G); w.W(fx,y+G,fx+4*G,y+G); w.W(fx+4*G,y+G,fx+4*G,y-2*G); w.PW('+5V',fx+4*G,y-2*G)
    w.W(fx+4*G,y+G,fx+8*G,y+G); w.pwr_flag(fx+8*G,y+G)
    R('+5V',36.2,17.9,36.2,YV1,0.8)                                                                           # fuse to the top +5V trunk
    # power LED, its resistor on the trunk, its cathode on the first ground bar
    lx=fx+22*G
    w.PW('+5V',lx,y-4*G); w.W(lx,y-4*G,lx,y-3*G); w.at(w.R('1k',lx,y-1.5*G),46.0,YV1,270); w.W(lx,y,lx,y+0.5*G); w.at(w.LED(lx,y+2*G),50.0,YV1+7.0,90); w.label("PWR",49.0,YV1+10.0,1.0); w.W(lx,y+3.5*G,lx,y+5*G); w.PW('GND',lx,y+5*G); w.T("power",lx+1.5*G,y+2*G,1.0)
    R('GND',50.0,YV1+7.0,50.0,YB1)
    # bulk + decoupling, on the trunk, grounds to the first bar
    c1,c2=frame.decoupling(w,lx+8*G,y,values=(('100n',False),('100u',True))); w.at(c1,57.0,YV1,270); w.at(c2,62.0,YV1,270)
    R('GND',57.0,YV1+2.5,57.0,YB1); R('GND',62.0,YV1+2.5,62.0,YB1); R('GND',50.0,YB1,XG,YB1)
    # bus pull-ups, top pad on the trunk
    px=lx+24*G
    w.T("Bus pull-ups (the only ones in the machine)",px-2*G,y-6*G,1.27)
    for i in range(4):
        xx=px+i*5*G; w.PW('+5V',xx,y-4*G); w.W(xx,y-4*G,xx,y-3*G); w.at(w.R('10k',xx,y-1.5*G),68.0+i*4,YV1,270); w.W(xx,y,xx,y+2*G); w.L(f'BUS{i}#',xx,y+2*G,270,'bidirectional')
    w.label("BUS PULL-UPS 3 2 1 0",66.0,YV1+7.0,0.8)
    # M-line pull-downs (220k) in a row below, ground pads on the second bar
    mx=px+24*G; RY=YB2-5.08
    w.T("M-line pull-downs (the program cards only pull high)",mx-2*G,y-6*G,1.27)
    for i in range(8):
        xx=mx+i*4*G; w.L(f'M{i}',xx,y-4*G,90,'input'); w.W(xx,y-4*G,xx,y-3*G); w.at(w.R('220k',xx,y-1.5*G),50.0+i*5,RY,270); w.W(xx,y,xx,y+2*G); w.PW('GND',xx,y+2*G)
    R('GND',50.0,YB2,XG,YB2)
    w.label("M PULL-DOWNS 220k  0 .. 7",50.0,RY-2.5,0.8)
    # test loops on bus lines + CLK, RST
    tx=mx+36*G; TY=60.0
    w.T("Test loops",tx-2*G,y-6*G,1.27)
    for k,n in enumerate(['BUS0#','BUS1#','BUS2#','BUS3#','CLK','RST']):
        xx=tx+k*5*G; w.at(w.testpoint(n,xx,y),30.0+k*8,TY,0); w.label(n.replace("#",""),28.0+k*8,TY+4.0,0.8); w.W(xx,y,xx,y+2*G); w.L(n,xx,y+2*G,270,'input')
    w.label("TEST LOOPS",30.0,TY-3.5,0.8)
    # an empty spot for a capacitor from RST to ground, beside the RST loop (D062, bring-up section 9): the simulation says RST picks up 0.3 to 0.4 V
    # from BUS1# on the ribbon, under the 0.6 V it may; if the scope says more, a 2.2 nF disc goes here. Do not populate: pads on the board, nothing
    # in the parts list or in the simulation (the deck is the one the gates ran)
    cx=tx+6*5*G
    w.L('RST',cx,y-4*G,90,'input'); w.W(cx,y-4*G,cx,y-3*G)
    crst=w.symbol("Device","C",w.ref('C'),"2.2n",cx,y-1.5*G,0,('1','2'),w.C_FOOT,[("Description","capacitor RST to ground: fit only if the scope shows over 0.6 V on RST (bring-up 9)",True)],dnp=True)
    w.W(cx,y,cx,y+2*G); w.PW('GND',cx,y+2*G); w.T("fit if needed",cx+1.5*G,y-1.5*G,1.0)
    w.at(crst,78.0,TY,0); R('GND',80.5,TY,XG,TY)      # pad 1 (RST) at 78, pad 2 (GND) at 80.5, wired across to the ring
    w.label("C-RST",76.5,TY-3.5,1.0); w.label("FIT IF NEEDED",73.5,TY+4.0,1.0)
    frame.holes(w,tx+34*G,y,2)
    # the two bus headers: every line on both
    used=set(s for s in bus.PINS.values() if s not in ('+5V','GND'))
    hy=70*G
    for k,(hyy,yv) in enumerate([(frame.HY,YV1),(HY2,YV2)]):
        w.T(f"face {'A' if k==0 else 'B'} ribbon",30*G+k*22*G-4*G,hy-16*G,1.6,True)
        j=frame.bus_header(w,30*G+k*22*G,hy,used,through=True); w.at(j,frame.HX,hyy,90,'B'); w.silk+=[tuple(l) for l in bus.header_labels(frame.HX,hyy)]
        w.label("BUS  FACE A" if k==0 else "BUS  FACE B  (pin 1 left)",3.0 if k==0 else frame.HX+30,19.0 if k==0 else 84.0,1.0)      # A's short, left of the fuse's body (x 19 to 43) and above the red socket
        # the pins as the header on the back numbers them (D059, bus.hole): the odd pins are the upper row
        (x1,y1),(x2,y2),(x3,y3),(x4,y4),(x7,y7),(x63,y63),(x64,y64)=[bus.hole(frame.HX,hyy,n) for n in (1,2,3,4,7,63,64)]
        R('+5V',x2,y2,x1,y1); R('GND',x3,y3,x7,y7); R('GND',x4,y4,x3,y3)      # pins 1-2 joined; 3-5-7 along the upper row; 3-4
        R('+5V',frame.HX,yv,XT,yv,0.8)                                            # the trunk
        if k==0:    # top: +5V pins 2 and 64 straight down to the trunk; ground pins 3 and 63 up to the bar above the pads
            R('+5V',x2,y2,x2,yv); R('+5V',x64,y64,x64,yv)
            R('GND',x3,y3,x3,YG1); R('GND',x63,y63,x63,YG1)
        else:       # bottom: pin 1 (above pin 2) up to the trunk; pin 64 down, then round the back to the right-edge link; ground pin 4 down to the bar, pin 63 sideways to the ring
            R('+5V',x1,y1,x1,yv)
            R('+5V',x64,y64,x64,95.5); w.vias.append(('+5V',x64,95.5)); R('+5V',x64,95.5,XV,95.5,0.8,'B.Cu'); R('+5V',XV,95.5,XV,YV1,0.8,'B.Cu')
            R('GND',x4,y4,x4,YG2); R('GND',x63,y63,XG,y63)
    for yv in (YV1,YV2): R('+5V',XT,yv,XV,yv,0.8,'B.Cu'); w.vias.append(('+5V',XT,yv))      # the trunks' ends meet the back-side link
    R('GND',3.0,YG1,XG,YG1); R('GND',XG,YG1,XG,YG2); R('GND',13.17,YG2,XG,YG2)                # the ground ring (its top bar starts at the black socket's run)
    crowbar(w,R,100*G,60*G,WIDE,YK)      # last, so that every part that is in the machine's simulation keeps the reference it had (the export is the same line for line)
    # the 64 lines are the router's (through-hole pads sit on both layers, so no straight pre-route can pass the parts): no ground pour,
    # its ring and bars are wired above, so the lines cannot cut the ground into islands
    W=16*G+2*22*G+10*G; H=hy+24*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=dict(silk_big=[("NIBBLE  BUS HUB",34.0,76.0,1.5)],hide_refs=['R','D','C','J','TP','F','Q'],rules=dict(track=0.2,clearance=0.15),holes=frame.HOLES,no_pour=True,router=dict(jar='freerouting-2.4.1.jar')))      # freerouting 1.9 drops an M5 via inside the 0.35 mm-pitch bundle of the 64 bus lines (two shorts, both runs); 2.4.1 (Java 25, NIBBLE_JAVA) routes it clean
    ksch.write_project(OUT,PROJECT)
    open(os.path.join(OUT,'fp-lib-table'),'w').write('(fp_lib_table\n\t(version 7)\n\t(lib (name "nibble") (type "KiCad") (uri "${KIPRJMOD}/../../lib/nibble.pretty") (options "") (descr "Nibble\'s own footprints, drawn from makers\' drawings"))\n)\n')      # the project's own table: KiCad and kicad-cli find the sockets' footprint
    print("wrote",OUT)
if __name__=='__main__': main()
