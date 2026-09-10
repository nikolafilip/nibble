"""Generate boards/04-program (KiCad project) from program.py plus the switch/diode array. Run from sim/.
Also writes program.map.json: which diode is word w bit i, so machine.py can close switches in the simulation."""
import os, json
import ksch, program, bus, frame
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','04-program')
PROJECT='program'

def board_frame(w,used):
    """Two bus headers wired pin for pin in parallel (D039): the hub's ribbon on the left one, the next page's on the
    right one, both on the top edge so a 10 cm hop joins pages side by side. Every line is carried, not just PC and M."""
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used,through=True); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",26,14,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    j=frame.bus_header(w,x+18*G,y,used,through=True); w.at(j,118,8,90); w.label("BUS to next page  (pin 1 left)",118,14,1.2); frame.header_gnd(w,118,8,-1)
    w.T("Both headers carry all 64 lines: the hub's ribbon on the left, the next page's on the right (D039).",x-8*G,y-20*G,1.6)
    frame.power_flags(w,x+28*G,y-8*G)
    c1,c2=frame.decoupling(w,x+36*G,y-8*G); w.at(c1,200,15,270); w.at(c2,206,15,270); frame.cap_gnd(w,200,15,2.5); frame.cap_gnd(w,206,15,2.0)
    frame.holes(w,x+56*G,y-8*G,4)

def word_block(w,n,x,y,pcb,mapping):
    """One word: DIP-8 with the row line on the left pins, a diode from each right pin to M7..M0 (top to bottom)."""
    sw=w.dipswitch(8,x,y,f"WORD {n}"); px,py=pcb; w.at(sw,px,py,0)
    top=y-4*G; bot=top+7*G
    w.W(x-3*G,top,x-3*G,bot); w.W(x-3*G,top,x-3*G,top-2*G); w.L(f'ROW{n}',x-3*G,top-2*G,90,'input')
    w.label(f"{n:2d}",px-5,py+8,1.2)
    for i in range(8):
        sy=top+i*G; bit=7-i
        if i not in (0,7): w.J(x-3*G,sy)
        w.W(x+3*G,sy,x+4*G,sy); d=w.diode(x+5.5*G,sy,180); w.W(x+7*G,sy,x+8*G,sy); w.L(f'M{bit}',x+8*G,sy,0,'output')   # rot 180: A on the left (switch), K on the right (M)
        w.at(d,px+18.3,py+i*2.54,180); mapping[d]=[n,bit]      # footprint rot 180: K pad at (x,y), A pad 7.62 to the left, next to the switch pin
        if n==0: w.label(f"M{bit}",px+20,py+i*2.54-0.8,0.7)
    return sw

def main():
    d=program.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 04 - PROGRAM MEMORY: 16 words of 8 bits on DIP switches, one page of 256",10*G,6*G,3.5,True)
    w.T(f"{d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs, 16 DIP-8 switches, 128 diodes.\n"
        "From the bus: PC7..PC0.   To the bus: M7..M0 through diodes (the hub holds M low; several pages OR together).   Two headers in parallel: hub in, next page out.\n"
        "PC3..0 select the word.  PC7..4 are compared with the four PAGE jumpers: each jumper picks PC(4+i) (pins 1-2, page bit = 1) or its inverse (pins 2-3, page bit = 0).\n"
        "A row line goes high while its word is selected and the page matches; every closed switch on that row pulls its M line high through a diode.  Closed = 1.\n"
        "Bit 7 (the top switch of each word) is the top bit of the opcode; bit 0 the low bit of the operand.  Blank memory (all open) reads 0000 0000 = NOP.",10*G,16*G,1.6)
    used={f'PC{i}' for i in range(8)}|{f'M{i}' for i in range(8)}
    board_frame(w,used)
    # page jumpers: 1x3 headers, pin 1 = PC(4+i), pin 2 = JS_i, pin 3 = PN_i
    w.T("PAGE JUMPERS: 1-2 = this page has a 1 in that bit, 2-3 = a 0.  All four on 2-3 = page 0 (addresses 0..15).",110*G,30*G,1.6,True)
    for i in range(4):
        x=118*G+i*12*G; y=36*G
        j=w.pinheader(3,x,y,f"PAGE{i}"); w.at(j,132+i*7,15,0)
        w.W(x-2*G,y-G,x-4*G,y-G); w.L(f'PC{i+4}',x-4*G,y-G,180,'input')
        w.W(x-2*G,y,x-4*G,y); w.L(f'JS{i}',x-4*G,y,180,'output')
        w.W(x-2*G,y+G,x-4*G,y+G); w.L(f'PN{i}',x-4*G,y+G,180,'input')
    w.label("PAGE jumpers 3 2 1 0",132,13.3,1.0)
    cols=14; w.PCB_COL=12.7
    yend=w.layout(d.gates,program.GROUP_TITLES,10*G,60*G,cols,pcb_origin=(8.0,22.0),pcb_cols=8)
    # the switch array: 16 words in two columns of eight, to the right of the tiles
    mapping={}
    w.T("THE PROGRAM: 16 words, bit 7 at the top of each switch",10*G,yend+4*G,2.0,True)
    ax0=8+8*12.7+10
    for n in range(16):
        c,r=divmod(n,8)
        word_block(w,n,16*G+(n%4)*20*G,yend+12*G+(n//4)*12*G,(ax0+c*40,24+r*27),mapping)
    BW=ax0+2*40+16; BH=max(w.pcb_extent[1],24+8*27)+4     # 12 mm wider than the switch array needs: two 64-way headers plus the corner hole span the top edge
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE PROGRAM MEMORY",BW-56,BH-4,1.8)],hide_refs=['Q','R','D']))
    json.dump(dict(diodes=mapping,jumpers={f'JS{i}':[f'PC{i+4}',f'PN{i}'] for i in range(4)}),open(os.path.join(OUT,f'{PROJECT}.map.json'),'w'),indent=0)
    W=10*G+cols*w.CELL_W+30*G; H=yend+12*G+4*12*G+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"board",(BW,BH),"tiles",w.pcb_extent)

if __name__=='__main__': main()
