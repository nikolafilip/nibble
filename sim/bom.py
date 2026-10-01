"""The order's tables, from the routed boards: which boards to have made, which parts to buy and how many.

    python3 bom.py               the three tables, as Markdown
    python3 bom.py --write       put them into docs/order-1.md, between its markers
    python3 bom.py --check       exit 1 unless docs/order-1.md carries these tables as they are now, and the two counts agree
    python3 bom.py --per         the parts, one column per design (one board of each)

Two counts, made independently, must agree before a table is printed: the schematic's bill of materials (fab/<board>-bom.csv,
written by kicad-cli from the schematic) and the footprints on the routed board (<board>.kicad_pcb, the do-not-populate
positions left out). A part the schematic has and the board has not, or the other way round, stops the script.

A DESIGN is a set of files (26 of them); a BOARD is a piece of fibreglass built and soldered (52: eight memory slot cards and
twenty program cards are one design each). The fab sells boards in fives, so a design is ordered as one five-pack, or as many
as its pieces need. NEED is what the 52 boards carry. BUY is NEED with spares, by the rule beside it (RULES below): parts that
cost a cent and get dropped are bought by the hundred, connectors and switches a few over, the one-off parts one over."""
import csv, glob, os, sys, re, math, collections
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..'); DOC=os.path.join(ROOT,'docs','order-1.md')
COPIES={'memslot':8,'prog':20}      # boards built of a design, where it is not one: eight slot pairs; program cards for the longest program (sort, 80 words, four to a card)
SPARE_PACKS={'prog':1}             # five-packs ordered over what the boards built need: twenty program cards are four packs to the last board (decided 2026-09-29: a fifth)
PILOT=['coupon','reg0','hub']
WHAT={'alu':'ALU bit','reg':'register bit','ctr':'counter bit','memctl':'memory control','memslot':'memory slots (one pair of slots a card)','prog':'program (four words a card)','clock':'clock',
      'hub':'bus hub','panela':'panel A','panelb':'panel B','panelc':'panel C','coupon':'gate coupon (a test card, not in the machine)','sequencer':'sequencer'}

# (footprint begins with, what it is called, the kind its rule goes by); {v} is the schematic's value
NAMES=[('TO-92','2N7000 transistor, TO-92','semi'),('TO-220','SCR BT151-500R, TO-220 (the crowbar)','one'),('D_DO-41','Zener diode 1N4735A, 6.2 V 1.3 W (the crowbar)','one'),
       ('D_DO-201','Rectifier diode 1N5408, 3 A (crossed leads)','one'),('R_Axial','Resistor {v}, 1/4 W axial','resistor'),('D_DO-35','1N4148 diode, DO-35','semi'),('LED','LED, 3 mm','led'),
       ('CP_Radial','Electrolytic capacitor {v}F, 5 mm can, 2 mm pitch, 16 V or more','cap'),('C_Disc','Ceramic capacitor {v}F, 2.5 mm pitch','cap'),
       ('IDC-Header_2x32','Box header 2x32, 2.54 mm (the bus)','conn'),('IDC-Header_2x06','Box header 2x6, 2.54 mm (link)','conn'),('IDC-Header_2x03','Box header 2x3, 2.54 mm (link)','conn'),
       ('PinHeader_1x03','Pin header 1x3, 2.54 mm (address jumper)','conn'),('PinHeader_1x02','Pin header 1x2, 2.54 mm','conn'),('PinHeader_1x06','Pin header 1x6, 2.54 mm','conn'),
       ('SW_DIP_SPSTx08','DIP switch, 8-way','conn'),('SW_DIP_SPSTx04','DIP switch, 4-way','one'),('SW_DIP_SPSTx01','DIP switch, 1-way','one'),('SW_PUSH','Push button, 6 mm tactile','one'),
       ('Potentiometer','Potentiometer 1 M linear, 9 mm upright (Alpha RD901F-40)','one'),('Fuse','Polyfuse 1.5 A (Bel 0ZRE0150FF)','one'),('TestPoint','Test loop, 1.0 mm hole','conn'),
       ('Banana_CalTest','Banana socket, 4 mm, for the board, upright: Cal Test CT3151V1-2 (red) and CT3151V1-0 (black), one of each','none2')]
RULES={'semi':('a tenth over, to the next 100',lambda n:math.ceil(n*1.1/100)*100),'resistor':('a tenth over, to the next 100 (they come in hundreds)',lambda n:math.ceil(n*1.1/100)*100),
       'led':('a tenth over, to the next 50',lambda n:math.ceil(n*1.1/50)*50),'cap':('a tenth over, to the next 10',lambda n:math.ceil(n*1.1/10)*10),
       'conn':('a twentieth over, two at the least',lambda n:n+max(2,math.ceil(n*0.05))),'one':('one over',lambda n:n+1),'none2':('none over: two are fitted',lambda n:n)}
ORDER=['semi','resistor','led','cap','conn','one','none2']

def designs():
    d=sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT,'cards','*','*.kicad_pcb')))
    return d+['sequencer']
def folder(name): return os.path.join(ROOT,'boards','03-sequencer') if name=='sequencer' else os.path.join(ROOT,'cards',name)
def ohms(v):
    m=re.match(r'^([\d.]+)(k|Meg|M)?$',v); return float(m.group(1))*{None:1,'k':1e3,'Meg':1e6,'M':1e6}[m.group(2)]
def farads(v):
    m=re.match(r'^([\d.]+)(p|n|u)$',v); return float(m.group(1))*{'p':1e-12,'n':1e-9,'u':1e-6}[m.group(2)]
def named(fp,v):
    """(what the part is called in the table, the kind its rule goes by, its place among its kind)"""
    for i,(pre,what,kind) in enumerate(NAMES):
        if not fp.startswith(pre): continue
        if kind=='resistor': o=ohms(v); return what.format(v=f'{o/1e6:g} Mohm' if o>=1e6 else f'{o/1e3:g} kohm' if o>=1e3 else f'{o:g} ohm'),kind,(i,o)
        if kind=='cap': return what.format(v=v.replace('u',' u').replace('n',' n')),kind,(i,-farads(v))
        return what,kind,(i,0)
    raise SystemExit(f'bom.py has no name for the footprint {fp}')

def from_schematic(name):
    c=collections.Counter()
    for r in csv.DictReader(open(os.path.join(folder(name),'fab',f'{name}-bom.csv'))):
        fp=r['Footprint'].split(':')[-1]
        if fp.startswith('MountingHole'): continue
        c[named(fp,r['Value'])]+=int(r['QUANTITY'])
    return c
def from_board(name):
    s=open(os.path.join(folder(name),f'{name}.kicad_pcb')).read(); c=collections.Counter()
    for m in re.finditer(r'^\t\(footprint "([^"]+)"(.*?)^\t\)$',s,re.S|re.M):
        fp,b=m.group(1),m.group(2); a=re.search(r'\(attr ([^)]*)\)',b)
        if fp.startswith('MountingHole') or fp.startswith('Logo_') or (a and 'dnp' in a.group(1).split()): continue      # a hole, the logo (silkscreen only) and a do-not-populate spot are no parts
        c[named(fp,re.search(r'\(property "Value" "([^"]*)"',b).group(1))]+=1
    return c

def load():
    per={}; wrong=[]
    for n in designs():
        a,b=from_schematic(n),from_board(n)
        if a!=b: wrong+=[f'{n}: {k[0]}: the schematic has {a[k]}, the board {b[k]}' for k in sorted(set(a)|set(b)) if a[k]!=b[k]]
        per[n]=b
    if wrong: raise SystemExit('the two counts differ:\n  '+'\n  '.join(wrong))
    return per
def key(k): return (ORDER.index(k[1]),k[2])

def tables():
    per=load(); names=designs(); T={}
    # the boards
    groups=collections.OrderedDict()
    for n in names: groups.setdefault(re.sub(r'\d+$','',n) if re.match(r'(alu|reg|ctr)\d$',n) else n,[]).append(n)
    L=['| Design | Files | Boards built of each | Five-packs to order | Boards over |','|---|---|---|---|---|']; packs=boards=0
    for g,ns in groups.items():
        cp=COPIES.get(g,1); pk=math.ceil(cp/5)+SPARE_PACKS.get(g,0); packs+=pk*len(ns); boards+=cp*len(ns)
        files=f'`cards/{ns[0]}`' if len(ns)==1 and g!='sequencer' else '`boards/03-sequencer`' if g=='sequencer' else f'`cards/{ns[0]}` to `{ns[-1]}`'
        L.append(f"| {WHAT[g]}{' (245 x 255 mm, four layers)' if g=='sequencer' else ''} | {files}{'' if len(ns)==1 else f', {len(ns)} designs'} | {cp} | {pk}{'' if len(ns)==1 else ' each'} | {pk*5-cp}{'' if len(ns)==1 else ' each'} |")
    L.append(f"| **{len(names)} designs** | | **{boards} boards** | **{packs} five-packs** | |")
    T['boards']=L
    # the parts
    total=collections.Counter()
    for n in names:
        for k,v in per[n].items(): total[k]+=v*COPIES.get(n,1)
    L=['| Part | Need | Buy | Spares rule |','|---|---|---|---|']
    for k in sorted(total,key=key): L.append(f"| {k[0]} | {total[k]} | {RULES[k[1]][1](total[k]) or ''} | {RULES[k[1]][0]} |")
    jump=sum(v for k,v in total.items() if 'Pin header 1x3' in k[0] or 'Pin header 1x2' in k[0])
    L.append(f"| Jumper cap, 2.54 mm (one on every 1x3 and 1x2 pin header) | {jump} | {RULES['conn'][1](jump)} | {RULES['conn'][0]} |")
    L.append(f"| **{sum(total.values())} parts soldered on {boards} boards** | | | |")
    T['parts']=L
    # the pilot
    L=['| Part | '+' | '.join(PILOT)+' | Together |','|---|'+'---|'*(len(PILOT)+1)]; pt=collections.Counter()
    for n in PILOT: pt.update(per[n])
    for k in sorted(pt,key=key): L.append(f"| {k[0]} | "+' | '.join(str(per[n][k] or '') for n in PILOT)+f" | {pt[k]} |")
    L.append(f"| **{sum(pt.values())} parts on one board of each** | "+' | '.join(str(sum(per[n].values())) for n in PILOT)+' | |')
    T['pilot']=L
    return T,per

def put(doc,T):
    for name,L in T.items():
        a,b=f'<!-- bom.py: {name} -->',f'<!-- bom.py: end {name} -->'
        if doc.count(a)!=1 or doc.count(b)!=1: raise SystemExit(f'docs/order-1.md has no pair of markers for "{name}"')
        i,j=doc.index(a)+len(a),doc.index(b); doc=doc[:i]+'\n'+'\n'.join(L)+'\n'+doc[j:]
    return doc

if __name__=='__main__':
    T,per=tables()
    if '--per' in sys.argv:
        names=designs(); keys=sorted({k for n in names for k in per[n]},key=key)
        print('| Part | '+' | '.join(names)+' |'); print('|---|'+'---|'*len(names))
        for k in keys: print(f'| {k[0]} | '+' | '.join(str(per[n][k] or '') for n in names)+' |')
    elif '--write' in sys.argv:
        doc=put(open(DOC).read(),T)      # read and filled before the file is opened for writing (open(DOC,'w') first emptied it, 2026-09-28)
        open(DOC,'w').write(doc); print('docs/order-1.md: the three tables written')
    elif '--check' in sys.argv:
        doc=open(DOC).read(); same=put(doc,T)==doc
        print('docs/order-1.md carries the tables of the boards as they are; the schematics\' count and the boards\' count agree' if same else 'docs/order-1.md is stale: python3 bom.py --write'); sys.exit(0 if same else 1)
    else:
        for name,L in T.items(): print(f'\n{name}\n'); print('\n'.join(L))
