"""What differs between two gerber files as copper, not as text.

    python3 gerber_diff.py old.gbr new.gbr

kicad-cli numbers a layer's apertures in the order it meets them, so moving one pad renumbers the table and a text diff of two
nearly equal layers runs to a thousand lines. This reads each file into what it draws: every flash (the aperture's shape and
size at a point), every stroke (aperture, from, to) and every filled region (its outline), and compares the two as sets.
Coordinates print in mm. Exit status 1 if anything differs."""
import sys, re, collections
def read(path):
    ap={}; cur=None; x=y=0; out=collections.Counter(); region=None; scale=1e6; macros={}; macro=None
    for raw in open(path).read().replace('\r','').split('\n'):
        l=raw.strip()
        if not l or l.startswith('G04'): continue
        m=re.match(r'%FSLAX(\d)(\d)Y\d\d\*%',l)
        if m: scale=10**int(m.group(2)); continue
        if l.startswith('%AM'): macro=l[3:].rstrip('*%'); macros[macro]=[]; continue
        if macro is not None:
            macros[macro].append(l.rstrip('%'))
            if l.endswith('%'): macro=None
            continue
        m=re.match(r'%ADD(\d+)([^,*]+),?([^*]*)\*%',l)
        if m: ap[m.group(1)]=(m.group(2),m.group(3),tuple(macros.get(m.group(2),()))); continue
        if l.startswith('%'): continue
        for c in [c for c in l.split('*') if c]:
            if c=='G36': region=[]; continue
            if c=='G37':
                if region: out[('region',tuple(region))]+=1
                region=None; continue
            m=re.match(r'^(?:G54)?D(\d+)$',c)
            if m and int(m.group(1))>=10: cur=m.group(1); continue
            m=re.match(r'^(?:G0?[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?(?:D0?([123]))?$',c)
            if not m or not (m.group(1) or m.group(2) or m.group(5)): continue
            nx=int(m.group(1))/scale if m.group(1) else x; ny=int(m.group(2))/scale if m.group(2) else y; d=m.group(5)
            if region is not None: region.append((round(nx,4),round(ny,4),d,m.group(3),m.group(4)))
            elif d=='3': out[('flash',ap.get(cur),round(nx,4),round(ny,4))]+=1
            elif d=='1': out[('stroke',ap.get(cur),)+tuple(sorted([(round(x,4),round(y,4)),(round(nx,4),round(ny,4))]))+(m.group(3),m.group(4))]+=1
            x,y=nx,ny
    return out
def show(k):
    if k[0]=='flash': return f'flash {k[1][0]} {k[1][1]} at ({k[2]:.3f}, {-k[3]:.3f})'
    if k[0]=='stroke': return f'stroke {k[1][0]} {k[1][1]} from ({k[2][0]:.3f}, {-k[2][1]:.3f}) to ({k[3][0]:.3f}, {-k[3][1]:.3f})'
    xs=[p[0] for p in k[1]]; ys=[-p[1] for p in k[1]]
    return f'region of {len(k[1])} points, x {min(xs):.2f}..{max(xs):.2f} y {min(ys):.2f}..{max(ys):.2f}'
def diff(a,b):
    A,B=read(a),read(b); gone=list((A-B).elements()); new=list((B-A).elements()); return gone,new,sum(A.values()),sum(B.values())
if __name__=='__main__':
    if len(sys.argv)!=3: print(__doc__); sys.exit(2)
    gone,new,na,nb=diff(*sys.argv[1:])
    print(f'{na} and {nb} items; {len(gone)} only in the first, {len(new)} only in the second')
    for k in gone[:40]: print('  -',show(k))
    for k in new[:40]: print('  +',show(k))
    sys.exit(1 if gone or new else 0)
