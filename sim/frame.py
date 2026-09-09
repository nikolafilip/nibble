"""Common board frame pieces: bus header, decoupling, power flags, mounting holes, testbench supply."""
import ksch, bus
G=ksch.G

def bus_header(w,x,y,used):
    """50-pin header at (x,y); `used` = signals this board connects. Unused pins get no-connect flags. Returns ref."""
    ref=w.header(x,y)
    for pin,sig in bus.PINS.items():
        odd=pin%2==1; px=x-2*G if odd else x+3*G; py=y-12*G+((pin-1)//2)*G
        if sig in ('+5V','GND'):
            ex=px-3*G if odd else px+3*G
            w.W(px,py,ex,py); w.PW(sig,ex,py)
        elif sig in used:
            ex=px-4*G if odd else px+4*G
            w.W(px,py,ex,py); w.L(sig,ex,py,180 if odd else 0,'bidirectional' if sig.startswith('BUS') else 'input')
        else:
            w.body+=f'\t(no_connect\n\t\t(at {ksch.f(px)} {ksch.f(py)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
    return ref

def decoupling(w,x,y,values=(('100n',False),('10u',True))):
    refs=[]
    for k,(val,pol) in enumerate(values):
        xx=x+k*6*G
        w.PW('+5V',xx,y-2.5*G); w.W(xx,y-2.5*G,xx,y-1.5*G); refs.append(w.C(val,xx,y,pol)); w.W(xx,y+1.5*G,xx,y+2.5*G); w.PW('GND',xx,y+2.5*G)
    w.T("Decoupling",x-2*G,y-4*G,1.27); return refs

def cap_gnd(w,px,py,pitch):
    """A capacitor placed at (px,py) rot 270 has pad 2 (GND) at (px,py+pitch); pre-route it to a via 2.5 mm below."""
    w.rails.append(('GND','F.Cu',px,py+pitch,px,py+pitch+2.5,0.5)); w.vias.append(('GND',px,py+pitch+2.5))

def power_flags(w,x,y):
    w.PW('+5V',x,y-2.5*G); w.W(x,y-2.5*G,x,y-1.5*G); w.pwr_flag(x,y-1.5*G)
    w.PW('GND',x,y+2.5*G); w.W(x,y+2.5*G,x,y+1.5*G); w.pwr_flag(x,y+1.5*G)

def holes(w,x,y,n=4):
    for k in range(n): w.hole(x+k*5*G,y)
    w.T("Mounting holes",x-2*G,y-4*G,1.27)

def supply(t,x,y):
    """5 V DC source on a testbench sheet."""
    t.T("5 V supply (the hub board / bench supply)",x-2*G,y-6*G,1.27)
    t.vsource("DC","5",x,y); t.W(x,y-2*G,x,y-3*G); t.PW('+5V',x,y-3*G); t.W(x,y+2*G,x,y+3*G); t.PW('GND',x,y+3*G)

def pulldown(w,net,x,y,value='1Meg'):
    """net label -> resistor -> GND, vertical, label at top (x,y)."""
    w.L(net,x,y,90,'input'); w.W(x,y,x,y+G); r=w.R(value,x,y+2.5*G); w.W(x,y+4*G,x,y+5*G); w.PW('GND',x,y+5*G); return r

def header_gnd(w,hx,hy,outward,y_gnd_trunk=None):
    """Pre-route the bus header's GND pins (3,4,6,8,50) for a header placed at (hx,hy) rot 90.
    Pads: pin n at (hx+((n-1)//2)*2.54, hy-((n-1)%2)*2.54). outward=-1 if the header is at the top edge, +1 at the bottom."""
    P=lambda n:(hx+((n-1)//2)*2.54, hy-((n-1)%2)*2.54)
    (x4,y4),(x8,y8),(x3,y3),(x50,y50)=P(4),P(8),P(3),P(50)
    w.rails.append(('GND','F.Cu',x4,y4,x8,y8,0.5))        # 4-6-8 along the upper row
    w.rails.append(('GND','F.Cu',x3,y3,x4,y4,0.5))        # 3-4
    if outward<0:
        w.rails.append(('GND','F.Cu',x8,y8,x8,y8-2.5,0.5)); w.vias.append(('GND',x8,y8-2.5))
        w.rails.append(('GND','F.Cu',x50,y50,x50,y50-2.5,0.5)); w.vias.append(('GND',x50,y50-2.5))
        if y_gnd_trunk: w.rails.append(('GND','F.Cu',x3,y3,x3,y_gnd_trunk,0.5))
    else:
        w.rails.append(('GND','F.Cu',x3,y3,x3,y3+2.5,0.5)); w.vias.append(('GND',x3,y3+2.5))
        w.rails.append(('GND','F.Cu',x50,y50,x50+2.5,y50,0.5)); w.vias.append(('GND',x50+2.5,y50))

def gnd_bar(w,x1,x2,y,join=None):
    """Pre-routed GND bar on F.Cu through a row of ground pads at height y; `join`=(x,y2) adds a vertical link to another GND track."""
    w.rails.append(('GND','F.Cu',x1,y,x2,y,0.5))
    if join: w.rails.append(('GND','F.Cu',join[0],y,join[0],join[1],0.5))
