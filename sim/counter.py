"""Board 09: the program counter (8 bits) and the return register (8 bits).
Header in : PCE, PCL, CLK, RST.   Header out: PC0..PC7.
Link in   : OPR0..7, PCR, RAI from the sequencer (D035).
PC: every bit is a master-slave flip-flop whose input is one of  PC xor carry (count, or hold when PCE=0),
OPR (PCL: jump, call) or RA (PCR: return).  The count carry ripples: t0 = PCE, t(i+1) = t(i) and PC(i).
RA: eight transparent latches open while RAI and PH1: they capture the old PC during the low half of the
CALL's execute tick, and close before the edge on which PC loads the target.
"""
import nmos

GROUP_TITLES={
 'clock':'TWO-PHASE CLOCK and RSTN (as on the register and sequencer boards)',
 'sel':'INPUT SELECT: LOADN = neither PCL nor PCR: the counter counts (or holds) unless a load line is high',
 'carry':'COUNT CARRY CHAIN: t0 = PCE, t(i+1) = t(i) and PC(i).  Bit i toggles when t(i) is 1.',
 'pc':'PROGRAM COUNTER: D = LOADN.(PC xor t) + PCL.OPR + PCR.RA, then a master-slave flip-flop with reset',
 'ra':'RETURN REGISTER: transparent latches open while RAI and PH1',
 'leds':'INDICATORS: PC7..0, RA7..0',
}

def build():
    d=nmos.Design('counter')
    d.inputs={'PCE','CLK','RST','PCL','PCR','RAI'}|{f'OPR{i}' for i in range(8)}
    d.group='clock'
    d.inv('CLKN','CLK'); d.inv('RSTN','RST',pu='10k')
    d.nor('PH1','CLK','PH2',pu='10k'); d.nor('PH2','CLKN','PH1',pu='10k')
    d.group='sel'
    d.nor('LOADN','PCL','PCR',pu='22k')
    d.group='carry'
    t='PCE'
    for i in range(7):
        d.nand(f'TC{i+1}N',t,f'PC{i}'); d.inv(f'TC{i+1}',f'TC{i+1}N'); t=f'TC{i+1}'
    d.group='pc'
    for i in range(8):
        t='PCE' if i==0 else f'TC{i}'
        d.xor(f'PX{i}',f'PC{i}',t)
        d.nand(f'PD{i}_1','LOADN',f'PX{i}'); d.nand(f'PD{i}_2','PCL',f'OPR{i}'); d.nand(f'PD{i}_3','PCR',f'RA{i}')
        d.nand(f'PD{i}',f'PD{i}_1',f'PD{i}_2',f'PD{i}_3')
        d.ff(f'PC{i}',f'PD{i}',ckn='PH1',ckb='PH2',rstn='RSTN',qpu='22k')
    d.group='ra'
    d.nand('ENRAN','RAI','PH1'); d.inv('ENRA','ENRAN',pu='22k')
    for i in range(8): d.latch(f'RA{i}',f'PC{i}','ENRA',rstn='RSTN')
    d.group='leds'
    for n in [f'PC{i}' for i in range(7,-1,-1)]+[f'RA{i}' for i in range(7,-1,-1)]: d.led('LED_'+n,n)
    for i in range(8): d.ext_loads[f'PC{i}']+=2      # the memory boards' address compare, the panel LED
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
