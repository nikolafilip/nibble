"""Generate boards/09-counter (KiCad project) from counter.py. Run from sim/."""
import os
import ksch, counter, bus, frame
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','09-counter')
PROJECT='counter'
PCB_COLS=18

def board_frame(w,used):
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",26,14,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G); w.at(c1,118,6,270); w.at(c2,124,6,270); frame.cap_gnd(w,118,6,2.5); frame.cap_gnd(w,124,6,2.0)
    frame.holes(w,x+46*G,y-8*G,4)
    lk=frame.link_header(w,x+62*G,y,'input'); w.at(lk,140,10,90)

def main():
    d=counter.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 09 - COUNTER: the 8-bit program counter and the return register",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs.\n"
        "From the bus header: PCE (count), PCL (load the jump target), CLK, RST.   To the bus header: PC7..PC0 (the program memory boards compare their page against PC7..4 and select a word with PC3..0).\n"
        "From board 03 (sequencer) over the LINK header: OPR7..0 (the jump target), PCR (load the return address), RAI (save the return address).\n"
        "PC: eight master-slave flip-flops; each bit's input is PC xor carry (count, or hold when PCE is low), OPR (PCL) or RA (PCR).  The count carry ripples through seven AND gates.\n"
        "RA: eight transparent latches open while RAI and PH1, so CALL captures the old PC during the low half of its execute tick and PC loads the target on the edge that follows.\n"
        "RST clears PC and RA.  docs/isa.md is the specification; sim/emu.py the reference the whole-machine simulation checks this board against.",10*G,18*G,1.6)
    used={'PCE','PCL','CLK','RST'}|{f'PC{i}' for i in range(8)}
    board_frame(w,used)
    cols=14; w.PCB_COL=12.7
    yend=w.layout(d.gates,counter.GROUP_TITLES,10*G,66*G,cols,pcb_origin=(8.0,22.0),pcb_cols=PCB_COLS)
    BW=8+PCB_COLS*12.7+4; BH=w.pcb_extent[1]+4
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE COUNTER",BW-36,3,1.8)],hide_refs=['Q','R'],rules=dict(track=0.2,clearance=0.15)))
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"sheet",W,"x",H,"mm, board",(BW,BH))

if __name__=='__main__': main()
