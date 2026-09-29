"""The order gate: what must be true of a card's committed files before its gerbers go to the fab.

    python3 order_check.py coupon reg0 hub          (from sim/; plain python3, kicad-cli only)
    python3 order_check.py --zip coupon             (also write fab/<card>-gerbers.zip from the fab files)

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
  pins     every through-hole pad of every part is on a net; each 2N7000 has its gate off the rails, its source on GND, a stack
           or a resistor, its drain on a pull-up, a stack, an LED, the bus header or a rail; no diode, LED or electrolytic
           reversed against the rails (pad 1 is the cathode / the plus, as the KiCad symbols and footprints number them)
  asm      fab/<card>-assembly.svg, the drawing that says which value goes where (the cards print none), is the committed board's
  clamp    no copper of another net, on either face, within reach of the hardware clamped on the board: 7.5 mm of a banana socket's
           centre (an M6 nut's corners and a 12 mm solder tag reach 6.4 mm over 25 um of mask) and 3.3 mm of a mounting hole's (an M3
           hex standoff's corners reach 3.2 mm, no washers: docs/mounting.md). The DRC sees 0.15 mm of clearance and is content; the
           first hub route had CLK 0.17 mm from the +5V socket's ring, under its nut (2026-09-28)
Exit status 1 if any check fails."""
import sys, os, re, json, subprocess, tempfile, zipfile, shutil, collections, math
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
HERE=os.path.dirname(os.path.abspath(__file__)); CARDS=os.path.join(HERE,'..','cards'); DRU=os.path.join(HERE,'jlcpcb.kicad_dru')
ZIP_SUFFIXES=['-F_Cu.gtl','-B_Cu.gbl','-F_Mask.gts','-B_Mask.gbs','-F_Silkscreen.gto','-B_Silkscreen.gbo','-Edge_Cuts.gm1','.drl','-job.gbrjob']
CARD=100.0; HOLES=[(4.0,50.0),(96.0,50.0)]; HOLE_D=3.2
CLAMP={'Banana_Jack_1Pin':7.5,'MountingHole_3.2mm_M3_Pad':3.3}     # mm from the centre that the hardware on the board can touch, plus margin

def run(args): return subprocess.run(args,capture_output=True,text=True)
def jload(p): return json.load(open(p))

def write_zip(fab,name):
    """fab/<name>-gerbers.zip: the nine fab files, fixed timestamps so the zip changes only when the gerbers do."""
    path=os.path.join(fab,f'{name}-gerbers.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for suf in ZIP_SUFFIXES:
            fn=f'{name}{suf}'; zi=zipfile.ZipInfo(fn,date_time=(2026,1,1,0,0,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=0o644<<16
            z.writestr(zi,open(os.path.join(fab,fn),'rb').read())
    return path

def strip_dates(text,drill=False):
    return '\n'.join(l for l in text.splitlines() if not (l.startswith('G04') or 'CreationDate' in l or (drill and l.startswith(';'))))

def check_card(name,make_zip=False):
    d=os.path.join(CARDS,name); pcb=os.path.join(d,f'{name}.kicad_pcb'); sch=os.path.join(d,f'{name}.kicad_sch'); pro=os.path.join(d,f'{name}.kicad_pro')
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
    for suf in ZIP_SUFFIXES:
        fn=f'{name}{suf}'; a=os.path.join(fab,fn); b=os.path.join(gd,fn)
        if not os.path.exists(a) or not os.path.exists(b): bad.append(fn+' missing'); continue
        if strip_dates(open(a).read(),suf=='.drl')!=strip_dates(open(b).read(),suf=='.drl'): bad.append(fn)
    res['fab']=not bad; note['fab']='nine files equal the committed board' if not bad else 'stale: '+', '.join(bad)
    # zip
    zp=os.path.join(fab,f'{name}-gerbers.zip')
    if make_zip: write_zip(fab,name)
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as z:
            names=sorted(z.namelist()); want=sorted(f'{name}{s}' for s in ZIP_SUFFIXES)
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
    okh=len(mh)==len(HOLES) and all(any(abs(x-hx)<0.01 and abs(abs(y)-hy)<0.01 for x,y in mh) for hx,hy in HOLES)     # the drill file has y up: (4,50) is X4Y-50
    res['outline']=abs(w-CARD)<0.005 and abs(h-CARD)<0.005 and okh
    note['outline']=f'{w:.2f} x {h:.2f} mm, {len(holes)} holes, {len(mh)} of {HOLE_D} mm'
    # pins
    bad=pin_rules(pcb); res['pins']=not bad; note['pins']='all parts on nets, polarity rules pass' if not bad else '; '.join(f'{r} {w}' for r,w,_ in bad[:4])
    # asm
    import assembly; ap=os.path.join(fab,f'{name}-assembly.svg'); at=os.path.join(tmp,'asm.svg'); assembly.draw(name,out=at,d=d)
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
    fps=parse_pcb(pcb); RAIL={'GND','+5V','VBUS'}; bad=[]
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
            if P['1'][1] not in ('+5V','VBUS') or P['2'][1]!='GND': bad.append((ref,'electrolytic polarity',(P['1'][1],P['2'][1])))
        if not fp.startswith('MountingHole'):
            for pn,(typ,net) in P.items():
                if typ=='thru_hole' and (net is None or net==''): bad.append((ref,f'pad {pn} on no net',None))
    return bad

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
    args=[a for a in sys.argv[1:] if not a.startswith('--')]; make_zip='--zip' in sys.argv
    if not args: print(__doc__); sys.exit(2)
    allok=True; rows=[]
    for name in args:
        res,note=check_card(name,make_zip)
        print(f'== {name}')
        for k,ok in res.items(): print(f'   {"pass" if ok else "FAIL"}  {k:8s} {note[k]}'); allok&=ok
    print('ORDER GATE:','all pass' if allok else 'FAILED'); sys.exit(0 if allok else 1)
