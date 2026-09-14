"""Generate cards/ctr<i> (KiCad project) from counter.build_bit(i): the counter bit card (docs/cards.md).
Run from sim/:  python3 build_ctr_card.py <bit> [--pack skyline|column]"""
import os, sys
import ksch, counter, frame
G=ksch.G
HERE=os.path.dirname(os.path.abspath(__file__))
LINK_PINS=lambda t:[t,'GND','GND','GND','GND','GND']      # the 2x3 neighbour link: the count carry on pin 1

def main(i,pack='column'):
    d=counter.build_bit(i); pr=d.check(); assert not pr, pr
    OUT=os.path.join(HERE,'..','cards',f'ctr{i}'); PROJECT=f'ctr{i}'
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid); w.HCOL=frame.RIBBON_HCOL
    w.T(f"NIBBLE CARD CTR{i} - COUNTER BIT {i}: program counter bit {i} and return register bit {i}",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 100 x 100 mm (docs/cards.md).\n"
        f"From the bus header: PCE (count), PCL (load the jump target), CLK, RST.   To the bus header: PC{i}.\n"
        f"From the sequencer over the LINK ribbon (2x6, chained along the eight counter cards): OPR{i} (the jump target bit), PCR (load the return address), RAI (save the return address).\n"
        +(f"Count carry TC{i} in from bit {i-1} over the IN link" if i else "Bit 0 counts on PCE itself")+(f"; TC{i+1} = TC{i} and PC{i} out to bit {i+1} over the OUT link.\n" if i<7 else "; the carry chain ends here.\n")+
        f"PC{i}: a master-slave flip-flop whose input is PC xor carry (count, or hold when PCE is low), OPR{i} (PCL) or RA{i} (PCR).  RA{i}: a transparent latch open while RAI and PH1.  RST clears both.\n"
        "docs/isa.md is the specification; sim/emu.py the reference the whole-machine simulation checks the cards against.",10*G,18*G,1.6)
    used={'PCL','CLK','RST',f'PC{i}'}|({'PCE'} if i==0 else set())     # PCE counts bit 0; the others take the carry
    cols=8
    yend=w.layout(d.gates,counter.CARD_TITLES,10*G,66*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=frame.COLS,pack=pack)
    extra=frame.card_frame(w,30*G,40*G,used,f"NIBBLE  COUNTER BIT {i}",name_xy=(44.0,frame.CARD-12.5))
    frame.card_links(w,66*G,40*G,LINK_PINS(f'TC{i}') if i else None,LINK_PINS(f'TC{i+1}') if i<7 else None,'bit')
    frame.card_ribbon(w,66*G,52*G,{f'OPR{i}','PCR','RAI'},f"LINK ribbon from the sequencer: this card takes OPR{i}, PCR and RAI")
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=[round(v,1) for v in sorted(w.rail_end.values())]
    print("wrote",OUT,"transistors",d.ntransistors(),"lowest stub per rail",fill)

if __name__=='__main__':
    a=sys.argv; main(int(a[1]),a[a.index('--pack')+1] if '--pack' in a else 'column')
