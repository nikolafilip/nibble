"""The assembly drawing: which part goes where, for the person with the soldering iron.

    python3 assembly.py coupon reg0 hub          (from sim/; plain python3)

The cards print no references and no values (a dense tile has no room), so a register card shows 54 resistor positions that look
alike, seven of which are not 47k. This writes cards/<card>/fab/<card>-assembly.svg from the committed board: the front as the
silkscreen shows it, every pad, and each part that is not the card's commonest resistor or a 2N7000 coloured and labelled with
its value. The commonest resistor value is drawn grey and unlabelled: fit the coloured ones first, then every position left is
that value. A square pad is pad 1: the cathode of a diode or an LED, the plus of an electrolytic, pin 1 of a header.
Positions and angles are the board's own (a pad's place is its footprint's plus its offset turned by the footprint's angle)."""
import sys, os, re, math, collections
HERE=os.path.dirname(os.path.abspath(__file__)); CARDS=os.path.join(HERE,'..','cards')
S=10                                                  # px per mm
COL={'1k':'#d62728','10k':'#1f77b4','22k':'#ff7f0e','1Meg':'#9467bd','220k':'#2ca02c','100k':'#17becf','4.7k':'#8c564b','3.3k':'#e377c2','100':'#bcbd22'}
MORE=['#7f3c8d','#11a579','#3969ac','#f2b701','#e73f74','#80ba5a','#e68310','#008695']
KIND=[('R_Axial','resistor'),('TO-92','2N7000'),('D_DO-35','diode'),('LED','LED'),('CP_Radial','electrolytic'),('C_Disc','capacitor'),('TestPoint','test loop'),
      ('IDC-Header','header'),('PinHeader','header'),('MountingHole','hole'),('Banana','socket'),('Fuse','fuse')]

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
        pads=[(p.group(1),p.group(2),)+T(float(p.group(3)),float(p.group(4)))+(max(float(p.group(5)),float(p.group(6)))/2,)
              for p in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\s*\(at ([\d.-]+) ([\d.-]+)(?: [\d.-]+)?\)\s*\(size ([\d.]+) ([\d.]+)\)',b)]
        g=[]
        for q in re.finditer(r'\(fp_line\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(6)=='F.SilkS' and len(q.group(5))<200: g.append(('line',T(float(q.group(1)),float(q.group(2))),T(float(q.group(3)),float(q.group(4)))))
        for q in re.finditer(r'\(fp_rect\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(6)=='F.SilkS' and len(q.group(5))<200:
                x1,y1,x2,y2=[float(q.group(k)) for k in (1,2,3,4)]; P=[T(x1,y1),T(x2,y1),T(x2,y2),T(x1,y2)]
                g+=[('line',P[k],P[(k+1)%4]) for k in range(4)]
        for q in re.finditer(r'\(fp_circle\s*\(center ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(6)=='F.SilkS' and len(q.group(5))<200:
                cx,cy,ex,ey=[float(q.group(k)) for k in (1,2,3,4)]; g.append(('circle',T(cx,cy),math.hypot(ex-cx,ey-cy)))
        for q in re.finditer(r'\(fp_arc\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(mid ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)(.*?)\(layer "([^"]+)"\)',b,re.S):
            if q.group(8)=='F.SilkS' and len(q.group(7))<200: g.append(('arc',)+tuple(T(float(q.group(k)),float(q.group(k+1))) for k in (1,3,5)))
        out.append(dict(fp=fp,kind=kind(fp),ref=ref,val=val,at=(X,Y),pads=pads,g=g,back=layer!='F.Cu'))
    texts=[(t.group(1),float(t.group(2)),float(t.group(3)),float(t.group(4) or 0),float(t.group(5))) for t in
           re.finditer(r'^\t\(gr_text "([^"]*)"\s*\(at ([\d.-]+) ([\d.-]+)(?: ([\d.-]+))?\)\s*\(layer "F\.SilkS"\).*?\(size ([\d.]+) [\d.]+\)',s,re.M|re.S)]
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
    d=d or os.path.join(CARDS,name); parts,texts=parse(os.path.join(d,f'{name}.kicad_pcb'))
    rv=collections.Counter(p['val'] for p in parts if p['kind']=='resistor'); common=rv.most_common(1)[0][0] if rv else None
    col=dict(COL); spare=list(MORE)
    for v in rv:
        if v!=common and v not in col: col[v]=spare.pop(0) if spare else '#444444'
    W=100*S; LEG=400; H=W+110                       # the sheet: the board, the legend beside it, three lines of notes below
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W+LEG} {H}" width="{W+LEG}" height="{H}" font-family="Helvetica,Arial,sans-serif">',
       f'<rect width="{W+LEG}" height="{H}" fill="#ffffff"/>',f'<rect x="1" y="1" width="{W-2}" height="{100*S-2}" fill="#f7f7f2" stroke="#222" stroke-width="2"/>']
    for p in parts:                                   # the silkscreen outlines, as printed
        for g in p['g']:
            if g[0]=='line': o.append(f'<path d="M{g[1][0]*S:.1f} {g[1][1]*S:.1f}L{g[2][0]*S:.1f} {g[2][1]*S:.1f}" stroke="#999" stroke-width="1.2" fill="none"/>')
            elif g[0]=='circle': o.append(f'<circle cx="{g[1][0]*S:.1f}" cy="{g[1][1]*S:.1f}" r="{g[2]*S:.1f}" stroke="#999" stroke-width="1.2" fill="none"/>')
            else: o.append(f'<path d="{arc_path(g[1],g[2],g[3])}" stroke="#999" stroke-width="1.2" fill="none"/>')
    for t,x,y,a,sz in texts: o.append(f'<text x="{x*S:.1f}" y="{y*S:.1f}" font-size="{sz*S*1.3:.0f}" fill="#777" dominant-baseline="middle" transform="rotate({-a:.0f} {x*S:.1f} {y*S:.1f})">{t.replace("&","&amp;").replace("<","&lt;")}</text>')
    labels=[]
    for p in parts:
        k=p['kind']; pads=p['pads']
        if not pads: continue
        c='#bdbdbd' if (k=='resistor' and p['val']==common) or k in ('2N7000','header','hole') else col.get(p['val'],'#111111') if k=='resistor' else {'diode':'#111111','LED':'#d62728','electrolytic':'#1f77b4','capacitor':'#ff7f0e','test loop':'#2ca02c','socket':'#111111','fuse':'#8c564b'}.get(k,'#111111')
        if k in ('resistor','diode','LED','electrolytic','capacitor','fuse') and len(pads)==2:
            o.append(f'<path d="M{pads[0][2]*S:.1f} {pads[0][3]*S:.1f}L{pads[1][2]*S:.1f} {pads[1][3]*S:.1f}" stroke="{c}" stroke-width="{7 if c!="#bdbdbd" else 4}" stroke-linecap="round" fill="none" opacity="0.85"/>')
        for n,typ,x,y,r in pads:
            r=min(r,3.2) if k!='socket' else r; f='#ffffff' if typ!='np_thru_hole' else '#dddddd'
            if n=='1' and k in ('diode','LED','electrolytic','header'): o.append(f'<rect x="{(x-r*0.8)*S:.1f}" y="{(y-r*0.8)*S:.1f}" width="{r*1.6*S:.1f}" height="{r*1.6*S:.1f}" fill="{f}" stroke="{c if c!="#bdbdbd" else "#555"}" stroke-width="2"/>')
            else: o.append(f'<circle cx="{x*S:.1f}" cy="{y*S:.1f}" r="{r*0.8*S:.1f}" fill="{f}" stroke="{c if c!="#bdbdbd" else "#888"}" stroke-width="{2 if c!="#bdbdbd" else 1.2}"/>')
        if c!='#bdbdbd':
            cx=sum(q[2] for q in pads)/len(pads); cy=sum(q[3] for q in pads)/len(pads)
            horiz=len(pads)<2 or abs(pads[0][2]-pads[-1][2])>=abs(pads[0][3]-pads[-1][3])
            t=p['val'] if k not in ('test loop','socket') else p['val'].replace('TP_','')
            labels.append((cx,cy-2.3,t,c,0) if horiz or len(pads)<2 else (cx+1.9,cy,t,c,-90))     # beside an upright part, reading upward
    for x,y,t,c,rot in labels:
        o.append(f'<text x="{x*S:.1f}" y="{y*S:.1f}" font-size="17" font-weight="bold" fill="{c}" text-anchor="middle" dominant-baseline="middle" stroke="#ffffff" stroke-width="3" paint-order="stroke" transform="rotate({rot} {x*S:.1f} {y*S:.1f})">{t.replace("&","&amp;").replace("<","&lt;")}</text>')
    # the legend
    x0=W+18; y=34; L=lambda t,size=17,fill='#111',bold=False: o.append(f'<text x="{x0}" y="{y}" font-size="{size}" fill="{fill}"{" font-weight=\"bold\"" if bold else ""}>{t}</text>')
    L(f'{name}: assembly, front',22,bold=True); y+=30; L('Fit the coloured parts first.',15,'#444'); y+=34
    L('Resistors',18,bold=True); y+=26
    for v,n in sorted(rv.items(),key=lambda kv:(kv[0]==common,-kv[1])):
        c='#bdbdbd' if v==common else col[v]
        o.append(f'<path d="M{x0} {y-6}L{x0+34} {y-6}" stroke="{c}" stroke-width="{7 if v!=common else 4}" stroke-linecap="round"/>'); o.append(f'<text x="{x0+46}" y="{y}" font-size="17" fill="#111">{v}  x {n}{"  (every unlabelled one)" if v==common else ""}</text>'); y+=26
    y+=12; L('Other parts',18,bold=True); y+=26
    oc=collections.Counter((p['kind'],p['val'] if p['kind'] not in ('test loop','socket','header','hole') else '') for p in parts if p['kind']!='resistor')
    for (k,v),n in sorted(oc.items(),key=lambda kv:-kv[1]): L(f'{k}{" "+v if v and v!=k else ""}  x {n}',16); y+=24
    x0=18; y=W+40
    for t in ('Square pad = pad 1: the cathode of a diode or an LED, the plus of an electrolytic, pin 1 of a header.',
              'Grey and unlabelled: the commonest resistor of the card (see the legend) and the 2N7000, flat side as the outline shows. Resistors stand upright on 5.08 mm.',
              'Drawn from the committed board by sim/assembly.py; the values are the schematic\'s. Front view, the header along the top edge.'): L(t,16,'#444'); y+=26
    o.append('</svg>'); out=out or os.path.join(d,'fab',f'{name}-assembly.svg'); open(out,'w').write('\n'.join(o)+'\n'); return out,rv,len(parts)

if __name__=='__main__':
    if len(sys.argv)<2: print(__doc__); sys.exit(2)
    for name in sys.argv[1:]:
        out,rv,n=draw(name); print(f'{name}: {n} parts, resistors {dict(rv)} -> {os.path.relpath(out,HERE)}')
