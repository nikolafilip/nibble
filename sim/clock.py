"""Board 05: clock. A Schmitt-trigger RC oscillator with a speed pot, RUN/STEP switch, halt gate, power-on reset.
Header in : HLT.   Header out: CLK (pulled up through the RUN switch, pulled low by a transistor), RST (power-on pulse).
RUN: the switch puts 10k from +5V on CLK; the clock's transistor pulls CLK low for the low half of each cycle and
whenever HLT is high. STEP: the switch is open, the transistor is held off, and the panel's CLK button owns the line.

The oscillator (drawn in build_clock.py) is a source-coupled Schmitt trigger: Q1 (gate = the RC node X) and Q2
(gate = Q1's drain) share a 1k source resistor. Q2's 10k drain load sets the source at 0.45 V while Q2 conducts,
Q1's 47k load at 0.1 V while Q1 conducts, so X trips at about Vth + 0.55 V going up and Vth + 0.15 V going down.
Both trip points move with the same transistor's threshold: the hysteresis is 0.4 V whatever the parts, which a pair
of plain inverters cannot promise (with unequal thresholds they find a dead point; the mixed-threshold simulation
found it). The state is read at Q2's drain, VD2 (0.5 V while Q2 conducts, 5 V otherwise): that node does not move
until the pair snaps, so the outer loop cannot settle half way (reading Q1's drain, which drifts before the snap,
let it: another mixed-threshold find). SA = NOT VD2 with a 4.7k pull-up drives R (100k plus the 1M pot) back to X;
C is 47 nF on X. Measured at the fastest setting: 1.6 to 2.5 ms per cycle over the corners (400 to 600 Hz); with the pot
up about 20 to 30 ms (40 Hz); the SLOW jumper adds 2.2 uF for 0.1 to 1.2 s (10 Hz to 0.8 Hz).
Power-on reset: 2.2 uF charging through 100k into a Schmitt trigger holds RST high for a tenth of a second.
This file is the logic; the Schmitt pair and the RC parts are on the sheet.
"""
import nmos

GROUP_TITLES={
 'osc':'OSCILLATOR BUFFERS: SA = NOT VD2 (VD2 is Q2\'s drain, high while X is above the trip point) with a 4.7k pull-up: SA charges and discharges X through R.  SB = NOT SA is the clock phase',
 'gate':'CLOCK GATE: the CLK pull-down transistor is on while RUN and (oscillator low or HLT)',
 'por':'POWER-ON RESET SCHMITT: PA = NOT PN, PB = NOT PA; PN is the RC node through 100k with 1 Meg from PB (drawn on the sheet).  While PA is high (the capacitor still low) RST is pulled high through 10k and a diode',
 'leds':'INDICATORS: RUN, OSC',
}

def build():
    d=nmos.Design('clock')
    d.inputs={'VD2','RUNSW','HLT','PN'}
    d.group='osc'
    d.inv('SA','VD2',pu='4.7k'); d.inv('SB','SA')
    d.group='gate'
    d.inv('HLTN','HLT'); d.nand('OSCGN','SB','HLTN'); d.inv('OSCG','OSCGN'); d.inv('RUNN','RUNSW')
    d.nor('PULL','RUNN','OSCG'); d.bus('CLK','PULL')
    d.group='por'
    d.inv('PA','PN'); d.inv('PB','PA')
    d.group='leds'
    d.led('LED_RUN','RUNSW'); d.led('LED_OSC','SB')
    d.ext_loads['PA']+=1; d.ext_loads['PB']+=1; d.ext_loads['SA']+=1
    return d

if __name__=='__main__':
    d=build(); print(d.check()); print('transistors',d.ntransistors(),'resistors',d.nresistors(),'leds',d.nleds())
