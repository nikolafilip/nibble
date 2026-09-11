"""Generate cards/memctl and cards/memslot (KiCad projects) from memory.build_ctl / build_slot (docs/cards.md).
Run from sim/:  python3 build_mem_card.py ctl|slot [--pack skyline|column]"""
import os, sys
import ksch, memory, frame
G=ksch.G
HERE=os.path.dirname(os.path.abspath(__file__))

def main(which,pack='column'):
    d=memory.build_ctl() if which=='ctl' else memory.build_slot(); pr=d.check(); assert not pr, pr
    PROJECT='memctl' if which=='ctl' else 'memslot'; OUT=os.path.join(HERE,'..','cards',PROJECT)
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid); w.HCOL=frame.RIBBON_HCOL
    if which=='ctl':
        w.T("NIBBLE CARD MEMCTL - DATA MEMORY CONTROL: the address register and the write and read gates for the slot cards",10*G,6*G,3.5,True)
        w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 100 x 100 mm (docs/cards.md).\n"
            "From the bus header: BUS3#..BUS0# (an address while MAI), MAI, MI, MO, CLK.\n"
            "To the slot cards over the LINK ribbon (2x6, chained along the eight slot cards): MAR3..0 and their complements, MIN (low = write allowed: MI and PH1), MON (low = read: MO).\n"
            "MAR is four transparent latches open while MAI and PH1 (the address rides the bus for the whole tick).  The write ends at the clock edge because PH1 does (D0xx: a write that\n"
            "outlasted the data flipped cells at the mixed corner).  Each slot card selects its pair of slots from MAR3..1 with jumpers and its even/odd slot with MAR0.",10*G,18*G,1.6)
        used={'BUS0#','BUS1#','BUS2#','BUS3#','MAI','MI','MO','CLK'}; titles=memory.CTL_TITLES; name="NIBBLE  MEMORY CONTROL"
    else:
        w.T("NIBBLE CARD MEMSLOT - DATA MEMORY SLOT PAIR: two 4-bit slots of the pair the jumpers select",10*G,6*G,3.5,True)
        w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 100 x 100 mm (docs/cards.md).  One design, eight cards.\n"
            "From the bus header: BUS3#..BUS0# (data while MI).   To the bus: BUS3#..BUS0# driven (open drain) with the addressed slot while MO.\n"
            "From the memory control card over the LINK ribbon: MAR3..0 and their complements, MIN (low = write allowed), MON (low = read).\n"
            "Jumpers A3 A2 A1 pick the slot pair: SEL = NOR(X3, X2, X1) is high only for that address; the even slot is MAR0 = 0, the odd slot MAR0 = 1 (slots 2p and 2p+1).\n"
            "A cell is two cross-coupled inverters; while WR (slot and write allowed) the bus data forces it, while RD (slot and read) it pulls its bus line.  Every cell has an LED: the memory is visible.",10*G,18*G,1.6)
        used={'BUS0#','BUS1#','BUS2#','BUS3#'}; titles=memory.SLOT_TITLES; name="NIBBLE  MEMORY SLOTS"
    cols=8
    yend=w.layout(d.gates,titles,10*G,66*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=frame.COLS,pack=pack)
    extra=frame.card_frame(w,30*G,40*G,used,name,name_xy=(44.0,frame.CARD-12.5))
    sig=[s for s in memory.MLINK if s!='GND']
    if which=='ctl':
        frame.card_ribbon(w,66*G,52*G,set(sig),"LINK ribbon to the slot cards: MAR3..0, their complements, MIN, MON",pins=memory.MLINK,direction='output')
    else:
        frame.card_ribbon(w,66*G,52*G,set(sig),"LINK ribbon from the memory control card",pins=memory.MLINK,direction='input')
        frame.card_jumpers(w,66*G,64*G,['A3','A2','A1'],lambda k:(f'MAR{3-k}',f'MAR{3-k}N'),lambda k:f'X{3-k}')
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=[round(v,1) for v in sorted(w.rail_end.values())]
    print("wrote",OUT,"transistors",d.ntransistors(),"lowest stub per rail",fill)

if __name__=='__main__':
    a=sys.argv; main(a[1],a[a.index('--pack')+1] if '--pack' in a else 'column')
