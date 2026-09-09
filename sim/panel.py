"""Board 06: front panel. Switches to force any bus line, debounced CLK/RST buttons, an LED on every line."""
import nmos
LEVEL_SW=['A0','A1','A2','A3','B0','B1','B2','B3']                         # DIP-8 #1
CTRL_SW1=['SUB','EO','AI','AO','BI','BA','AB','OI']                        # DIP-8 #2
CTRL_SW2=['IO','II','PCE','PCL','FI','HLT',None,None]                      # DIP-8 #3 (two spare)
DATA_SW=['BUS0#','BUS1#','BUS2#','BUS3#']                                  # DIP-4, closed = 1 on the bus
OBSERVED=['PC0','PC1','PC2','PC3','M0','M1','M2','M3','M4','M5','M6','M7','CF','ZF']
BUTTONS=['CLK','RST']
# LED order = front panel rows of 8 (see build_panel.py): D3..D0 are the bus data bits (inverted from BUS_i#)
LED_ROWS=[['A3','A2','A1','A0','B3','B2','B1','B0'],
          ['D3','D2','D1','D0','PC3','PC2','PC1','PC0'],
          ['M7','M6','M5','M4','M3','M2','M1','M0'],
          ['CF','ZF','CLK','RST','SUB','EO','AI','AO'],
          ['BI','BA','AB','OI','IO','II','PCE','PCL'],
          ['FI','HLT']]
LEDS=[n for row in LED_ROWS for n in row if not n.startswith('D')]
PULLDOWNS=LEVEL_SW+CTRL_SW1+[s for s in CTRL_SW2 if s]+OBSERVED+BUTTONS
GROUP_TITLES={
 'busled':'BUS DATA: BUS_i# is active-low, so an inverter turns it into the data bit D_i for its LED',
 'schmitt':'BUTTON DEBOUNCE: RC-filtered button -> Schmitt trigger (two inverters with a 1Meg feedback resistor) -> 10k -> diode -> line.  One clean edge per press.',
 'leds':'INDICATORS: one LED per bus line.  A MOSFET gate draws no current, so the LEDs load nothing.',
}
def build():
    d=nmos.Design('panel')
    d.inputs=set(LEDS)|set(DATA_SW)|{'CLK_N','RST_N'}
    d.group='leds'
    for row in LED_ROWS:
        for n in row: d.led(f'LED_{n}',n)
    d.group='busled'
    for i in range(4): d.inv(f'D{i}',f'BUS{i}#')
    d.group='schmitt'
    for b in BUTTONS: d.inv(f'{b}_S1',f'{b}_N'); d.inv(f'{b}_S2',f'{b}_S1')
    return d
