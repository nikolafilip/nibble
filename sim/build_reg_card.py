"""Generate cards/reg<i> (KiCad project) from registers.build_bit(i): the register bit card (docs/cards.md).
Run from sim/:  python3 build_reg_card.py <bit> [--pack skyline|column]"""
import os, sys
import ksch, registers, frame
G=ksch.G
HERE=os.path.dirname(os.path.abspath(__file__))

CARD_TITLES={
 'clock':'TWO-PHASE CLOCK (one per card): PH1 = NOR(CLK, PH2) opens the masters while CLK is low, PH2 = NOR(CLKN, PH1) opens the slaves while CLK is high.  The cross-coupling means a phase cannot start rising until the other is fully low, so a flip-flop is never transparent.',
 'busin':'BUS INPUT: D = NOT BUS# (the bus is active low)',
 'muxA':'REGISTER A INPUT MUX: DA = AI.D + AB.B + HOLDA.A, HOLDA = NOR(AI, AB).  NAND-NAND form: three 2-input NANDs into a 3-input NAND',
 'regA':'REGISTER A: master-slave D flip-flop, 22k pull-up on Q (A feeds the ALU, the panel, both muxes and the bus driver)',
 'muxB':'REGISTER B INPUT MUX: DB = BI.D + BA.A + HOLDB.B',
 'regB':'REGISTER B',
 'muxO':'OUT REGISTER INPUT MUX: DO = OI.D + OIN.OUT',
 'regO':'OUT REGISTER (the display)',
 'drv':'BUS DRIVER: pull BUS# low when AO.A or BO.B',
 'leds':'INDICATORS: OUT, A, B',
}

def main(i,pack='column'):
    d=registers.build_bit(i); pr=d.check(); assert not pr, pr
    OUT=os.path.join(HERE,'..','cards',f'reg{i}'); PROJECT=f'reg{i}'
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid); w.HCOL=frame.HCOL
    w.T(f"NIBBLE CARD REG{i} - REGISTER BIT {i}: bit {i} of A, B and OUT",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 100 x 100 mm (docs/cards.md).\n"
        f"From the bus header: BUS{i}# (data, active low), CLK, and the control lines AI AO BI BO BA AB OI (docs/isa.md).\n"
        f"To the bus header: A{i} and B{i} (for the ALU and the panel); BUS{i}# driven open-drain when AO or BO.\n"
        "Each register bit is a master-slave D flip-flop. The card's own two-phase clock (PH1, PH2) makes the masters transparent while CLK is low\n"
        "and copies them to the slaves on the rising edge. In front of each flip-flop an AND-OR mux selects: A <- bus (AI), B (AB) or hold; B <- bus (BI), A (BA) or hold; OUT <- bus (OI) or hold.\n"
        "AB and BA together exchange A and B in one clock. A, B and OUT have no reset. The four bit cards are this design with the bit baked in.",10*G,18*G,1.6)
    used={f'BUS{i}#','CLK','AI','AO','BI','BO','BA','AB','OI',f'A{i}',f'B{i}'}
    cols=8
    yend=w.layout(d.gates,CARD_TITLES,10*G,66*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=frame.COLS,pack=pack)
    extra=frame.card_frame(w,30*G,40*G,used,f"NIBBLE  REGISTER BIT {i}")
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=[round(v,1) for v in sorted(w.rail_end.values())]
    print("wrote",OUT,"transistors",d.ntransistors(),"sheet",W,"x",H,"mm; lowest stub per rail",fill)

if __name__=='__main__':
    a=sys.argv; main(int(a[1]),a[a.index('--pack')+1] if '--pack' in a else 'column')
