"""Whole-machine simulation (docs/plan.md): every board's kicad-cli SPICE export
in one ngspice deck, running a real program, checked tick for tick against emu.py.

    python3 machine.py programs/fib.asm --boards alu,panel,hub [--corner TYP|LO|HI|MIX] [--seed N] [--ticks N]

A board given as name@dev uses the gate list's own netlist instead of the
schematic export (for trying a design before drawing it). Corner MIX gives every
transistor a random threshold from the three models: the test that catches
latches which are only correct when all parts match.

Boards that exist are included as subcircuits. Boards that do not exist yet are
played by the emulator: the sequencer's control lines and PC, the registers' A
and B lines, come from piecewise-linear sources that reproduce the emulator's trace. So the
same deck tests the ALU alone today, ALU + registers next, and the full machine
once the sequencer exists, and a board is always judged against the hardware
around it, real or virtual.

Program memory is a behavioural model (M = f(PC) through a diode, like the
switch boards) until the memory board exists. The clock is a pulse source
gated by HLT until the clock board exists.
"""
import os, re, random, subprocess, sys
import numpy as np
import spicedat
import bus, asm, emu

HERE=os.path.dirname(os.path.abspath(__file__)); BOARDS=os.path.join(HERE,'..','boards'); OUT=os.path.join(HERE,'out')
KICAD_CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
T=1e-3          # clock period
T0=2e-3         # first rising edge
STEP_DELAY=20e-6   # virtual sequencer: control lines change this long after the edge
CONTROL=['SUB','EO','AI','AO','BI','BO','BA','AB','OI','IO','II','PCE','PCL','FI','HLT','MAI','MI','MO','ONE','F0','F1','INP']
SW=[f'SW{i}' for i in range(4)]   # the panel's data switch levels, ports of the panel subcircuit so the deck can set them
PC=[f'PC{i}' for i in range(8)]; M=[f'M{i}' for i in range(8)]
# per board: schematic path, the design module for a dev netlist (board@dev), and the internal nets to probe
BOARD={'alu':('01-alu/alu.kicad_sch','alu',[]),
       'reg':('02-registers/registers.kicad_sch','registers',['OUT0','OUT1','OUT2','OUT3']),
       'seq':('03-sequencer/sequencer.kicad_sch','sequencer',['T0','T1','T2','T3','T4','CFQ','ZFQ']),
       'mem':('08-memory/memory.kicad_sch','memory',[]),
       'panel':('06-panel/panel.kicad_sch','panel',[]),
       'hub':('07-hub/hub.kicad_sch',None,[])}

def export(board,dev=False):
    """A board's netlist: the kicad-cli SPICE export of its schematic, or (dev) the gate list's own flat netlist."""
    if dev:
        import importlib; d=importlib.import_module(BOARD[board][1]).build(); assert not d.check(), d.check()
        return d.spice(vdd='+5V')
    sch=os.path.join(BOARDS,BOARD[board][0]); cir=os.path.join(OUT,f'{board}_kicad.cir')
    r=subprocess.run([KICAD_CLI,'sch','export','netlist','--format','spice','-o',cir,sch],capture_output=True,text=True)
    if not os.path.exists(cir): raise SystemExit(r.stdout+r.stderr)
    return [l.rstrip() for l in open(cir) if l.strip()]

def subckt(board,lines,corner,rng=None):
    """Wrap a board's export as .subckt <board> <bus ports>. Drops directives and testbench parts (refs >= 9000).
    corner TYP/LO/HI gives every transistor that model; MIX gives each transistor a random one (threshold spread between parts)."""
    models={'TYP':'2N7000','LO':'2N7000_LO','HI':'2N7000_HI'}
    body=[]
    for l in lines:
        if l.startswith(('.','*')): continue
        ref=l.split()[0]; num=re.sub(r'\D','',ref)
        if num and int(num)>=9000: continue
        if l[0] in 'Mm':
            model=models[rng.choice(['LO','TYP','HI'])] if corner=='MIX' else models[corner]
            l=l.replace(' 2N7000',' '+model)
        body.append(l)
    nodes=set(tok for l in body for tok in l.split()[1:])
    ports=[s for s in bus.SIGNALS+SW if s in nodes]
    return ports, [f".subckt {board} "+" ".join(ports)]+body+[".ends"]

def od(en,x,i,tag):
    """An ideal open-drain driver on BUS<i>#: a switch to ground closed when both en and x are high (ngspice's SW model converges where a stepping B-source does not)."""
    return [f"Ben{tag}{i} en{tag}{i} 0 V = V({en})>2.5 && V({x})>2.5 ? 5 : 0", f"S{tag}{i} BUS{i}# 0 en{tag}{i} 0 ODRV"]

def pwl(times,values,delay):
    pts=[(0,values[0])]
    for t,v in zip(times,values): pts.append((t+delay-1e-6,pts[-1][1])); pts.append((t+delay+1e-6,v))
    return "PWL("+" ".join(f"{t:.7g} {5*v}" for t,v in pts)+")"

def deck(program,boards,corner,trace,outfile,seed=1):
    edges=[T0+k*T for k in range(len(trace))]
    starts=[e-T for e in edges]      # the state of tick k is set up during the period before edge k
    import nmos
    L=["* Nibble whole-machine deck",'.include "../lib/2N7000.lib"','.include "../lib/led.lib"',nmos.SW_MODEL,'.global +5V','V5 +5V 0 5']
    probes=[]; rng=random.Random(seed)
    for spec in boards:
        b,_,dev=spec.partition('@')
        ports,sub=subckt(b,export(b,dev=='dev'),corner,rng); L+=sub; L.append(f"X{b} "+" ".join(ports)+f" {b}")
        probes+=[f"x{b}.{n}" for n in BOARD[b][2]]
    probes+=bus.SIGNALS+['CLK','RST']
    # clock and reset (until the clock board exists): pulse gated by HLT
    L.append(f"Vclk clkraw 0 PULSE(0 5 {T0:.6g} 1u 1u {T/2-1e-6:.6g} {T:.6g})")
    # gate the clock with HLT through a smooth function (a ternary is a zero-time step: "timestep too small" at every edge)
    L.append("Bclk clkb 0 V = V(clkraw)*pwl(V(HLT),0,1,2,1,3,0,5,0)"); L.append("Rclk clkb CLK 100")     # pwl() extrapolates outside its points: give it the whole 0..5 V range
    L.append(f"Vrst rstraw 0 PULSE(5 0 {T0*0.4:.6g} 1u 1u 1 2)"); L.append("Rrst rstraw RST 100")
    # program memory model: M = mem[PC] through a diode (the hub pulls M down)
    idx="+".join(f"{1<<i}*u(V(PC{i})-2.5)" for i in range(8))
    for i in range(8):
        tbl=",".join(f"{a},{(w>>i)&1}" for a,w in enumerate(program))+(f",{len(program)},0,255,0" if len(program)<256 else "")   # pwl() extrapolates past its last point: pin it to 0 up to address 255
        L.append(f"Bm{i} mraw{i} 0 V = 5*pwl({idx},{tbl})"); L.append(f"Dm{i} mraw{i} M{i} D1N4148")
    # boards played by the emulator
    virt=[]
    boards=[b.partition('@')[0] for b in boards]
    if 'seq' not in boards:
        for n in CONTROL: virt.append(n)
        for n in PC: virt.append(n)
        for n in CONTROL:
            L.append(f"V{n} v{n} 0 "+pwl(starts,[int(n in s['ctl']) for s in trace],STEP_DELAY)); L.append(f"R{n} v{n} {n} 100")
        for i,n in enumerate(PC):
            L.append(f"V{n} v{n} 0 "+pwl(starts,[(s['pc']>>i)&1 for s in trace],STEP_DELAY)); L.append(f"R{n} v{n} {n} 100")
        # the virtual sequencer's operand register drives the bus when IO is high (ideal open-drain driver)
        for i in range(4):
            L.append(f"Vopr{i} opr{i} 0 "+pwl(starts,[(s['opr']>>i)&1 for s in trace],STEP_DELAY))
            L+=od('IO',f'opr{i}',i,'io')
    if 'reg' not in boards:
        for i in range(4):
            for n,f in ((f'A{i}','a'),(f'B{i}','b')):
                L.append(f"V{n} v{n} 0 "+pwl(starts,[(s[f]>>i)&1 for s in trace],STEP_DELAY)); L.append(f"R{n} v{n} {n} 100")
        # a virtual register board also has to drive the bus for AO / BO: modelled as ideal open-drain drivers
        for i in range(4):
            L+=od('AO',f'A{i}',i,'ao')+od('BO',f'B{i}',i,'bo')
    if 'mem' not in boards:      # virtual data memory: drives the bus with the emulator's memory value while MO is high
        for i in range(4):
            L.append(f"Vmo{i} mo{i} 0 "+pwl(starts,[(s['bus']>>i)&1 if 'MO' in s['ctl'] else 0 for s in trace],STEP_DELAY))
            L+=od('MO',f'mo{i}',i,'mo')
    # the panel's data switches: driven from the trace (what the program expects to read with IN)
    for i in range(4):
        L.append(f"Vsw{i} SW{i} 0 "+pwl(starts,[(s['sw']>>i)&1 for s in trace],STEP_DELAY))
    if 'panel' not in boards:     # virtual input port
        for i in range(4):
            L+=od('INP',f'SW{i}',i,'in')
    tend=edges[-1]+T/2
    top=set(tok for l in L if l[0] not in '.*+' and not l.startswith(('.subckt','.ends')) for tok in l.split()[1:])
    probes=[p for p in probes if '.' in p or p in top]     # a bus line no board touches is not a node in the deck
    L+=[f".tran 1u {tend:.6g}",".option method=gear",".control","run","set wr_singlescale","set wr_vecnames",
        f"wrdata {outfile} "+" ".join(f"v({p})" for p in probes),"quit",".endc",".end"]
    return "\n".join(L)+"\n", probes, edges

def sample(dat,probes,edges):
    names,a=spicedat.read(dat); t=a[:,0]; col={n.lower():a[:,k] for k,n in enumerate(names)}
    def bit(name,tt):
        v=col.get(f'v({name.lower()})')
        return 0 if v is None else int(np.interp(tt,t,v)>2.5)
    rows=[]
    for e in edges:
        tt=e-5e-6; rows.append({p:bit(p,tt) for p in probes})
    # a rising edge really happened at e (CLK low before, high after) unless the clock was halted
    for k,e in enumerate(edges): rows[k]['edge']=int(bit('CLK',e-5e-6)==0 and bit('CLK',e+5e-6)==1)
    return rows

def compare(rows,trace,boards):
    """Returns a list of (tick, field, want, got) mismatches."""
    bad=[]
    def num(row,names): return sum(row[n]<<i for i,n in enumerate(names))
    # A, B and OUT have no reset (docs/isa.md): their power-on state is whatever the flip-flops fall into, so they and
    # the flags the ALU computes from them are compared only once the program has written them
    known={'a':False,'b':False,'out':False}
    for k,(row,s) in enumerate(zip(rows,trace)):
        chk={}
        chk['m']=(s['m'],num(row,M))
        chk['bus']=(s['bus'],15-num(row,[f'BUS{i}#' for i in range(4)]))
        chk['pc']=(s['pc'],num(row,PC))
        chk['ctl']=(" ".join(c for c in CONTROL if c in s['ctl'])," ".join(c for c in CONTROL if row[c]))
        chk['edge']=(int(not s['halted'] and 'HLT' not in s['ctl']),row['edge'])
        if 'alu' in boards and (known['a'] and known['b'] or 'reg' not in boards):
            res,cf,zf=emu.Machine.alu_static(s['a'],s['b'],set(s['ctl']))
            chk['CF']=(cf,row['CF']); chk['ZF']=(zf,row['ZF'])
        if 'reg' in boards:
            if known['a']: chk['a']=(s['a'],num(row,[f'A{i}' for i in range(4)]))
            if known['b']: chk['b']=(s['b'],num(row,[f'B{i}' for i in range(4)]))
            if known['out']: chk['out']=(s['out'],num(row,[f'xreg.OUT{i}' for i in range(4)]))
        c=set(s['ctl'])
        if c&{'AI','AB'}: known['a']=True
        if c&{'BI','BA'}: known['b']=True
        if 'OI' in c: known['out']=True
        if 'seq' in boards:
            chk['step']=(s['step'],[row[f'xseq.T{i}'] for i in range(5)].index(1) if 1 in [row[f'xseq.T{i}'] for i in range(5)] else -1)
            chk['cf']=(s['cf'],row['xseq.CFQ']); chk['zf']=(s['zf'],row['xseq.ZFQ'])
        for f,(want,got) in chk.items():
            if want!=got: bad.append((k,f,want,got))
    return bad

def run_trace(words,trace,boards,corner='TYP',tag='machine',seed=1):
    os.makedirs(OUT,exist_ok=True); cir=os.path.join(OUT,tag+'.cir'); dat=os.path.join(OUT,tag+'.dat')
    if os.path.exists(dat): os.remove(dat)
    text,probes,edges=deck(words,boards,corner,trace,dat,seed); open(cir,'w').write(text)
    r=subprocess.run(['ngspice','-b',cir],capture_output=True,text=True,cwd=HERE)
    if not os.path.exists(dat): print(r.stdout[-4000:],r.stderr[-4000:]); raise SystemExit('ngspice failed')
    if 'aborted' in r.stdout+r.stderr:
        print("\n".join(l for l in (r.stdout+r.stderr).splitlines() if 'Timestep' in l or 'aborted' in l)); raise SystemExit('ngspice aborted the transient')
    rows=sample(dat,probes,edges); bad=compare(rows,trace,[b.partition('@')[0] for b in boards])
    return rows,bad

def run(prog,boards,corner='TYP',ticks=None,tag=None,seed=1):
    words,labels,meta=asm.assemble(open(prog).read())
    m=emu.Machine(words,inputs=[int(x) for x in meta.get('input','').split()]); m.run()
    trace=m.trace if ticks is None else m.trace[:ticks]
    tag=tag or f"machine_{os.path.basename(prog).split('.')[0]}_{'-'.join(boards).replace('@','')}_{corner}{seed if corner=='MIX' else ''}"
    rows,bad=run_trace(words,trace,boards,corner,tag,seed)
    return trace,rows,bad

if __name__=='__main__':
    prog=sys.argv[1]; boards=sys.argv[sys.argv.index('--boards')+1].split(',')
    corner=sys.argv[sys.argv.index('--corner')+1] if '--corner' in sys.argv else 'TYP'
    ticks=int(sys.argv[sys.argv.index('--ticks')+1]) if '--ticks' in sys.argv else None
    seed=int(sys.argv[sys.argv.index('--seed')+1]) if '--seed' in sys.argv else 1
    trace,rows,bad=run(prog,boards,corner,ticks,seed=seed)
    print(f"{os.path.basename(prog)} on {'+'.join(boards)} @ {corner}: {len(trace)} ticks, {len(bad)} mismatches")
    for k,f,want,got in bad[:40]: print(f"  tick {k:4d} step {trace[k]['step']} {f}: want {want!r} got {got!r}")
    sys.exit(1 if bad else 0)
