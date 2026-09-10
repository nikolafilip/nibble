"""The 64-pin Nibble bus header (docs/bus-header.md, D017). pin -> signal."""
N=64
PINS={1:'+5V',2:'+5V',3:'GND',4:'GND',5:'CLK',6:'GND',7:'RST',8:'GND'}
_SIG=(['BUS0#','BUS1#','BUS2#','BUS3#','A0','A1','A2','A3','B0','B1','B2','B3']
      +[f'PC{i}' for i in range(8)]+[f'M{i}' for i in range(8)]
      +['CF','ZF','SUB','EO','AI','AO','BI','BO','BA','AB','OI','IO','II','PCE','PCL','FI','HLT',
        'MAI','MI','MO','WRL','WRH','ONE','F0','F1','INP'])
for _i,_s in enumerate(_SIG): PINS[9+_i]=_s
PINS[63]='+5V'; PINS[64]='GND'
assert len(PINS)==N and sorted(PINS)==list(range(1,N+1))
GND_PINS=[p for p,s in PINS.items() if s=='GND']      # 3,4,6,8,64
SIGNALS=[s for s in PINS.values() if s not in ('+5V','GND')]
