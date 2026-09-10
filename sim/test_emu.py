"""Run every program in programs/ on the emulator and check its ; expect directives."""
import glob, os, sys
import asm, emu
def check(path,has_datamem=True):
    words,labels,meta=asm.assemble(open(path).read())
    m=emu.Machine(words,has_datamem=has_datamem); outs=m.run()
    want=[int(x) for x in meta.get('expect','').split()]
    ok=outs==want and m.halted
    if 'expect-halt' in meta: ok=ok and m.trace[-1]['pc']==labels[meta['expect-halt']]+1   # PC has already stepped past the HLT word
    return ok,outs,want,m
if __name__=='__main__':
    bad=0
    for p in sorted(glob.glob(os.path.join(os.path.dirname(__file__),'programs','*.asm'))):
        ok,outs,want,m=check(p)
        print(f"{'ok  ' if ok else 'FAIL'} {os.path.basename(p):10s} {len(asm.assemble(open(p).read())[0]):3d} words {len(m.trace):4d} ticks  out={outs}" + ('' if ok else f'  want={want} halted={m.halted} pc={m.trace[-1]["pc"]}'))
        bad+=not ok
    sys.exit(1 if bad else 0)
