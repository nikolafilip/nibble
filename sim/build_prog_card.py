"""Generate cards/prog (KiCad project) from program.build_card(): the program card, four words of eight switches on
one page and word group set by jumpers (docs/cards.md). Run from sim/:  python3 build_prog_card.py [--pack skyline|column]
Also writes prog.map.json: which diode is word w bit i, so machine.py can close switches in the simulation."""
import os, sys, json
import ksch, program, frame
G=ksch.G
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'..','cards','prog'); PROJECT='prog'
WORD_XY=[(57.0,34.0),(74.0,34.0),(57.0,60.0),(74.0,60.0)]      # DIP-16 pin 1 of word 0..3: two by two right of the six tile columns, below the decoupling caps, clear of the right hole
JUMPER_HX=[14.0+9.5*k for k in range(6)]                    # six 1x3 jumpers along the bottom edge, PC7 leftmost

def word_block(w,n,x,y,pcb,mapping):
    """One word: DIP-8 with the row line on the left pins, a diode from each right pin to M7..M0 (top to bottom).
    PCB: the switch at pcb (pin 1), the diode of bit 7-i standing at row i to its right (vertical DO-35, A pad next to the pin, K pad 12.7 mm right of pin 1)."""
    sw=w.dipswitch(8,x,y,f"WORD {n}"); px,py=pcb; w.at(sw,px,py,0)
    top=y-4*G; bot=top+7*G
    w.W(x-3*G,top,x-3*G,bot); w.W(x-3*G,top,x-3*G,top-2*G); w.L(f'ROW{n}',x-3*G,top-2*G,90,'input')
    for i in range(8):
        sy=top+i*G; bit=7-i
        if i not in (0,7): w.J(x-3*G,sy)
        w.W(x+3*G,sy,x+4*G,sy); d=w.diode(x+5.5*G,sy,180,foot=w.D_FOOT_V); w.W(x+7*G,sy,x+8*G,sy); w.L(f'M{bit}',x+8*G,sy,0,'output')   # rot 180: A on the left (switch), K on the right (M)
        w.at(d,px+12.7,py+i*2.54,180); mapping[d]=[n,bit]      # footprint rot 180: K pad at (x,y), A pad 2.54 to the left, next to the switch pin
        if px==WORD_XY[1][0]: w.label(f"M{bit}",px+14.6,py+i*2.54-0.4,0.8)
    w.label(f"WORD {n}",px-1.0,py-4.4,0.8)
    return sw

def main(pack='column'):
    d=program.build_card(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.DenseWriter(PROJECT,root_uuid); w.HCOL=frame.LINK_HCOL
    w.T("NIBBLE CARD PROG - PROGRAM MEMORY: four words of 8 bits on DIP switches, jumpered to their place in the 256-word space",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 4 DIP-8 switches, 32 diodes, 100 x 100 mm (docs/cards.md).  One design, one card per four words.\n"
        "From the bus: PC7..PC0.   To the bus: M7..M0 through diodes (the hub holds M low; the cards OR together).\n"
        "PC1..0 select the word.  PC7..2 are compared with the six jumpers: jumper k picks PC(k) (pins 2-3, '1') or its inverse (pins 1-2, '0'); the card holds addresses 4c..4c+3 where c = PC7..2.\n"
        "A row line goes high while its word is selected and the card matches; every closed switch on that row pulls its M line high through a diode.  Closed = 1.\n"
        "Bit 7 (the top switch of each word) is the top bit of the opcode; bit 0 the low bit of the operand.  Blank memory (all open) reads 0000 0000 = NOP.",10*G,18*G,1.6)
    used={f'PC{i}' for i in range(8)}|{f'M{i}' for i in range(8)}
    cols=6
    yend=w.layout(d.gates,program.CARD_TITLES,10*G,66*G,cols,pcb_origin=(frame.X0,frame.Y0),pcb_cols=6,pack=pack)
    extra=frame.card_frame(w,30*G,40*G,used,"NIBBLE  PROGRAM",name_xy=(72.0,frame.CARD-1.8)); extra['hide_refs'].append('SW')
    frame.card_jumpers(w,66*G,52*G,['P7','P6','P5','P4','G3','G2'],lambda k:(f'PN{7-k}',f'PC{7-k}'),lambda k:f'JS{7-k}',hx=JUMPER_HX,
                       title="ADDRESS JUMPERS: P7..P4 the page (PC7..4), G3 G2 the word group (PC3..2): the centre pin to '1' where the address bit is 1, to '0' where it is 0")
    mapping={}
    w.T("THE PROGRAM: 4 words, bit 7 at the top of each switch",10*G,yend+4*G,2.0,True)
    for n in range(4): word_block(w,n,16*G+n*20*G,yend+12*G,WORD_XY[n],mapping)
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(frame.CARD,frame.CARD),extra=extra)
    json.dump(dict(diodes=mapping,jumpers={f'JS{k}':[f'PN{k}',f'PC{k}'] for k in range(2,8)}),open(os.path.join(OUT,f'{PROJECT}.map.json'),'w'),indent=0)
    W=10*G+cols*w.CELL_W+30*G; H=yend+12*G+12*G+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    fill=[round(v,1) for v in sorted(w.rail_end.values())]
    print("wrote",OUT,"transistors",d.ntransistors(),"lowest stub per rail",fill)

if __name__=='__main__':
    a=sys.argv; main(a[a.index('--pack')+1] if '--pack' in a else 'column')
