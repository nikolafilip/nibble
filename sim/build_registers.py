"""Generate boards/02-registers (KiCad project) from registers.py. Run from sim/."""
import os
import ksch, registers, bus, frame, tb_registers
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','02-registers')
PROJECT='registers'
BW=8+20*12.7+4   # board width (mm): 20 tile columns
PCB_COLS=20

def board_frame(w,used):
    x,y=30*G,40*G
    j=frame.bus_header(w,x,y,used); w.at(j,26,8,90); w.label("BUS  (pin 1 left)",26,14,1.2); frame.header_gnd(w,26,8,-1,y_gnd_trunk=16)
    frame.power_flags(w,x+8*G,y-8*G)
    c1,c2=frame.decoupling(w,x+16*G,y-8*G); w.at(c1,118,6,270); w.at(c2,124,6,270); frame.cap_gnd(w,118,6,2.5); frame.cap_gnd(w,124,6,2.0)
    frame.holes(w,x+46*G,y-8*G,4)

def main():
    d=registers.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U(); tb_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 02 - REGISTERS: A, B and OUT, three 4-bit registers on the bus",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs.\n"
        "From the bus header: BUS3#..BUS0# (data, active low), CLK, and the control lines AI AO BI BO BA AB OI (docs/isa.md).\n"
        "To the bus header: A3..A0 and B3..B0 (register contents, for the ALU and the panel); BUS3#..BUS0# driven open-drain when AO or BO.\n"
        "Every register is four master-slave D flip-flops. A two-phase clock (PH1, PH2) derived from CLK makes the masters transparent while CLK is low\n"
        "and copies them to the slaves on the rising edge. In front of each bit an AND-OR mux selects: A <- bus (AI), B (AB) or hold; B <- bus (BI), A (BA) or hold; OUT <- bus (OI) or hold.\n"
        "AB and BA together exchange A and B in one clock. A, B and OUT have no reset: they power up in whatever state the latches fall into.\n"
        "Sheet 2 (TESTBENCH) holds the clock, control stimulus, bus drivers and hub pull-ups; it is excluded from the board.",10*G,18*G,1.6)
    board_frame(w,{'BUS0#','BUS1#','BUS2#','BUS3#','CLK','AI','AO','BI','BO','BA','AB','OI','A0','A1','A2','A3','B0','B1','B2','B3'})
    cols=14; w.PCB_COL=12.7
    yend=w.layout(d.gates,registers.GROUP_TITLES,10*G,66*G,cols,pcb_origin=(8.0,22.0),pcb_cols=PCB_COLS)
    ksch.write_plan(w,os.path.join(OUT,f'{PROJECT}.plan.json'),(BW,w.pcb_extent[1]+4),extra=dict(silk_big=[("NIBBLE REGISTERS",BW-40,3,1.8)],hide_refs=['Q','R'],rules=dict(track=0.2,clearance=0.15)))
    w.sheet("TESTBENCH",f"{PROJECT}-testbench.kicad_sch",x=10*G+cols*w.CELL_W+4*G,y=40*G,w=20*G,h=10*G,page="2",sheet_uuid=tb_uuid)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    # ---- testbench sheet: the tb_registers script as PWL sources, a clock, diode bus drivers, supply, hub pull-ups ----
    t=ksch.Writer(PROJECT,root_uuid,tb_uuid)
    for k in t.n: t.n[k]=9001
    s=tb_registers.script(); exp=tb_registers.expected(s)
    T,T0,DELAY=tb_registers.T,tb_registers.T0,tb_registers.DELAY
    edges=[T0+k*T for k in range(len(s))]; starts=[e-T+DELAY for e in edges]
    t.T("TESTBENCH for board 02.  Excluded from the board and the BOM.  Run the simulator (Inspect > Simulator) and plot A3..A0, B3..B0, OUT3..OUT0, BUS3#..BUS0#.\n"
        "The clock rises every 1 ms from 2 ms; the control lines and the bus data change 20 us after each rising edge (as the sequencer would).",10*G,6*G,2.5,True)
    txt="Case   edge   controls      bus in  -> A   B  OUT  (values sampled just before that edge; - = not yet written)\n"
    for k,((ctl,v),e) in enumerate(zip(s,exp)):
        f=lambda x:'-' if x is None else f"{x:2d}"
        txt+=f"{k:3d}  {edges[k]*1e3:5.1f} ms  {' '.join(sorted(ctl)) or '(hold)':12s} {'-' if v is None else f'{v:2d}':>4s}   -> {f(e['a']):>2s}  {f(e['b']):>2s}  {f(e['out']):>3s}\n"
    t.T(txt,10*G,120*G,1.2)
    t.T(f".tran 1u {edges[-1]+T/2:.4g}",10*G,124*G,1.6)
    x=12*G; y=24*G
    t.vsource("PULSE",f'pulse=\\"0 5 {T0:.6g} 1u 1u {T/2-1e-6:.6g} {T:.6g}\\"',x,y); t.W(x,y-2*G,x,y-3*G); t.L('CLK',x,y-3*G,90,'output'); t.PW('GND',x,y+2*G); x+=9*G
    for c in tb_registers.CTL:
        spec=tb_registers.pwl(starts,[int(c in ctl) for ctl,v in s])
        t.vsource("PWL",f'pwl=\\"{spec[4:-1]}\\"',x,y); t.W(x,y-2*G,x,y-3*G); t.L(c,x,y-3*G,90,'output'); t.PW('GND',x,y+2*G); x+=9*G
    # bus data: a source per bit through a diode, so a 0 V source pulls BUS_i# low (like an open-drain driver) and a 5 V source lets it float
    t.T("Bus data in: BUS_i# is pulled low through a diode when the source is 0 V (the sequencer's operand register does the same with a transistor)",12*G,y+6*G,1.27)
    for i in range(4):
        spec=tb_registers.pwl(starts,[1-(((v or 0)>>i)&1) for ctl,v in s])
        xx=12*G+i*9*G; yy=y+12*G
        t.vsource("PWL",f'pwl=\\"{spec[4:-1]}\\"',xx,yy); t.PW('GND',xx,yy+2*G)
        t.W(xx,yy-2*G,xx,yy-3.5*G); dd=t.diode(xx,yy-5*G,90); t.W(xx,yy-6.5*G,xx,yy-8*G); t.L(f'BUS{i}#',xx,yy-8*G,90,'bidirectional')   # rot 90: A at yy-6.5G (bus side), K at yy-3.5G
    # supply and hub pull-ups
    frame.supply(t,x+4*G,y)
    t.T("Hub pull-ups (these live on the bus hub board, not here)",x+10*G,y-8*G,1.27)
    for i in range(4):
        xx=x+10*G+i*6*G
        t.PW('+5V',xx,y-5.5*G); t.W(xx,y-5.5*G,xx,y-4.5*G)
        t.symbol("Device","R",t.ref('R'),tb_registers.HUB_PU,xx,y-3*G,0,('1','2'),"",[("Description","Resistor",True)],in_bom=False,on_board=False)
        t.W(xx,y-1.5*G,xx,y); t.L(f'BUS{i}#',xx,y,270,'bidirectional')
    open(os.path.join(OUT,f'{PROJECT}-testbench.kicad_sch'),'w').write(t.file(x+40*G,130*G))
    open(os.path.join(OUT,f'{PROJECT}.kicad_pro'),'w').write(ksch.project_file(PROJECT))
    print("wrote",OUT,"transistors",d.ntransistors(),"sheet",W,"x",H,"mm, pcb extent",w.pcb_extent)

if __name__=='__main__': main()
