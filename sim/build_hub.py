"""Board 07: bus hub. Power entry, bus pull-ups, M-line pull-downs, eight identical 64-pin headers, no logic."""
import os, ksch, frame, bus
G=ksch.G; OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','07-hub'); PROJECT='hub'
N_HEADERS=8
def main():
    os.makedirs(OUT,exist_ok=True); root=ksch.U()
    w=ksch.Writer(PROJECT,root)
    w.T("NIBBLE BOARD 07 - BUS HUB: power entry, the four bus pull-ups, the eight M-line pull-downs, and one 64-pin header per board",10*G,6*G,3.5,True)
    w.T(f"No logic on this board.  {N_HEADERS} identical headers wired pin-for-pin; every board plugs in with a straight 64-way ribbon cable (docs/bus-header.md).\n"
        "Power: USB-B 5 V through a 750 mA polyfuse (the USB plug is the power switch).  The BUS0#..BUS3# pull-ups (10k) live here and nowhere else.\n"
        "The M0..M7 pull-downs (1Meg) also live here: the program memory boards diode-OR onto the M lines, so an unselected page leaves them floating and the hub reads them as 0 (D019, D021).\n"
        "Bulk capacitance for the whole machine, a power LED, and test loops on every bus line for a logic analyser.",10*G,14*G,1.6)
    # power entry: USB_B -> polyfuse -> switch -> +5V
    x,y=16*G,30*G
    w.at(w.symbol("Connector","USB_B",w.ref('J'),"USB_B",x,y,0,('1','2','3','4','SH'),"Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal",[("Description","USB-B receptacle, power only",True)],sim=False),18,14,90)
    w.W(x+3*G,y-2*G,x+5*G,y-2*G); w.L('VBUS',x+5*G,y-2*G,0,'output')
    w.body+=f'\t(no_connect\n\t\t(at {ksch.f(x+3*G)} {ksch.f(y)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
    w.body+=f'\t(no_connect\n\t\t(at {ksch.f(x+3*G)} {ksch.f(y+G)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
    w.W(x,y+4*G,x,y+5*G); w.PW('GND',x,y+5*G); w.W(x-G,y+4*G,x-G,y+5*G); w.W(x-G,y+5*G,x,y+5*G)
    fx=x+12*G
    w.L('VBUS',fx,y-4*G,180,'input'); w.W(fx,y-4*G,fx,y-3*G)
    w.at(w.symbol("Device","Polyfuse",w.ref('F'),"750mA",fx,y-1.5*G,0,('1','2'),"Fuse:Fuse_BelFuse_0ZRE0075FF_L11.5mm_W4.8mm",[("Description","resettable fuse",True)],sim=False),34,8,0); w.label("750mA",32,4,1.0)
    w.W(fx,y,fx,y+G); w.W(fx,y+G,fx+4*G,y+G); w.W(fx+4*G,y+G,fx+4*G,y-2*G); w.PW('+5V',fx+4*G,y-2*G)
    w.W(fx+4*G,y+G,fx+8*G,y+G); w.pwr_flag(fx+8*G,y+G)
    # power LED
    lx=fx+22*G
    w.PW('+5V',lx,y-4*G); w.W(lx,y-4*G,lx,y-3*G); w.at(w.R('1k',lx,y-1.5*G),46,6,270); w.W(lx,y,lx,y+0.5*G); w.at(w.LED(lx,y+2*G),50,8,90); w.label("PWR",53,7,1.0); w.W(lx,y+3.5*G,lx,y+5*G); w.PW('GND',lx,y+5*G); w.T("power",lx+1.5*G,y+2*G,1.0)
    # bulk + decoupling
    c1,c2=frame.decoupling(w,lx+8*G,y,values=(('100n',False),('100u',True))); w.at(c1,57,6,270); w.at(c2,62,7,270)
    # bus pull-ups
    px=lx+24*G
    w.T("Bus pull-ups (the only ones in the machine)",px-2*G,y-6*G,1.27)
    for i in range(4):
        xx=px+i*5*G; w.PW('+5V',xx,y-4*G); w.W(xx,y-4*G,xx,y-3*G); w.at(w.R('10k',xx,y-1.5*G),68+i*4,6,270); w.W(xx,y,xx,y+2*G); w.L(f'BUS{i}#',xx,y+2*G,270,'bidirectional')
    w.label("BUS PULL-UPS",66,3,1.0)
    # M-line pull-downs (1Meg): the memory boards drive M through diodes and only ever pull high
    mx=px+24*G
    w.T("M-line pull-downs (the memory boards only pull high)",mx-2*G,y-6*G,1.27)
    for i in range(8):
        xx=mx+i*4*G; w.L(f'M{i}',xx,y-4*G,90,'input'); w.W(xx,y-4*G,xx,y-3*G); w.at(w.R('1Meg',xx,y-1.5*G),86+i*4,6,270); w.W(xx,y,xx,y+2*G); w.PW('GND',xx,y+2*G)
    w.label("M PULL-DOWNS 1Meg",84,3,1.0)
    frame.gnd_bar(w,86,86+7*4,6+5.08,join=(114,13.6)); w.vias.append(('GND',114,13.6))
    # test loops on bus lines + CLK
    tx=mx+36*G
    w.T("Test loops",tx-2*G,y-6*G,1.27)
    for k,n in enumerate(['BUS0#','BUS1#','BUS2#','BUS3#','CLK','RST']):
        xx=tx+k*5*G; w.at(w.testpoint(n,xx,y),120+(k%3)*6,7+(k//3)*6,0); w.label(n.replace("#",""),117.5+(k%3)*6,11.2+(k//3)*6,0.8); w.W(xx,y,xx,y+2*G); w.L(n,xx,y+2*G,270,'input')
    frame.holes(w,tx+34*G,y,4)
    # headers: all signals connected
    used=set(s for s in bus.PINS.values() if s not in ('+5V','GND'))
    hy=70*G; BW,BH=142,22+31*2.54+14   # headers run from y=22 to the last pin row at y=22+78.74; labels and margin below
    HX0,HP,HY0=12,15,22; ylast=HY0+31*2.54
    for k in range(N_HEADERS):
        hx=16*G+k*22*G; px=HX0+k*HP
        w.T(f"slot {k+1}",hx-4*G,hy-16*G,1.6,True)
        j=frame.bus_header(w,hx,hy,used); w.at(j,px,HY0,0); w.label(f"SLOT {k+1}",px-3,107,1.2)
        # power pre-routes per header (rot 0: pin n at (px+((n-1)%2)*2.54, HY0+((n-1)//2)*2.54)): GND 4-6-8 down the second column,
        # pin 64 and pin 63 stubs to the ground via / the bottom +5V bar
        w.rails.append(('GND','F.Cu',px+2.54,HY0+2.54,px+2.54,HY0+3*2.54,0.5))
        w.rails.append(('GND','F.Cu',px+2.54,ylast,px+2.54,ylast+2.5,0.5)); w.vias.append(('GND',px+2.54,ylast+2.5))
        w.rails.append(('+5V','F.Cu',px,ylast,px,ylast+3.8,0.5))
    xl=HX0+(N_HEADERS-1)*HP+2.54
    w.rails.append(('+5V','F.Cu',6,HY0,xl,HY0,0.8))                 # +5V bar through pins 1 and 2 of every header
    w.rails.append(('GND','F.Cu',HX0,HY0+2.54,xl,HY0+2.54,0.8))     # GND bar through pins 3 and 4
    w.rails.append(('+5V','F.Cu',6,ylast+3.8,HX0+(N_HEADERS-1)*HP,ylast+3.8,0.8))   # bottom +5V bar through the pin-63 stubs
    w.rails.append(('+5V','B.Cu',6,HY0,6,ylast+3.8,0.8)); w.vias.append(('+5V',6,HY0)); w.vias.append(('+5V',6,ylast+3.8))   # left link between the two bars
    W=16*G+N_HEADERS*22*G+10*G; H=hy+24*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE BUS HUB",BW-44,BH-3.2,1.5)],rules=dict(track=0.2,clearance=0.15)))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT)
if __name__=='__main__': main()
