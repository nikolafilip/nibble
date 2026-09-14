"""Common board frame pieces: bus header, decoupling, power flags, mounting holes, testbench supply."""
import ksch, bus
G=ksch.G

def bus_header(w,x,y,used,through=False):
    """64-pin header at (x,y); `used` = signals this board connects. Unused pins get no-connect flags, or with
    `through` a passive label so a second header on the same board carries every line in parallel (D039). Returns ref."""
    ref=w.header(x,y)
    for pin,sig in bus.PINS.items():
        odd=pin%2==1; px=x-2*G if odd else x+3*G; py=y-15*G+((pin-1)//2)*G
        if sig in ('+5V','GND'):
            ex=px-3*G if odd else px+3*G
            w.W(px,py,ex,py); w.PW(sig,ex,py)
        elif sig in used or through:
            ex=px-4*G if odd else px+4*G
            kind='bidirectional' if sig.startswith('BUS') else 'input' if sig in used else 'passive'
            w.W(px,py,ex,py); w.L(sig,ex,py,180 if odd else 0,kind)
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
    """Pre-route the bus header's GND pins (3,4,6,8,64) for a header placed at (hx,hy) rot 90.
    Pads: pin n at (hx+((n-1)//2)*2.54, hy-((n-1)%2)*2.54). outward=-1 if the header is at the top edge, +1 at the bottom."""
    P=lambda n:(hx+((n-1)//2)*2.54, hy-((n-1)%2)*2.54)
    (x4,y4),(x8,y8),(x3,y3),(x50,y50)=P(4),P(8),P(3),P(bus.N)
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

def header_gnd_link(w,hx,hy,ylink):
    """After layout(): link the bottom header's GND pin 3 to the nearest column GND rail on B.Cu, below the tiles at height ylink."""
    x3,y3=hx+2.54,hy
    rails=[(r[2],r[5]) for r in w.rails if r[0]=='GND' and r[1]=='B.Cu' and abs(r[2]-r[4])<0.01 and r[5]>r[3]]   # vertical GND rails: (x, y_end)
    if not rails: return
    xr,yend=min(rails,key=lambda r:abs(r[0]-x3))
    w.rails.append(('GND','B.Cu',x3,y3,x3,ylink,0.5)); w.rails.append(('GND','B.Cu',x3,ylink,xr,ylink,0.5)); w.rails.append(('GND','B.Cu',xr,yend,xr,ylink,0.5))

LINK=['OPR0','OPR1','OPR2','OPR3','OPR4','OPR5','OPR6','OPR7','PCR','RAI','GND','GND']   # the sequencer-counter link header (D035), pins 1..12
def link_header(w,x,y,direction,pins=LINK,value="LINK",note=None,used=None):
    """IDC link header (2x6 for 12 pins, 2x3 for 6) carrying signals between neighbouring boards: the operand register
    and the counter's load lines (D035), a bit card's carry and zero chain (D042). pins: the signal per pin 1..n, GND
    for ground pins; with `used`, signals not in it get a no-connect (a chained ribbon: each card takes its own line).
    direction: 'output' or 'input' for the labels. Returns the ref."""
    n=len(pins); rows=n//2
    ref=w.symbol("Connector_Generic",f"Conn_02x{rows:02d}_Odd_Even",w.ref('J'),value,x,y,0,tuple(str(i) for i in range(1,n+1)),
                 f"Connector_IDC:IDC-Header_2x{rows:02d}_P2.54mm_Vertical",[("Description","link between neighbouring boards",True)],sim=False)
    y0=y-((rows-1)//2)*G if rows>2 else y-G      # the symbol's pin rows straddle y
    for pin,sig in enumerate(pins,1):
        odd=pin%2==1; px=x-2*G if odd else x+3*G; py=y0+((pin-1)//2)*G
        if sig=='GND':
            ex=px-3*G if odd else px+3*G; w.W(px,py,ex,py); w.PW('GND',ex,py)
        elif used is not None and sig not in used:
            w.body+=f'\t(no_connect\n\t\t(at {ksch.f(px)} {ksch.f(py)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
        else:
            ex=px-4*G if odd else px+4*G; w.W(px,py,ex,py); w.L(sig,ex,py,180 if odd else 0,direction)
    w.T(note or ("LINK to board 09 (counter)" if direction=='output' else "LINK from board 03 (sequencer)"),x-6*G,y-4*G,1.27,True)
    return ref

# ---- the 100 x 100 mm card (D042, docs/cards.md) ----
CARD=100.0
HX,HY=10.63,7.5          # bus header, rot 90 along the top edge: pin 1 at (HX,HY), pin 2 above it; the shroud is centred, x 5.03 to 94.97
X0,Y0=9.0,16.0           # tile origin: first column's left pad, first pull-up row
COLS=11                  # 11 columns of 7.68 mm between the mid-side holes
HCOL=82.0                # usable column height: tiles end by y = 98, the name runs along the bottom edge
HOLES=[(4.0,50.0),(CARD-4.0,50.0)]
def card_frame(w,x,y,used,name,name_xy=(X0+20,CARD-1.8)):
    """Everything on a card that is not a tile: the bus header (pin 1 left), two M3 holes mid-height, 100 n + 10 u in the
    strip right of the tiles, PWR_FLAGs; and the pre-routes: header GND to the GND trunk and the pour, header +5V pins
    down on B.Cu to the +5V trunk, the trunk extended to the decoupling. (x,y): where the header symbol goes on the
    schematic. Call after layout(): it needs w.trunks. Returns the plan's `extra`."""
    (xg1,xg2,yg),(xv1,xv2,yv)=w.trunks[0]
    header_top(w,x,y,used,yg,yv,xv1)
    xc=CARD-5.0; xt=CARD-2.0
    w.rails.append(('+5V','F.Cu',xv2,yv,xt,yv,0.8))                  # trunk on to the decoupling strip
    power_flags(w,x+8*G,y-8*G)
    c1,c2=decoupling(w,x+16*G,y-8*G)
    w.at(c1,xc,16.5,270); w.rails.append(('+5V','F.Cu',xc,yv,xc,16.5,0.5)); cap_gnd(w,xc,16.5,2.5)
    w.at(c2,xc,26.0,270); w.rails.append(('+5V','F.Cu',xt,yv,xt,26.0,0.5)); w.rails.append(('+5V','F.Cu',xt,26.0,xc,26.0,0.5)); cap_gnd(w,xc,26.0,2.0)
    holes(w,x+46*G,y-8*G,2)
    return dict(silk_big=[(name,name_xy[0],name_xy[1],1.5)],hide_refs=['Q','R','D','J'],rules=dict(track=0.2,clearance=0.15),holes=HOLES)

def header_top(w,x,y,used,yg,yv,xv1):
    """The bus header along the top edge at (HX,HY), pin 1 left, with its power pre-routed: GND pin 3 down to the GND trunk
    at yg (pins 8 and 64 get vias to the pour), +5V pins 1-2 joined and pins 1 and 63 dropped on B.Cu to vias on the +5V
    trunk at yv, the trunk extended left from its first rail xv1 to pin 1. (x,y): the symbol on the schematic. Returns the ref."""
    j=bus_header(w,x,y,used); w.at(j,HX,HY,90); w.label("1",HX-7.0,HY+0.9,1.0)
    header_gnd(w,HX,HY,-1,y_gnd_trunk=yg)
    P=lambda n:(HX+((n-1)//2)*2.54, HY-((n-1)%2)*2.54)
    (xa,ya),(xb,yb)=P(1),P(2); w.rails.append(('+5V','F.Cu',xa,ya,xb,yb,0.5))
    for n in (1,63):
        px,py=P(n)
        near=[r[2] for r in w.rails if r[1]=='B.Cu' and abs(r[2]-r[4])<0.01 and abs(r[2]-px)<0.7]     # a tile rail under the pin's column (the sequencer's 10.16 pitch puts one at 89.0)
        if near:    # jog 1.5 mm past the rail before dropping to the trunk
            xj=near[0]+1.5; w.rails.append(('+5V','B.Cu',px,py,px,py+2.0,0.5)); w.rails.append(('+5V','B.Cu',px,py+2.0,xj,py+3.5,0.5)); w.rails.append(('+5V','B.Cu',xj,py+3.5,xj,yv,0.5)); w.vias.append(('+5V',xj,yv))
        else: w.rails.append(('+5V','B.Cu',px,py,px,yv,0.5)); w.vias.append(('+5V',px,yv))
    w.rails.append(('+5V','F.Cu',HX,yv,xv1,yv,0.8))
    return j

LINK_HY=95.0                       # a card's neighbour links (2x3) sit along the bottom edge: IN at the left, OUT at the right
LINK_IN_HX,LINK_OUT_HX=14.0,80.0
LINK_HCOL=72.0                     # tiles must end above the link headers' courtyard (y 88.8)
def link_gnd(w,hx,pins):
    """Pre-route every GND pin of a link header at (hx, LINK_HY) rot 90 to its own via: the top row 2.5 mm up, the bottom
    row 2.5 mm down. The pour then never has to reach under the header (on memslot it did not, and the stitch found no spot)."""
    for n,sig in enumerate(pins,1):
        if sig!='GND': continue
        top=n%2==0; px=hx+((n-1)//2)*2.54; py=LINK_HY-(2.54 if top else 0); ey=py-2.5 if top else py+2.5
        w.rails.append(('GND','F.Cu',px,py,px,ey,0.5)); w.vias.append(('GND',px,ey))

def card_links(w,x,y,pins_in,pins_out,what):
    """The two 2x3 neighbour links of a bit card (D042): pins_in from the card below (None on the lowest bit), pins_out to
    the card above (None on the highest). Placed rot 90 along the bottom edge, pin 1 left. what: 'bit', for the notes."""
    refs=[]
    if pins_in:
        j=link_header(w,x,y,'input',pins_in,"IN",f"LINK IN from the {what} below"); w.at(j,LINK_IN_HX,LINK_HY,90); w.label("IN",LINK_IN_HX-5.0,LINK_HY-7.6,0.8); refs.append(j); link_gnd(w,LINK_IN_HX,pins_in)
    if pins_out:
        j=link_header(w,x+16*G,y,'output',pins_out,"OUT",f"LINK OUT to the {what} above"); w.at(j,LINK_OUT_HX,LINK_HY,90); w.label("OUT",LINK_OUT_HX-5.0,LINK_HY-7.6,0.8); refs.append(j); link_gnd(w,LINK_OUT_HX,pins_out)
    return refs

RIBBON_HX=40.0                     # a chained 2x6 ribbon header (the counter cards' operand lines) between the two neighbour links
RIBBON_HCOL=68.0                   # with the name above the headers at y 87.5
def card_ribbon(w,x,y,used,note,pins=LINK,direction='input'):
    """A 2x6 header on a chained ribbon (the sequencer's link along the counter cards, D035; the memory control card's
    along the slot cards): the card connects only the lines in `used`, the rest are no-connects. Along the bottom edge
    between IN and OUT."""
    j=link_header(w,x,y,direction,pins,"LINK",note,used=used); w.at(j,RIBBON_HX,LINK_HY,90); w.label("LINK",RIBBON_HX-5.0,LINK_HY-7.6,0.8); link_gnd(w,RIBBON_HX,pins)
    return j

JUMPER_HX=[62.0,71.5,81.0]
def card_jumpers(w,x,y,names,sides,net,hx=None,title=None):
    """1x3 jumper headers along the bottom edge at hx (default: three right of the ribbon): the centre pin is net(k), pin 1 (left, '0')
    and pin 3 (right, '1') the two choices sides(k). names: the silk caption per jumper."""
    refs=[]
    for k,(nm,hx) in enumerate(zip(names,hx or JUMPER_HX)):
        xx=x+k*12*G
        j=w.pinheader(3,xx,y,nm); refs.append(j)
        lo,hi=sides(k)
        w.W(xx-2*G,y-G,xx-4*G,y-G); w.L(lo,xx-4*G,y-G,180,'input')
        w.W(xx-2*G,y,xx-4*G,y); w.L(net(k),xx-4*G,y,180,'output')
        w.W(xx-2*G,y+G,xx-4*G,y+G); w.L(hi,xx-4*G,y+G,180,'input')
        w.at(j,hx,LINK_HY,90)      # pads at hx, hx+2.54, hx+5.08
        w.label(nm,hx+0.6,LINK_HY-4.2,0.8); w.label("0",hx-0.5,LINK_HY+3.2,0.8); w.label("1",hx+4.6,LINK_HY+3.2,0.8)
    w.T(title or "SLOT PAIR JUMPERS: the centre pin to '1' where the address bit is 1 (the complement then holds the select NOR low only for this address), to '0' where it is 0",x-6*G,y-4*G,1.27,True)
    return refs

