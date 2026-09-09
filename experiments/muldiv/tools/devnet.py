"""Build the development netlist: original exported netlist + the root-sheet edits applied at netlist level + new logic."""
import sys, re, collections
sys.path.insert(0,'.')
from kisch import *
import logic

SCH='/Users/nikolafilip/Documents/Calculator/Untitled.kicad_sch'

def root_edit_plan():
    """Everything that changes in the root sheet, derived from geometry so the same plan drives the schematic editor."""
    s=Sch(open(SCH).read()); uf,pins=connectivity(s)
    node=collections.defaultdict(list)
    for ref,num,name,xy,sym in pins: node[uf.f(xy)].append((ref,num))
    byref={}
    for ref,num,name,xy,sym in pins: byref.setdefault(ref,{})[num]=xy
    lab={}
    for l in s.labels: lab.setdefault(l[1],[]).append(l)
    plan={}
    # 1. encoder output inverters to delete; label goes where the base resistor met the NOR collector wire
    enc=[('A0','Q96','R250','R248','R249'),('A1','Q91','R238','R236','R237'),('A2','Q84','R222','R220','R221'),
         ('EB0','Q111','R286','R284','R285'),('EB1','Q110','R283','R280','R281'),('EB2','Q109','R282','R278','R279')]
    plan['encoder']=[]
    for net,q,rpu,rb,rpd in enc:
        pw=[r for r,n in node[uf.f(byref[rpu]['1'])] if r.startswith('#PWR')]     # +5V on pull-up
        pw+=[r for r,n in node[uf.f(byref[q]['1'])] if r.startswith('#PWR')]      # GND on emitter
        pw+=[r for r,n in node[uf.f(byref[rpd]['1'])] if r.startswith('#PWR')]    # GND on 22k
        plan['encoder'].append(dict(net=net,delete=[q,rpu,rb,rpd]+pw,
                                    label_in=(('ENCA_N' if net[0]=='A' else 'ENCB_N')+net[-1], byref[rb]['1']),   # NOR output side of base resistor
                                    label_out=(net, byref[q]['3'])))                        # collector wire end -> adder input net
    # 2. FF-side labels to rename (the label instance nearest the register block, y>1100)
    plan['rename_labels']=[]
    for old,new in [('OUT0','REG_D0'),('OUT1','REG_D1'),('OUT2','REG_D2'),('OUT3','REG_D3'),('SIG','REG_DS')]:
        cands=[l for l in lab[old] if l.at()[1]>1100]
        assert len(cands)==1,(old,[l.at() for l in lab[old]])
        l=cands[0]
        rs=[r for r,n in node[uf.f(key(l.at()[:2]))] if r.startswith('R')]
        plan['rename_labels'].append(dict(old=old,new=new,uuid=l.find('uuid')[1],resistors=rs))
    # 3. power-symbol value changes
    plan['power_values']=[('#PWR0319','SUB2'),('#PWR0320','SUB2'),('#PWR0321','SUB2'),
                          ('#PWR0459','SIGB'),('#PWR0460','SIGB'),('#PWR0461','SIGB'),
                          ('#PWR0189','Y2'),('#PWR0190','X5')]
    # 4. sources & directives to delete (moved to the testbench sheet); power symbols hanging on them
    plan['delete_sources']=['V2','#PWR0317','#PWR0318','V4','#PWR0487']
    plan['clock_label']=('MEMCLK', byref['V4']['1'])       # wire end where V4 pin 1 was
    plan['rename_local']=[('CLOCK','MEMCLK')]
    # 5. sum-bit pull-ups to 2.2k
    plan['pullup_22k']=[]
    for l in open('orig.cir'):
        t=l.split()
        if t and t[0][0]=='R' and len(t)==4 and t[3]=='4.7k' and '+5V' in t[1:3] and any(n in('/S0','/S1','/S2','/S3','OUT_B0','OUT_B1') for n in t[1:3]):
            plan['pullup_22k'].append(t[0])
    return plan, s, uf, pins

def netmap_root(name):
    m={'/A0':'A0','/A1':'A1','/A2':'A2','/EB0':'EB0','/EB1':'EB1','/EB2':'EB2','/S0':'S0','/S1':'S1','/S2':'S2','/S3':'S3','/CLOCK':'MEMCLK'}
    if name in m: return m[name]
    if re.fullmatch(r'/[XY][1-7]',name): return name[1:]
    return name

def build_dev_root(orig='orig.cir'):
    plan,s,uf,pins=root_edit_plan()
    lines=[l.rstrip('\n') for l in open(orig)]
    delete=set(plan['delete_sources'])
    for e in plan['encoder']: delete|=set(e['delete'])
    renames={}   # (ref, netname) -> new net
    for e in plan['encoder']:
        pass
    ffres={}
    for r in plan['rename_labels']:
        for rr in r['resistors']: ffres[(rr,r['old'])]=r['new']
    pwr={'SUB2':['R287','R292','R308','R313','R329','R334'],'SIGB':['R450','R454','R471','R475','R492','R496'],'Y2':['R232'],'X5':['R252','R273']}
    encnet={'Net-_Q92-C_':'ENCA_N0','Net-_Q87-C_':'ENCA_N1','Net-_Q82-C_':'ENCA_N2','Net-_Q105-C_':'ENCB_N0','Net-_Q101-C_':'ENCB_N1','Net-_Q100-C_':'ENCB_N2'}
    out=[]
    for l in lines:
        t=l.split()
        if not t or t[0].startswith('.') : continue
        ref=t[0]
        if ref in delete: continue
        if ref[0] in 'RQ':
            nets=[netmap_root(encnet.get(n,n)) for n in t[1:-1]]
            if ref[0]=='R':
                nets=[ffres.get((ref,n),n) for n in nets]
                for newn,refs in pwr.items():
                    if ref in refs: nets=[newn if (n in('SUB','+5V')) else n for n in nets]
                if ref in plan['pullup_22k']: t[-1]='2.2k'
            out.append(" ".join([ref]+nets+[t[-1]]))
        elif ref[0]=='V':
            out.append(l)      # V1 (+5V)
        else: out.append(l)
    return out, plan

if __name__=='__main__':
    root,plan=build_dev_root()
    import json
    for k,v in plan.items(): print(k, v if k!='encoder' else [(e['net'],e['delete'],e['label_in'],e['label_out']) for e in v])
    d=logic.build()
    new=logic.spice(d)
    open('dev_root.cir','w').write("\n".join(root)+"\n")
    open('dev_full.cir','w').write("\n".join(root+new)+"\n")
    print(len(root),len(new))
