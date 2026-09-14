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

# ---- the program card (D042, docs/cards.md): four words, jumpered to its page and word group ----
CARD_TITLES={
 'sel':'CARD SELECT: jumper k picks PC(k) or its inverse as JS(k), k = 7..2 (the page PC7..4 and the word group PC3..2 this card holds); SEL = all six JS high',
 'dec':'WORD DECODER: PC1..0 -> W0..W3 (active high)',
 'rows':'ROW DRIVERS: ROWn = word n selected AND SEL.  3.3k pull-ups: a row feeds up to eight diodes into the hub\'s 220k pull-downs (D048)',
 'leds':'INDICATORS: the selected row (the instruction being fetched) and SEL',
}
def build_card():
    """Four words of eight switches; six jumpers strap the card to addresses 4c..4c+3 (PC7..2 = c)."""
    d=nmos.Design('progc')
    d.inputs={f'PC{i}' for i in range(8)}|{f'JS{k}' for k in range(2,8)}     # JS_k: the jumper outputs
    d.group='sel'
    for k in range(2,8): d.inv(f'PN{k}',f'PC{k}')
    d.nand('SELA#','JS2','JS3','JS4'); d.nand('SELB#','JS5','JS6','JS7'); d.nor('SEL','SELA#','SELB#')
    d.group='dec'
    d.inv('PC0N','PC0'); d.inv('PC1N','PC1')
    d.nor('W0','PC1','PC0'); d.nor('W1','PC1','PC0N'); d.nor('W2','PC1N','PC0'); d.nor('W3','PC1N','PC0N')
    d.group='rows'
    for n in range(4): d.nand(f'ROW{n}#',f'W{n}','SEL'); d.inv(f'ROW{n}',f'ROW{n}#',pu='3.3k')      # 3.3k: a row of eight ones into eight 220k hub pull-downs still reads 3.8 V on M (D048)
    d.group='leds'
    for n in range(4): d.led(f'LED_R{n}',f'ROW{n}')          # R0..R3 on the silk: a four-letter name runs into the LED
    d.led('LED_SEL','SEL')
    for n in range(4): d.ext_loads[f'ROW{n}']+=8       # the eight switch diodes
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
