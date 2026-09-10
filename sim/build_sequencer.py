"""Generate boards/03-sequencer (KiCad project) from sequencer.py. Run from sim/."""
import os
import ksch, sequencer, bus, frame
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','03-sequencer')
PROJECT='sequencer'
PCB_COLS=22
TILE_W=8+PCB_COLS*12.7          # tiles occupy x = 8 .. TILE_W; the matrix sits to the right
MX=TILE_W+6                     # matrix origin x

def board_frame(w,used):
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",26,14,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G); w.at(c1,118,6,270); w.at(c2,124,6,270); frame.cap_gnd(w,118,6,2.5); frame.cap_gnd(w,124,6,2.0)
    frame.holes(w,x+46*G,y-8*G,4)
    lk=frame.link_header(w,x+62*G,y,'output'); w.at(lk,140,10,90)     # 2x6 at the top, right of the decoupling

def main():
    d=sequencer.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 03 - SEQUENCER: step counter, instruction and operand registers, flags, decoders and the diode control matrix",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.ndiodes()} matrix diodes, {d.nleds()} LEDs.\n"
        "From the bus header: M7..M0 (the program memory word), CF and ZF (from the ALU), CLK, RST.\n"
        "To the bus header: II, PCE and the matrix columns SUB EO AI AO BI BO BA AB OI IO PCL FI HLT MAI MI MO ONE F0 F1 INP; BUS3#..BUS0# driven (open drain) with OPR3..0 while IO.\n"
        "To board 09 (counter) over the LINK header: OPR7..0, PCR, RAI.  The program counter and the return register live there (D035).\n"
        "Steps S0..S4 are a one-hot ring of flip-flops: S0 loads IR/OPR (II), S1 counts (PCE), S2 loads the second word of a jump or call (OPI, PCE), S3 and S4 drive the matrix rows; DONE returns to S0.\n"
        "docs/isa.md is the specification; sim/emu.py the reference the whole-machine simulation checks this board against.",10*G,18*G,1.6)
    used={f'M{i}' for i in range(8)}|{'CF','ZF','CLK','RST','II','PCE'}|set(c for c in sequencer.COLS if c in bus.SIGNALS)|{'BUS0#','BUS1#','BUS2#','BUS3#'}
    board_frame(w,used)
    cols=14; w.PCB_COL=12.7
    tiles=[g for g in d.gates if g['kind'] not in ('DIODE','PD')]
    yend=w.layout(tiles,sequencer.GROUP_TITLES,10*G,66*G,cols,pcb_origin=(8.0,22.0),pcb_cols=PCB_COLS)
    # the matrix: rows in the order of the gate list, columns as sequencer.COLS
    rows=[]
    for net,name,step in d.rows:
        cap=f"{name or 'free'} S{step}" if name else f"OP{net.split('_')[1][2:]} (free) S{step}"
        rows.append((net,cap))
    rows+=[('R_JCC','JC if C (PCL)'),('R_JZZ','JZ if Z (PCL)')]
    diodes=[(g['ins'][0],g['out']) for g in d.gates if g['kind']=='DIODE']
    w.T("THE CONTROL MATRIX",10*G+cols*w.CELL_W+6*G,66*G-G,2.0,True)
    mh,(mxe,mye)=ksch.matrix(w,rows,[f'{c}_m' for c in sequencer.COLS],diodes,10*G+cols*w.CELL_W+6*G,66*G,(MX,22.0),caption=lambda c:c[:-2])   # columns are the diode nodes; the buffers (D041) drive the lines
    BW=max(mxe,w.pcb_extent[0])+4; BH=max(mye,w.pcb_extent[1])+4
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,BH),extra=dict(silk_big=[("NIBBLE SEQUENCER",BW-40,3,1.8)],hide_refs=['Q','R','D'],rules=dict(track=0.2,clearance=0.15)))
    W=10*G+cols*w.CELL_W+6*G+(len(sequencer.COLS)+10)*5*G+10*G; H=max(yend,66*G+mh)+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"diodes",d.ndiodes(),"sheet",W,"x",H,"mm, tiles",w.pcb_extent,"matrix to",(mxe,mye),"board",(BW,BH))

if __name__=='__main__': main()
