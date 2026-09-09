"""Generate muldiv.kicad_sch (logic) and testbench.kicad_sch (stimulus) from logic.py / tb.py."""
import sys; sys.path.insert(0,'.')
import kiw, logic, tb

G=2.54
GROUP_TITLES={
 'decode':'OP-CODE DECODE & BUFFERS   (OP1 OP0: 00=ADD 01=SUB 10=MUL 11=DIV).  SUB/SUB2 drive the root adder; SIGB drives the sign-magnitude converter (bug fix: was SUB).',
 'clock':'CLOCK BUFFERS',
 'sequencer':'SEQUENCER: one-hot ring L -> T1 -> T2 -> T3 -> DN, started by START when idle in MUL/DIV mode.  T=step phase, IDLE=hold, TM/TD=step&MUL / step&DIV, Q=division quotient bit',
 'amux':'ADDER A-OPERAND MUX: keypad A (ADD/SUB and during load), P[5:3] (MUL step), P[4:2] (DIV step)',
 'bgate':'ADDER B-OPERAND GATE: B = keypad B, forced to 0 in MUL mode when P0 = 0',
 'div0':'DIVIDE-BY-ZERO FLAG',
 'pnext':'P REGISTER NEXT-STATE (AND-OR per bit): load A / MUL shift-add / DIV restoring step / hold',
 'preg':'P REGISTER (6 master-slave D flip-flops, same cell as the root memory register).  MUL result: P[5:0]=product.  DIV result: P[2:0]=quotient, P[5:3]=remainder',
 'memdata':'MEMORY REGISTER DATA MUX: REG_D[3:0] <- converter output (ADD/SUB) or P[3:0] (MUL/DIV); REG_DS <- sign (ADD/SUB only); OUT_B4/OUT_B5 = two extra memory bits',
 'clkgate':'GLITCH-FREE MEMORY CLOCK GATE: MEMCLK = CLOCK while ADD/SUB; one pulse after DN in MUL/DIV (enable latched while CLOCK is low)',
}

class Gen:
    def __init__(self,path):
        self.path=path; self.body=''; self.q=2000; self.r=2000; self.p=2000
    def R(self,val,x,y,rot):
        self.body+=kiw.resistor(f"R{self.r}",val,x,y,rot,self.path); self.r+=1
    def Q(self,x,y):
        self.body+=kiw.transistor(f"Q{self.q}",x,y,0,self.path); self.q+=1
    def PW(self,name,x,y):
        self.body+=kiw.power(f"#PWR{self.p}",name,x,y,0,self.path); self.p+=1
    def W(self,x1,y1,x2,y2): self.body+=kiw.wire(x1,y1,x2,y2)
    def J(self,x,y): self.body+=kiw.junction(x,y)
    def L(self,name,x,y,rot,shape='input'): self.body+=kiw.glabel(name,x,y,rot,shape)
    def T(self,s,x,y,size=1.27,bold=False): self.body+=kiw.text(s,x,y,size,bold)

    def gate(self,g,x0,y0):
        """One gate cell. Returns cell height."""
        ins=g['ins']; n=len(ins); kind=g['kind']
        xq=x0+35.56; xc=xq+2.54; xbus=x0+43.18; xout=x0+48.26
        # pull-up
        self.PW('+5V',xc,y0+3.81)
        self.R(g['pu'],xc,y0+7.62,0)          # pins at y0+3.81 (top) and y0+11.43 (bottom)
        yc0=y0+15.24
        self.W(xc,y0+11.43,xc,yc0)
        self.W(xc,yc0,xout,yc0)
        self.L(g['out'],xout,yc0,0,'output')
        if n>1 or kind=='NOR': self.J(xc,yc0)
        for k,inp in enumerate(ins):
            yq=y0+20.32+15.24*k; yc=yq-5.08; ye=yq+5.08
            self.Q(xq,yq)
            # base network
            xb=xq-5.08; xj=x0+27.94; xr=x0+22.86
            self.R('10k',xr,yq,90)                 # pins at x0+19.05 / x0+26.67
            self.W(x0+26.67,yq,xb,yq)
            self.W(x0+19.05,yq,x0+15.24,yq)
            self.L(inp,x0+15.24,yq,180,'input')
            self.J(xj,yq)
            self.W(xj,yq,xj,yq+2.54)
            self.R('22k',xj,yq+6.35,0)             # pins yq+2.54 / yq+10.16
            self.PW('GND',xj,yq+10.16)
            if kind=='NAND':
                if k<n-1: self.W(xc,ye,xc,ye+5.08)     # emitter -> next collector
                else: self.PW('GND',xc,ye)
            else:
                self.PW('GND',xc,ye)
                if k>0:
                    self.W(xc,yc,xbus,yc); self.J(xc,yc) if False else None
                    if k==1: self.W(xbus,yc0,xbus,yc); self.J(xbus,yc0)
                    else: self.W(xbus,yc-15.24,xbus,yc); self.J(xbus,yc-15.24)
        return 15.24*n+25.4

def layout(gen, gates, x_start, y_start, cols, cell_w):
    """place gates group by group; each group starts a new row with a title. returns y after last row"""
    y=y_start
    groups=[]
    for g in gates:
        if not groups or groups[-1][0]!=g['group']: groups.append((g['group'],[]))
        groups[-1][1].append(g)
    for name,gs in groups:
        gen.T(GROUP_TITLES.get(name,name),x_start,y-2.54,2.0,True)
        y+=5.08
        # sub-rows of `cols` cells
        for i in range(0,len(gs),cols):
            row=gs[i:i+cols]; hmax=0
            for j,g in enumerate(row):
                h=gen.gate(g,x_start+j*cell_w,y); hmax=max(hmax,h)
            y+=hmax+7.62
        y+=7.62
    return y

def gen_muldiv(root_text, sub_uuid):
    d=logic.build()
    assert not d.check(), d.check()
    path=f"/{kiw.ROOT_UUID}/{sub_uuid}"
    gen=Gen(path)
    libs=[kiw.lib_symbol_block(root_text,n) for n in ["Device:R","Transistor_BJT:2N3904","power:+5V","power:GND"]]
    gen.T("MULTIPLY / DIVIDE EXTENSION  -  sequential shift-add multiplier and restoring divider re-using the root sheet's 3-bit adder/subtractor.",25.4,17.78,3.0,True)
    gen.T("Every cell is one RTL gate in the same style as the root sheet: 10k base resistor, 22k base pull-down, 4.7k collector pull-up (2.2k where a gate drives 4..6 inputs), stacked NPN = NAND, parallel NPN = NOR.\n"
          "Inputs from the root sheet: ENCA_N[2:0] / ENCB_N[2:0] (keypad encoders, active low), S[3:0] (raw adder sum), OUT[3:0] and SIG (sign-magnitude converter).  Inputs from the test bench: OP0, OP1, START, CLOCK.\n"
          "Outputs to the root sheet: A[2:0], EB[2:0] (adder operands), SUB/SUB2 (subtract control), SIGB (converter control), REG_D[3:0], REG_DS (memory register data), MEMCLK (memory register clock).  New memory bits: OUT_B4, OUT_B5.  Flag: DIV0.\n"
          "Sequence for MUL/DIV (5 clocks after START): L: P[2:0] <- A ; T1..T3: P <- step(P) ; DN: memory captures P on the next MEMCLK.   MUL: P[5:0] = A*B.   DIV: P[2:0] = A div B, P[5:3] = A mod B.",25.4,33.02,1.6)
    cols=20; cell_w=63.5
    yend=layout(gen,d.gates,25.4,50.8,cols,cell_w)
    w=25.4*2+cols*cell_w; h=yend+25.4
    return kiw.sheet_file(sub_uuid,w,h,libs,gen.body), d

def gen_testbench(root_text, lib_text_vpwl, tb_uuid):
    path=f"/{kiw.ROOT_UUID}/{tb_uuid}"
    gen=Gen(path); gen.p=9000
    libs=[kiw.lib_symbol_block(root_text,n) for n in ["power:GND","Simulation_SPICE:VPULSE"]]+[lib_text_vpwl]
    src,checks,tend,windows=tb.build_stimulus(tb.sequence())
    gen.T("TEST BENCH  -  drives the keypads (Y1..Y7 = operand A key, X1..X7 = operand B key), the op-code, START and CLOCK.  Run the simulator on this project and plot OUT_SIGN, OUT_B5..OUT_B0, DIV0.",25.4,17.78,3.0,True)
    seqtxt="Sequence (time window -> operation -> expected memory contents):\n"
    for (t0,t1,op,a,b) in windows:
        e=tb.expected(op,a,b)
        if e.get('div0'): want="DIV0 flag = 1"
        elif op=='DIV': want=f"quotient {e['q']} (OUT_B2..0), remainder {e['r']} (OUT_B5..3)"
        else: want=f"{'-' if e['sign'] else ''}{e['mag']}  (OUT_SIGN, OUT_B5..0)"
        seqtxt+=f"{t0*1e3:5.2f} .. {t1*1e3:5.2f} ms   {op} {a},{b}   ->   {want}\n"
    gen.T(seqtxt,25.4,120.0,1.6)
    gen.T(f".tran 1u {tend:.4g}",25.4,132.0,1.6)
    gen.T(".ic "+" ".join(f"v({n})=0" for n in tb.IC),25.4,136.0,1.6)
    gen.T("Clock: 100us period, rising edges at 50us+k*100us.  Inputs change 40us before a rising edge.  ADD/SUB windows are 3 clocks, MUL/DIV windows 7 clocks (START high for one clock, 5 clocks of sequencing, 1 clock to store).",25.4,142.0,1.6)
    # sources in a row
    x=38.1; y=60.96; k=1
    for line in src:
        t=line.split(None,3)
        ref=t[0]; net=t[1]; spec=t[3]
        if spec.startswith('PULSE'):
            v=spec[6:-1].split(); params=f"y1={v[0]} y2={v[1]} td={v[2]} tr={v[3]} tf={v[4]} tw={v[5]} per={v[6]}"
            gen.body+=kiw.vsource(f"V{100+k}","PULSE",params,x,y,path)
        else:
            pts=spec[4:-1]
            gen.body+=kiw.vsource(f"V{100+k}","PWL",f'pwl=\\"{pts}\\"',x,y,path)
        gen.W(x,y-5.08,x,y-8.89); gen.L(net,x,y-8.89,90,'output')
        gen.PW('GND',x,y+5.08)
        x+=25.4; k+=1
    return kiw.sheet_file(tb_uuid,600,160,libs,gen.body)

if __name__=='__main__':
    root_text=open('/Users/nikolafilip/Documents/Calculator/Untitled.kicad_sch').read()
    lib=open('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Simulation_SPICE.kicad_sym').read()
    i=lib.find('\t(symbol "VPWL"'); j=lib.find('\n\t(symbol "',i+10); vpwl=lib[i:j].replace('(symbol "VPWL"','(symbol "Simulation_SPICE:VPWL"',1)
    vpwl="\n".join("\t"+l for l in vpwl.split("\n"))+"\n"
    sub_uuid=kiw.U(); tb_uuid=kiw.U()
    txt,d=gen_muldiv(root_text,sub_uuid)
    open('out_muldiv.kicad_sch','w').write(txt)
    open('out_testbench.kicad_sch','w').write(gen_testbench(root_text,vpwl,tb_uuid))
    open('uuids.txt','w').write(f"{sub_uuid}\n{tb_uuid}\n")
    print("muldiv gates",len(d.gates),"transistors",d.ntransistors(),"size",len(txt))
