"""Tick-accurate emulator of the Nibble instruction set (docs/isa.md).

One call to tick() is one rising clock edge. Between edges the machine sits in
one of five sequencer steps; the control lines are a combinational function of
(step, opcode, latched flags) and every register that has its load line high
captures its source on the edge. That is exactly what the hardware does, so
the trace this produces is compared tick for tick with the ngspice deck in
machine.py.

Registers: PC (8), IR (4-bit opcode), OPR (8-bit operand), A, B, OUT (4),
CF, ZF, step (0..4). II loads IR from M7..4 and OPR3..0 from M3..0; OPI loads
all of OPR from M. RST clears PC, IR, OPR, flags and step; A, B, OUT keep
their values (they are not on the reset line).
"""
OPS={0:'NOP',1:'LDI',2:'MOV',3:'XCH',4:'ADD',5:'SUB',6:'OUT',7:'JMP',8:'JC',9:'JZ',10:'HLT',11:'LOAD',12:'STORE'}
TWO_WORD={'JMP','JC','JZ'}
# execute-step recipes: opcode -> (S3 lines, S4 lines). PCL on JC/JZ is conditional (see controls()).
RECIPE={'NOP':({'DONE'},set()),
        'LDI':({'IO','AI','DONE'},set()),
        'MOV':({'BA','DONE'},set()),
        'XCH':({'AB','BA','DONE'},set()),
        'ADD':({'EO','AI','FI','DONE'},set()),
        'SUB':({'SUB','EO','AI','FI','DONE'},set()),
        'OUT':({'AO','OI','DONE'},set()),
        'JMP':({'PCL','DONE'},set()),
        'JC':({'PCL?','DONE'},set()),
        'JZ':({'PCL?','DONE'},set()),
        'HLT':({'HLT'},set()),
        'LOAD':({'IO','MAI'},{'MO','AI','DONE'}),
        'STORE':({'IO','MAI'},{'AO','MI','DONE'})}
DRIVERS=('AO','BO','EO','IO','MO')     # lines that put a value on the bus; at most one is ever high

class Machine:
    def __init__(self,program,data=None,has_datamem=True):
        self.mem=list(program)+[0]*(256-len(program)); self.mem=self.mem[:256]
        self.data=list(data or [])+[0]*16; self.data=self.data[:16]
        self.has_datamem=has_datamem
        self.reset(); self.trace=[]
    def reset(self):
        self.pc=0; self.ir=0; self.opr=0; self.cf=0; self.zf=0; self.step=0
        self.a=0; self.b=0; self.out=0; self.mar=0; self.halted=False
    # ---- combinational ----
    @property
    def op(self): return OPS.get(self.ir,'NOP')
    def alu(self,sub=None):
        """Result and flags of A +/- B for the current SUB line (or the given one)."""
        if sub is None: sub='SUB' in self.controls()
        s=self.a+((~self.b)&15)+1 if sub else self.a+self.b
        return s&15, (s>>4)&1, int((s&15)==0)
    def controls(self):
        """Set of control lines that are high in the current step."""
        s=self.step; op=self.op
        if s==0: return {'II'}
        if s==1: return {'PCE'}
        if s==2: return {'OPI','PCE'}
        lines=set(RECIPE[op][s-3])
        if 'PCL?' in lines:
            lines.discard('PCL?')
            if (op=='JC' and self.cf) or (op=='JZ' and self.zf): lines.add('PCL')
        return lines
    def bus(self,ctl=None):
        """Value on the bus (0 when nobody drives it: open-drain lines pulled up = all bits 0)."""
        ctl=ctl or self.controls()
        if 'AO' in ctl: return self.a
        if 'BO' in ctl: return self.b
        if 'EO' in ctl: return self.alu('SUB' in ctl)[0]
        if 'IO' in ctl: return self.opr&15
        if 'MO' in ctl: return self.data[self.mar] if self.has_datamem else 0
        return 0
    def snapshot(self):
        ctl=self.controls()
        return dict(step=self.step,pc=self.pc,ir=self.ir,opr=self.opr,a=self.a,b=self.b,out=self.out,cf=self.cf,zf=self.zf,
                    m=self.mem[self.pc],bus=self.bus(ctl),ctl=sorted(ctl),halted=self.halted)
    # ---- sequential ----
    def tick(self):
        """One rising edge. Returns False (and changes nothing) once HLT is high: the clock has stopped."""
        snap=self.snapshot(); self.trace.append(snap)
        ctl=set(snap['ctl'])
        if 'HLT' in ctl: self.halted=True; return False
        m=self.mem[self.pc]; bus=snap['bus']
        a,b=self.a,self.b
        res,cf,zf=self.alu('SUB' in ctl)
        # register loads (all from values present before the edge)
        if 'II' in ctl: self.ir=m>>4; self.opr=(self.opr&0xF0)|(m&15)
        if 'OPI' in ctl: self.opr=m
        if 'AI' in ctl: self.a=bus
        if 'BI' in ctl: self.b=bus
        if 'OI' in ctl: self.out=bus
        if 'AB' in ctl: self.a=b
        if 'BA' in ctl: self.b=a
        if 'FI' in ctl: self.cf,self.zf=cf,zf
        if 'MAI' in ctl: self.mar=bus
        if 'MI' in ctl and self.has_datamem: self.data[self.mar]=bus
        if 'PCL' in ctl: self.pc=self.opr
        elif 'PCE' in ctl: self.pc=(self.pc+1)&255
        # step counter
        if 'DONE' in ctl: self.step=0
        elif self.step==1: self.step=3 if self.op not in TWO_WORD else 2
        else: self.step=(self.step+1)%5
        return True
    def run(self,max_ticks=2000):
        """Run until HLT. Returns the list of OUT values in the order they were written."""
        outs=[]
        for _ in range(max_ticks):
            before=self.out
            if not self.tick(): break
            if 'OI' in self.trace[-1]['ctl']: outs.append(self.out)
        return outs

if __name__=='__main__':
    import sys, asm
    words,labels,_=asm.assemble(open(sys.argv[1]).read())
    m=Machine(words); outs=m.run()
    for s in m.trace: print(f"{len(m.trace) and s['step']} pc={s['pc']:3d} m={s['m']:08b} A={s['a']:2d} B={s['b']:2d} OUT={s['out']:2d} C={s['cf']} Z={s['zf']} bus={s['bus']:2d} {' '.join(s['ctl'])}")
    print('OUT sequence:',outs,'halted' if m.halted else 'NOT HALTED','after',len(m.trace),'ticks')
