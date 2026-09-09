"""Generate boards/01-alu (KiCad project) from alu.py. Run from sim/."""
import os, sys
import ksch, alu, bus, tb_alu
G=ksch.G
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','boards','01-alu')
PROJECT='alu'

def board_frame(w,used):
    """Bus header, decoupling, mounting holes. `used` = set of signals this board connects."""
    x,y=30*G,40*G
    w.header(x,y)
    for pin,sig in bus.PINS.items():
        odd=pin%2==1; px=x-2*G if odd else x+3*G; py=y-12*G+((pin-1)//2)*G
        if sig in ('+5V','GND'):
            ex=px-3*G if odd else px+3*G
            w.W(px,py,ex,py); w.PW(sig,ex,py)
        elif sig in used:
            ex=px-4*G if odd else px+4*G
            w.W(px,py,ex,py); w.L(sig,ex,py,180 if odd else 0,'bidirectional' if sig.startswith('BUS') else 'input')
        else:
            w.body+=f'\t(no_connect\n\t\t(at {ksch.f(px)} {ksch.f(py)})\n\t\t(uuid "{ksch.U()}")\n\t)\n'
    # decoupling
    cx=x+16*G; cy=y-8*G
    for k,(val,pol) in enumerate([('100n',False),('10u',True)]):
        xx=cx+k*6*G
        w.PW('+5V',xx,cy-2.5*G); w.W(xx,cy-2.5*G,xx,cy-1.5*G); w.C(val,xx,cy,pol); w.W(xx,cy+1.5*G,xx,cy+2.5*G); w.PW('GND',xx,cy+2.5*G)
    w.T("Decoupling at the header",cx-2*G,cy-4*G,1.27)
    # power flags: the supply enters through the header
    fx=cx-8*G
    w.PW('+5V',fx,cy-2.5*G); w.W(fx,cy-2.5*G,fx,cy-1.5*G); w.pwr_flag(fx,cy-1.5*G)
    w.PW('GND',fx,cy+2.5*G); w.W(fx,cy+2.5*G,fx,cy+1.5*G); w.pwr_flag(fx,cy+1.5*G)
    for k in range(4): w.hole(cx+30*G+k*5*G,cy)
    w.T("Mounting holes",cx+28*G,cy-4*G,1.27)

def main():
    d=alu.build(); pr=d.check(); assert not pr, pr
    os.makedirs(OUT,exist_ok=True)
    root_uuid=ksch.U(); tb_uuid=ksch.U()
    w=ksch.Writer(PROJECT,root_uuid)
    w.T("NIBBLE BOARD 01 - ALU: 4-bit two's-complement adder/subtractor with carry and zero flags",10*G,6*G,3.5,True)
    w.T(f"Cell: 2N7000 + 47k pull-up (NMOS, see docs/gate-cell.md).  {d.ntransistors()} transistors, {d.nresistors()} resistors, {d.nleds()} LEDs.\n"
        "Inputs from the bus header: A3..A0, B3..B0 (register contents), SUB (1 = subtract), EO (1 = drive the result onto the bus).\n"
        "Outputs: CF (carry out; for SUB, 1 = no borrow), ZF (result is zero), BUS3#..BUS0# (open-drain, active-low: pulled low where the result bit is 1 and EO = 1).\n"
        "Result S = A + (B xor SUB) + SUB.  Gates read left to right, top to bottom: input labels on the left of each cell, output label on the right.\n"
        "Sheet 2 (TESTBENCH) holds the stimulus sources and the hub pull-ups; they are excluded from the board.",10*G,16*G,1.6)
    board_frame(w,{'A0','A1','A2','A3','B0','B1','B2','B3','SUB','EO','CF','ZF','BUS0#','BUS1#','BUS2#','BUS3#'})
    # header outputs: CF/ZF labels are outputs of gates; the header side uses the same global label
    cols=14
    yend=w.layout(d.gates,alu.GROUP_TITLES,10*G,60*G,cols)
    w.sheet("TESTBENCH",f"{PROJECT}-testbench.kicad_sch",x=10*G+cols*w.CELL_W+4*G,y=40*G,w=20*G,h=10*G,page="2",sheet_uuid=tb_uuid)
    W=10*G+cols*w.CELL_W+30*G; H=yend+10*G
    open(os.path.join(OUT,f'{PROJECT}.kicad_sch'),'w').write(w.file(W,H))
    # ---- testbench sheet ----
    t=ksch.Writer(PROJECT,root_uuid,tb_uuid)
    for k in t.n: t.n[k]=9001
    cases=tb_alu.demo_cases(); tend=len(cases)*tb_alu.T
    t.T("TESTBENCH for board 01.  Excluded from the board and the BOM.  Run the simulator (Inspect > Simulator) and plot S3..S0, CF, ZF, BUS3#..BUS0#.",10*G,6*G,2.5,True)
    txt="Case  A   B  SUB EO ->  S  CF ZF   (S = 4-bit result; bus lines go low where S has a 1 and EO=1)\n"
    for k,(a,b,s,eo) in enumerate(cases):
        S,cf,zf=tb_alu.expected(a,b,s)
        txt+=f"{k:2d}  {k*tb_alu.T*1e3:5.2f}..{(k+1)*tb_alu.T*1e3:5.2f} ms   A={a:2d} B={b:2d} {'SUB' if s else 'ADD'} EO={eo} -> S={S:2d} CF={cf} ZF={zf}\n"
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
