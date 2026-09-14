"""Generate cards/panela, panelb, panelc (KiCad projects) from panel.build_a/b/c: the three front panel cards (docs/cards.md).
A: level switches A3..A0 B3..B0 and SUB..AB with their LEDs, the bus data LEDs, CF ZF CLK RST LEDs.
B: level switches OI..MAI and MI..INP with their LEDs, the CLK and RST buttons.   C (the operator's): PC and M LEDs, DATA switches and input port.
Run from sim/:  python3 build_panel_card.py a|b|c [--pack skyline|column]"""
import os, sys
import ksch, frame, panel
G=ksch.G
HERE=os.path.dirname(os.path.abspath(__file__))
FIELD={'a':(frame.X0,frame.Y0,frame.COLS,52.0),'b':(frame.X0,frame.Y0,frame.COLS,42.0),'c':(frame.X0,frame.Y0,frame.COLS,42.0)}   # 11 columns; 52 mm holds three LED cells (A: three rows of LEDs), 42 exactly two (B, C: two rows), so a tile column is a panel column
RAIL_R=frame.X0-1.27+7.68*11                      # the right-edge +5V rail (x 92.21); a switch's right pins sit on it
RAIL_M=frame.X0-1.27+7.68*7                       # the +5V rail at x 61.49
BLOCK_Y={'a':72.0,'b':74.0,'c':64.0}; ROW_P=7.7      # switch blocks: DIP pin 1 row (B: below the button row at 61); resistor rows (standing 0207: 7.6 mm courtyard)

def rail_down(w,xr,y):
    """Extend the field's +5V rail at xr (B.Cu) from where the tiles left it down to y."""
    end=w.rail_end.get(round(xr,3))
    if not end: end=frame.Y0-2.0; w.vias.append(('+5V',xr,end))      # a rail no tile used: start it at the +5V trunk with a via
    w.rails.append(('+5V','B.Cu',xr,end,xr,y,0.5))

def dip_levels(w,x,y,names,title,px,py):
    """DIP-8 or DIP-4 level switches: right pins (x = px+7.62, on a +5V rail) to +5V, left pins through 10k to the named
    lines. Resistors stand in columns left of the switch, three per column at ROW_P, the line name on the silk right of the switch."""
    nn=len(names); sw=w.dipswitch(nn,x,y,title); w.at(sw,px,py,0)
    top=y-(nn//2)*G; bot=top+(nn-1)*G
    w.W(x+3*G,top,x+3*G,bot); w.W(x+3*G,top,x+3*G,top-2*G); w.PW('+5V',x+3*G,top-2*G)
    rail_down(w,px+7.62,py+(nn-1)*2.54)
    for i in range(nn):
        sy=top+i*G
        if i not in (0,nn-1): w.J(x+3*G,sy)
        n=names[i]
        w.W(x-3*G,sy,x-4*G,sy); r=w.R('10k',x-5.5*G,sy,90); w.W(x-7*G,sy,x-8*G,sy); w.L(n,x-8*G,sy,180,'output')
        col,row=(divmod(i,3) if nn>4 else (i,0))
        w.at(r,px-4.0-6.0*col,py+ROW_P*row,270)
        w.label(n,px+9.2,py+i*2.54-0.4,0.8)
    w.label(title.split(' (')[0],px-16.0 if nn>4 else px-22.0,py-3.6,0.8)
    return sw

def button(w,x,y,name,px,py,xr):
    """+5V -> button -> 10k -> X (1u, 220k to GND) -> 100k -> N (label name_N); name_S2 -> 1Meg -> N; name_S2 -> 10k -> diode -> name.
    On the board the button's +5V pad (px+6.5, py) sits under the +5V rail xr, brought down from the tiles."""
    w.T(name+" button",x-4*G,y-4*G,1.27,True)
    w.PW('+5V',x-4*G,y-2*G); w.W(x-4*G,y-2*G,x-4*G,y); w.W(x-4*G,y,x-2*G,y)
    w.at(w.button(x,y,name),px,py,0); w.label(name,px+1.5,py-2.6,1.0)
    rail_down(w,xr,py); w.rails.append(('+5V','B.Cu',xr,py,px+6.5,py,0.5))
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
    w.rails.append(('GND','F.Cu',px+19,py,px+24,py+3.08,0.5))      # debounce cap ground -> 220k ground (pre-routed)

def main(which,pack='column'):
    d={'a':panel.build_a,'b':panel.build_b,'c':panel.build_c}[which](); pr=d.check(); assert not pr, pr
    PROJECT=f'panel{which}'; OUT=os.path.join(HERE,'..','cards',PROJECT); os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid)
    common=f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 100 x 100 mm (docs/cards.md).\n"
    if which=='a':
        w.T("NIBBLE CARD PANEL A - FRONT PANEL, LEVELS 1: switches for A3..A0 B3..B0 and SUB..AB, their LEDs, the bus data LEDs, CF ZF CLK RST LEDs",10*G,6*G,3.5,True)
        w.T(common+"Level switches connect a line to +5V through 10k: a switch left on can never fight a card that pulls the line low, it only adds a 1 where nothing else drives.\n"
            "Every switched or observed line has a 1Meg pull-down so it reads 0 when no card drives it.  BUS_i# is active-low: an inverter turns it into the data bit D_i for its LED.",10*G,16*G,1.6)
        used=set(panel.LEVEL_SW+panel.CTRL_SW1+['CF','ZF','CLK','RST','BUS0#','BUS1#','BUS2#','BUS3#']); name="NIBBLE  PANEL A  LEVELS 1"
    elif which=='b':
        w.T("NIBBLE CARD PANEL B - FRONT PANEL, LEVELS 2: switches for OI..MAI and MI..INP with their LEDs, the CLK and RST buttons",10*G,6*G,3.5,True)
        w.T(common+"Level switches connect a line to +5V through 10k: a switch left on can never fight a card that pulls the line low, it only adds a 1 where nothing else drives.\n"
            "Every switched line has a 1Meg pull-down so it reads 0 when no card drives it.  CLK and RST come from RC-debounced buttons through a Schmitt trigger and a diode, so the clock card can drive the same lines.",10*G,16*G,1.6)
        used=set(panel.CTRL_SW2+panel.CTRL_SW3+panel.BUTTONS); name="NIBBLE  PANEL B  LEVELS 2"
    else:
        w.T("NIBBLE CARD PANEL C - FRONT PANEL, OPERATOR: PC and M LEDs, the DATA switches and input port",10*G,6*G,3.5,True)
        w.T(common+"The DATA switches are the input port: a closed switch is a 1, and while INP=1 the four bits are driven onto the bus (open drain) for the IN instruction.\n"
            "PC and SW lines have 1Meg pull-downs; M is pulled down on the hub.",10*G,16*G,1.6)
        used=set(panel.OBSERVED[:16]+['INP','BUS0#','BUS1#','BUS2#','BUS3#']); name="NIBBLE  PANEL C  OPERATOR"
    cols=8
    F=FIELD[which]
    # packing order: a panel column's LEDs, then the pull-downs that fit under them, then everything else (B, C: two LEDs per column)
    leds=[g for g in d.gates if g['kind']=='LED']; pds=[g for g in d.gates if g['kind']=='PD']; rest=[g for g in d.gates if g['kind'] not in ('LED','PD')]
    rows=3 if which=='a' else 2; order=[]
    for k in range(0,len(leds),rows): order+=leds[k:k+rows]+(pds[:2] if rows==2 else []); pds=pds[2:] if rows==2 else pds
    order+=pds+rest
    yend=w.layout(d.gates,panel.CARD_TITLES,10*G,60*G,cols,pcb_origin=(F[0],F[1]),pcb_cols=F[2],pack=pack,fields=[F],pack_order=order)
    extra=frame.card_frame(w,30*G,40*G,used,name,name_xy=(9.0,frame.CARD-1.8)); extra['hide_refs']+=['SW','C']
    sx=10*G; sy=yend+16*G
    if which in 'ab':
        n1,n2=(panel.LEVEL_SW,panel.CTRL_SW1) if which=='a' else (panel.CTRL_SW2,panel.CTRL_SW3)
        dip_levels(w,sx,sy,n1," ".join(n1)+" (switch up = 1)",RAIL_M-7.62,BLOCK_Y[which])
        dip_levels(w,sx+30*G,sy,n2," ".join(n2),RAIL_R-7.62,BLOCK_Y[which])
    if which=='b':
        button(w,sx+60*G,sy-2*G,'CLK',8.0,61.0,frame.X0-1.27+7.68*1)
        button(w,sx+60*G,sy+10*G,'RST',52.0,61.0,RAIL_M)
    if which=='c':
        dip_levels(w,sx,sy,panel.DATA_SW,"DATA (input port, read by IN)",RAIL_R-7.62,BLOCK_Y[which])
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    W=10*G+cols*w.CELL_W+30*G; H=sy+24*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=[round(v,1) for v in sorted(w.rail_end.values())]
    print("wrote",OUT,"transistors",d.ntransistors(),"lowest stub per rail",fill)

if __name__=='__main__':
    a=sys.argv; main(a[1],a[a.index('--pack')+1] if '--pack' in a else 'column')
