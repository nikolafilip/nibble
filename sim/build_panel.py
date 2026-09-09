"""Generate boards/06-panel from panel.py."""
import os, ksch, frame, bus, panel
G=ksch.G; OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','06-panel'); PROJECT='panel'

def dip8_levels(w,x,y,names,title):
    """DIP-8: left pins to +5V, right pins through 10k to the named lines. None = spare (no-connect)."""
    w.dipswitch(8,x,y,title)
    w.W(x-3*G,y-4*G,x-3*G,y+3*G); w.W(x-3*G,y-4*G,x-3*G,y-6*G); w.PW('+5V',x-3*G,y-6*G)
    for i in range(8):
        py=y-4*G+i*G
        w.J(x-3*G,py) if i not in (0,7) else None
        w.W(x-3*G,py,x-3*G,py)
        n=names[i]
        if n is None:
            w.body+=f'\t(no_connect\n\t\t(at {ksch.f(x+3*G)} {ksch.f(py)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'; continue
        w.W(x+3*G,py,x+4*G,py); w.R('10k',x+5.5*G,py,90); w.W(x+7*G,py,x+8*G,py); w.L(n,x+8*G,py,0,'output')
    # left pins: wire stubs from pins to the bus wire (pins are at x-3G already on the wire)
def dip4_data(w,x,y):
    w.dipswitch(4,x,y,"DATA (closed = 1 on the bus)")
    w.W(x-3*G,y-2*G,x-3*G,y+G); w.W(x-3*G,y+G,x-3*G,y+3*G); w.PW('GND',x-3*G,y+3*G)
    for i in range(4):
        py=y-2*G+i*G
        if i not in (3,): w.J(x-3*G,py) if i!=0 else None
        w.W(x+3*G,py,x+5*G,py); w.L(panel.DATA_SW[i],x+5*G,py,0,'bidirectional')
def button(w,x,y,name):
    """+5V -> button -> 10k -> X (1u, 220k to GND) -> 100k -> N (label name_N); name_S2 -> 1Meg -> N; name_S2 -> 10k -> diode -> name"""
    w.T(name+" button",x-4*G,y-4*G,1.27,True)
    w.PW('+5V',x-4*G,y-2*G); w.W(x-4*G,y-2*G,x-4*G,y); w.W(x-4*G,y,x-2*G,y)
    w.button(x,y,name)
    w.W(x+2*G,y,x+3*G,y); w.R('10k',x+4.5*G,y,90); w.W(x+6*G,y,x+8*G,y)
    xx=x+8*G; w.J(xx,y)
    w.W(xx,y,xx,y+G); w.C('1u',xx,y+2.5*G,True); w.W(xx,y+4*G,xx,y+5*G); w.PW('GND',xx,y+5*G)
    w.W(xx,y,xx+3*G,y); w.J(xx+3*G,y); w.W(xx+3*G,y,xx+3*G,y+G); w.R('220k',xx+3*G,y+2.5*G); w.W(xx+3*G,y+4*G,xx+3*G,y+5*G); w.PW('GND',xx+3*G,y+5*G)
    w.W(xx+3*G,y,xx+4*G,y); w.R('100k',xx+5.5*G,y,90); w.W(xx+7*G,y,xx+9*G,y); xn=xx+9*G; w.J(xn,y)
    w.L(name+'_N',xn,y,0,'output')
    # feedback from the schmitt output
    w.L(name+'_S2',xn-G,y-4*G,180,'input'); w.W(xn-G,y-4*G,xn,y-4*G); w.W(xn,y-4*G,xn,y-3*G); w.R('1Meg',xn,y-1.5*G); w.W(xn,y-0*G,xn,y)
    # output driver
    xo=xn+6*G
    w.L(name+'_S2',xo,y,180,'input'); w.W(xo,y,xo+G,y); w.R('10k',xo+2.5*G,y,90); w.W(xo+4*G,y,xo+5*G,y)
    w.diode(xo+6.5*G,y,180); w.W(xo+8*G,y,xo+9*G,y); w.L(name,xo+9*G,y,0,'output')

def main():
    d=panel.build(); assert not d.check(), d.check()
    os.makedirs(OUT,exist_ok=True); root=ksch.U()
    w=ksch.Writer(PROJECT,root)
    w.T("NIBBLE BOARD 06 - FRONT PANEL: switches to force any bus line, debounced CLK and RST buttons, an LED on every line",10*G,6*G,3.5,True)
    w.T(f"{d.ntransistors()} transistors, {d.nleds()} LEDs.  Level switches connect a line to +5V through 10k: a switch left on can never fight a board that pulls the line low, it only adds a 1 where nothing else drives.\n"
        "Every switched or observed line has a 1Meg pull-down so it reads 0 when no board drives it.  DATA switches pull BUS_i# to GND directly (that is what an open-drain driver does), so closed = 1 on the bus.\n"
        "CLK and RST come from RC-debounced buttons through a Schmitt trigger and a diode, so the clock board can drive the same lines later.  Order 1 test: hub + panel + ALU: set A, B, SUB, EO; read S on the bus LEDs and CF/ZF.",10*G,16*G,1.6)
    used=set(s for s in bus.PINS.values() if s not in ('+5V','GND'))
    frame.bus_header(w,30*G,40*G,used)
    frame.power_flags(w,44*G,32*G); frame.decoupling(w,52*G,32*G); frame.holes(w,72*G,32*G,4)
    # switches
    sx=100*G
    dip8_levels(w,sx,34*G,panel.LEVEL_SW,"A3..A0 B3..B0")
    dip8_levels(w,sx+22*G,34*G,panel.CTRL_SW1,"SUB EO AI AO BI BA AB OI")
    dip8_levels(w,sx+44*G,34*G,panel.CTRL_SW2,"IO II PCE PCL FI HLT - -")
    dip4_data(w,sx+66*G,34*G)
    # buttons
    button(w,sx+80*G,30*G,'CLK'); button(w,sx+80*G,42*G,'RST')
    # pull-downs
    w.T("1Meg pull-downs: every line the panel switches or observes reads 0 when no board drives it",10*G,58*G,1.6,True)
    for k,n in enumerate(panel.PULLDOWNS):
        frame.pulldown(w,n,12*G+(k%20)*4*G,60*G+(k//20)*8*G)
    yend=w.layout(d.gates,panel.GROUP_TITLES,10*G,80*G,16)
    W=10*G+16*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"leds",d.nleds(),"resistors",d.nresistors())
if __name__=='__main__': main()
