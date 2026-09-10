"""Assembler for the Nibble ISA (docs/isa.md).

Syntax: one instruction per line, `label:` prefixes, `;` comments, numbers
decimal or 0x../0b... Directives in comments drive the tests:
  ; expect: 0 1 1 2 3        the OUT values the program must produce, in order
  ; expect-halt: end         the HLT that stops the machine must be the one at this label
  ; needs: datamem           program requires the data memory board
"""
import re
from emu import OPS, TWO_WORD
OPC={v:k for k,v in OPS.items()}

def _num(s,labels):
    s=s.strip()
    if s in labels: return labels[s]
    return int(s,0)

def assemble(text):
    """Returns (words, labels, meta). words = list of ints (8-bit), meta = the ; directives."""
    lines=[]; meta={}
    for raw in text.splitlines():
        code,_,comment=raw.partition(';')
        m=re.match(r'\s*([\w-]+):\s*(.*)',comment)
        if m and m.group(1) in ('expect','expect-halt','needs'): meta[m.group(1)]=m.group(2).strip()
        code=code.strip()
        if code: lines.append(code)
    # pass 1: labels
    labels={}; pc=0; items=[]
    for code in lines:
        while re.match(r'\w+:',code):
            lab,_,code=code.partition(':'); labels[lab.strip()]=pc; code=code.strip()
        if not code: continue
        parts=code.replace(',',' ').split(); mnem=parts[0].upper(); args=parts[1:]
        if mnem=='MOV':
            assert [a.upper() for a in args]==['B','A'], 'only MOV B,A exists'
            args=[]
        if mnem not in OPC: raise SystemExit(f'unknown instruction {mnem}')
        items.append((pc,mnem,args)); pc+=2 if mnem in TWO_WORD else 1
    # pass 2
    words=[]
    for pc,mnem,args in items:
        if mnem in TWO_WORD:
            words.append(OPC[mnem]<<4); words.append(_num(args[0],labels)&255)
        elif mnem in ('LDI','LOAD','STORE'):
            words.append((OPC[mnem]<<4)|(_num(args[0],labels)&15))
        else:
            words.append(OPC[mnem]<<4)
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
