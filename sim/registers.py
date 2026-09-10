"""Board 02: registers A, B and OUT.
Header in : BUS0..3# (data, active low), AI, AO, BI, BO, BA, AB, OI, CLK.   Header out: A0..3, B0..3.
Bus: BUS0..3# driven (open drain) when AO=1 (A) or BO=1 (B).
Every register is four master-slave D flip-flops clocked by the rising edge of CLK through a two-phase
non-overlapping clock (PH1 opens the masters while CLK is low, PH2 the slaves while CLK is high). In front of each bit sits an
AND-OR mux choosing what the flip-flop captures on the next edge:
  A <- bus if AI, B if AB, else A      B <- bus if BI, A if BA, else B      OUT <- bus if OI, else OUT
AB and BA together swap A and B (XCH): both masters capture the old values before the edge, both slaves change after it.
A, B and OUT are not on the reset line; they hold whatever they held (docs/isa.md).
"""
import nmos

GROUP_TITLES={
 'clock':'TWO-PHASE CLOCK: PH1 = NOR(CLK, PH2) opens the masters while CLK is low, PH2 = NOR(CLKN, PH1) opens the slaves while CLK is high.  The cross-coupling means a phase cannot start rising until the other is fully low, whatever the threshold spread between transistors, so a flip-flop is never transparent.  CLK from the header has one load here.',
 'busin':'BUS INPUT: D_i = NOT BUS_i# (the bus is active low)',
 'muxA':'REGISTER A INPUT MUX: DA_i = AI.D_i + AB.B_i + HOLDA.A_i, HOLDA = NOR(AI, AB).  NAND-NAND form: three 2-input NANDs into a 3-input NAND',
 'regA':'REGISTER A: four master-slave D flip-flops, 22k pull-ups on Q (A_i feeds the ALU, the panel, the mux, the B mux and the bus driver)',
 'muxB':'REGISTER B INPUT MUX: DB_i = BI.D_i + BA.A_i + HOLDB.B_i',
 'regB':'REGISTER B',
 'muxO':'OUT REGISTER INPUT MUX: DO_i = OI.D_i + OIN.OUT_i',
 'regO':'OUT REGISTER (the display)',
 'drv':'BUS DRIVERS: pull BUS_i# low when AO.A_i or BO.B_i',
 'leds':'INDICATORS: OUT3..0 (the result display), A3..0, B3..0',
}

def mux3(d,out,e1,x1,e2,x2,hold,xh):
    d.nand(out+'_1',e1,x1); d.nand(out+'_2',e2,x2); d.nand(out+'_3',hold,xh)
    return d.nand(out,out+'_1',out+'_2',out+'_3')

def build():
    d=nmos.Design('registers')
    d.inputs={'BUS0#','BUS1#','BUS2#','BUS3#','AI','AO','BI','BO','BA','AB','OI','CLK'}
    d.group='clock'
    d.inv('CLKN','CLK')
    d.nor('PH1','CLK','PH2',pu='10k'); d.nor('PH2','CLKN','PH1',pu='10k')    # 12 masters x 2 + 1 loads each: 10k
    d.group='busin'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#')
    d.group='muxA'
    d.nor('HOLDA','AI','AB')
    for i in range(4): mux3(d,f'DA{i}','AI',f'D{i}','AB',f'B{i}','HOLDA',f'A{i}')
    d.group='regA'
    for i in range(4): d.ff(f'A{i}',f'DA{i}',qpu='22k',ckn='PH1',ckb='PH2')
    d.group='muxB'
    d.nor('HOLDB','BI','BA')
    for i in range(4): mux3(d,f'DB{i}','BI',f'D{i}','BA',f'A{i}','HOLDB',f'B{i}')
    d.group='regB'
    for i in range(4): d.ff(f'B{i}',f'DB{i}',qpu='22k',ckn='PH1',ckb='PH2')
    d.group='muxO'
    d.inv('OIN','OI')
    for i in range(4):
        d.nand(f'DO{i}_1','OI',f'D{i}'); d.nand(f'DO{i}_2','OIN',f'OUT{i}'); d.nand(f'DO{i}',f'DO{i}_1',f'DO{i}_2')
    d.group='regO'
    for i in range(4): d.ff(f'OUT{i}',f'DO{i}',ckn='PH1',ckb='PH2')
    d.group='drv'
    for i in range(4):
        d.nand(f'AON{i}','AO',f'A{i}'); d.nand(f'BON{i}','BO',f'B{i}')
        d.nand(f'BD{i}',f'AON{i}',f'BON{i}')          # = AO.A + BO.B
        d.bus(f'BUS{i}#',f'BD{i}')
    d.group='leds'
    for n in ['OUT3','OUT2','OUT1','OUT0','A3','A2','A1','A0','B3','B2','B1','B0']: d.led('LED_'+n,n)
    # header loads: the ALU takes A_i and B_i into three gates each, the panel LED one
    for i in range(4): d.ext_loads[f'A{i}']+=4; d.ext_loads[f'B{i}']+=5   # B also feeds the ALU's conditional inverter
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
