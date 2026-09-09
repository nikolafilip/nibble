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
