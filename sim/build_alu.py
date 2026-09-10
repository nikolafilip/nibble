"""Generate boards/01-alu (KiCad project) from alu.py. Run from sim/."""
import os, sys
import ksch, alu, bus, tb_alu
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','01-alu')
PROJECT='alu'

import frame
def board_frame(w,used):
    """Bus header, decoupling, mounting holes. `used` = set of signals this board connects."""
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",26,14,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G); w.at(c1,118,6,270); w.at(c2,124,6,270); frame.cap_gnd(w,118,6,2.5); frame.cap_gnd(w,124,6,2.0)
    frame.holes(w,x+46*G,y-8*G,4)

def main():
    d=alu.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U(); tb_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 01 - ALU: 4-bit adder/subtractor, AND, OR, XOR, with carry and zero flags",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs.\n"
        "Inputs from the bus header: A3..A0, B3..B0 (register contents), SUB (1 = subtract), ONE (B input replaced by 0001: INC, DEC), F1 F0 (function), EO (1 = drive the result onto the bus).\n"
        "Outputs: CF (carry out; for SUB, 1 = no borrow; 0 for the logic functions), ZF (result is zero), BUS3#..BUS0# (open-drain, active-low: pulled low where the result bit is 1 and EO = 1).\n"
        "F1 F0 = 00: R = A + (B xor SUB) + SUB.   01: R = A and B.   10: R = A or B.   11: R = A xor B.   Gates read left to right, top to bottom: input labels on the left of each cell, output label on the right.\n"
        "Sheet 2 (TESTBENCH) holds the stimulus sources and the hub pull-ups; they are excluded from the board.",10*G,16*G,1.6)
    board_frame(w,{'A0','A1','A2','A3','B0','B1','B2','B3','SUB','ONE','F0','F1','EO','CF','ZF','BUS0#','BUS1#','BUS2#','BUS3#'})
    # header outputs: CF/ZF labels are outputs of gates; the header side uses the same global label
    cols=14; w.PCB_COL=12.7
    yend=w.layout(d.gates,alu.GROUP_TITLES,10*G,60*G,cols,pcb_origin=(8.0,22.0),pcb_cols=14)
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(8+14*12.7+4,w.pcb_extent[1]+4),extra=dict(silk_big=[("NIBBLE ALU",8+14*12.7-30,3,1.8)],hide_refs=['Q','R']))
    w.sheet("TESTBENCH",f"{PROJECT}-testbench.kicad_sch",x=10*G+cols*w.CELL_W+4*G,y=40*G,w=20*G,h=10*G,page="2",sheet_uuid=tb_uuid)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    # ---- testbench sheet ----
    t=ksch.Writer(PROJECT,root_uuid,tb_uuid)
    for k in t.n: t.n[k]=9001
    cases=tb_alu.demo_cases(); tend=len(cases)*tb_alu.T
    t.T("TESTBENCH for board 01.  Excluded from the board and the BOM.  Run the simulator (Inspect > Simulator) and plot R3..R0, CF, ZF, BUS3#..BUS0#.",10*G,6*G,2.5,True)
    txt="Case  A   B  controls  EO ->  R  CF ZF   (R = 4-bit result; bus lines go low where R has a 1 and EO=1)\n"
    for k,(a,b,ctl,eo) in enumerate(cases):
        S,cf,zf=tb_alu.expected(a,b,ctl)
        txt+=f"{k:2d}  {k*tb_alu.T*1e3:5.2f}..{(k+1)*tb_alu.T*1e3:5.2f} ms   A={a:2d} B={b:2d} {' '.join(ctl) or 'ADD':10s} EO={eo} -> R={S:2d} CF={cf} ZF={zf}\n"
    t.T(txt,10*G,40*G,1.5)
    t.T(f".tran 2u {tend:.4g}",10*G,44*G,1.6)
    x=12*G; y=24*G
    for line in tb_alu.sources(cases):
        parts=line.split(None,3); net=parts[1]; spec=parts[3]
        t.vsource("PWL",f'pwl=\\"{spec[4:-1]}\\"',x,y)
        t.W(x,y-2*G,x,y-3*G); t.L(net,x,y-3*G,90,'output'); t.PW('GND',x,y+2*G)
        x+=9*G
    # supply (lives on the hub board)
    t.T("5 V supply (from the hub board)",x+2*G,y-14*G,1.27)
    t.vsource("DC","5",x+4*G,y-10*G); t.W(x+4*G,y-12*G,x+4*G,y-13*G); t.PW('+5V',x+4*G,y-13*G); t.W(x+4*G,y-8*G,x+4*G,y-7*G); t.PW('GND',x+4*G,y-7*G)
    # hub pull-ups
    t.T("Hub pull-ups (these live on the bus hub board, not here)",x+2*G,y-8*G,1.27)
    for i in range(4):
        xx=x+2*G+i*6*G
        t.PW('+5V',xx,y-5.5*G); t.W(xx,y-5.5*G,xx,y-4.5*G)
        t.symbol("Device","R",t.ref('R'),tb_alu.HUB_PU,xx,y-3*G,0,('1','2'),"",[("Description","Resistor",True)],in_bom=False,on_board=False)
        t.W(xx,y-1.5*G,xx,y); t.L(f'BUS{i}#',xx,y,270,'bidirectional')
    open(os.path.join(OUT,f'{PROJECT}-testbench.kicad_sch'),'w').write(t.file(x+40*G,60*G))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"sheet",W,"x",H,"mm")

if __name__=='__main__': main()
