"""Board 06: front panel. Switches to force any bus line, debounced CLK/RST buttons, an LED on every line,
and the input port: four DATA switches that the IN instruction reads (INP gates them onto the bus, D031)."""
import nmos
LEVEL_SW=['A0','A1','A2','A3','B0','B1','B2','B3']                         # DIP-8 #1
CTRL_SW1=['SUB','EO','AI','AO','BI','BO','BA','AB']                        # DIP-8 #2
CTRL_SW2=['OI','IO','II','PCE','PCL','FI','HLT','MAI']                     # DIP-8 #3
CTRL_SW3=['MI','MO','WRL','WRH','ONE','F0','F1','INP']                     # DIP-8 #4 (data memory / program write D020; ALU function and input port D031)
DATA_SW=['SW0','SW1','SW2','SW3']                                          # DIP-4: the input port. Closed = 1; put on BUS_i# when INP=1
OBSERVED=[f'PC{i}' for i in range(8)]+[f'M{i}' for i in range(8)]+['CF','ZF']
BUTTONS=['CLK','RST']
# LED order = front panel rows of 8 (see build_panel.py): D3..D0 are the bus data bits (inverted from BUS_i#)
LED_ROWS=[['A3','A2','A1','A0','B3','B2','B1','B0'],
          ['D3','D2','D1','D0','CF','ZF','CLK','RST'],
          ['PC7','PC6','PC5','PC4','PC3','PC2','PC1','PC0'],
          ['M7','M6','M5','M4','M3','M2','M1','M0'],
          ['SUB','EO','AI','AO','BI','BO','BA','AB'],
          ['OI','IO','II','PCE','PCL','FI','HLT','MAI'],
          ['MI','MO','WRL','WRH','ONE','F0','F1','INP']]
LEDS=[n for row in LED_ROWS for n in row if not n.startswith('D')]
# every line the panel switches or observes reads 0 when no board drives it; the M lines are pulled down on the hub (D021)
PULLDOWNS=LEVEL_SW+CTRL_SW1+CTRL_SW2+CTRL_SW3+DATA_SW+[s for s in OBSERVED if not s.startswith('M')]+BUTTONS
GROUP_TITLES={
 'busled':'BUS DATA: BUS_i# is active-low, so an inverter turns it into the data bit D_i for its LED',
 'inport':'INPUT PORT: when INP=1 each closed DATA switch (SW_i=1) pulls BUS_i# low, i.e. puts a 1 on the bus.  NAND(INP, SW_i) -> inverter -> open-drain transistor, the same driver every board uses',
 'schmitt':'BUTTON DEBOUNCE: RC-filtered button -> Schmitt trigger (two inverters with a 1Meg feedback resistor) -> 10k -> diode -> line.  One clean edge per press.',
 'leds':'INDICATORS: one LED per bus line.  A MOSFET gate draws no current, so the LEDs load nothing.',
}
def build():
    d=nmos.Design('panel')
    d.inputs=set(LEDS)|set(DATA_SW)|{'BUS0#','BUS1#','BUS2#','BUS3#','CLK_N','RST_N'}
    d.group='leds'
    for row in LED_ROWS:
        for n in row: d.led(f'LED_{n}',n)
    d.group='busled'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#')
    d.group='inport'
    for i in range(4): d.nand(f'IN{i}N','INP',f'SW{i}'); d.inv(f'IN{i}',f'IN{i}N'); d.bus(f'BUS{i}#',f'IN{i}')
    d.group='schmitt'
    for b in BUTTONS: d.inv(f'{b}_S1',f'{b}_N'); d.inv(f'{b}_S2',f'{b}_S1')
    return d

# ---- the three panel cards (D042, docs/cards.md) ----
CARD_A_LEDS=LED_ROWS[0]+LED_ROWS[1]+LED_ROWS[4]      # A3..B0, D3..D0 CF ZF CLK RST, SUB..AB: three rows of eight
CARD_B_LEDS=LED_ROWS[5]+LED_ROWS[6]                  # OI..MAI, MI..INP: two rows
CARD_C_LEDS=LED_ROWS[2]+LED_ROWS[3]                  # PC7..0, M7..0: two rows
CARD_A_PULLS=LEVEL_SW+CTRL_SW1+['CF','ZF','CLK','RST']
CARD_B_PULLS=CTRL_SW2+CTRL_SW3
CARD_C_PULLS=DATA_SW+[f'PC{i}' for i in range(8)]     # M0..7 are pulled down on the hub
CARD_TITLES=dict(GROUP_TITLES,pulls='PULL-DOWNS: 1Meg to ground on every line this card switches or observes, so it reads 0 when no card drives it')
def column_major(names,rows):
    """The LEDs in the order the tile packer wants: it fills a tile column top-down, so a panel column (rows of eight
    across the card) is emitted together and the card reads row by row like the old panel."""
    return [names[r*8+c] for c in range(8) for r in range(rows)]
def build_a():
    """Panel card A: level switches A3..A0 B3..B0 and SUB..AB, their LEDs, the bus data LEDs, CF ZF CLK RST LEDs."""
    d=nmos.Design('panela')
    d.inputs=set(n for n in CARD_A_LEDS if not n.startswith('D'))|{'BUS0#','BUS1#','BUS2#','BUS3#'}
    d.group='leds'
    for n in column_major(CARD_A_LEDS,3): d.led(f'LED_{n}',n)
    d.group='busled'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#')
    d.group='pulls'
    for n in CARD_A_PULLS: d.pulldown(n)
    return d
def build_b():
    """Panel card B: level switches OI..MAI and MI..INP with their LEDs, and the CLK and RST buttons' Schmitt triggers."""
    d=nmos.Design('panelb')
    d.inputs=set(CARD_B_LEDS)|{'CLK_N','RST_N'}
    d.group='leds'
    for n in column_major(CARD_B_LEDS,2): d.led(f'LED_{n}',n)
    d.group='schmitt'
    for b in BUTTONS: d.inv(f'{b}_S1',f'{b}_N'); d.inv(f'{b}_S2',f'{b}_S1')
    d.group='pulls'
    for n in CARD_B_PULLS: d.pulldown(n)
    return d
def build_c():
    """Panel card C, the operator's: PC and M LEDs, the DATA switches and input port."""
    d=nmos.Design('panelc')
    d.inputs=set(CARD_C_LEDS)|set(DATA_SW)|{'INP','BUS0#','BUS1#','BUS2#','BUS3#'}
    d.group='leds'
    for n in column_major(CARD_C_LEDS,2): d.led(f'LED_{n}',n)
    d.group='inport'
    for i in range(4): d.nand(f'IN{i}N','INP',f'SW{i}'); d.inv(f'IN{i}',f'IN{i}N'); d.bus(f'BUS{i}#',f'IN{i}')
    d.group='pulls'
    for n in CARD_C_PULLS: d.pulldown(n)
    return d
