"""Gate-level description of the MUL/DIV extension in the schematic's RTL family:
10k base resistor, 22k base pull-down, 4.7k (or 2.2k for high fan-out) collector pull-up,
series-stacked NPNs = NAND, parallel NPNs = NOR."""
import collections

MAX_LOADS={'4.7k':3,'2.2k':6}

class Design:
    def __init__(self):
        self.gates=[]          # dicts: out, kind, ins, pu, group
        self.group='misc'
        self.ext_loads=collections.Counter()   # loads that live in the root sheet
        self.notes={}
    def g(self,kind,out,ins,pu='4.7k'):
        self.gates.append(dict(kind=kind,out=out,ins=list(ins),pu=pu,group=self.group)); return out
    def nand(self,out,*ins,pu='4.7k'): return self.g('NAND',out,ins,pu)
    def nor(self,out,*ins,pu='4.7k'):  return self.g('NOR',out,ins,pu)
    def inv(self,out,a,pu='4.7k'):     return self.g('NAND',out,[a],pu)
    def ff(self,q,d,clk,qpu='4.7k'):
        """Master-slave D flip-flop, exact copy of the register cell used in the root sheet (20 BJTs)."""
        p=q+'.'
        self.inv(p+'CLKN',clk,pu='2.2k')
        self.inv(p+'CLKB',p+'CLKN')
        self.inv(p+'DN',d)
        self.nand(p+'M1',d,p+'CLKN')
        self.nand(p+'M2',p+'CLKN',p+'DN')
        self.nand(p+'MQ',p+'M1',p+'MQN')
        self.nand(p+'MQN',p+'MQ',p+'M2')
        self.inv(p+'MQI',p+'MQ')
        self.nand(p+'S1',p+'MQ',p+'CLKB')
        self.nand(p+'S2',p+'CLKB',p+'MQI')
        self.nand(q,p+'S1',p+'QN',pu=qpu)
        self.nand(p+'QN',q,p+'S2')
        return q
    # ---- checks ----
    def loads(self):
        c=collections.Counter(self.ext_loads)
        for g in self.gates:
            for i in g['ins']: c[i]+=1
        return c
    def check(self):
        c=self.loads(); outs={g['out']:g for g in self.gates}; problems=[]
        for net,n in c.items():
            if net in outs:
                pu=outs[net]['pu']
                if n>MAX_LOADS[pu]: problems.append(f"{net}: {n} loads on {pu} pull-up")
        dup=[o for o,k in collections.Counter(g['out'].lower() for g in self.gates).items() if k>1]
        if dup: problems.append("duplicate outputs "+str(dup))
        return problems
    def ntransistors(self): return sum(len(g['ins']) for g in self.gates)

def build():
    d=Design()
    # ---------------- op-code decode & buffers ----------------
    d.group='decode'
    d.inv('OP0N','OP0',pu='2.2k')        # loads: SUB,SUB2,TM_N,X_N
    d.inv('SUB','OP0N',pu='2.2k')        # root: Cin0 gate (3) + SIG gate (1)
    d.inv('SUB2','OP0N',pu='2.2k')       # root: B conditional inverters (6)
    d.inv('OP1NA','OP1',pu='2.2k')       # selAS  -> memory data mux (4) + REG_DS
    d.inv('OP1NB','OP1',pu='2.2k')       # selAS  -> OP1BA, OP1BB, KSEL_N, EN_N
    d.inv('OP1BA','OP1NB',pu='2.2k')     # selMD  -> memory data mux (4) + L_D
    d.inv('OP1BB','OP1NB',pu='2.2k')     # selMD  -> D4, D5, X_N, DIV0_N
    d.inv('SIGN_','SIG')
    d.inv('SIGB','SIGN_',pu='2.2k')      # root: sign-magnitude converter XORs (6)  [bug fix]
    d.inv('SIGB2','SIGN_')               # REG_DS
    # ---------------- clock distribution ----------------
    d.group='clock'
    d.inv('CK_N','CLOCK',pu='2.2k')
    d.inv('CK1','CK_N',pu='2.2k')        # sequencer FFs L,T1,T2,T3,DN + clock gate
    d.inv('CK2','CK_N',pu='2.2k')        # P0..P5 FFs
    # ---------------- sequencer (one-hot ring) ----------------
    d.group='sequencer'
    d.nor('BUSY_N','L','T1','T2','T3','DN')
    d.nand('L_N_D','START','OP1BA','BUSY_N')
    d.inv('L_D','L_N_D')
    d.ff('L','L_D','CK1',qpu='2.2k')     # loads: T1 ff(2), L_N, BUSY_N, IDLE, QN
    d.inv('L_N','L')
    d.inv('LB','L_N',pu='2.2k')          # NEXT0..2, KSEL_N
    d.ff('T1','L','CK1',qpu='2.2k')
    d.ff('T2','T1','CK1',qpu='2.2k')
    d.ff('T3','T2','CK1',qpu='2.2k')
    d.ff('DN','T3','CK1')
    d.nor('T_N','T1','T2','T3')
    d.inv('T','T_N',pu='2.2k')           # TM_N, TD_N, IDLE
    d.nor('IDLE','L','T',pu='2.2k')      # NEXT0..5
    d.nand('TM_N','T','OP0N')
    d.inv('TMA','TM_N')                  # A-mux (3)
    d.inv('TMB','TM_N',pu='2.2k')        # NEXT0..5
    d.nand('TD_N','T','OP0')
    d.inv('TDA','TD_N')                  # A-mux (3)
    d.inv('TDB','TD_N',pu='2.2k')        # NEXT0..2, TDQ_N, TDNQ_N
    d.nor('Q_N','P5','S3')               # q = restore-or-not decision for division
    d.inv('QD','Q_N')
    d.nand('TDQ_N','TDB','QD');   d.inv('TDQ','TDQ_N')
    d.nand('TDNQ_N','TDB','Q_N'); d.inv('TDNQ','TDNQ_N')
    d.nor('KSEL_N','OP1NB','LB')
    d.inv('KSEL','KSEL_N',pu='2.2k')     # A-mux (3)
    # ---------------- operand muxes feeding the existing adder ----------------
    d.group='amux'
    for i in range(3):
        d.inv(f'KA{i}',f'ENCA_N{i}')
        d.nand(f'AK_N{i}','KSEL',f'KA{i}')
        d.nand(f'AM_N{i}','TMA',f'P{i+3}')
        d.nand(f'AD_N{i}','TDA',f'P{i+2}')
        d.nand(f'A{i}',f'AK_N{i}',f'AM_N{i}',f'AD_N{i}',pu='2.2k')   # root adder (3) + NEXT (1)
        d.ext_loads[f'A{i}']+=3
    d.group='bgate'
    d.inv('P0N','P0')
    d.nand('X_N','OP1BB','OP0N','P0N')   # X = (mode==MUL) & ~P0  -> force B operand to 0
    d.inv('X','X_N',pu='2.2k')
    for i in range(3):
        d.nor(f'EB{i}',f'ENCB_N{i}','X')  # root conditional inverters (2)
        d.ext_loads[f'EB{i}']+=2
    d.group='div0'
    d.nand('BZ_N','ENCB_N0','ENCB_N1','ENCB_N2')   # B operand == 0
    d.inv('BZ','BZ_N')
    d.nand('DIV0_N','OP1BB','OP0','BZ')
    d.inv('DIV0','DIV0_N')                          # divide-by-zero flag (for an LED)
    # ---------------- P register next-state ----------------
    d.group='pnext'
    def andor(out,terms):
        tn=[]
        for k,(a,b) in enumerate(terms):
            tn.append(d.nand(f'{out}.t{k}',a,b))
        d.nand(out,*tn)
    andor('NX5',[('TMB','S3'),('TDQ','S2'),('TDNQ','P4'),('IDLE','P5')])
    andor('NX4',[('TMB','S2'),('TDQ','S1'),('TDNQ','P3'),('IDLE','P4')])
    andor('NX3',[('TMB','S1'),('TDQ','S0'),('TDNQ','P2'),('IDLE','P3')])
    andor('NX2',[('TMB','S0'),('TDB','P1'),('IDLE','P2'),('LB','A2')])
    andor('NX1',[('TMB','P2'),('TDB','P0'),('IDLE','P1'),('LB','A1')])
    andor('NX0',[('TMB','P1'),('TDB','QD'),('IDLE','P0'),('LB','A0')])
    d.group='preg'
    for i in range(6):
        d.ff(f'P{i}',f'NX{i}','CK2',qpu='2.2k')
    # ---------------- result path into the memory register ----------------
    d.group='memdata'
    for i in range(4):
        if i==3: d.nand('RD_A3','OP1NA','OUT3','OP0N')   # bug fix: in SUB mode OUT3 carries the borrow flag, not a magnitude bit
        else:    d.nand(f'RD_A{i}','OP1NA',f'OUT{i}')
        d.nand(f'RD_M{i}','OP1BA',f'P{i}')
        d.nand(f'REG_D{i}',f'RD_A{i}',f'RD_M{i}')      # root FF D input (2 loads)
        d.ext_loads[f'REG_D{i}']+=2
    d.nand('RDS_N','OP1NA','SIGB2'); d.inv('REG_DS','RDS_N'); d.ext_loads['REG_DS']+=2
    d.nand('D4_N','OP1BB','P4'); d.inv('D4','D4_N')
    d.nand('D5_N','OP1BB','P5'); d.inv('D5','D5_N')
    d.ff('OUT_B4','D4','MEMCLK2',qpu='2.2k')
    d.ff('OUT_B5','D5','MEMCLK2',qpu='2.2k')
    # ---------------- glitch-free memory clock gate ----------------
    d.group='clkgate'
    d.nor('EN_N','OP1NB','DN')           # EN = ADD/SUB mode  OR  sequence done
    d.inv('EN','EN_N')
    d.nand('G1','EN','CK_N')             # latch transparent while CLOCK is low
    d.nand('G2','EN_N','CK_N')
    d.nand('ENL','G1','ENLN')
    d.nand('ENLN','ENL','G2')
    d.nand('MEMCLK_N','CK1','ENL')
    d.inv('MEMCLK','MEMCLK_N',pu='2.2k');  d.ext_loads['MEMCLK']+=5    # root register (5 FFs)
    d.inv('MEMCLK2','MEMCLK_N')                                          # OUT_B4/5
    # root nets consumed here (for the record): S0..S3 pull-ups in root are changed to 2.2k
    return d

def spice(d, ref_start=2000, netmap=lambda n:n):
    """Flat SPICE lines for the design."""
    lines=[]; q=ref_start; r=ref_start
    for g in d.gates:
        out=netmap(g['out'])
        lines.append(f"R{r} +5V {out} {g['pu']}"); r+=1
        n=len(g['ins'])
        for k,inp in enumerate(g['ins']):
            b=f"{out}_bs{k}"
            if g['kind']=='NAND':
                c=out if k==0 else f"{out}_st{k}"
                e='GND' if k==n-1 else f"{out}_st{k+1}"
            else:
                c=out; e='GND'
            lines.append(f"Q{q} {c} {b} {e} 2N3904"); q+=1
            lines.append(f"R{r} {netmap(inp)} {b} 10k"); r+=1
            lines.append(f"R{r} GND {b} 22k"); r+=1
    return lines

if __name__=='__main__':
    d=build()
    print("gates",len(d.gates),"transistors",d.ntransistors())
    for p in d.check(): print("PROBLEM",p)
    c=d.loads()
    for net in ['CLOCK','OP0','OP1','START','S0','S1','S2','S3','SIG','OUT0','ENCA_N0','ENCB_N0']:
        print(net,c[net])
