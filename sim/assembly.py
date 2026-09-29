"""The assembly drawing: which part goes where, for the person with the soldering iron.

    python3 assembly.py coupon reg0 hub          (from sim/; plain python3)
    python3 assembly.py sequencer                (the one board that is not a card: boards/03-sequencer, 245 x 255 mm)

The cards print no references and no values (a dense tile has no room), so a register card shows 54 resistor positions that look
alike, seven of which are not 47k. This writes cards/<card>/fab/<card>-assembly.svg from the committed board: the front as the
silkscreen shows it, every pad, and each part that is not the card's commonest resistor or a 2N7000 coloured and labelled with
its value. The commonest resistor value is drawn grey and unlabelled: fit the coloured ones first, then every position left is
that value. A square pad is pad 1: the cathode of a diode or an LED, the plus of an electrolytic, pin 1 of a header.
Switches, buttons and upright diodes carry no label of their own (the silkscreen names the switches, and a label on each of 32
diodes at 2.54 mm hid the diodes): the legend counts them and a note below the board says how they sit.
A part on the back of the board (the bus header, D059) is drawn with a dashed blue outline: its pins are soldered on the front.
A position marked do-not-populate on the board (the sequencer's 948 empty matrix crossings) is drawn as two faint pads and
counted apart: the board prints a circle only where a diode goes.
Positions and angles are the board's own (a pad's place is its footprint's plus its offset turned by the footprint's angle)."""
import sys, os, re, math, collections
HERE=os.path.dirname(os.path.abspath(__file__)); CARDS=os.path.join(HERE,'..','cards')
CARD=dict(size=(100.0,100.0),holes=[(4.0,50.0),(96.0,50.0)],layers=2)
BOARDS={'sequencer':dict(dir=os.path.join(HERE,'..','boards','03-sequencer'),size=(245.0,255.0),holes=[(4.0,20.0),(241.0,20.0),(4.0,251.0),(241.0,251.0)],layers=4)}
def board(name):
    """Where a board's files are and what its outline, mounting holes and layer count must be: a card unless BOARDS says otherwise."""
    return {**CARD,'dir':os.path.join(CARDS,name),**BOARDS.get(name,{})}
S=10                                                  # px per mm
COL={'1k':'#d62728','10k':'#1f77b4','22k':'#ff7f0e','1Meg':'#9467bd','220k':'#2ca02c','100k':'#17becf','4.7k':'#8c564b','3.3k':'#e377c2','100':'#bcbd22'}
MORE=['#7f3c8d','#11a579','#3969ac','#f2b701','#e73f74','#80ba5a','#e68310','#008695']
KIND=[('R_Axial','resistor'),('TO-92','2N7000'),('D_DO-35','diode'),('LED','LED'),('CP_Radial','electrolytic'),('C_Disc','capacitor'),('TestPoint','test loop'),
      ('IDC-Header','box header'),('PinHeader','pin header'),('MountingHole','mounting hole'),('Banana','socket'),('Fuse','fuse'),
      ('SW_DIP','DIP switch'),('SW_PUSH','push button'),('Potentiometer','potentiometer')]
GREY=('2N7000','box header','pin header','mounting hole')     # drawn grey: nothing to tell apart
BARE=('DIP switch','push button')                             # drawn dark, no label: the silkscreen names them

def kind(fp):
    for k,v in KIND:
        if fp.startswith(k): return v
    return 'part'

def parse(path):
    s=open(path).read(); out=[]
    for m in re.finditer(r'^\t\(footprint "([^"]+)"\s*\(layer "([^"]+)"\)\s*\(uuid "[^"]+"\)\s*\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)(.*?)^\t\)$',s,re.M|re.S):
        fp,layer,X,Y,a,b=m.group(1),m.group(2),float(m.group(3)),float(m.group(4)),math.radians(float(m.group(5) or 0)),m.group(6)
        c,sn=math.cos(a),math.sin(a); T=lambda x,y:(X+x*c+y*sn,Y-x*sn+y*c)
        val=re.search(r'\(property "Value" "([^"]*)"',b).group(1); ref=re.search(r'\(property "Reference" "([^"]*)"',b).group(1)
        SILK='F.SilkS' if layer=='F.Cu' else 'B.SilkS'      # a part on the back prints its outline on the back
        pads=[(p.group(1),p.group(2),)+T(float(p.group(3)),float(p.group(4)))+(max(float(p.group(5)),float(p.group(6)))/2,)
              for p in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\s*\(at ([\d.-]+) ([\d.-]+)(?: [\d.-]+)?\)\s*\(size ([\d.]+) ([\d.]+)\)',b)]
        g=[]
        for q in re.finditer(r'\(fp_line\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(6)==SILK and len(q.group(5))<200: g.append(('line',T(float(q.group(1)),float(q.group(2))),T(float(q.group(3)),float(q.group(4)))))
        for q in re.finditer(r'\(fp_rect\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(6)==SILK and len(q.group(5))<200:
                x1,y1,x2,y2=[float(q.group(k)) for k in (1,2,3,4)]; P=[T(x1,y1),T(x2,y1),T(x2,y2),T(x1,y2)]
                g+=[('line',P[k],P[(k+1)%4]) for k in range(4)]
        for q in re.finditer(r'\(fp_circle\s*\(center ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(6)==SILK and len(q.group(5))<200:
                cx,cy,ex,ey=[float(q.group(k)) for k in (1,2,3,4)]; g.append(('circle',T(cx,cy),math.hypot(ex-cx,ey-cy)))
        for q in re.finditer(r'\(fp_arc\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(mid ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(8)==SILK and len(q.group(7))<200: g.append(('arc',)+tuple(T(float(q.group(k)),float(q.group(k+1))) for k in (1,3,5)))
        attr=re.search(r'\(attr ([^)]*)\)',b)
        out.append(dict(fp=fp,kind=kind(fp),ref=ref,val=val,at=(X,Y),pads=pads,g=g,back=layer!='F.Cu',upright='Vertical' in fp,dnp=bool(attr) and 'dnp' in attr.group(1).split()))
    texts=[(t.group(1),float(t.group(2)),float(t.group(3)),float(t.group(4) or 0),float(t.group(5)),'start' if 'left' in (t.group(6) or '') else 'end' if 'right' in (t.group(6) or '') else 'middle') for t in
           re.finditer(r'^\t\(gr_text "([^"]*)"\s*\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)\s*\(layer "F\.SilkS"\).*?\(size ([\d.]+) [\d.]+\).*?\)\s*\)(?:\s*\(justify ([^)]*)\))?',s,re.M|re.S)]
    return out,texts

def arc_path(a,m,e):
    """An SVG arc through three points (start, middle, end)."""
    (x1,y1),(x2,y2),(x3,y3)=a,m,e; d=2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    if abs(d)<1e-9: return f'M{x1*S:.1f} {y1*S:.1f}L{x3*S:.1f} {y3*S:.1f}'
    ux=((x1*x1+y1*y1)*(y2-y3)+(x2*x2+y2*y2)*(y3-y1)+(x3*x3+y3*y3)*(y1-y2))/d; uy=((x1*x1+y1*y1)*(x3-x2)+(x2*x2+y2*y2)*(x1-x3)+(x3*x3+y3*y3)*(x2-x1))/d
    r=math.hypot(x1-ux,y1-uy); cr=(x2-x1)*(y3-y1)-(y2-y1)*(x3-x1)
    a1,a3,a2=[math.atan2(y-uy,x-ux) for x,y in (a,e,m)]; sweep=1 if cr>0 else 0
    span=(a3-a1)%(2*math.pi) if sweep else (a1-a3)%(2*math.pi)
    return f'M{x1*S:.1f} {y1*S:.1f}A{r*S:.1f} {r*S:.1f} 0 {1 if span>math.pi else 0} {sweep} {x3*S:.1f} {y3*S:.1f}'

def draw(name,out=None,d=None):
    B=board(name); d=d or B['dir']; parts,texts=parse(os.path.join(d,f'{name}.kicad_pcb'))
    empty=[p for p in parts if p['dnp']]; parts=[p for p in parts if not p['dnp']]
    rv=collections.Counter(p['val'] for p in parts if p['kind']=='resistor'); common=min(rv,key=lambda v:(-rv[v],v)) if rv else None     # a tie goes to the name, not to the order of the file
    col=dict(COL); spare=list(MORE)
    for v in rv:
        if v!=common and v not in col: col[v]=spare.pop(0) if spare else '#444444'
    kinds={p['kind'] for p in parts}
    notes=['Square pad = pad 1: the cathode of a diode or an LED, the plus of an electrolytic, pin 1 of a header.',
           'Grey and unlabelled: the commonest resistor of the card (see the legend) and the 2N7000, flat side as the outline shows. Resistors stand upright on 5.08 mm.']
    if any(p['kind']=='diode' and p['upright'] for p in parts): notes.append('Upright diodes (black, unlabelled): the body stands on the square pad, band down; the bare lead bends over to the round pad.')
    dips={len(p['pads'])//2 for p in parts if p['kind']=='DIP switch'}
    if dips: notes.append('DIP switches (black pads, named on the silkscreen): a closed switch (ON) is '+('a 1' if max(dips)>1 else 'RUN, an open one STEP')+'. They work either way round: fit each with ON toward the right edge.')
    if any(p['back'] for p in parts): notes.append('Dashed blue outline: the bus header, soldered on the BACK of the board with its notch toward the top edge (D059). Its 64 pins are soldered on this face.')
    if empty: notes.append(f'Faint pads: {len(empty)} positions that stay empty. The board prints a circle only where a part goes.')
    notes.append('Drawn from the committed board by sim/assembly.py; the values are the schematic\'s. Front view, the header along the top edge.')
    W=int(B['size'][0]*S); HB=int(B['size'][1]*S); LEG=400; H=HB+32+26*len(notes)          # the sheet: the board, the legend beside it, the notes below
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W+LEG} {H}" width="{W+LEG}" height="{H}" font-family="Helvetica,Arial,sans-serif">',
       f'<rect width="{W+LEG}" height="{H}" fill="#ffffff"/>',f'<rect x="1" y="1" width="{W-2}" height="{HB-2}" fill="#f7f7f2" stroke="#222" stroke-width="2"/>']
    for p in empty:
        for n,typ,x,y,r in p['pads']: o.append(f'<circle cx="{x*S:.1f}" cy="{y*S:.1f}" r="{r*0.5*S:.1f}" fill="none" stroke="#d8d8d0" stroke-width="1"/>')
    for p in parts:                                   # the silkscreen outlines, as printed; a part on the back dashed
        look='stroke="#5b6fd6" stroke-width="1.6" stroke-dasharray="7 5" fill="none"' if p['back'] else 'stroke="#999" stroke-width="1.2" fill="none"'
        for g in p['g']:
            if g[0]=='line': o.append(f'<path d="M{g[1][0]*S:.1f} {g[1][1]*S:.1f}L{g[2][0]*S:.1f} {g[2][1]*S:.1f}" {look}/>')
            elif g[0]=='circle': o.append(f'<circle cx="{g[1][0]*S:.1f}" cy="{g[1][1]*S:.1f}" r="{g[2]*S:.1f}" {look}/>')
            else: o.append(f'<path d="{arc_path(g[1],g[2],g[3])}" {look}/>')
    for t,x,y,a,sz,anchor in texts: o.append(f'<text x="{x*S:.1f}" y="{y*S:.1f}" font-size="{sz*S*1.3:.0f}" fill="#777" text-anchor="{anchor}" dominant-baseline="middle" transform="rotate({-a:.0f} {x*S:.1f} {y*S:.1f})">{t.replace("&","&amp;").replace("<","&lt;")}</text>')
    labels=[]
    for p in parts:
        k=p['kind']; pads=p['pads']
        if not pads: continue
        c='#bdbdbd' if (k=='resistor' and p['val']==common) or k in GREY else col.get(p['val'],'#111111') if k=='resistor' else {'diode':'#111111','LED':'#d62728','electrolytic':'#1f77b4','capacitor':'#ff7f0e','test loop':'#2ca02c','socket':'#111111','fuse':'#8c564b'}.get(k,'#111111')
        if k in ('resistor','diode','LED','electrolytic','capacitor','fuse') and len(pads)==2:
            o.append(f'<path d="M{pads[0][2]*S:.1f} {pads[0][3]*S:.1f}L{pads[1][2]*S:.1f} {pads[1][3]*S:.1f}" stroke="{c}" stroke-width="{7 if c!="#bdbdbd" else 4}" stroke-linecap="round" fill="none" opacity="0.85"/>')
        for n,typ,x,y,r in pads:
            r=min(r,3.2) if k!='socket' else r; f='#ffffff' if typ!='np_thru_hole' else '#dddddd'
            if n=='1' and k in ('diode','LED','electrolytic','box header','pin header'): o.append(f'<rect x="{(x-r*0.8)*S:.1f}" y="{(y-r*0.8)*S:.1f}" width="{r*1.6*S:.1f}" height="{r*1.6*S:.1f}" fill="{f}" stroke="{c if c!="#bdbdbd" else "#555"}" stroke-width="2"/>')
            else: o.append(f'<circle cx="{x*S:.1f}" cy="{y*S:.1f}" r="{r*0.8*S:.1f}" fill="{f}" stroke="{c if c!="#bdbdbd" else "#888"}" stroke-width="{2 if c!="#bdbdbd" else 1.2}"/>')
        if c!='#bdbdbd' and k not in BARE and not (k=='diode' and p['upright']):
            cx=sum(q[2] for q in pads)/len(pads); cy=sum(q[3] for q in pads)/len(pads)
            horiz=len(pads)<2 or abs(pads[0][2]-pads[-1][2])>=abs(pads[0][3]-pads[-1][3])
            t=p['val'] if k not in ('test loop','socket') else p['val'].replace('TP_','')
            wd=len(t)*1.0+0.4; spots=[(cx,cy-2.3,0),(cx,cy+2.4,0)] if horiz or len(pads)<2 else [(cx+1.9,cy,-90),(cx-1.9,cy,-90)]     # above, else below; beside an upright part (reading upward), right, else left
            def free(x,y,rot):                        # no pad of another part under the label's box
                hw,hh=(wd/2,0.9) if rot==0 else (0.9,wd/2)
                return not any(abs(qx-x)<hw+qr*0.8 and abs(qy-y)<hh+qr*0.8 for q in parts if q is not p for _,_,qx,qy,qr in q['pads'])
            x,y,rot=next((sp for sp in spots if free(*sp)),spots[0]); labels.append((x,y,t,c,rot))
    for x,y,t,c,rot in labels:
        o.append(f'<text x="{x*S:.1f}" y="{y*S:.1f}" font-size="17" font-weight="bold" fill="{c}" text-anchor="middle" dominant-baseline="middle" stroke="#ffffff" stroke-width="3" paint-order="stroke" transform="rotate({rot} {x*S:.1f} {y*S:.1f})">{t.replace("&","&amp;").replace("<","&lt;")}</text>')
    # the legend
    x0=W+18; y=34; BOLD=' font-weight="bold"'; L=lambda t,size=17,fill='#111',bold=False: o.append(f'<text x="{x0}" y="{y}" font-size="{size}" fill="{fill}"{BOLD if bold else ""}>{t}</text>')     # (KiCad's python is 3.9: no backslash inside an f-string's braces)
    L(f'{name}: assembly, front',22,bold=True); y+=30; L('Fit the coloured parts first.',15,'#444'); y+=34
    L('Resistors',18,bold=True); y+=26
    for v,n in sorted(rv.items(),key=lambda kv:(kv[0]==common,-kv[1],kv[0])):
        c='#bdbdbd' if v==common else col[v]
        o.append(f'<path d="M{x0} {y-6}L{x0+34} {y-6}" stroke="{c}" stroke-width="{7 if v!=common else 4}" stroke-linecap="round"/>'); o.append(f'<text x="{x0+46}" y="{y}" font-size="17" fill="#111">{v}  x {n}{"  (every unlabelled one)" if v==common else ""}</text>'); y+=26
    y+=12; L('Other parts',18,bold=True); y+=26
    def what(p):                                      # the legend's name of a part that is not a resistor
        k=p['kind']; m=re.search(r'_(\d)x(\d+)_',p['fp'])
        if k in ('box header','pin header'): return f'{k} {int(m.group(1))}x{int(m.group(2))}'+(', on the back' if p['back'] else '')
        if k=='DIP switch': return f'DIP switch, {len(p["pads"])//2}-way'
        if k=='diode' and p['upright']: return f'diode {p["val"]}, upright'
        return k if k in ('test loop','socket','mounting hole','push button') or p['val']==k else f'{k} {p["val"]}'
    oc=collections.Counter(what(p) for p in parts if p['kind']!='resistor')
    for t,n in sorted(oc.items(),key=lambda kv:(-kv[1],kv[0])): L(f'{t}  x {n}',16); y+=24
    if empty: y+=12; L(f'left empty  x {len(empty)}',16,'#777'); y+=24
    x0=18; y=HB+40
    for t in notes: L(t,16,'#444'); y+=26
    o.append('</svg>'); out=out or os.path.join(d,'fab',f'{name}-assembly.svg'); open(out,'w').write('\n'.join(o)+'\n'); return out,rv,len(parts)

if __name__=='__main__':
    if len(sys.argv)<2: print(__doc__); sys.exit(2)
    for name in sys.argv[1:]:
        out,rv,n=draw(name); print(f'{name}: {n} parts, resistors {dict(rv)} -> {os.path.relpath(out,HERE)}')
