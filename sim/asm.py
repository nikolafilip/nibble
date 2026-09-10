"""Assembler for the Nibble ISA (docs/isa.md, v2).

Syntax: one instruction per line, `label:` prefixes, `;` comments, numbers
decimal or 0x../0b... `LOAD [B]` / `STORE [B]` are the indirect forms.
Directives in comments drive the tests:
  ; expect: 0 1 1 2 3        the OUT values the program must produce, in order
  ; expect-halt: end         the HLT that stops the machine must be the one at this label
  ; input: 7 6               values the panel switches show to successive IN instructions
  ; needs: datamem           program requires the data memory board
"""
import re
from emu import OPS, FAMILY, TWO_WORD
OPC={v:k for k,v in OPS.items()}; FAM={v:k for k,v in FAMILY.items()}
DIRECTIVES=('expect','expect-halt','input','needs')

def _num(s,labels):
    s=s.strip()
    if s in labels: return labels[s]
    return int(s,0)

def parse(code):
    """'LOAD [B]' -> ('LOADB',[]), 'MOV B,A' -> ('MOV',[]), 'LDI 3' -> ('LDI',['3'])"""
    parts=code.replace(',',' ').split(); mnem=parts[0].upper(); args=parts[1:]
    if mnem=='MOV':
        assert [a.upper() for a in args]==['B','A'], 'only MOV B,A exists'
        return 'MOV',[]
    if mnem in ('LOAD','STORE') and args and args[0].upper()=='[B]': return mnem+'B',[]
    return mnem,args

def encode(mnem,args,labels):
    if mnem in FAM: return [FAM[mnem]]                                   # opcode 0000, operand = family member
    if mnem in TWO_WORD: return [OPC[mnem]<<4, _num(args[0],labels)&255]
    if mnem in ('LDI','LOAD','STORE'): return [(OPC[mnem]<<4)|(_num(args[0],labels)&15)]
    raise SystemExit(f'unknown instruction {mnem}')

def assemble(text):
    """Returns (words, labels, meta). words = list of ints (8-bit), meta = the ; directives."""
    lines=[]; meta={}
    for raw in text.splitlines():
        code,_,comment=raw.partition(';')
        m=re.match(r'\s*([\w-]+):\s*(.*)',comment)
        if m and m.group(1) in DIRECTIVES: meta[m.group(1)]=m.group(2).strip()
        code=code.strip()
        if code: lines.append(code)
    labels={}; pc=0; items=[]
    for code in lines:
        while re.match(r'\w+:',code):
            lab,_,code=code.partition(':'); labels[lab.strip()]=pc; code=code.strip()
        if not code: continue
        mnem,args=parse(code)
        if mnem not in FAM and mnem not in OPC: raise SystemExit(f'unknown instruction {mnem}')
        items.append((pc,mnem,args)); pc+=2 if mnem in TWO_WORD else 1
    words=[]
    for pc,mnem,args in items: words+=encode(mnem,args,labels)
    if len(words)>256: raise SystemExit('program longer than 256 words')
    return words,labels,meta

def listing(words,labels):
    """Human listing with the switch settings, one row per word, grouped by 16-word page."""
    inv={v:k for k,v in labels.items()}
    out=[]
    for a,wd in enumerate(words):
        if a%16==0: out.append(f"--- page {a//16} (PC7..4 = {a//16:04b}) ---")
        out.append(f"{a:3d}  row {a%16:2d}  {wd>>4:04b} {wd&15:04b}  {inv.get(a,'')}")
    return "\n".join(out)

if __name__=='__main__':
    import sys
    w,l,m=assemble(open(sys.argv[1]).read()); print(listing(w,l)); print(len(w),'words',m)
