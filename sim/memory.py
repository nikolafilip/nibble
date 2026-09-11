"""Board 08: data memory, 16 slots of 4 bits, with its own address register.
Header in : BUS0..3# (data and address), MAI (load the address register from the bus), MI (write), MO (read), CLK.
Bus       : BUS0..3# driven (open drain) with the addressed slot while MO is high.

MAR is four transparent latches open while MAI and PH1 (the address is on the bus for the whole S3 tick of a
memory instruction). A 4-to-16 decoder selects the slot; per slot a write line WR = slot AND MI AND PH1 and a read
line RD = slot AND MO. The write is gated by PH1 (the second half of the tick) so it ends at the clock edge, before
MI and the bus data change: a write line that outlasted the data by a microsecond flipped cells at the mixed
threshold corner (the write stacks briefly saw the next tick's bus with WR still high). A cell is a pair of cross-coupled inverters (the latch) plus two write pull-downs that force it
to the bus data while WR is high, and a read pull-down that puts its content on the bus while RD is high. Every
cell has an LED: the memory is visible.
"""
import nmos

GROUP_TITLES={
 'clock':'TWO-PHASE CLOCK: only PH1 is used here, to close the address latches and end the write before the rising edge',
 'mar':'ADDRESS REGISTER: four transparent latches, open while MAI and PH1',
 'dec':'ADDRESS DECODER: MAR3..0 -> W0#..W15# (active low), through 2-to-4 predecoders',
 'wl':'WORD LINES: WRn = slot n AND MI AND PH1 (write, ends at the clock edge), RDn = slot n AND MO (read)',
 'data':'DATA IN: D_i = NOT BUS_i# (a 1 on the bus); BUS_i# itself is the inverted data',
 'cells':'CELLS: Q and QN cross-coupled inverters.  While WR: D pulls QN low (writes 1), BUS# pulls Q low (writes 0).  While RD and Q: BUS_i# pulled low (reads 1).',
 'leds':'INDICATORS: the address, and every cell',
}

def build():
    d=nmos.Design('memory')
    d.inputs={'BUS0#','BUS1#','BUS2#','BUS3#','MAI','MI','MO','CLK'}
    d.group='clock'
    d.inv('CLKN','CLK'); d.nor('PH1','CLK','PH2',pu='10k'); d.nor('PH2','CLKN','PH1',pu='10k')
    d.group='data'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#',pu='10k')       # 16 cells and the address latch each
    d.group='mar'
    d.nand('ENMN','MAI','PH1'); d.inv('ENM','ENMN')
    for i in range(4): d.latch(f'MAR{i}',f'D{i}','ENM')
    d.group='dec'
    for i in range(4): d.inv(f'MAR{i}N',f'MAR{i}')
    d.nor('L0','MAR1','MAR0'); d.nor('L1','MAR1','MAR0N'); d.nor('L2','MAR1N','MAR0'); d.nor('L3','MAR1N','MAR0N')
    d.nor('H0','MAR3','MAR2'); d.nor('H1','MAR3','MAR2N'); d.nor('H2','MAR3N','MAR2'); d.nor('H3','MAR3N','MAR2N')
    for n in range(16): d.nand(f'W{n}#',f'H{n>>2}',f'L{n&3}')
    d.group='wl'
    d.nand('MIN','MI','PH1',pu='4.7k'); d.inv('MON','MO',pu='22k')    # MIN low (write allowed) only while MI and PH1; 4.7k so the 16 write lines drop within microseconds of the edge
    for n in range(16): d.nor(f'WR{n}',f'W{n}#','MIN',pu='22k'); d.nor(f'RD{n}',f'W{n}#','MON')
    d.group='cells'
    for n in range(16):
        for i in range(4):
            q=f'Q{n}_{i}'
            d.inv(q,q+'N'); d.inv(q+'N',q)                                 # the latch
            d.pull(q+'N',f'WR{n}',f'D{i}')                                 # write 1: pull QN low
            d.pull(q,f'WR{n}',f'BUS{i}#')                                  # write 0: pull Q low
            d.pull(f'BUS{i}#',f'RD{n}',q)                                  # read: pull the bus line low while RD and Q
    d.group='leds'
    for n in ['MAR3','MAR2','MAR1','MAR0']: d.led('LED_'+n,n)
    for n in range(16):
        for i in (3,2,1,0): d.led(f'LED_M{n}_{i}',f'Q{n}_{i}')
    return d

# ---- the cards (D042): a control card and eight slot-pair cards of one design ----
MLINK=['MAR0','MAR0N','MAR1','MAR1N','MAR2','MAR2N','MAR3','MAR3N','MIN','MON','GND','GND']   # the control card's ribbon to the slot cards (2x6, chained), pins 1..12
CTL_TITLES={
 'clock':GROUP_TITLES['clock'],
 'data':'DATA IN: D_i = NOT BUS_i#, for the address latches',
 'mar':'ADDRESS REGISTER: four transparent latches, open while MAI and PH1.  MAR3..0 and their complements go to the slot cards over the ribbon; each card picks its address with jumpers.',
 'wl':'WRITE AND READ GATES for all slots: MIN low (write allowed) only while MI and PH1, so a write ends at the clock edge; MON low while MO.  4.7k on MIN: sixteen write lines on eight cards drop within microseconds of the edge.',
 'leds':'INDICATORS: the address',
}
SLOT_TITLES={
 'data':'DATA IN: D_i = NOT BUS_i# (a 1 on the bus); BUS_i# itself is the inverted data',
 'dec':'SLOT SELECT: SEL = NOR(X3, X2, X1), the three jumpers giving MAR3..1 or their complements so SEL is high for this card\'s pair of slots; the even slot is MAR0 = 0, the odd slot MAR0 = 1',
 'wl':'WORD LINES: WR = slot AND write allowed (MIN low), RD = slot AND MON low',
 'cells':GROUP_TITLES['cells'],
 'leds':'INDICATORS: the eight cells',
}

def build_ctl():
    """Memory control card: PH1, the address register with both polarities out, the write and read gates (docs/cards.md)."""
    d=nmos.Design('memctl')
    d.inputs={'BUS0#','BUS1#','BUS2#','BUS3#','MAI','MI','MO','CLK'}
    d.group='clock'
    d.inv('CLKN','CLK'); d.nor('PH1','CLK','PH2',pu='10k'); d.nor('PH2','CLKN','PH1',pu='10k')
    d.group='data'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#')
    d.group='mar'
    d.nand('ENMN','MAI','PH1'); d.inv('ENM','ENMN')
    for i in range(4): d.latch(f'MAR{i}',f'D{i}','ENM',qpu='22k'); 
    for i in range(4): d.inv(f'MAR{i}N',f'MAR{i}',pu='22k')
    d.group='wl'
    d.nand('MIN','MI','PH1',pu='4.7k'); d.inv('MON','MO',pu='22k')
    d.group='leds'
    for n in ['MAR3','MAR2','MAR1','MAR0']: d.led('LED_'+n,n)
    for i in range(4): d.ext_loads[f'MAR{i}']+=8; d.ext_loads[f'MAR{i}N']+=8      # a jumper on each of the eight slot cards, worst case all on one polarity
    d.ext_loads['MIN']+=16; d.ext_loads['MON']+=16
    return d

def build_slot():
    """Memory slot card: two 4-bit slots (even: MAR0 = 0, odd: MAR0 = 1) of the pair the jumpers X3 X2 X1 select."""
    d=nmos.Design('memslot')
    d.inputs={'BUS0#','BUS1#','BUS2#','BUS3#','MAR0','MAR0N','MIN','MON','X1','X2','X3'}
    d.group='data'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#')
    d.group='dec'
    d.nor('SEL','X3','X2','X1'); d.nand('WE#','SEL','MAR0N'); d.nand('WO#','SEL','MAR0')
    d.group='wl'
    for s,wn in (('E','WE#'),('O','WO#')): d.nor(f'WR{s}',wn,'MIN',pu='22k'); d.nor(f'RD{s}',wn,'MON')
    d.group='cells'
    for s in 'EO':
        for i in range(4):
            q=f'Q{s}{i}'
            d.inv(q,q+'N'); d.inv(q+'N',q)
            d.pull(q+'N',f'WR{s}',f'D{i}'); d.pull(q,f'WR{s}',f'BUS{i}#'); d.pull(f'BUS{i}#',f'RD{s}',q)
    d.group='leds'
    for s in 'EO':
        for i in (3,2,1,0): d.led(f'LED_M{s}{i}',f'Q{s}{i}')
    return d

def slot_jumpers(p):
    """The jumper setting of slot pair p (slots 2p and 2p+1): X_k takes MAR_kN where bit k of the address is 1 (so SEL sees a 0 there), MAR_k where it is 0."""
    return {f'X{k}':(f'MAR{k}N' if (p>>(k-1))&1 else f'MAR{k}') for k in (1,2,3)}

if __name__=='__main__':
    d=build(); print(d.check()); print('board: transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
    d=build_ctl(); print(d.check()); print('control card: transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
    d=build_slot(); print(d.check()); print('slot card: transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
