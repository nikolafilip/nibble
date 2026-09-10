"""Gate-level design description in Nibble's NMOS cell family (docs/gate-cell.md).

One cell = 2N7000s pulling an output down + one pull-up resistor.
  INV  : one transistor
  NAND : transistors in series (max 3)
  NOR  : transistors in parallel
  BUS  : open-drain driver, no pull-up (the hub has it)
  LED  : indicator: +5V -> 1k -> LED -> drain
A Design is emitted as a flat SPICE netlist (dev simulation) and drawn as a
KiCad sheet (ksch.py). Both come from the same gate list.
"""
import collections

PU_DEFAULT='47k'
MAX_SERIES=3
MAX_LOADS={'47k':8,'22k':16,'10k':32}   # rising-edge budget, see docs/gate-cell.md
LED_R='1k'

class Design:
    def __init__(self,name):
        self.name=name
        self.gates=[]            # dict(kind,out,ins,pu,group,note)
        self.inputs=set()        # primary inputs (header pins, constants)
        self.group='misc'
        self.ext_loads=collections.Counter()
    # ---- cells ----
    def _g(self,kind,out,ins,pu,note=''):
        ins=list(ins)
        if kind=='NAND': assert len(ins)<=MAX_SERIES, (out,ins)
        self.gates.append(dict(kind=kind,out=out,ins=ins,pu=pu,group=self.group,note=note)); return out
    def inv(self,out,a,pu=PU_DEFAULT,note=''):   return self._g('NAND',out,[a],pu,note)
    def nand(self,out,*ins,pu=PU_DEFAULT,note=''):return self._g('NAND',out,ins,pu,note)
    def nor(self,out,*ins,pu=PU_DEFAULT,note=''): return self._g('NOR',out,ins,pu,note)
    def bus(self,line,a,note=''):                  return self._g('BUS',line,[a],None,note)
    def led(self,name,a,note=''):                  return self._g('LED',name,[a],LED_R,note)
    def xor(self,out,a,b,pu=PU_DEFAULT):
        """7 transistors: out = NOR(NOR(a,b), AND(a,b))"""
        p=out+'_'
        self.nor(p+'n',a,b); self.nand(p+'a',a,b); self.inv(p+'d',p+'a')
        return self.nor(out,p+'n',p+'d',pu=pu)
    def ff(self,q,d,clk=None,qpu=PU_DEFAULT,ckn=None,ckb=None):
        """Positive-edge master-slave D flip-flop from NANDs (20 transistors, 18 when the clock pair ckn/ckb is shared).
        Master is transparent while clk is low, slave copies it on the rising edge."""
        p=q+'_'
        if ckn is None: self.inv(p+'ckn',clk); ckn=p+'ckn'
        if ckb is None: self.inv(p+'ckb',ckn); ckb=p+'ckb'
        self.inv(p+'dn',d)
        self.nand(p+'m1',d,ckn); self.nand(p+'m2',ckn,p+'dn')
        self.nand(p+'mq',p+'m1',p+'mqn'); self.nand(p+'mqn',p+'mq',p+'m2')
        self.inv(p+'mqi',p+'mq')
        self.nand(p+'sa',p+'mq',ckb); self.nand(p+'sb',ckb,p+'mqi')      # not 's1'/'s2': <q>_s1 is the series node of the q NAND
        self.nand(q,p+'sa',p+'qn',pu=qpu); self.nand(p+'qn',q,p+'sb')
        return q
    # ---- checks ----
    def outputs(self): return {g['out']:g for g in self.gates if g['kind'] not in ('BUS','LED')}
    def loads(self):
        c=collections.Counter(self.ext_loads)
        for g in self.gates:
            for i in g['ins']: c[i]+=1
        return c
    def check(self):
        outs=self.outputs(); c=self.loads(); pr=[]
        lower=collections.Counter(g['out'].lower() for g in self.gates if g['kind']!='BUS')
        pr+=[f"duplicate output {o}" for o,k in lower.items() if k>1]
        for g in self.gates:
            for i in g['ins']:
                if i not in outs and i not in self.inputs: pr.append(f"{g['out']}: input {i} is driven by nothing (floating gate)")
        for net,n in c.items():
            if net in outs and n>MAX_LOADS[outs[net]['pu']]: pr.append(f"{net}: {n} loads on {outs[net]['pu']}")
        for g in self.gates:
            if g['kind']=='NAND' and len(g['ins'])>MAX_SERIES: pr.append(f"{g['out']}: {len(g['ins'])} in series")
        # a NAND's internal series nodes are <out>_s1, _s2: they must not collide with a net of that name
        nets=set(lower)|set(i.lower() for g in self.gates for i in g['ins'])
        for g in self.gates:
            if g['kind']=='NAND':
                for k in range(1,len(g['ins'])):
                    if f"{g['out']}_s{k}".lower() in nets: pr.append(f"{g['out']}: series node {g['out']}_s{k} collides with a net of that name")
        return pr
    def ntransistors(self): return sum(len(g['ins']) for g in self.gates)
    def nresistors(self): return sum(1 for g in self.gates if g['pu'])
    def nleds(self): return sum(1 for g in self.gates if g['kind']=='LED')
    # ---- SPICE ----
    def spice(self,model='2N7000',vdd='VDD'):
        """Flat netlist lines. Node names are the net names; internal series nodes get _s<k>."""
        L=[]; q=1; r=1
        for g in self.gates:
            ins=g['ins']; out=g['out']; kind=g['kind']
            if kind=='LED':
                L.append(f"R{r} {vdd} {out}_a {g['pu']}"); r+=1
                L.append(f"D{r} {out}_a {out}_k LEDRED"); r+=1
                L.append(f"M{q} {out}_k {ins[0]} 0 {model}"); q+=1
                continue
            if kind=='BUS':
                L.append(f"M{q} {out} {ins[0]} 0 {model}"); q+=1
                continue
            L.append(f"R{r} {vdd} {out} {g['pu']}"); r+=1
            if kind=='NAND':
                node=out
                for k,i in enumerate(ins):
                    nxt='0' if k==len(ins)-1 else f"{out}_s{k+1}"
                    L.append(f"M{q} {node} {i} {nxt} {model}"); q+=1; node=nxt
            else:
                for i in ins:
                    L.append(f"M{q} {out} {i} 0 {model}"); q+=1
        return L

LED_MODEL=".model LEDRED D(Is=1e-18 Rs=3 N=1.8 Cjo=20p)"
SW_MODEL=".model ODRV SW(VT=2.5 VH=0.2 RON=20 ROFF=1e9)"   # ideal open-drain driver for testbenches: closes to ground when its control is high
