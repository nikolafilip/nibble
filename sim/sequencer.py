"""Board 03: the sequencer. Step counter, instruction and operand registers, flags, two decoders and the diode
control matrix (docs/isa.md). The program counter and the return register live on board 09 (counter.py) and get
OPR7..0, PCR and RAI from this board over a link header (D035); PCL is on the bus header.

Header in : M0..M7 (program memory word), CF, ZF (from the ALU), CLK, RST.
Header out: II, PCE and the 19 matrix-driven control lines SUB EO AI AO BI BO BA AB OI IO FI HLT MAI MI MO ONE F0 F1 INP.
Bus       : BUS0..3# driven (open drain) with OPR3..0 while IO is high.
Link out  : OPR0..7, PCR, RAI (PCL goes over the bus header, pin 51).

Steps (one-hot T0..T4, master-slave flip-flops with asynchronous reset): S0 II, S1 PCE, S2 OPI+PCE (two-word
instructions only), S3 and S4 the matrix rows; DONE returns to S0. IR (4) and OPR (8) are transparent latches open
while their load line and PH1 are both high, so they capture the memory word during the low half of the clock and
are closed before the rising edge. The flags are the same kind of latch, open during FI.
"""
import nmos

COLS=['SUB','EO','AI','AO','BI','BO','BA','AB','OI','IO','FI','HLT','MAI','MI','MO','ONE','F0','F1','INP','PCL','PCR','RAI','DONE']
OPCODE={1:'LDI',2:'JMP',3:'JC',4:'JZ',5:'LOAD',6:'STORE',7:'CALL'}
FAMILY={0:'NOP',1:'MOV',2:'XCH',3:'ADD',4:'SUB',5:'OUT',6:'HLT',7:'DEC',8:'INC',9:'LOADB',10:'STOREB',11:'IN',12:'RET',13:'AND',14:'OR',15:'XOR'}
TWO_WORD=(2,3,4,7)
# the matrix, exactly as docs/isa.md: instruction -> (S3 lines, S4 lines). JC/JZ put PCL on their conditional rows.
RECIPE={'NOP':({'DONE'},set()),'MOV':({'BA','DONE'},set()),'XCH':({'AB','BA','DONE'},set()),
        'ADD':({'EO','AI','FI','DONE'},set()),'SUB':({'SUB','EO','AI','FI','DONE'},set()),'OUT':({'AO','OI','DONE'},set()),
        'HLT':({'HLT'},set()),'DEC':({'ONE','SUB','EO','AI','FI','DONE'},set()),'INC':({'ONE','EO','AI','FI','DONE'},set()),
        'LOADB':({'BO','MAI'},{'MO','AI','DONE'}),'STOREB':({'BO','MAI'},{'AO','MI','DONE'}),'IN':({'INP','AI','DONE'},set()),
        'RET':({'PCR','DONE'},set()),'AND':({'F0','EO','AI','FI','DONE'},set()),'OR':({'F1','EO','AI','FI','DONE'},set()),
        'XOR':({'F0','F1','EO','AI','FI','DONE'},set()),'LDI':({'IO','AI','DONE'},set()),'JMP':({'PCL','DONE'},set()),
        'JC':({'DONE'},set()),'JZ':({'DONE'},set()),'LOAD':({'IO','MAI'},{'MO','AI','DONE'}),'STORE':({'IO','MAI'},{'AO','MI','DONE'}),
        'CALL':({'RAI','PCL','DONE'},set())}
LINK=['OPR0','OPR1','OPR2','OPR3','OPR4','OPR5','OPR6','OPR7','PCR','RAI']     # PCL is a header line (pin 51)

GROUP_TITLES={
 'clock':'TWO-PHASE CLOCK (as on the register board): PH1 opens masters and latches while CLK is low, PH2 copies to slaves while CLK is high.  RSTN for the asynchronous resets.',
 'steps':'STEP COUNTER, one-hot: T0N (0 = step S0, so reset lands in S0), T1..T4.  Next state: S0 -> S1; S1 -> S2 if the opcode is two-word (TWO) else S3; S2 -> S3; S3 -> S4 unless DONE; S4 or DONE -> S0.  II = T0, PCE = T1 or T2, OPI = T2.',
 'ir':'INSTRUCTION REGISTER (4 bits, the opcode) and OPERAND REGISTER (8 bits): transparent latches.  IR and OPR3..0 open while II and PH1; OPR7..4 open while OPI and PH1.  They close before the rising edge.',
 'opdec':'OPCODE DECODER: IR3..0 -> OP0#..OP15# (active low), through a pair of 2-to-4 predecoders so no NAND has more than two transistors in series.  TWO = JMP or JC or JZ or CALL.',
 'famdec':'FAMILY DECODER: OPR3..0 -> F0#..F15#, the member of the opcode-0000 family.',
 'flags':'FLAGS: CFQ, ZFQ latched from the ALU while FI and PH1.  Only ADD SUB INC DEC AND OR XOR assert FI.',
 'rows':'MATRIX ROWS: one per instruction for S3, and for S4 where the instruction uses it (the four memory accesses) and for every free opcode.  Row = NOR(OPn#, T3N) or NOR(OPn#, T4N); family rows also include F#.  JC/JZ have a conditional row for PCL: NOR(OP#, T3N, flag-not).  10k pull-ups: a row drives up to ten diodes into 1 Meg column pull-downs.',
 'matrix':'THE CONTROL MATRIX: a diode from a row to a column pulls that control line high while the row is active.  Every crossing has a diode pad pair on the board (D040); the ones drawn DNP are empty.  A new one-word instruction on the free rows OP8..OP15 (S3 and S4) is diodes soldered in; a conditional jump needs a flag-gated row, i.e. a new board.',
 'cols':'COLUMN BUFFERS (D041): the diode node of each column has a 1 Meg pull-down and feeds one inverter; a second inverter (22k) drives the control line, so the line falls through a transistor in microseconds instead of decaying through 1 Meg into every board and the ribbons.',
 'outs':'STEP OUTPUTS to the header: II = T0, PCE = T1 or T2.',
 'bus':'BUS DRIVERS: OPR3..0 onto BUS3#..BUS0# while IO (LDI, LOAD n, STORE n).',
 'leds':'INDICATORS: steps T0..T4, IR3..0, OPR7..0, CF, ZF.',
}

def decoder(d,prefix,bits,outp):
    """4-to-16 decoder, active-low outputs outp0#..outp15#, from bits [b0,b1,b2,b3]."""
    b0,b1,b2,b3=bits
    for b in bits: d.inv(f'{prefix}{b}N',b)
    d.nor(f'{prefix}L0',b1,b0); d.nor(f'{prefix}L1',b1,f'{prefix}{b0}N'); d.nor(f'{prefix}L2',f'{prefix}{b1}N',b0); d.nor(f'{prefix}L3',f'{prefix}{b1}N',f'{prefix}{b0}N')
    d.nor(f'{prefix}H0',b3,b2); d.nor(f'{prefix}H1',b3,f'{prefix}{b2}N'); d.nor(f'{prefix}H2',f'{prefix}{b3}N',b2); d.nor(f'{prefix}H3',f'{prefix}{b3}N',f'{prefix}{b2}N')
    for n in range(16): d.nand(f'{outp}{n}#',f'{prefix}H{n>>2}',f'{prefix}L{n&3}',pu='10k' if (outp,n)==('OP',0) else nmos.PU_DEFAULT)   # OP0# feeds 32 family rows

def build():
    d=nmos.Design('sequencer')
    d.inputs={f'M{i}' for i in range(8)}|{'CF','ZF','CLK','RST'}
    d.group='clock'
    d.inv('CLKN','CLK'); d.inv('RSTN','RST',pu='10k')          # RSTN reaches every flip-flop and latch
    d.nor('PH1','CLK','PH2',pu='10k'); d.nor('PH2','CLKN','PH1',pu='10k')
    # ---- step counter ----
    d.group='steps'
    d.nor('T0N_D','DONE','T4')                                   # next is S0 when DONE, or after S4
    d.ff('T0N','T0N_D',ckn='PH1',ckb='PH2',rstn='RSTN'); d.inv('T0','T0N',pu='22k')
    d.ff('T1','T0',ckn='PH1',ckb='PH2',rstn='RSTN')
    d.nand('T2D_N','T1','TWO'); d.inv('T2_D','T2D_N')
    d.ff('T2','T2_D',ckn='PH1',ckb='PH2',rstn='RSTN')
    d.nand('T3_A','T1','TWON'); d.inv('T2N','T2'); d.nand('T3_D','T3_A','T2N')   # T1.TWON + T2
    d.ff('T3','T3_D',ckn='PH1',ckb='PH2',rstn='RSTN',qpu='22k')
    d.inv('DONEN','DONE'); d.nand('T4D_N','T3','DONEN'); d.inv('T4_D','T4D_N')
    d.ff('T4','T4_D',ckn='PH1',ckb='PH2',rstn='RSTN',qpu='22k')
    d.inv('T3N','T3',pu='10k'); d.inv('T3NB','T3',pu='10k'); d.inv('T4N','T4',pu='10k')        # feed every row: 10k for the fan-out, T3 split in two; T4N feeds 14 rows since D040
    # ---- IR, OPR ----
    d.group='ir'
    d.nand('ENIRN','T0','PH1'); d.inv('ENIR','ENIRN')              # II = T0
    d.nor('IIOPIN','T0','T2'); d.inv('IIOPI','IIOPIN'); d.nand('ENOLN','IIOPI','PH1'); d.inv('ENOL','ENOLN')
    d.nand('ENOHN','T2','PH1'); d.inv('ENOH','ENOHN')
    for i in range(4): d.latch(f'IR{i}',f'M{i+4}','ENIR',rstn='RSTN')
    for i in range(4): d.latch(f'OPR{i}',f'M{i}','ENOL',rstn='RSTN',qpu='22k')
    for i in range(4,8): d.latch(f'OPR{i}',f'M{i}','ENOH',rstn='RSTN')
    # ---- decoders ----
    d.group='opdec'
    decoder(d,'OD_',['IR0','IR1','IR2','IR3'],'OP')
    d.nand('TWO_A','OP2#','OP3#','OP4#'); d.inv('TWO_AN','TWO_A'); d.nand('TWO','TWO_AN','OP7#'); d.inv('TWON','TWO')
    d.group='famdec'
    decoder(d,'FD_',['OPR0','OPR1','OPR2','OPR3'],'F')
    # ---- flags ----
    d.group='flags'
    d.nand('ENFN','FI','PH1'); d.inv('ENF','ENFN')
    d.latch('CFQ','CF','ENF',rstn='RSTN'); d.latch('ZFQ','ZF','ENF',rstn='RSTN')
    # ---- rows ----
    d.group='rows'
    rows=[]   # (row net, instruction name or None, step). S4 rows only for the instructions that use S4 (memory access)
    for n in range(16):
        for step,tn in ((3,'T3N'),(4,'T4N')):
            if step==4 and not RECIPE[FAMILY[n]][1]: continue
            d.nor(f'R_F{n}_{step}','OP0#',f'F{n}#',tn,pu='10k'); rows.append((f'R_F{n}_{step}',FAMILY[n],step))
    for n in range(1,16):
        for step,tn in ((3,'T3NB'),(4,'T4N')):
            if step==4 and n in OPCODE and not RECIPE[OPCODE[n]][1]: continue      # free opcodes get both rows (D040)
            d.nor(f'R_OP{n}_{step}',f'OP{n}#',tn,pu='10k'); rows.append((f'R_OP{n}_{step}',OPCODE.get(n),step))
    d.nor('R_JCC','OP3#','T3N','CFQ_qn',pu='10k'); d.nor('R_JZZ','OP4#','T3N','ZFQ_qn',pu='10k')
    # ---- the matrix ----
    d.group='matrix'
    for row,name,step in rows:
        if name is None: continue
        for col in sorted(RECIPE[name][step-3],key=COLS.index): d.diode(row,f'{col}_m')
    d.diode('R_JCC','PCL_m'); d.diode('R_JZZ','PCL_m')
    d.group='cols'
    # D041: the diode node <col>_m (1 Meg pull-down) feeds one gate only; a two-inverter buffer drives the line, so a
    # control line falls in microseconds through a transistor instead of decaying through 1 Meg into every board's gates
    # and the ribbons (350 us to 1 V bare, 800 us with cables, most of a tick). 22k on the output stage for the cable capacitance.
    for c in COLS: d.pulldown(f'{c}_m'); d.inv(f'{c}_mn',f'{c}_m'); d.inv(c,f'{c}_mn',pu='22k')
    # ---- outputs ----
    d.group='outs'
    d.inv('IIN','T0'); d.inv('II','IIN'); d.nor('PCEN','T1','T2'); d.inv('PCE','PCEN')
    d.group='bus'
    for i in range(4): d.nand(f'IOD{i}N','IO',f'OPR{i}'); d.inv(f'IOD{i}',f'IOD{i}N'); d.bus(f'BUS{i}#',f'IOD{i}')
    d.group='leds'
    for n in ['T0','T1','T2','T3','T4','IR3','IR2','IR1','IR0','OPR7','OPR6','OPR5','OPR4','OPR3','OPR2','OPR1','OPR0','CFQ','ZFQ']: d.led('LED_'+n,n)
    # loads elsewhere: the counter board takes OPR7..0, PCL, PCR, RAI over the link; the panel LEDs load nothing
    for n in LINK: d.ext_loads[n]+=2
    d.rows=rows
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'diodes',d.ndiodes(),'leds',d.nleds(),'rows',len(d.rows)+2)
