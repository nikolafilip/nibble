"""Generate cards/hub (KiCad project): the bus hub card (docs/cards.md, D043). Power entry, the four bus pull-ups, the
eight M-line pull-downs, test loops, and two bus headers, one per column face's ribbon, wired pin for pin. No logic.
The 64 lines are routed; ground is wired on the front as a ring and bars instead of a pour, which the lines cut to islands. Run from sim/:  python3 build_hub_card.py"""
import os, ksch, frame, bus
G=ksch.G; OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','cards','hub'); PROJECT='hub'
HY2=93.0                    # the second bus header along the bottom edge (rot 90 like the top one: pin 1 left, pin 2 above it)
YV1,YV2=14.0,86.0           # the +5V trunks (front) below the top header and above the bottom one
XT=90.0; XV=92.2            # the trunks end at XT; a back-side link at XV joins them and feeds the bottom header's pin 63
XG=91.0; YG1,YG2=2.0,97.5   # the ground ring on the front: a bar above the top header's pads, one below the bottom's, joined down the right edge
YB1,YB2=22.0,45.08          # ground bars: the LED and capacitors; the M pull-downs
P=lambda hx,hy,n:(hx+((n-1)//2)*2.54, hy-((n-1)%2)*2.54)      # pin n of a rot-90 header at (hx,hy)

def main():
    os.makedirs(OUT,exist_ok=True); root=ksch.U()
    w=ksch.Writer(PROJECT,root)
    R=lambda net,x1,y1,x2,y2,wd=0.5,layer='F.Cu': w.rails.append((net,layer,x1,y1,x2,y2,wd))
    w.T("NIBBLE CARD HUB - BUS HUB: power entry, the four bus pull-ups, the eight M-line pull-downs, and a header for each face's ribbon",10*G,6*G,3.5,True)
    w.T("No logic on this card.  Two 64-pin headers wired pin for pin: the top one takes one column face's ribbon, the bottom one the other's (docs/cards.md, D043).\n"
        "Power: USB-B 5 V through a 750 mA polyfuse (the USB plug is the power switch).  The BUS0#..BUS3# pull-ups (10k) live here and nowhere else.\n"
        "The M0..M7 pull-downs (220k) also live here: the program cards diode-OR onto the M lines, so an unselected card leaves them floating and the hub reads them as 0 (D019, D021); 220k, not 1 Meg, so a line falls within the fetch tick against the ribbon and the cards' diodes (D048).\n"
        "Bulk capacitance for the whole machine, a power LED, and test loops on the bus lines and the clock for a logic analyser.\n"
        "Board: ground is a wired ring and bars, not a pour (the 64 lines through the card cut a pour to islands).",10*G,14*G,1.6)
    # power entry: USB_B -> polyfuse -> +5V
    x,y=16*G,30*G
    usb=w.symbol("Connector","USB_B",w.ref('J'),"USB_B",x,y,0,('1','2','3','4','SH'),"Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal",[("Description","USB-B receptacle, power only",True)],sim=False)
    w.at(usb,14.0,30.0,180)      # rot 180: the socket opens 1.5 mm past the left edge; pin 1 (VBUS) at (14,30), pin 4 (GND) at (12,30), shields at (9.29, 22.73 and 34.77)
    w.W(x+3*G,y-2*G,x+5*G,y-2*G); w.L('VBUS',x+5*G,y-2*G,0,'output')
    w.body+=f'\t(no_connect\n\t\t(at {ksch.f(x+3*G)} {ksch.f(y)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
    w.body+=f'\t(no_connect\n\t\t(at {ksch.f(x+3*G)} {ksch.f(y+G)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
    w.W(x,y+4*G,x,y+5*G); w.PW('GND',x,y+5*G); w.W(x-G,y+4*G,x-G,y+5*G); w.W(x-G,y+5*G,x,y+5*G)
    R('GND',12.0,30.0,9.29,30.0); R('GND',9.29,34.77,9.29,YG1)      # USB ground and shields up to the top ground bar
    fx=x+12*G
    w.L('VBUS',fx,y-4*G,180,'input'); w.W(fx,y-4*G,fx,y-3*G)
    fuse=w.symbol("Device","Polyfuse",w.ref('F'),"750mA",fx,y-1.5*G,0,('1','2'),"Fuse:Fuse_BelFuse_0ZRE0075FF_L11.5mm_W4.8mm",[("Description","resettable fuse",True)],sim=False)
    w.at(fuse,26.0,16.0,0); w.label("750mA",24.5,21.5,1.0)     # pad 1 (VBUS) at (26,16), pad 2 (+5V) at (31.1,17.9)
    w.W(fx,y,fx,y+G); w.W(fx,y+G,fx+4*G,y+G); w.W(fx+4*G,y+G,fx+4*G,y-2*G); w.PW('+5V',fx+4*G,y-2*G)
    w.W(fx+4*G,y+G,fx+8*G,y+G); w.pwr_flag(fx+8*G,y+G)
    R('VBUS',14.0,30.0,20.0,30.0,0.8); R('VBUS',20.0,30.0,20.0,16.0,0.8); R('VBUS',20.0,16.0,26.0,16.0,0.8)     # USB pin 1 to the fuse, wide
    R('+5V',31.1,17.9,31.1,YV1,0.8)                                                                           # fuse to the top +5V trunk
    w.label("USB 5V IN",3.0,18.5,1.0)
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
    frame.holes(w,tx+34*G,y,2)
    # the two bus headers: every line on both
    used=set(s for s in bus.PINS.values() if s not in ('+5V','GND'))
    hy=70*G
    for k,(hyy,yv) in enumerate([(frame.HY,YV1),(HY2,YV2)]):
        w.T(f"face {'A' if k==0 else 'B'} ribbon",30*G+k*22*G-4*G,hy-16*G,1.6,True)
        j=frame.bus_header(w,30*G+k*22*G,hy,used,through=True); w.at(j,frame.HX,hyy,90); w.label("1",frame.HX-7.0,hyy+0.9,1.0)
        w.label(f"BUS  FACE {'A' if k==0 else 'B'}  (pin 1 left)",frame.HX+3.0 if k==0 else frame.HX+30,12.0 if k==0 else 84.0,1.0)
        (x1,y1),(x2,y2),(x3,y3),(x4,y4),(x8,y8),(x63,y63),(x64,y64)=[P(frame.HX,hyy,n) for n in (1,2,3,4,8,63,64)]
        R('+5V',x1,y1,x2,y2); R('GND',x4,y4,x8,y8); R('GND',x3,y3,x4,y4)      # pins 1-2 joined; 4-6-8 along the even row; 3-4
        R('+5V',frame.HX,yv,XT,yv,0.8)                                            # the trunk
        if k==0:    # top: +5V pins 1 and 63 straight down to the trunk; ground pins 4 and 64 up to the bar above the pads
            R('+5V',x1,y1,x1,yv); R('+5V',x63,y63,x63,yv)
            R('GND',x4,y4,x4,YG1); R('GND',x64,y64,x64,YG1)
        else:       # bottom: pin 2 (above pin 1) up to the trunk; pin 63 down, then round the back to the right-edge link; ground pin 3 down to the bar, pin 64 sideways to the ring
            R('+5V',x2,y2,x2,yv)
            R('+5V',x63,y63,x63,95.5); w.vias.append(('+5V',x63,95.5)); R('+5V',x63,95.5,XV,95.5,0.8,'B.Cu'); R('+5V',XV,95.5,XV,YV1,0.8,'B.Cu')
            R('GND',x3,y3,x3,YG2); R('GND',x64,y64,XG,y64)
    for yv in (YV1,YV2): R('+5V',XT,yv,XV,yv,0.8,'B.Cu'); w.vias.append(('+5V',XT,yv))      # the trunks' ends meet the back-side link
    R('GND',9.29,YG1,XG,YG1); R('GND',XG,YG1,XG,YG2); R('GND',13.17,YG2,XG,YG2)              # the ground ring
    # the 64 lines are the router's (through-hole pads sit on both layers, so no straight pre-route can pass the parts): no ground pour,
    # its ring and bars are wired above, so the lines cannot cut the ground into islands
    W=16*G+2*22*G+10*G; H=hy+24*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=dict(silk_big=[("NIBBLE  BUS HUB",34.0,76.0,1.5)],hide_refs=['R','D','C','J','TP','F'],rules=dict(track=0.2,clearance=0.15),holes=frame.HOLES,no_pour=True))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT)
if __name__=='__main__': main()
