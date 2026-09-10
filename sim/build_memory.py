"""Generate boards/08-memory (KiCad project) from memory.py. Run from sim/."""
import os
import ksch, memory, bus, frame
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','08-memory')
PROJECT='memory'
PCB_COLS=28

def board_frame(w,used):
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",28,3,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G); w.at(c1,118,6,270); w.at(c2,124,6,270); frame.cap_gnd(w,118,6,2.5); frame.cap_gnd(w,124,6,2.0)
    frame.holes(w,x+46*G,y-8*G,4)

def main():
    d=memory.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 08 - DATA MEMORY: 16 slots of 4 bits, with its own address register",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs.\n"
        "From the bus header: BUS3#..BUS0# (an address while MAI, data while MI), MAI, MI, MO, CLK.   To the bus: BUS3#..BUS0# driven (open drain) with the addressed slot while MO.\n"
        "The address register is four transparent latches open while MAI and PH1 (S3 of a memory instruction, when B or the operand is on the bus).\n"
        "A 4-to-16 decoder selects the slot.  A cell is two cross-coupled inverters; while WR (slot and MI) the bus data forces it, while RD (slot and MO) it pulls its bus line.\n"
        "Every cell has an LED: the memory is visible.  Nothing here is reset: memory keeps its contents through RST, and powers up random (programs write before they read).\n"
        "docs/isa.md is the specification; sim/emu.py the reference the whole-machine simulation checks this board against.",10*G,18*G,1.6)
    used={'BUS0#','BUS1#','BUS2#','BUS3#','MAI','MI','MO','CLK'}
    board_frame(w,used)
    cols=14; w.PCB_COL=12.7
    yend=w.layout(d.gates,memory.GROUP_TITLES,10*G,66*G,cols,pcb_origin=(8.0,22.0),pcb_cols=PCB_COLS)
    BW=8+PCB_COLS*12.7+4; BH=w.pcb_extent[1]+4
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE DATA MEMORY",BW-44,3,1.8)],hide_refs=['Q','R'],rules=dict(track=0.2,clearance=0.15)))
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"sheet",W,"x",H,"mm, board",(BW,BH))

if __name__=='__main__': main()
