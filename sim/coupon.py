"""Gate coupon: every cell the machine is built from, in copper, with a test loop on each, measured before any card is trusted.

What it measures and which card each number stands for (docs/gate-cell.md, docs/bring-up.md section 1):
  ring      five inverters in a loop: the gate delay of the 47k cell (every card)
  fan-out   one inverter into one gate and one into ten: the rising edge against the gate capacitance (the control lines)
  nand/nor  three in series and three in parallel: the output low with the stack on (every NAND3 in the sequencer's decoders)
  bus       an open-drain driver against the hub's 10k: the bus low (the register and ALU bus drivers)
  osc       the clock card's oscillator: the Schmitt pair (drawn on the sheet, Q1/Q2 with a shared 1k source) and its two buffers,
            100k + 47 nF from SA back to X: the trip points and the period, the same parts as cards/clock at its fastest setting
  ff        a master-slave D flip-flop wired as a toggle, clocked by the oscillator, with the asynchronous reset the counter and
            sequencer flops have: Q at half the oscillator rate proves the edge-triggered cell in copper; RST high holds Q at 0
  drv       the D053 line driver: a 1k inverter through 100 ohm and a diode against a 10k pull-down (the clock card's CLK and RST,
            the panel's buttons): the edge into a clipped-on 3.3 nF is the edge every card sees
  vto       a diode-connected transistor on 4.7k: the node sits about 0.1 V above that transistor's threshold (the model's Vto)
  rom       a program-card row: a 3.3k inverter through a 1N4148 into the hub's 220k pull-down: the M-line high
  led       the indicator cell
The Schmitt pair, the RC, the driver's 100 ohm / diode / 10k, the ROM diode and its 220k are drawn on the sheet by build_coupon_card.py."""
import nmos
GROUP_TITLES={
 'ring':'RING OSCILLATOR: 5 inverters in a loop, buffered to TP_RING.  Period = 10 gate delays.',
 'fanout':'FAN-OUT: IN -> INV_A (drives 1 gate, TP_FO1) -> INV_B (drives 10 gates, TP_FO10).  Compare rise times.',
 'nand':'3-INPUT NAND (three in series, TP_NAND) and 3-INPUT NOR (three in parallel, TP_NOR) on N1..N3.  Measure output low.',
 'bus':'BUS DRIVER: open drain on IN, 10k pull-up as on the hub, TP_BUS.',
 'osc':'OSCILLATOR BUFFERS (the clock card\'s): SA = NOT VD2 (VD2 is the Schmitt pair\'s output, drawn below) with a 4.7k pull-up drives 100k back to X; SB = NOT SA is the clock, TP_OSC.',
 'ff':'TOGGLE FLIP-FLOP: the NAND master-slave D flip-flop (nmos.ff) with D = NOT Q, clocked by SB, reset by RSTN = NOT RST.  TP_Q runs at half the oscillator rate while RST is low; RST high holds it at 0.',
 'drv':'LINE DRIVER (D053): DRVN = NOT SB with a 1k pull-up, through 100 ohm and a diode (drawn below) into TP_DRV with a 10k pull-down.  Clip 3.3 nF on TP_DRV: the CLK edge every card sees.',
 'vto':'THRESHOLD: gate tied to drain, 4.7k pull-up.  TP_VTO settles about 0.1 V above this transistor\'s threshold (0.6 mA).',
 'rom':'PROGRAM ROW: ROW = NOT IN with a 3.3k pull-up, through a 1N4148 (drawn below) into TP_ROM with the hub\'s 220k pull-down.  TP_ROM high = 5 V less a diode.',
 'led':'INDICATOR: LED on IN.',
}
def build():
    d=nmos.Design('coupon'); d.inputs={'IN','N1','N2','N3','RST','VD2'}     # VD2: the Schmitt pair's output, on the sheet
    d.group='ring'
    for k in range(5): d.inv(f'RING{(k+1)%5}',f'RING{k}')
    d.inv('TP_RING','RING0')
    d.group='fanout'
    d.inv('TP_FO1','IN'); d.inv('TP_FO10','TP_FO1')
    for k in range(10): d.inv(f'LOAD{k}','TP_FO10')
    d.group='nand'
    d.nand('TP_NAND','N1','N2','N3'); d.nor('TP_NOR','N1','N2','N3')
    d.group='bus'
    d.bus('TP_BUS','IN')
    d.group='osc'
    d.inv('SA','VD2',pu='4.7k'); d.inv('TP_OSC','SA')
    d.group='ff'
    d.inv('RSTN','RST')
    d.ff('TP_Q','QN',clk='TP_OSC',rstn='RSTN'); d.inv('QN','TP_Q')
    d.group='drv'
    d.inv('DRVN','TP_OSC',pu='1k')
    d.group='vto'
    d.inv('TP_VTO','TP_VTO',pu='4.7k')
    d.group='rom'
    d.inv('ROW','IN',pu='3.3k')
    d.group='led'
    d.led('LED_IN','IN')
    d.ext_loads['SA']+=1; d.ext_loads['DRVN']+=1; d.ext_loads['ROW']+=1      # the 100k, the 100 ohm, the diode on the sheet
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
