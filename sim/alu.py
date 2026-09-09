"""Board 01: 4-bit two's-complement adder/subtractor with carry and zero flags.
Header in : A0..3, B0..3, SUB, EO.   Header out: CF, ZF.   Bus: BUS0#..BUS3# (open drain, driven when EO=1).
Result S = A + (B xor SUB) + SUB.  CF = carry out (for SUB: 1 = no borrow).  ZF = S == 0.
"""
import nmos

GROUP_TITLES={
 'binv':'B CONDITIONAL INVERT: XB = B when SUB=0, NOT B when SUB=1 (two\'s complement: A - B = A + NOT B + 1, the +1 is SUB fed into the carry-in)',
 'adder':'RIPPLE-CARRY FULL ADDERS, bit 0 to bit 3: P = A xor XB, S = P xor Cin, Cout = A.XB + P.Cin',
 'flags':'FLAGS: CF = carry out of bit 3, ZF = all sum bits zero',
 'bus':'BUS DRIVERS: pull BUS_i# low when EO=1 and S_i=1 (open drain, pull-ups live on the hub board)',
 'leds':'INDICATORS: result S3..S0, CF, ZF',
}

def build():
    d=nmos.Design('alu')
    d.inputs={'A0','A1','A2','A3','B0','B1','B2','B3','SUB','EO'}
    d.group='binv'
    d.inv('SUBN','SUB')
    for i in range(4):
        d.inv(f'BN{i}',f'B{i}')
        d.nand(f'XBA{i}',f'B{i}','SUBN'); d.nand(f'XBB{i}',f'BN{i}','SUB')
        d.nand(f'XB{i}',f'XBA{i}',f'XBB{i}')
    d.group='adder'
    c='SUB'                       # carry into bit 0
    for i in range(4):
        d.xor(f'P{i}',f'A{i}',f'XB{i}')
        d.xor(f'S{i}',f'P{i}',c)
        d.nand(f'G{i}',f'A{i}',f'XB{i}'); d.nand(f'T{i}',f'P{i}',c)
        d.nand(f'C{i+1}',f'G{i}',f'T{i}')
        c=f'C{i+1}'
    d.group='flags'
    d.inv('CF','C4N'); d.inv('C4N','C4')      # CF buffered for the header (C4 also feeds an LED)
    d.nor('ZF','S0','S1','S2','S3')
    d.group='bus'
    for i in range(4):
        d.nand(f'BDN{i}',f'S{i}','EO'); d.inv(f'BD{i}',f'BDN{i}'); d.bus(f'BUS{i}#',f'BD{i}')
    d.group='leds'
    for n in ['S3','S2','S1','S0','CF','ZF']: d.led('LED_'+n,n)
    # header loads (other boards) so fan-out is checked honestly
    d.ext_loads['CF']+=2; d.ext_loads['ZF']+=2
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
