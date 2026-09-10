"""Tick-accurate emulator of the Nibble instruction set (docs/isa.md, v2).

One call to tick() is one rising clock edge. Between edges the machine sits in
one of five sequencer steps; the control lines are a combinational function of
(step, instruction, latched flags) and every register that has its load line
high captures its source on the edge. That is exactly what the hardware does,
so the trace this produces is compared tick for tick with the ngspice deck in
machine.py.

Registers: PC (8), IR (4-bit opcode), OPR (8-bit operand), RA (8-bit return
address), A, B, OUT (4), MAR (4), CF, ZF, step (0..4). II loads IR from M7..4
and OPR3..0 from M3..0; OPI loads all of OPR from M. RST clears PC, IR, OPR,
RA, flags and step; A, B, OUT and memory keep their values.
"""
OPS={0:'EXT',1:'LDI',2:'JMP',3:'JC',4:'JZ',5:'LOAD',6:'STORE',7:'CALL'}
FAMILY={0:'NOP',1:'MOV',2:'XCH',3:'ADD',4:'SUB',5:'OUT',6:'HLT',7:'DEC',8:'INC',9:'LOADB',10:'STOREB',11:'IN',12:'RET',13:'AND',14:'OR',15:'XOR'}
TWO_WORD={'JMP','JC','JZ','CALL'}
# execute-step recipes: instruction -> (S3 lines, S4 lines). PCL on JC/JZ is conditional (see controls()).
RECIPE={'NOP':({'DONE'},set()),
        'MOV':({'BA','DONE'},set()),
        'XCH':({'AB','BA','DONE'},set()),
        'ADD':({'EO','AI','FI','DONE'},set()),
        'SUB':({'SUB','EO','AI','FI','DONE'},set()),
        'OUT':({'AO','OI','DONE'},set()),
        'HLT':({'HLT'},set()),
        'DEC':({'ONE','SUB','EO','AI','FI','DONE'},set()),
        'INC':({'ONE','EO','AI','FI','DONE'},set()),
        'LOADB':({'BO','MAI'},{'MO','AI','DONE'}),
        'STOREB':({'BO','MAI'},{'AO','MI','DONE'}),
        'IN':({'INP','AI','DONE'},set()),
        'RET':({'PCR','DONE'},set()),
        'AND':({'F0','EO','AI','FI','DONE'},set()),
        'OR':({'F1','EO','AI','FI','DONE'},set()),
        'XOR':({'F0','F1','EO','AI','FI','DONE'},set()),
        'LDI':({'IO','AI','DONE'},set()),
        'JMP':({'PCL','DONE'},set()),
        'JC':({'PCL?','DONE'},set()),
        'JZ':({'PCL?','DONE'},set()),
        'LOAD':({'IO','MAI'},{'MO','AI','DONE'}),
        'STORE':({'IO','MAI'},{'AO','MI','DONE'}),
        'CALL':({'RAI','PCL','DONE'},set())}
DRIVERS=('AO','BO','EO','IO','MO','INP')     # lines that put a value on the bus; at most one is ever high

class Machine:
    def __init__(self,program,data=None,inputs=(),has_datamem=True):
        self.mem=(list(program)+[0]*256)[:256]
        self.data=(list(data or [])+[0]*16)[:16]
        self.inputs=list(inputs); self.has_datamem=has_datamem
        self.reset(); self.trace=[]
    def reset(self):
        self.pc=0; self.ir=0; self.opr=0; self.ra=0; self.cf=0; self.zf=0; self.step=0
        self.a=0; self.b=0; self.out=0; self.mar=0; self.halted=False; self.nin=0
    # ---- combinational ----
    @property
    def op(self):
        """Instruction name: the opcode, or for opcode 0000 the family member the operand nibble selects."""
        name=OPS.get(self.ir,'NOP')
        return FAMILY[self.opr&15] if name=='EXT' else name
    @staticmethod
    def alu_static(a,b,ctl):
        """(result, carry, zero) of the ALU for the control lines in ctl (SUB, ONE, F0, F1)."""
        if 'ONE' in ctl: b=1
        f=(2 if 'F1' in ctl else 0)+(1 if 'F0' in ctl else 0)
        if f==0:
            s=a+((~b)&15)+1 if 'SUB' in ctl else a+b
            return s&15, (s>>4)&1, int((s&15)==0)
        r=[0,a&b,a|b,a^b][f]&15
        return r, 0, int(r==0)
    def alu(self,ctl=None):
        return self.alu_static(self.a,self.b,ctl if ctl is not None else self.controls())
    @property
    def switches(self):
        """What the panel's data switches show: the next input value, or the last one once all are consumed."""
        if not self.inputs: return 0
        return self.inputs[min(self.nin,len(self.inputs)-1)]
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
        if 'EO' in ctl: return self.alu(ctl)[0]
        if 'IO' in ctl: return self.opr&15
        if 'MO' in ctl: return self.data[self.mar] if self.has_datamem else 0
        if 'INP' in ctl: return self.switches
        return 0
    def snapshot(self):
        ctl=self.controls()
        return dict(step=self.step,pc=self.pc,ir=self.ir,opr=self.opr,ra=self.ra,a=self.a,b=self.b,out=self.out,cf=self.cf,zf=self.zf,
                    m=self.mem[self.pc],bus=self.bus(ctl),sw=self.switches,ctl=sorted(ctl),op=self.op,halted=self.halted)
    # ---- sequential ----
    def tick(self):
        """One rising edge. Returns False (and changes nothing) once HLT is high: the clock has stopped."""
        snap=self.snapshot(); self.trace.append(snap)
        ctl=set(snap['ctl'])
        if 'HLT' in ctl: self.halted=True; return False
        m=self.mem[self.pc]; bus=snap['bus']
        a,b,pc=self.a,self.b,self.pc
        res,cf,zf=self.alu(ctl)
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
        if 'INP' in ctl: self.nin+=1
        if 'RAI' in ctl: self.ra=pc
        if 'PCL' in ctl: self.pc=self.opr
        elif 'PCR' in ctl: self.pc=self.ra
        elif 'PCE' in ctl: self.pc=(pc+1)&255
        # step counter
        if 'DONE' in ctl: self.step=0
        elif self.step==1: self.step=2 if self.op in TWO_WORD else 3
        else: self.step=(self.step+1)%5
        return True
    def run(self,max_ticks=5000):
        """Run until HLT. Returns the list of OUT values in the order they were written."""
        outs=[]
        for _ in range(max_ticks):
            if not self.tick(): break
            if 'OI' in self.trace[-1]['ctl']: outs.append(self.out)
        return outs

if __name__=='__main__':
    import sys, asm
    words,labels,meta=asm.assemble(open(sys.argv[1]).read())
    m=Machine(words,inputs=[int(x) for x in meta.get('input','').split()]); outs=m.run()
    for s in m.trace: print(f"{s['step']} pc={s['pc']:3d} m={s['m']:08b} {s['op']:6s} A={s['a']:2d} B={s['b']:2d} OUT={s['out']:2d} C={s['cf']} Z={s['zf']} bus={s['bus']:2d} {' '.join(s['ctl'])}")
    print('OUT sequence:',outs,'halted' if m.halted else 'NOT HALTED','after',len(m.trace),'ticks')
