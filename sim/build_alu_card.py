"""Generate cards/alu<i> (KiCad project) from alu.build_bit(i): the ALU bit card (docs/cards.md).
Run from sim/:  python3 build_alu_card.py <bit> [--pack skyline|column]"""
import os, sys
import ksch, alu, frame
G=ksch.G
HERE=os.path.dirname(os.path.abspath(__file__))
LINK_PINS=lambda c,z:[c,'GND',z,'GND','GND','GND']      # the 2x3 neighbour link: carry, zero-so-far, the rest ground

def main(i,pack='column'):
    d=alu.build_bit(i); pr=d.check(); assert not pr, pr
    OUT=os.path.join(HERE,'..','cards',f'alu{i}'); PROJECT=f'alu{i}'
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid); w.HCOL=frame.LINK_HCOL
    w.T(f"NIBBLE CARD ALU{i} - ALU BIT {i}: one bit of the adder/subtractor, AND, OR, XOR",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 100 x 100 mm (docs/cards.md).\n"
        f"From the bus header: A{i}, B{i} (register bits), SUB (1 = subtract), ONE (B replaced by 0001: INC, DEC), F1 F0 (function), EO (1 = drive the result onto the bus).\n"
        f"To the bus header: BUS{i}# (open-drain, active-low: pulled low when the result bit is 1 and EO = 1)"+(", CF (carry out; for SUB, 1 = no borrow; 0 for the logic functions), ZF (result is zero).\n" if i==3 else ".\n")+
        (f"Links: carry C{i} and zero-so-far ZS{i-1} in from bit {i-1}" if i else "Links: bit 0 starts the carry (SUB) and the zero chain")+(f"; C{i+1} and ZS{i} out to bit {i+1}.\n" if i<3 else "; the chains end here in CF and ZF.\n")+
        "F1 F0 = 00: R = A + (B xor SUB) + SUB.   01: R = A and B.   10: R = A or B.   11: R = A xor B.  The four bit cards are this design with the bit baked in.",10*G,18*G,1.6)
    used={f'A{i}',f'B{i}','SUB','ONE','F0','F1','EO',f'BUS{i}#'}|({'CF','ZF'} if i==3 else set())
    cols=8
    yend=w.layout(d.gates,alu.CARD_TITLES,10*G,66*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=frame.COLS,pack=pack)
    extra=frame.card_frame(w,30*G,40*G,used,f"NIBBLE  ALU BIT {i}")
    frame.card_links(w,66*G,40*G,LINK_PINS(f'C{i}',f'ZS{i-1}') if i else None,LINK_PINS(f'C{i+1}',f'ZS{i}') if i<3 else None,'bit')
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=[round(v,1) for v in sorted(w.rail_end.values())]
    print("wrote",OUT,"transistors",d.ntransistors(),"lowest stub per rail",fill)

if __name__=='__main__':
    a=sys.argv; main(int(a[1]),a[a.index('--pack')+1] if '--pack' in a else 'column')
