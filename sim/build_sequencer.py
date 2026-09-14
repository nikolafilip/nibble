"""Generate boards/03-sequencer (KiCad project) from sequencer.py, at the card pitch (D045). Run from sim/.
The one board that is not a card: the 45 x 23 diode matrix would cross card boundaries. Bus header top left,
decoupling and the link header beside it, the matrix top right with its diodes standing up (rows 2.54, columns
5.08 mm), dense tiles below the matrix (rows, column buffers, decoders) and down the left side (the rest)."""
import os, sys
import ksch, sequencer, bus, frame
G=ksch.G
OUT=os.environ.get('SEQ_OUT') or os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','03-sequencer')     # SEQ_OUT: build a trial elsewhere while the real board routes
PROJECT='sequencer'
W,H=245.0,255.0                          # D051: four layers at the card pitch. (Two layers plateaued: 240 x 280 at the card pitch at ~100 unrouted nets, 260 x 310 at a 10.16 pitch at ~70, D049.)
LEFT=(frame.X0,frame.Y0,12)                # tile field down the left: x 9 .. 101 at the card pitch
LEFT_SPLIT=7                               # its columns 7..11 start one tile row lower: an 8 mm strip under the header's right half for the fan-out to pins 42..64
MX,MY=102.0,14.0                           # matrix origin: captions from x 102, column tracks from y 26
RIGHT_X=104.0
RIGHT_COLS=17                              # x 104 .. 234.6 under the matrix
TILE_PITCH=7.68                            # the card pitch again: four layers give the router the room the 10.16 pitch gave it on two (D049 -> D051)
PATCHES=[dict(net='ENF',layer='In2.Cu',      # v9 (2026-09-14): freerouting hooked ENF across CFQ_m1 on In2 beside Q380 (its own tracks crossing, 4 DRC errors); the hook goes
    remove=[[63.86,185.26,64.26,185.66],[64.26,185.66,64.30,185.62],[64.26,185.66,64.26,185.66],[64.30,185.62,64.30,184.88],[64.30,184.88,64.89,184.29],[63.86,173.40,63.86,185.26]],
    add=[[63.86,173.40,63.86,184.70],[63.86,184.70,64.27,184.29],[64.27,184.29,64.89,184.29]])]
PACK_FIRST=['rows','cols','opdec','famdec']   # groups packed first, so they land below the matrix, next to the rows
def main(pack='column'):
    d=sequencer.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid); w.PCB_COL=TILE_PITCH
    w.T("NIBBLE BOARD 03 - SEQUENCER: step counter, instruction and operand registers, flags, decoders and the diode control matrix",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.ndiodes()} matrix diodes, {d.nleds()} LEDs, {W:.0f} x {H:.0f} mm (D045).\n"
        "From the bus header: M7..M0 (the program memory word), CF and ZF (from the ALU), CLK, RST.\n"
        "To the bus header: II, PCE and the matrix columns SUB EO AI AO BI BO BA AB OI IO PCL FI HLT MAI MI MO ONE F0 F1 INP; BUS3#..BUS0# driven (open drain) with OPR3..0 while IO.\n"
        "To the counter cards over the LINK header: OPR7..0, PCR, RAI.  The program counter and the return register live there (D035, D042).\n"
        "Steps S0..S4 are a one-hot ring of flip-flops: S0 loads IR/OPR (II), S1 counts (PCE), S2 loads the second word of a jump or call (OPI, PCE), S3 and S4 drive the matrix rows; DONE returns to S0.\n"
        "docs/isa.md is the specification; sim/emu.py the reference the whole-machine simulation checks this board against.",10*G,18*G,1.6)
    used={f'M{i}' for i in range(8)}|{'CF','ZF','CLK','RST','II','PCE'}|set(c for c in sequencer.COLS if c in bus.SIGNALS)|{'BUS0#','BUS1#','BUS2#','BUS3#'}
    # ---- the matrix (placed first: the right tile field starts below it) ----
    rows=[]
    for net,name,step in d.rows:
        rows.append((net,f"{name} S{step}" if name else f"OP{net.split('_')[1][2:]} (free) S{step}"))
    rows+=[('R_JCC','JC&C'),('R_JZZ','JZ&Z'),('R_JNZZ','JNZ&!Z'),('R_JNCC','JNC&!C')]     # the conditional second rows (the flag itself is in the NOR); short: the captions sit 7.62 mm apart
    diodes=[(g['ins'][0],g['out']) for g in d.gates if g['kind']=='DIODE']
    cols=14
    mx0=10*G+cols*w.CELL_W+6*G
    w.T("THE CONTROL MATRIX",mx0,66*G-G,2.0,True)
    mh,(mxe,mye)=ksch.matrix(w,rows,[f'{c}_m' for c in sequencer.COLS],diodes,mx0,66*G,(MX,MY),caption=lambda c:c[:-2],vertical=True,tails='left')
    assert mxe<=W-2, (mxe,W)
    # ---- tiles: two fields, the one below the matrix filled first ----
    ry=mye+6.0                                                       # right field's first pull-up row: trunks at ry-3.5 and ry-2
    YB=H-4.5                                                         # tiles may reach 4.5 mm from the bottom edge (the holes are in the corners, beside column 0 and the last column)
    ys=LEFT[1]+8.0
    fields=[(RIGHT_X,ry,RIGHT_COLS,YB-ry),(LEFT[0],LEFT[1],LEFT_SPLIT,YB-LEFT[1]),(LEFT[0]+LEFT_SPLIT*TILE_PITCH,ys,LEFT[2]-LEFT_SPLIT,YB-ys,LEFT_SPLIT)]   # fifth element: the rail parity continues across the seam (v8 drew a +5V and a GND rail on the same x there)
    tiles=[g for g in d.gates if g['kind'] not in ('DIODE','PD')]
    seq=PACK_FIRST+['steps','ir','flags','leds','clock','outs','bus']       # the small tiles last: they fill the remainders under the pre-placed ones
    order=sorted(tiles,key=lambda g:seq.index(g['group']))
    # D051 placement: the 45 row drivers stand under their matrix columns (three per tile column, left to right, so no tail
    # drifts more than about 10 mm sideways); the 23 column buffers and their inverters fill the left field's two columns
    # beside the matrix, where the column tails come out. Two-layer and the first four-layer routes lost about 70 nets
    # because the buffers had spilled to the far left and every column net crossed the board.
    byout={g['out']:g for g in tiles}
    pre=[(byout[net],0,k//3) for k,(net,cap) in enumerate(rows)]
    # the column inverters (X_mn) stand in column 11 beside the tails; each output buffer (X) stands in the column under its own
    # bus-header pin (columns 7..10), so its run to the pin is a short vertical: with all of them in column 10, 16 header pins stayed open
    pinx={sig:frame.HX+((pin-1)//2)*2.54 for pin,sig in bus.PINS.items()}
    def outcol(sig): return min(max(int((pinx.get(sig,90.0)-LEFT[0])//TILE_PITCH),LEFT_SPLIT),10)-LEFT_SPLIT
    pre+=[(g,2,11-LEFT_SPLIT if g['out'].endswith('_mn') else outcol(g['out'])) for g in tiles if g['group']=='cols']
    import collections; print('output buffers per column:',sorted(collections.Counter(LEFT_SPLIT+c for g,f,c in pre if f==2).items()))
    yend=w.layout(tiles,sequencer.GROUP_TITLES,10*G,66*G,cols,pack=pack,fields=fields,pack_order=order,pre=pre)
    (rg,rv),(lg,lv),(sg,sv)=w.trunks                                 # (GND trunk, +5V trunk) per field, in field order
    # ---- frame: header, decoupling, link header, holes; +5V from the header's trunk on to the right field and the capacitors ----
    x,y=30*G,40*G
    frame.header_top(w,x,y,used,lg[2],lv[2],lv[0])
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G)
    xf=236.2                                                         # the +5V feed for the right field: along the top edge over the matrix and down its right side (D051: the
    # gap between the left field and the matrix is the routing corridor for the column tails; a feed there blocked F.Cu and left every tail open)
    xs_=sv[0] if sv[0]<sg[0] else sv[1]; assert xs_<sg[0] or xs_>sg[1], (sv,sg)                      # the lower columns' trunk hangs from the feed at whichever end lies outside its GND trunk
    w.rails.append(('+5V','F.Cu',lv[1],lv[2],xf,lv[2],0.8)); w.rails.append(('+5V','F.Cu',xs_,lv[2],xs_,sv[2],0.8))
    w.rails.append(('+5V','F.Cu',xf,10.5,xf,rv[2],0.8)); w.rails.append(('+5V','F.Cu',rv[1],rv[2],xf,rv[2],0.8))
    w.at(c1,xf,10.5,90); w.rails.append(('GND','F.Cu',xf,8.0,xf,5.5,0.5)); w.vias.append(('GND',xf,5.5))          # rot 90: pad 1 (+5V) at (x,y) on the feed, pad 2 (GND) 2.5 above
    w.at(c2,xf-5.0,10.5,90); w.rails.append(('+5V','F.Cu',xf-5.0,10.5,xf,10.5,0.5)); w.rails.append(('GND','F.Cu',xf-5.0,8.5,xf-5.0,6.0,0.5)); w.vias.append(('GND',xf-5.0,6.0))
    frame.holes(w,x+46*G,y-8*G,4)
    lk=frame.link_header(w,x+62*G,y,'output'); w.at(lk,115.0,10.0,90)
    holes=[(4.0,20.0),(W-4.0,20.0),(4.0,H-4.0),(W-4.0,H-4.0)]          # the top corners are under the header and the matrix's pull-downs
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(W,H),extra=dict(silk_big=[("NIBBLE  SEQUENCER",frame.X0+20,H-1.8,1.5)],hide_refs=['Q','R','D'],patches=PATCHES,rules=dict(track=0.2,clearance=0.15),holes=holes,layers=4,router=dict(timeout=36000,attempts=2,route_in1=True,jar='freerouting-2.4.1.jar',layer_order=['In2.Cu','F.Cu','B.Cu','In1.Cu'],exclude_nets=['GND','+5V'])))      # freerouting 1.9 needs hours per pass on this board (a thread dump shows it deep in the maze search); 2.x does a pass in minutes. 2.4.1 (Java 25, NIBBLE_JAVA) headless: it stops at the pass cap and saves; 2.1.0 ignores the cap headless and, with its window, sometimes never saves
    Wsch=mx0+(len(sequencer.COLS)+10)*5*G+10*G; Hsch=max(yend,66*G+mh)+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(Wsch,Hsch))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=sorted((round(x,1),round(y,1)) for x,y in w.rail_end.items())
    print("wrote",OUT,"transistors",d.ntransistors(),"diodes",d.ndiodes(),"matrix to",(mxe,mye),"right field from y",ry,"tile extent",w.pcb_extent,"board",(W,H))
    print("rail ends:",fill)

if __name__=='__main__':
    a=sys.argv; main(a[a.index('--pack')+1] if '--pack' in a else 'column')
