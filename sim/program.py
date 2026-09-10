"""Board 04: program memory, 16 words of 8 bits on DIP switches, one page of the 256-word space.
Header in : PC0..PC7.   Header out: M0..M7 (a diode per bit, OR-ed with the other pages; the hub pulls M down).
PC3..0 select the word; PC7..4 are compared with four jumpers (each picks PC or NOT PC) and the board drives
its rows only when the page matches. A closed switch is a 1: the row line pulls M_i high through the switch and a
diode. More program: more copies of this board, each strapped to its page.
"""
import nmos

GROUP_TITLES={
 'page':'PAGE COMPARE: jumper i selects PC(4+i) or its inverse as JS_i; PAGE = all four JS high',
 'dec':'WORD DECODER: PC3..0 -> W0#..W15# (active low), through 2-to-4 predecoders',
 'rows':'ROW DRIVERS: ROWn = word n selected AND page matches.  10k pull-ups: a row feeds up to eight diodes',
 'leds':'INDICATORS: the selected row (the instruction being fetched) and PAGE',
}

def build():
    d=nmos.Design('program')
    d.inputs={f'PC{i}' for i in range(8)}|{'JS0','JS1','JS2','JS3'}     # JS_i: the jumper outputs
    d.group='page'
    for i in range(4): d.inv(f'PN{i}',f'PC{i+4}')
    d.nand('PAGEA','JS0','JS1','JS2'); d.inv('PAGEAN','PAGEA'); d.nand('PAGEN','PAGEAN','JS3',pu='10k'); d.inv('PAGE','PAGEN')
    d.group='dec'
    for i in range(4): d.inv(f'PC{i}N',f'PC{i}')
    d.nor('L0','PC1','PC0'); d.nor('L1','PC1','PC0N'); d.nor('L2','PC1N','PC0'); d.nor('L3','PC1N','PC0N')
    d.nor('H0','PC3','PC2'); d.nor('H1','PC3','PC2N'); d.nor('H2','PC3N','PC2'); d.nor('H3','PC3N','PC2N')
    for n in range(16): d.nand(f'W{n}#',f'H{n>>2}',f'L{n&3}')
    d.group='rows'
    for n in range(16): d.nor(f'ROW{n}',f'W{n}#','PAGEN',pu='10k')
    d.group='leds'
    for n in range(16): d.led(f'LED_ROW{n}',f'ROW{n}')
    d.led('LED_PAGE','PAGE')
    for n in range(16): d.ext_loads[f'ROW{n}']+=8       # the eight switch diodes
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
