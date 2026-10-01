"""The 64-pin Nibble bus header (docs/bus-header.md, D017, D059). pin -> signal.

The header is soldered on the BACK of every board (D059: the ribbon runs behind the cards). The boards were routed with it on
the front, and no track moved: the header went over onto the back in the holes it had, mirrored top to bottom about the middle of
its two rows, the notch toward the top edge. A pin of the odd row therefore sits in the hole its even neighbour had: the two
signals of every pair of pins changed places. HOLES is the table the copper was routed to (hole -> signal, a hole numbered as
the front-mounted header numbered it, D017); PINS is what the header's pins carry now, and the only table to wire a cable by."""
N=64
HOLES={1:'+5V',2:'+5V',3:'GND',4:'GND',5:'CLK',6:'GND',7:'RST',8:'GND'}
_SIG=(['BUS0#','BUS1#','BUS2#','BUS3#','A0','A1','A2','A3','B0','B1','B2','B3']
      +[f'PC{i}' for i in range(8)]+[f'M{i}' for i in range(8)]
      +['CF','ZF','SUB','EO','AI','AO','BI','BO','BA','AB','OI','IO','II','PCE','PCL','FI','HLT',
        'MAI','MI','MO','WRL','WRH','ONE','F0','F1','INP'])
for _i,_s in enumerate(_SIG): HOLES[9+_i]=_s
HOLES[63]='+5V'; HOLES[64]='GND'
mate=lambda n:n+1 if n%2 else n-1                     # the other pin of the pair: 1 <-> 2, 3 <-> 4, ...
PINS={n:HOLES[mate(n)] for n in range(1,N+1)}         # 1 +5V 2 +5V 3 GND 4 GND 5 GND 6 CLK 7 GND 8 RST 9 BUS1# 10 BUS0# ... 63 GND 64 +5V
assert len(PINS)==N and sorted(PINS)==list(range(1,N+1))
GND_PINS=[p for p,s in PINS.items() if s=='GND']      # 3,4,5,7,63
def hole(hx,hy,n):
    """Where pin n's hole is for a header placed at (hx,hy) rot 90 (as on the front, pin 1's old hole) and turned onto the back:
    the odd row is the upper one (hy-2.54), the columns run left to right."""
    return (hx+((n-1)//2)*2.54, hy-(n%2)*2.54)
def header_labels(hx,hy):
    """The silkscreen that goes with a header on the back: on the front only the pin numbers at the four corners of the rows
    of solder joints; on the back, under the header's printed outline, what goes there and which way round: two short
    labels, each between two of the ground vias that stand in a row there every 15.36 mm (one label of 31 mm lay across
    two of them on every card). The front said HEADER ON THE BACK until 2026-10-01: a "not here" note under the holes, the
    kind of text that narrates instead of naming, and the back already says where. The notch is toward the card's top
    edge on every header, the hub's lower one too: all 27 sit the same way round, or a ribbon could not join them. A label
    on the back is mirrored and runs toward the left of the board as the front sees it: its x is its right-hand end.
    [text, x, y, size, angle, face]."""
    r=lambda v:round(v,2); xl=r(hx-2.9); xr=r(hx+31*2.54+1.5); yu=r(hy-2.54); yt=r(hy+4.7 if hy<50 else hy+5.2)
    return [["1",xl,yu,1.0,0,'F'],["2",xl,hy,1.0,0,'F'],["63",xr,yu,1.0,0,'F'],["64",xr,hy,1.0,0,'F'],
            ["HEADER HERE",r(hx+56.0),yt,1.0,0,'B'],["NOTCH TO TOP",r(hx+41.2),yt,1.0,0,'B']]
SIGNALS=[s for s in PINS.values() if s not in ('+5V','GND')]
