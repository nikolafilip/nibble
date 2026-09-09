"""Gate coupon: the cell in copper, with test points, before anything else is trusted."""
import nmos
GROUP_TITLES={
 'ring':'RING OSCILLATOR: 5 inverters in a loop, buffered to TP_RING.  Period = 10 gate delays (simulated 12 us).',
 'fanout':'FAN-OUT: IN -> INV_A (drives 1 gate, TP_FO1) -> INV_B (drives 10 gates, TP_FO10).  Compare rise times.',
 'nand':'3-INPUT NAND (three in series, TP_NAND) and 3-INPUT NOR (three in parallel, TP_NOR) on N1..N3.  Measure output low.',
 'bus':'BUS DRIVER: open drain on IN, 10k pull-up as on the hub, TP_BUS.',
 'led':'INDICATOR: LED on IN.',
}
def build():
    d=nmos.Design('coupon'); d.inputs={'IN','N1','N2','N3'}
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
    d.group='led'
    d.led('LED_IN','IN')
    return d
