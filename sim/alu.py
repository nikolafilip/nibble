"""Board 01: 4-bit ALU: two's-complement adder/subtractor, AND, OR, XOR, with carry and zero flags.
Header in : A0..3, B0..3, SUB, ONE, F0, F1, EO.   Header out: CF, ZF.   Bus: BUS0#..BUS3# (open drain, driven when EO=1).
ONE replaces the B input by 0001 (INC/DEC).  XB = BB xor SUB (BB = B or 0001).
F1 F0 = 00: R = A + XB + SUB, CF = carry out (for SUB: 1 = no borrow).
F1 F0 = 01: R = A and XB;  10: R = A or XB;  11: R = A xor XB;  CF = 0 for the three logic functions.
ZF = R == 0.  The sequencer never asserts SUB with F0/F1, so the logic functions see B itself (docs/isa.md).
"""
import nmos

GROUP_TITLES={
 'bin':'B INPUT: BB = B, or 0001 when ONE=1 (INC, DEC).  Then the conditional invert: XB = BB when SUB=0, NOT BB when SUB=1 (two\'s complement: A - B = A + NOT B + 1, the +1 is SUB fed into the carry-in)',
 'adder':'RIPPLE-CARRY FULL ADDERS, bit 0 to bit 3: P = A xor XB, S = P xor Cin, Cout = A.XB + P.Cin.  G = NAND(A, XB) is also NOT (A and XB), P is A xor XB, and A or XB = NAND(NOT P, G): the logic functions fall out of the adder',
 'fsel':'FUNCTION DECODE: FS = add/sub (F1 F0 = 00), FA = and (01), FO = or (10), FX = xor (11)',
 'rmux':'RESULT SELECT, per bit: R = FS.S + FA.AND + FO.OR + FX.P.  NAND-NAND form with the four-way OR split as NAND3 then NAND2 (never more than three transistors in series)',
 'flags':'FLAGS: CF = carry out of bit 3, only for add/sub (0 for the logic functions); ZF = all result bits zero',
 'bus':'BUS DRIVERS: pull BUS_i# low when EO=1 and R_i=1 (open drain, pull-ups live on the hub board)',
 'leds':'INDICATORS: result R3..R0, CF, ZF',
}

def build():
    d=nmos.Design('alu')
    d.inputs={'A0','A1','A2','A3','B0','B1','B2','B3','SUB','ONE','F0','F1','EO'}
    d.group='bin'
    d.inv('SUBN','SUB')
    for i in range(4):
        d.inv(f'BN{i}',f'B{i}')
        if i==0: d.nor('BB0N','B0','ONE'); d.inv('BB0','BB0N')            # BB0 = B0 or ONE
        else:    d.nor(f'BB{i}',f'BN{i}','ONE'); d.inv(f'BB{i}N',f'BB{i}') # BBi = Bi and not ONE
        d.nand(f'XBA{i}',f'BB{i}','SUBN'); d.nand(f'XBB{i}',f'BB{i}N','SUB')
        d.nand(f'XB{i}',f'XBA{i}',f'XBB{i}')
    d.group='adder'
    c='SUB'                       # carry into bit 0
    for i in range(4):
        d.xor(f'P{i}',f'A{i}',f'XB{i}')
        d.xor(f'S{i}',f'P{i}',c)
        d.nand(f'G{i}',f'A{i}',f'XB{i}'); d.nand(f'T{i}',f'P{i}',c)
        d.nand(f'C{i+1}',f'G{i}',f'T{i}')
        c=f'C{i+1}'
    d.group='fsel'
    d.inv('F0N','F0'); d.inv('F1N','F1')
    d.nor('FS','F1','F0'); d.nor('FA','F1','F0N'); d.nor('FO','F1N','F0'); d.nand('FXN','F1','F0'); d.inv('FX','FXN')
    d.group='rmux'
    for i in range(4):
        d.inv(f'AND{i}',f'G{i}'); d.inv(f'PN{i}',f'P{i}'); d.nand(f'OR{i}',f'PN{i}',f'G{i}')
        d.nand(f'RS{i}','FS',f'S{i}'); d.nand(f'RA{i}','FA',f'AND{i}'); d.nand(f'RO{i}','FO',f'OR{i}'); d.nand(f'RX{i}','FX',f'P{i}')
        d.nand(f'RM{i}',f'RS{i}',f'RA{i}',f'RO{i}'); d.inv(f'RMN{i}',f'RM{i}')    # RM = FS.S + FA.AND + FO.OR
        d.nand(f'R{i}',f'RMN{i}',f'RX{i}')                                       # R = RM + FX.P
    d.group='flags'
    d.nand('CFN','C4','FS'); d.inv('CF','CFN')
    d.nor('ZF','R0','R1','R2','R3')
    d.group='bus'
    for i in range(4):
        d.nand(f'BDN{i}',f'R{i}','EO'); d.inv(f'BD{i}',f'BDN{i}'); d.bus(f'BUS{i}#',f'BD{i}')
    d.group='leds'
    for n in ['R3','R2','R1','R0','CF','ZF']: d.led('LED_'+n,n)
    # header loads (other boards) so fan-out is checked honestly
    d.ext_loads['CF']+=2; d.ext_loads['ZF']+=2
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
