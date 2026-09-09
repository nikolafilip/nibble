"""Generate boards/06-panel from panel.py: schematic + PCB placement plan."""
import os, ksch, frame, bus, panel
G=ksch.G; OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','06-panel'); PROJECT='panel'

def dip8_levels(w,x,y,names,title,pcb):
    """DIP-8: left pins to +5V, right pins through 10k to the named lines. pcb=(x,y,rx,ry): switch and resistor column positions."""
    sw=w.dipswitch(8,x,y,title); px,py,rx,ry=pcb; w.at(sw,px,py,0); w.rails.append(('+5V','F.Cu',px,py,px,py+7*2.54,0.5))
    w.W(x-3*G,y-4*G,x-3*G,y+3*G); w.W(x-3*G,y-4*G,x-3*G,y-6*G); w.PW('+5V',x-3*G,y-6*G)
    for i in range(8):
        sy=y-4*G+i*G
        if i not in (0,7): w.J(x-3*G,sy)
        n=names[i]
        w.label(n or '-',px-9,py+i*2.54-0.6,1.0)
        if n is None:
            w.body+=f'\t(no_connect\n\t\t(at {ksch.f(x+3*G)} {ksch.f(sy)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'; continue
        w.W(x+3*G,sy,x+4*G,sy); r=w.R('10k',x+5.5*G,sy,90); w.W(x+7*G,sy,x+8*G,sy); w.L(n,x+8*G,sy,0,'output')
        w.at(r,rx+(i%2)*6,ry+(i//2)*8,270)
def dip4_data(w,x,y,pcb):
    sw=w.dipswitch(4,x,y,"DATA (closed = 1 on the bus)"); px,py=pcb; w.at(sw,px,py,0); w.rails.append(('GND','F.Cu',px,py,px,py+3*2.54,0.5))
    w.W(x-3*G,y-2*G,x-3*G,y+G); w.W(x-3*G,y+G,x-3*G,y+3*G); w.PW('GND',x-3*G,y+3*G)
    for i in range(4):
        sy=y-2*G+i*G
        if i not in (0,3): w.J(x-3*G,sy)
        w.W(x+3*G,sy,x+5*G,sy); w.L(panel.DATA_SW[i],x+5*G,sy,0,'bidirectional')
        w.label(f"D{i}",px-6,py+i*2.54-0.6,1.0)
def button(w,x,y,name,pcb):
    """+5V -> button -> 10k -> X (1u, 220k to GND) -> 100k -> N (label name_N); name_S2 -> 1Meg -> N; name_S2 -> 10k -> diode -> name"""
    px,py=pcb
    w.T(name+" button",x-4*G,y-4*G,1.27,True)
    w.PW('+5V',x-4*G,y-2*G); w.W(x-4*G,y-2*G,x-4*G,y); w.W(x-4*G,y,x-2*G,y)
    w.at(w.button(x,y,name),px,py,0); w.label(name,px+1,py-3.5,1.5)
    w.W(x+2*G,y,x+3*G,y); w.at(w.R('10k',x+4.5*G,y,90),px+14,py-2,270); w.W(x+6*G,y,x+8*G,y)
    xx=x+8*G; w.J(xx,y)
    w.W(xx,y,xx,y+G); w.at(w.C('1u',xx,y+2.5*G,True),px+19,py-2,270); w.W(xx,y+4*G,xx,y+5*G); w.PW('GND',xx,y+5*G)
    w.W(xx,y,xx+3*G,y); w.J(xx+3*G,y); w.W(xx+3*G,y,xx+3*G,y+G); w.at(w.R('220k',xx+3*G,y+2.5*G),px+24,py-2,270); w.W(xx+3*G,y+4*G,xx+3*G,y+5*G); w.PW('GND',xx+3*G,y+5*G)
    w.W(xx+3*G,y,xx+4*G,y); w.at(w.R('100k',xx+5.5*G,y,90),px+29,py-2,270); w.W(xx+7*G,y,xx+9*G,y); xn=xx+9*G; w.J(xn,y)
    w.L(name+'_N',xn,y,0,'output')
    w.L(name+'_S2',xn-G,y-4*G,180,'input'); w.W(xn-G,y-4*G,xn,y-4*G); w.W(xn,y-4*G,xn,y-3*G); w.at(w.R('1Meg',xn,y-1.5*G),px+34,py-2,270); w.W(xn,y-0*G,xn,y)
    xo=xn+6*G
    w.L(name+'_S2',xo,y,180,'input'); w.W(xo,y,xo+G,y); w.at(w.R('10k',xo+2.5*G,y,90),px+39,py-2,270); w.W(xo+4*G,y,xo+5*G,y)
    w.at(w.diode(xo+6.5*G,y,180),px+14,py+7,0); w.W(xo+8*G,y,xo+9*G,y); w.L(name,xo+9*G,y,0,'output')

def main():
    d=panel.build(); assert not d.check(), d.check()
    os.makedirs(OUT,exist_ok=True); root=ksch.U()
    w=ksch.Writer(PROJECT,root)
    w.T("NIBBLE BOARD 06 - FRONT PANEL: switches to force any bus line, debounced CLK and RST buttons, an LED on every line",10*G,6*G,3.5,True)
    w.T(f"{d.ntransistors()} transistors, {d.nleds()} LEDs.  Level switches connect a line to +5V through 10k: a switch left on can never fight a board that pulls the line low, it only adds a 1 where nothing else drives.\n"
        "Every switched or observed line has a 1Meg pull-down so it reads 0 when no board drives it.  DATA switches pull BUS_i# to GND directly (that is what an open-drain driver does), so closed = 1 on the bus.\n"
        "CLK and RST come from RC-debounced buttons through a Schmitt trigger and a diode, so the clock board can drive the same lines later.  Order 1 test: hub + panel + ALU: set A, B, SUB, EO; read S on the D3..D0 LEDs and CF/ZF.",10*G,16*G,1.6)
    used=set(s for s in bus.PINS.values() if s not in ('+5V','GND'))
    BW,BH=190,222; w.PCB_COL=15.24
    j=frame.bus_header(w,30*G,40*G,used); w.at(j,50,214,90); w.label("BUS  (pin 1 left)",52,206,1.2); frame.header_gnd(w,50,214,+1)
    frame.power_flags(w,44*G,32*G)
    c1,c2=frame.decoupling(w,52*G,32*G); w.at(c1,12,200,270); w.at(c2,18,200,270); frame.cap_gnd(w,12,200,2.5); frame.cap_gnd(w,18,200,2.0)
    frame.holes(w,72*G,32*G,4)
    sx=100*G
    dip8_levels(w,sx,34*G,panel.LEVEL_SW,"A3..A0 B3..B0",(144,12,160,10))
    dip8_levels(w,sx+22*G,34*G,panel.CTRL_SW1,"SUB EO AI AO BI BA AB OI",(144,46,160,44))
    dip8_levels(w,sx+44*G,34*G,panel.CTRL_SW2,"IO II PCE PCL FI HLT - -",(144,80,160,78))
    dip4_data(w,sx+66*G,34*G,(144,114))
    w.rails.append(('+5V','F.Cu',144,12,144,80,0.5))   # one +5V spine through all three level-switch columns
    w.label("A3..B0",143,8,1.0); w.label("CONTROL",143,42,1.0); w.label("CONTROL",143,76,1.0); w.label("DATA",143,110,1.0)
    button(w,sx+80*G,30*G,'CLK',(136,140)); button(w,sx+80*G,42*G,'RST',(136,160))
    w.T("1Meg pull-downs: every line the panel switches or observes reads 0 when no board drives it",10*G,58*G,1.6,True)
    for k,n in enumerate(panel.PULLDOWNS):
        r=frame.pulldown(w,n,12*G+(k%20)*4*G,60*G+(k//20)*8*G); w.at(r,140+(k%10)*5,180+(k//10)*9,270)
    w.label("1Meg PULL-DOWNS",140,176,1.0)
    nrow=(len(panel.PULLDOWNS)+9)//10
    for r in range(nrow):   # GND bar through each row's ground pads, joined at the right end
        last=140+(min(10,len(panel.PULLDOWNS)-r*10)-1)*5
        w.rails.append(('GND','F.Cu',137,180+r*9+5.08,last,180+r*9+5.08,0.5))
    w.rails.append(('GND','F.Cu',137,185.08,137,180+(nrow-1)*9+5.08,0.5))
    yend=w.layout(d.gates,panel.GROUP_TITLES,10*G,80*G,16,pcb_origin=(12.0,16.0),pcb_cols=8)
    W=10*G+16*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE FRONT PANEL",8,5,1.8)],hide_refs=['Q','R','D']))
    print("wrote",OUT,"transistors",d.ntransistors(),"leds",d.nleds(),"resistors",d.nresistors(),"pcb extent",w.pcb_extent)
if __name__=='__main__': main()
