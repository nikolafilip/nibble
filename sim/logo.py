"""The Nibble logo as silkscreen: lib/logo/nibble.png traced into two footprints of filled polygons on F.SilkS,
lib/nibble.pretty/Logo_Nibble_Icon.kicad_mod (the square icon alone) and Logo_Nibble.kicad_mod (icon and word).

    python3 logo.py            (from sim/; plain python3 with Pillow and numpy; the tracer is potracer, a pure-python
                                potrace: pip install --target <dir> potracer, and that dir on PYTHONPATH)

The icon is HEIGHT mm tall (8: its ribbon's lines then print 0.39 mm wide with 0.24 mm gaps, over the fab's 0.15 mm
minimum for silkscreen; the word is as tall). Each traced contour is flattened to a polygon; a hole is joined to the
polygon around it by a slit of no width, the way KiCad's own image converter does it, since a filled polygon in a
footprint has no holes of its own. The footprint's origin is the middle of its ink. pcb.py puts one of these on every
board (see place_logo there)."""
import os, sys, math
import numpy as np
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(HERE,'..')
PNG=os.path.join(R,'lib','logo','nibble.png'); LIB=os.path.join(R,'lib','nibble.pretty')
HEIGHT=8.0            # mm, the icon's height (the word is the same height)
ICON_RIGHT=640        # px: the icon's ink ends before this column, the word's begins after it
THRESHOLD=128

def ink():
    """The logo's ink as a boolean array, the picture laid on white first (the PNG is transparent around the ink)."""
    im=Image.open(PNG).convert('RGBA'); bg=Image.new('RGBA',im.size,(255,255,255,255)); bg.alpha_composite(im)
    return np.array(bg.convert('L'))<THRESHOLD

def trace(mask):
    """Closed contours of the ink: [(outer: bool, [(x,y) px, ...]), ...], every curve flattened to lines."""
    import potrace
    path=potrace.Bitmap(~mask).trace(turdsize=20,alphamax=1.0,opttolerance=0.2); out=[]
    P=lambda v:(float(v.x),float(v.y))
    for c in path.curves:
        pts=[P(c.start_point)]
        for s in c.segments:
            if s.is_corner: pts+=[P(s.c),P(s.end_point)]
            else:
                p0=pts[-1]; p1,p2,p3=P(s.c1),P(s.c2),P(s.end_point)
                for k in range(1,13):
                    t=k/12; u=1-t
                    pts.append((u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0], u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]))
        q=[pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0]-q[-1][0],p[1]-q[-1][1])>0.5: q.append(p)
        if math.hypot(q[0][0]-q[-1][0],q[0][1]-q[-1][1])<=0.5: q.pop()
        out.append((bool(c._path.sign),q))
    return out

def area(p): return 0.5*sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))
def inside(pt,poly):
    x,y=pt; n=len(poly); c=False
    for i in range(n):
        (x1,y1),(x2,y2)=poly[i],poly[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c

def merge(outer,hole):
    """The hole cut into the outer polygon through a slit: from the hole's rightmost point straight right to the first
    edge of the outer polygon (which already holds the holes merged before, so the slit stops at whichever boundary
    comes first). The outer runs one way round, the hole the other."""
    if area(outer)<0: outer=outer[::-1]
    if area(hole)>0: hole=hole[::-1]
    k=max(range(len(hole)),key=lambda i:(hole[i][0],-hole[i][1])); hx,hy=hole[k]; best=None
    for i in range(len(outer)):
        (x1,y1),(x2,y2)=outer[i],outer[(i+1)%len(outer)]
        if (y1>hy)!=(y2>hy) or y1==hy or y2==hy:
            if y1==y2: continue
            x=(x2-x1)*(hy-y1)/(y2-y1)+x1
            if x>hx and (best is None or x<best[0]): best=(x,i)
    if best is None: raise SystemExit('a hole with nothing to its right')
    x,i=best; q=(x,hy)
    return outer[:i+1]+[q,(hx,hy)]+hole[k+1:]+hole[:k]+[(hx,hy),q]+outer[i+1:]

def polygons(contours):
    """Simple polygons, px: every outer contour with its holes slit in, the holes of the smallest outer around them."""
    outers=[(abs(area(p)),p) for o,p in contours if o]; holes=[p for o,p in contours if not o]
    outers.sort(key=lambda t:t[0]); own={i:[] for i in range(len(outers))}
    for h in holes:
        k=max(range(len(h)),key=lambda i:h[i][0]); pt=h[k]
        i=next((i for i,(a,p) in enumerate(outers) if inside(pt,p)),None)
        if i is None: raise SystemExit('a hole in nothing')
        own[i].append(h)
    out=[]
    for i,(a,p) in enumerate(outers):
        q=p[::-1] if area(p)<0 else p
        for h in sorted(own[i],key=lambda h:-max(x for x,y in h)): q=merge(q,h)
        out.append(q)
    return out

def footprint(name,polys,descr):
    """A footprint of filled F.SilkS polygons in mm, its origin the middle of the ink's box; nothing on any copper layer,
    no pads, out of the position file and the parts list."""
    xs=[x for p in polys for x,y in p]; ys=[y for p in polys for x,y in p]; cx,cy=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2
    f=lambda v:f'{v:.3f}'.rstrip('0').rstrip('.') if abs(v)>=5e-4 else '0'
    s=[f'(footprint "{name}"','\t(version 20260206)','\t(generator "nibble")','\t(generator_version "1")','\t(layer "F.Cu")',f'\t(descr "{descr}")','\t(tags "logo silkscreen")',
       '\t(property "Reference" "REF**"\n\t\t(at 0 0 0)\n\t\t(layer "F.SilkS")\n\t\thide\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)',
       f'\t(property "Value" "{name}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\thide\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)',
       '\t(attr board_only exclude_from_pos_files exclude_from_bom)']
    for p in polys:
        pts=''.join(f'\n\t\t\t(xy {f(x-cx)} {f(y-cy)})' for x,y in p)
        s.append(f'\t(fp_poly\n\t\t(pts{pts}\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "F.SilkS")\n\t)')
    s.append(')'); return '\n'.join(s)+'\n', (max(xs)-min(xs),max(ys)-min(ys))

def main():
    m=ink(); ys,xs=np.nonzero(m); scale=HEIGHT/(ys.max()-ys.min()+1)
    contours=trace(m)
    icon=[(o,p) for o,p in contours if max(x for x,y in p)<ICON_RIGHT]
    for name,cs,descr in (('Logo_Nibble_Icon',icon,'The Nibble logo, the icon alone, %.0f mm, silkscreen'%HEIGHT),('Logo_Nibble',contours,'The Nibble logo, icon and word, %.0f mm tall, silkscreen'%HEIGHT)):
        polys=[[(x*scale,y*scale) for x,y in p] for p in polygons(cs)]
        text,(w,h)=footprint(name,polys,descr); open(os.path.join(LIB,f'{name}.kicad_mod'),'w').write(text)
        print(f'{name}: {len(polys)} polygons, {sum(len(p) for p in polys)} points, {w:.2f} x {h:.2f} mm')

if __name__=='__main__': main()
