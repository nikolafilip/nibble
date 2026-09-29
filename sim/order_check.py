"""The order gate: what must be true of a card's committed files before its gerbers go to the fab.

    python3 order_check.py coupon reg0 hub          (from sim/; plain python3, kicad-cli only)
    python3 order_check.py --zip coupon             (also write fab/<card>-gerbers.zip from the fab files)
    python3 order_check.py --selftest               (the pins rule against parts made up to break it)
    python3 order_check.py --machine                (what joins the boards: every bus header against bus.py, every link against its far end)

    python3 order_check.py sequencer                (boards/03-sequencer: 245 x 255 mm, four layers, four corner holes; assembly.BOARDS)

Per card, from the files in cards/<card>/ as committed:
  clean    git reports nothing modified under cards/<card>/ (the gerbers are the commit's)
  rules    <card>.kicad_pro carries the design rules of <card>.plan.json (a schematic rebuild used to wipe them, and kicad-cli
           then judged the board by KiCad's 0.2 mm default: 206 false clearance errors on the coupon, 2026-09-28)
  erc      0 violations on the sheet
  drc      0 errors and 0 unconnected on the board under the project's rules; schematic parity: no net conflicts, no missing or
           extra footprints (the footprint-name mismatches are pcb.py writing ids without the library prefix, cosmetic)
  jlc      0 errors under JLCPCB's minimum rules (jlcpcb.kicad_dru: 0.127 track and clearance, 0.5/0.3 via, 0.13 annular, 0.5 hole to hole, 0.3 edge)
  fab      gerbers and drill regenerated from the committed board equal fab/ (creation dates ignored)
  zip      fab/<card>-gerbers.zip holds exactly the nine files the fab needs, byte-identical to fab/
  outline  the edge cuts span exactly 100.00 x 100.00 mm; the drill file has two 3.2 mm mounting holes at (4,50) and (96,50)
           (the sequencer: 245.00 x 255.00 mm and four holes, 4 mm in from the sides at y = 20 and 251)
  pins     every numbered through-hole pad of every part is on a net; each 2N7000 has its gate off the rails, its source on GND, a
           stack or a resistor, its drain on a pull-up, a stack, an LED, the bus header or a rail; no diode, LED or electrolytic
           reversed against the rails (pad 1 is the cathode / the plus, as the KiCad symbols and footprints number them); an
           electrolytic has its minus on GND or its plus on the supply (a timing capacitor sits between a signal and GND)
  silk     no board label is clipped by a pad's mask opening or smaller than 0.8 mm (the note counts the ones under 1.0 mm, the
           height JLCPCB says it prints: pcb.fit_silk grows every label that has the room); the 64-pin bus header is on the back
           of the board (D059) and the front says so
  asm      fab/<card>-assembly.svg, the drawing that says which value goes where (the cards print none), is the committed board's
  clamp    no copper of another net, on either face, within reach of the hardware clamped on the board: 7.5 mm of a banana socket's
           centre (an M6 nut's corners and a 12 mm solder tag reach 6.4 mm over 25 um of mask) and 3.3 mm of a mounting hole's (an M3
           hex standoff's corners reach 3.2 mm, no washers: docs/mounting.md). The DRC sees 0.15 mm of clearance and is content; the
           first hub route had CLK 0.17 mm from the +5V socket's ring, under its nut (2026-09-28)

--machine, over every routed board at once (no card's own checks can see these, and the simulation joins the cards by net name,
so a header wired to the wrong pin would pass every deck):
  bus      on every board, every 2x32 header is on the back and every pad of it carries the signal bus.py gives that pin, or
           nothing; the power pins (+5V 1 2 64, GND 3 4 5 7 63) are all connected; the hub's two headers carry all 64 lines
  links    a link ribbon joins pin n to pin n: each pair of headers that a ribbon joins (ALU carry chain, counter carry chain,
           the sequencer's operand link to the eight counter cards, memory control to the slots) has the same signal on the
           same pin at both ends, or nothing at the end that does not take it
Exit status 1 if any check fails."""
import sys, os, re, json, subprocess, tempfile, zipfile, shutil, collections, math
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
import assembly
HERE=os.path.dirname(os.path.abspath(__file__)); CARDS=os.path.join(HERE,'..','cards'); DRU=os.path.join(HERE,'jlcpcb.kicad_dru')
ZIP_SUFFIXES=['-F_Cu.gtl','-B_Cu.gbl','-F_Mask.gts','-B_Mask.gbs','-F_Silkscreen.gto','-B_Silkscreen.gbo','-Edge_Cuts.gm1','.drl','-job.gbrjob']
INNER=['-In1_Cu.g1','-In2_Cu.g2']                                   # a four-layer board's zip carries these too
HOLE_D=3.2
def suffixes(name): return ZIP_SUFFIXES[:2]+(INNER if assembly.board(name)['layers']==4 else [])+ZIP_SUFFIXES[2:]
CLAMP={'Banana_Jack_1Pin':7.5,'MountingHole_3.2mm_M3_Pad':3.3}     # mm from the centre that the hardware on the board can touch, plus margin

def run(args): return subprocess.run(args,capture_output=True,text=True)
def jload(p): return json.load(open(p))

def write_zip(fab,name):
    """fab/<name>-gerbers.zip: the nine fab files, fixed timestamps so the zip changes only when the gerbers do."""
    path=os.path.join(fab,f'{name}-gerbers.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for suf in suffixes(name):
            fn=f'{name}{suf}'; zi=zipfile.ZipInfo(fn,date_time=(2026,1,1,0,0,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=0o644<<16
            z.writestr(zi,open(os.path.join(fab,fn),'rb').read())
    return path

def strip_dates(text,drill=False):
    return '\n'.join(l for l in text.splitlines() if not (l.startswith('G04') or 'CreationDate' in l or (drill and l.startswith(';'))))

def check_card(name,make_zip=False):
    B=assembly.board(name); d=B['dir']; SUF=suffixes(name); pcb=os.path.join(d,f'{name}.kicad_pcb'); sch=os.path.join(d,f'{name}.kicad_sch'); pro=os.path.join(d,f'{name}.kicad_pro')
    fab=os.path.join(d,'fab'); res=collections.OrderedDict(); note={}
    tmp=tempfile.mkdtemp(prefix=f'order_{name}_')
    # clean
    st=run(['git','-C',d,'status','--porcelain','--untracked-files=all','--','.']).stdout.strip()
    res['clean']=st==''; note['clean']=st.replace('\n','; ')[:80]
    # rules
    plan=jload(os.path.join(d,f'{name}.plan.json')).get('extra',{}).get('rules',{}); pj=jload(pro)
    cls=pj.get('net_settings',{}).get('classes',[{}]); c0=cls[0] if cls else {}
    res['rules']=bool(plan) and c0.get('clearance')==plan.get('clearance') and c0.get('track_width')==plan.get('track')
    note['rules']=f"project {c0.get('clearance')}/{c0.get('track_width')} plan {plan.get('clearance')}/{plan.get('track')}"
    # erc
    ej=os.path.join(tmp,'erc.json'); run([K,'sch','erc','--format','json','--severity-all','-o',ej,sch])
    v=[x for s in jload(ej)['sheets'] for x in s['violations']] if os.path.exists(ej) else None
    res['erc']=v is not None and len(v)==0; note['erc']=f'{len(v)} violations' if v is not None else 'erc did not run'
    # drc + parity
    dj=os.path.join(tmp,'drc.json'); run([K,'pcb','drc','--format','json','--severity-all','--schematic-parity','-o',dj,pcb])
    j=jload(dj); errs=[x for x in j['violations'] if x['severity']=='error']; unc=j['unconnected_items']
    par=[x for x in j['schematic_parity'] if x['type'] not in ('footprint_symbol_mismatch','footprint_symbol_field_mismatch')]
    res['drc']=not errs and not unc and not par
    note['drc']=f"{len(errs)} errors, {len(unc)} unconnected, {len(par)} parity, {sum(1 for x in j['violations'] if x['severity']=='warning')} warnings"
    if errs: note['drc']+=' :: '+'; '.join(sorted({x['description'][:50] for x in errs})[:3])
    if par: note['drc']+=' :: '+'; '.join(sorted({x['type'] for x in par}))
    # jlc
    jd=os.path.join(tmp,'jlc'); os.makedirs(jd); shutil.copy(pcb,jd); shutil.copy(pro,jd); shutil.copy(DRU,os.path.join(jd,f'{name}.kicad_dru'))
    jj=os.path.join(tmp,'jlc.json'); run([K,'pcb','drc','--format','json','--severity-all','-o',jj,os.path.join(jd,f'{name}.kicad_pcb')])
    j2=jload(jj); e2=[x for x in j2['violations'] if x['severity']=='error']
    res['jlc']=not e2 and not j2['unconnected_items']; note['jlc']=f"{len(e2)} errors under jlcpcb.kicad_dru"
    if e2: note['jlc']+=' :: '+'; '.join(sorted({x['description'][:50] for x in e2})[:3])
    # fab: regenerate and compare
    gd=os.path.join(tmp,'fab'); os.makedirs(gd); run([K,'pcb','export','gerbers','-o',gd+'/',pcb]); run([K,'pcb','export','drill','-o',gd+'/',pcb])
    bad=[]
    for suf in SUF:
        fn=f'{name}{suf}'; a=os.path.join(fab,fn); b=os.path.join(gd,fn)
        if not os.path.exists(a) or not os.path.exists(b): bad.append(fn+' missing'); continue
        if strip_dates(open(a).read(),suf=='.drl')!=strip_dates(open(b).read(),suf=='.drl'): bad.append(fn)
    res['fab']=not bad; note['fab']=f'{len(SUF)} files equal the committed board' if not bad else 'stale: '+', '.join(bad)
    # zip
    zp=os.path.join(fab,f'{name}-gerbers.zip')
    if make_zip: write_zip(fab,name)
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as z:
            names=sorted(z.namelist()); want=sorted(f'{name}{s}' for s in SUF)
            same=names==want and all(z.read(n)==open(os.path.join(fab,n),'rb').read() for n in want if os.path.exists(os.path.join(fab,n)))
        res['zip']=same; note['zip']=f'{len(names)} files, identical to fab/' if same else f'zip differs from fab/ ({len(names)} files)'
    else: res['zip']=False; note['zip']='no fab/<card>-gerbers.zip (run with --zip)'
    # outline + holes
    e=open(os.path.join(fab,f'{name}-Edge_Cuts.gm1')).read()
    xs=[int(x)/1e6 for x in re.findall(r'X(-?\d+)Y',e)]; ys=[int(y)/1e6 for y in re.findall(r'Y(-?\d+)D',e)]
    w,h=(max(xs)-min(xs),max(ys)-min(ys)) if xs else (0,0)
    drl=open(os.path.join(fab,f'{name}.drl')).read(); tools=dict(re.findall(r'^(T\d+)C([\d.]+)',drl,re.M)); cur=None; holes=[]
    for line in drl.splitlines():
        m=re.match(r'^(T\d+)$',line)
        if m: cur=m.group(1); continue
        m=re.match(r'^X(-?[\d.]+)Y(-?[\d.]+)',line)
        if m and cur: holes.append((float(tools[cur]),float(m.group(1)),float(m.group(2))))
    mh=[(x,y) for dd,x,y in holes if abs(dd-HOLE_D)<0.01]
    HOLES=B['holes']; okh=len(mh)==len(HOLES) and all(any(abs(x-hx)<0.01 and abs(abs(y)-hy)<0.01 for x,y in mh) for hx,hy in HOLES)     # the drill file has y up: (4,50) is X4Y-50
    res['outline']=abs(w-B['size'][0])<0.005 and abs(h-B['size'][1])<0.005 and okh
    note['outline']=f'{w:.2f} x {h:.2f} mm, {len(holes)} holes, {len(mh)} of {HOLE_D} mm'
    # pins
    bad=pin_rules(pcb); res['pins']=not bad; note['pins']='all parts on nets, polarity rules pass' if not bad else '; '.join(f'{r} {w}' for r,w,_ in bad[:4])
    # silk
    sp=open(pcb).read(); sizes=[float(x) for x in re.findall(r'^\t\(gr_text "[^"]*"\s*\(at [^)]*\)\s*\(layer "[FB]\.SilkS"\).*?\(size ([\d.]+) [\d.]+\)',sp,re.M|re.S)]
    clipped=[x for x in j['violations'] if x['type']=='silk_over_copper' and any('PCB text' in i['description'] for i in x['items'])]
    front=re.findall(r'\(footprint "IDC-Header_2x32[^"]*"\s*\(layer "F\.Cu"\)',sp); said='"HEADER ON THE BACK"' in sp
    res['silk']=bool(sizes) and min(sizes)>=0.8 and not clipped and not front and said
    note['silk']=(f'{len(sizes)} labels, {sum(1 for x in sizes if x<1.0)} under 1.0 mm, none clipped; the bus header is on the back' if res['silk'] else
                  '; '.join(([f'{len(clipped)} labels clipped by a pad'] if clipped else [])+([f'a label of {min(sizes)} mm'] if sizes and min(sizes)<0.8 else [])+(['the bus header is on the front'] if front else [])+(['the front does not say where the header goes'] if not said else [])))
    # asm
    ap=os.path.join(fab,f'{name}-assembly.svg'); at=os.path.join(tmp,'asm.svg'); assembly.draw(name,out=at,d=d)
    res['asm']=os.path.exists(ap) and open(ap).read()==open(at).read(); note['asm']='the drawing is the board\'s' if res['asm'] else 'missing or stale (python3 assembly.py <card>)'
    # clamp
    bad,nclamp=clamp_rules(pcb); res['clamp']=not bad and nclamp>0
    note['clamp']=f'{nclamp} clamp sites, nothing of another net in reach' if not bad else '; '.join(f'{r}: {w}' for r,w in bad[:4])
    shutil.rmtree(tmp,ignore_errors=True)
    return res,note

def parse_pcb(path):
    s=open(path).read(); fps=[]
    for m in re.finditer(r'^\t\(footprint "([^"]+)"(.*?)^\t\)$',s,re.S|re.M):
        b=m.group(2); ref=re.search(r'\(property "Reference" "([^"]+)"',b); pads={}
        for p in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)(.*?)\n\t\t\)',b,re.S):
            net=re.search(r'\(net (?:\d+ )?"([^"]*)"\)',p.group(4)); pads[p.group(1)]=(p.group(2),net.group(1) if net else None)
        fps.append((m.group(1),ref.group(1) if ref else '?',pads))
    return fps

def pin_rules(pcb):
    fps=parse_pcb(pcb) if isinstance(pcb,str) else pcb; RAIL={'GND','+5V','VBUS'}; bad=[]
    q_s=set(); q_d=set(); r_nets=set(); led_nets=set(); hdr_nets=set()
    for fp,ref,P in fps:
        if fp.startswith('TO-92'): q_s.add(P['1'][1]); q_d.add(P['3'][1])
        if fp.startswith('R_Axial'): r_nets|={P['1'][1],P['2'][1]}
        if fp.startswith('LED'): led_nets|={P['1'][1],P['2'][1]}
        if fp.startswith('IDC-Header') or fp.startswith('PinHeader'): hdr_nets|={v[1] for v in P.values()}
    for fp,ref,P in fps:
        if fp.startswith('TO-92'):
            s,g,d=P['1'][1],P['2'][1],P['3'][1]
            if g in RAIL: bad.append((ref,'gate on a rail',g))
            if s in ('+5V','VBUS') or not (s=='GND' or s in q_d or s in r_nets): bad.append((ref,'source not GND/stack/resistor',s))
            if d=='GND' or not (d in r_nets or d in q_s or d in led_nets or d in hdr_nets or d in RAIL): bad.append((ref,'drain on nothing that pulls up',d))
        elif fp.startswith('D_DO-35') or fp.startswith('LED'):
            k,a=P['1'][1],P['2'][1]
            if k in ('+5V','VBUS') or a=='GND': bad.append((ref,'reversed against the rails',(k,a)))
        elif fp.startswith('CP_Radial'):
            p,m=P['1'][1],P['2'][1]          # a timing capacitor has its plus on a signal and its minus on GND; between two signals nothing here says which way round, so that fails until someone looks
            if p=='GND' or m in ('+5V','VBUS') or not (m=='GND' or p in ('+5V','VBUS')): bad.append((ref,'electrolytic polarity',(p,m)))
        if not fp.startswith('MountingHole'):
            for pn,(typ,net) in P.items():   # a pad without a number is a part's mounting lug (the potentiometer's), on no net by design
                if pn and typ=='thru_hole' and (net is None or net==''): bad.append((ref,f'pad {pn} on no net',None))
    return bad

def selftest():
    """The pins rule on boards made up to break it: each line is a part, its pads' nets, and whether the rule must object."""
    T=lambda *nets:{str(i+1):('thru_hole',n) for i,n in enumerate(nets)}
    base=[('R_Axial_DIN0207','R1',T('+5V','Y')),('TO-92_Inline','Q1',T('GND','A','Y'))]
    cases=[('CP_Radial_D5.0mm','C2',T('+5V','GND'),False),('CP_Radial_D5.0mm','C4',T('POR','GND'),False),('CP_Radial_D5.0mm','C5',T('+5V','POR'),False),
           ('CP_Radial_D5.0mm','C6',T('GND','POR'),True),('CP_Radial_D5.0mm','C7',T('GND','+5V'),True),('CP_Radial_D5.0mm','C8',T('POR','+5V'),True),
           ('CP_Radial_D5.0mm','C9',T('POR','Y'),True),
           ('Potentiometer_Alpha','RV1',{'':('thru_hole',None),'1':('thru_hole','Y'),'2':('thru_hole','A'),'3':('thru_hole','A')},False),
           ('Potentiometer_Alpha','RV2',{'':('thru_hole',None),'1':('thru_hole','Y'),'2':('thru_hole',None),'3':('thru_hole','A')},True),
           ('D_DO-35_SOD27','D1',T('+5V','Y'),True),('D_DO-35_SOD27','D2',T('Y','GND'),True),('D_DO-35_SOD27','D3',T('Y','A'),False),
           ('LED_D5.0mm','D4',T('GND','Y'),False),('TO-92_Inline','Q2',T('GND','+5V','Y'),True),('TO-92_Inline','Q3',T('+5V','A','Y'),True),
           ('TO-92_Inline','Q4',T('GND','A','GND'),True),('TO-92_Inline','Q5',T('Y','A','Z'),True)]
    wrong=[(ref,want) for fp,ref,P,want in cases if bool([b for b in pin_rules(base+[(fp,ref,P)]) if b[0]==ref])!=want]
    print(f'pins selftest: {len(cases)-len(wrong)} of {len(cases)} cases as expected'+''.join(f'\n  {r}: the rule {"kept quiet" if w else "objected"}' for r,w in wrong))
    # the machine rules on the real boards with one thing broken at a time: each must be caught, and on its own board
    import copy; H0={n:headers(n) for n in BOARDS}; ok=not machine_rules(copy.deepcopy(H0))[0]; mw=[] if ok else ['the boards as they are']
    def broken(board,val,f,what):
        H=copy.deepcopy(H0); f(H[board][val][2]); b=machine_rules(H)[0]
        if not b or any(n not in (board,what) for n,_ in b): mw.append(f'{board} {val}: {b[:2]}')
    def swap(i,j): return lambda P:P.update({i:P[j],j:P[i]})
    broken('reg0','BUS',swap(5,6),'reg0')                                     # CLK and its ground changed places (what a header on the wrong face does)
    H=copy.deepcopy(H0); H['alu2']['BUS']=(H['alu2']['BUS'][0],'F.Cu',H['alu2']['BUS'][2])
    if [n for n,_ in machine_rules(H)[0]]!=['alu2']: mw.append('alu2: a header on the front')
    broken('ctr3','BUS',lambda P:P.update({64:None}),'ctr3')                  # a ground pin left open
    broken('hub','BUS J4',lambda P:P.update({33:None}),'hub')                # the hub's second header drops a line
    broken('alu1','IN',swap(1,3),'alu0')                                      # the carry and the zero chain crossed in a link
    broken('ctr5','LINK',swap(6,7),'sequencer')                               # a counter card taking its neighbour's operand bit
    print(f'machine selftest: {6-len(mw) if ok else 0} of 6 faults caught'+''.join(f'\n  not as expected: {m}' for m in mw))
    return not wrong and not mw

BOARDS=['alu0','alu1','alu2','alu3','clock','coupon','ctr0','ctr1','ctr2','ctr3','ctr4','ctr5','ctr6','ctr7','hub','memctl','memslot',
        'panela','panelb','panelc','prog','reg0','reg1','reg2','reg3','sequencer']
LINKS=([(f'alu{i}','OUT',f'alu{i+1}','IN') for i in range(3)]+[(f'ctr{i}','OUT',f'ctr{i+1}','IN') for i in range(7)]
       +[('sequencer','LINK',f'ctr{i}','LINK') for i in range(8)]+[('memctl','LINK','memslot','LINK')])

def headers(name):
    """A board's connectors: {value: (footprint, layer, {pad number: net or None})}; a net KiCad named unconnected-... is None."""
    B=assembly.board(name); s=open(os.path.join(B['dir'],f'{name}.kicad_pcb')).read(); out={}
    for m in re.finditer(r'^\t\(footprint "((?:IDC-Header|PinHeader)[^"]*)"\s*\(layer "([^"]+)"\)(.*?)^\t\)$',s,re.S|re.M):
        b=m.group(3); val=re.search(r'\(property "Value" "([^"]*)"',b).group(1); ref=re.search(r'\(property "Reference" "([^"]*)"',b).group(1); pads={}
        for p in re.finditer(r'\(pad "(\d+)" \w+ \w+(.*?)\n\t\t\)',b,re.S):
            net=re.search(r'\(net (?:\d+ )?"([^"]*)"\)',p.group(2)); net=net.group(1) if net else None
            pads[int(p.group(1))]=None if not net or net.startswith('unconnected-') else net
        out[val if val not in out else f'{val} {ref}']=(m.group(1),m.group(2),pads)
    return out

def machine_rules(H=None):
    import bus
    bad=[]; nb=nl=0; H=H or {n:headers(n) for n in BOARDS}
    for n in BOARDS:
        hs=[(v,h) for v,h in H[n].items() if h[0].startswith('IDC-Header_2x32')]
        if not hs: bad.append((n,'no bus header'))
        for v,(fp,layer,pads) in hs:
            nb+=1
            if layer!='B.Cu': bad.append((n,f'{v}: the header is on {layer}, not on the back (D059)'))
            for pin,sig in bus.PINS.items():
                got=pads.get(pin)
                if got is None and (sig in ('+5V','GND') or n=='hub'): bad.append((n,f'{v} pin {pin}: {sig} not connected'))
                elif got is not None and got!=sig: bad.append((n,f'{v} pin {pin}: {got}, bus.py says {sig}'))
    for a,va,b,vb in LINKS:
        nl+=1; A=H[a].get(va); Bh=H[b].get(vb)
        if not A or not Bh: bad.append((a,f'link {va} to {b} {vb}: header missing')); continue
        if A[0]!=Bh[0]: bad.append((a,f'link {va} to {b} {vb}: {A[0]} against {Bh[0]}'))
        if not any(A[2][k] and A[2][k]==Bh[2].get(k) and A[2][k]!='GND' for k in A[2]): bad.append((a,f'link {va} to {b} {vb}: no signal in common'))
        for k in sorted(A[2]):
            x,y=A[2][k],Bh[2].get(k)
            if x and y and x!=y: bad.append((a,f'link {va} pin {k} {x} meets {b} {vb} pin {k} {y}'))
            if (x=='GND')!=(y=='GND') and (x or y) and 'GND' in (x,y) and (x and y): bad.append((a,f'link {va} pin {k}: ground against a signal'))
    return bad,nb,nl

def parse_copper(path):
    """The board's copper with positions: footprints (name, ref, centre, [pads: (x,y,radius,net)]), tracks, vias. A pad's position is
    its footprint's plus its local offset turned by the footprint's angle (KiCad: x' = x cos a + y sin a, y' = -x sin a + y cos a with
    y down); a pad's radius is half its larger side, so a rectangle is covered whole."""
    s=open(path).read(); fps=[]
    for m in re.finditer(r'^\t\(footprint "([^"]+)"\s*\(layer "[^"]+"\)\s*\(uuid "[^"]+"\)\s*\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)(.*?)^\t\)$',s,re.M|re.S):
        X,Y,ang,b=float(m.group(2)),float(m.group(3)),float(m.group(4) or 0),m.group(5); c,sn=math.cos(math.radians(ang)),math.sin(math.radians(ang))
        ref=re.search(r'\(property "Reference" "([^"]+)"',b); pads=[]
        for p in re.finditer(r'\(pad "[^"]*" (?:thru_hole|smd|np_thru_hole) \w+\s*\(at ([\d.-]+) ([\d.-]+)(?: [\d.-]+)?\)\s*\(size ([\d.]+) ([\d.]+)\)(.*?)\n\t\t\)',b,re.S):
            px,py=float(p.group(1)),float(p.group(2)); net=re.search(r'\(net (?:\d+ )?"([^"]*)"\)',p.group(5))
            pads.append((X+px*c+py*sn,Y-px*sn+py*c,max(float(p.group(3)),float(p.group(4)))/2,net.group(1) if net else None))
        fps.append((m.group(1),ref.group(1) if ref else '?',(X,Y),pads))
    tracks=[(float(a),float(b),float(c2),float(d),float(w),l,n) for a,b,c2,d,w,l,n in re.findall(r'\(segment\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)\s*\(width ([\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net (?:\d+ )?"([^"]+)"\)',s)]
    vias=[(float(x),float(y),float(sz),n) for x,y,sz,n in re.findall(r'\(via\s*\(at ([\d.-]+) ([\d.-]+)\)\s*\(size ([\d.]+)\).*?\(net (?:\d+ )?"([^"]+)"\)',s,re.S)]
    return fps,tracks,vias

def clamp_rules(pcb):
    """Copper of another net within CLAMP reach of a socket's or a mounting hole's centre, on any layer (the pour is GND at 0.3 mm from a
    pad: outside a mounting hole's reach and, on the hub, absent)."""
    fps,tracks,vias=parse_copper(pcb); bad=[]; n=0
    def dseg(px,py,x1,y1,x2,y2):
        dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy; t=0 if L2==0 else max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L2))
        return math.hypot(px-x1-t*dx,py-y1-t*dy)
    for name,ref,(cx,cy),pads in fps:
        if name not in CLAMP: continue
        R=CLAMP[name]; own=pads[0][3] if pads else None; n+=1
        for x1,y1,x2,y2,w,l,net in tracks:
            if l not in ('F.Cu','B.Cu'): continue      # the hardware touches the two faces only
            d=dseg(cx,cy,x1,y1,x2,y2)-w/2
            if d<R and net!=own: bad.append((ref,f'track {net} on {l} {d:.2f} mm from the centre'))
        for x,y,sz,net in vias:
            d=math.hypot(x-cx,y-cy)-sz/2
            if d<R and net!=own: bad.append((ref,f'via {net} {d:.2f} mm from the centre'))
        for name2,ref2,_,pads2 in fps:
            if ref2==ref: continue
            for x,y,r,net in pads2:
                d=math.hypot(x-cx,y-cy)-r
                if d<R and net!=own: bad.append((ref,f'pad of {ref2} ({net}) {d:.2f} mm from the centre'))
    return bad,n

if __name__=='__main__':
    if '--selftest' in sys.argv: sys.exit(0 if selftest() else 1)
    if '--machine' in sys.argv:
        bad,nb,nl=machine_rules()
        for n,w in bad: print(f'   FAIL  {n}: {w}')
        print(f'MACHINE: {nb} bus headers on {len(BOARDS)} boards, {nl} links: '+('all pass' if not bad else f'{len(bad)} FAILED')); sys.exit(1 if bad else 0)
    args=[a for a in sys.argv[1:] if not a.startswith('--')]; make_zip='--zip' in sys.argv
    if not args: print(__doc__); sys.exit(2)
    allok=True; rows=[]
    for name in args:
        res,note=check_card(name,make_zip)
        print(f'== {name}')
        for k,ok in res.items(): print(f'   {"pass" if ok else "FAIL"}  {k:8s} {note[k]}'); allok&=ok
    print('ORDER GATE:','all pass' if allok else 'FAILED'); sys.exit(0 if allok else 1)
