"""What changed on a routed board since a commit, measured on the files: the proof that goes with a change made in place.

    python3 board_diff.py <commit> coupon reg0 sequencer ...        (from sim/; plain python3, git, kicad-cli)

Per board, the committed files of <commit> against the files in the tree:
  netlist   the kicad-cli SPICE export of the schematic, element for element (what the machine gate simulates)
  tracks    every track segment and every via of the board file, as sets
  drill     the drill file
  copper    every copper and mask gerber read into what it draws (gerber_diff.py): flashes, strokes, filled outlines
and the verdict for a change that may move no copper: the netlist, the tracks, the vias and the holes are the same, no layer
has a stroke more or less, pads differ only in the two holes where a bus header turned onto the back (D059) has its pin 1 and
pin 2 (the square pad went from one to the other), and the ground pour's outline is within 20 um of where it was except
round those two pads. Exit status 1 otherwise."""
import sys, os, re, subprocess, tempfile, shutil
import gerber_diff, assembly
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,'..')); K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
seg=lambda s:sorted(re.findall(r'\(segment\s*\(start [^)]*\)\s*\(end [^)]*\)\s*\(width [^)]*\)\s*\(layer "[^"]+"\)\s*\(net (?:\d+ )?"[^"]*"\)',s))
via=lambda s:sorted(re.findall(r'\(via\s*\(at [^)]*\)\s*\(size [^)]*\)\s*\(drill [^)]*\)\s*\(layers [^)]*\)(?:\s*\([a-z_]+ [^)]*\))*?\s*\(net (?:\d+ )?"[^"]*"\)',s))
def old(rev,rel,dst):
    r=subprocess.run(['git','-C',REPO,'show',f'{rev}:{rel}'],capture_output=True)
    if r.returncode: raise SystemExit(f'{rel} is not in {rev}')
    os.makedirs(os.path.dirname(dst),exist_ok=True); open(dst,'wb').write(r.stdout); return dst
def spice(sch,out):
    subprocess.run([K,'sch','export','netlist','--format','spice','-o',out,sch],capture_output=True)
    return sorted(l.strip() for l in open(out) if l.strip() and not l.startswith(('*','.title','.include')))
def pour_shift(gone,new,holes):
    """How far the filled outlines moved: the largest distance from a corner that is in one file only to the other file's
    outline, in mm, leaving out the corners within 3 mm of the pads that changed shape. (KiCad draws the clearance round a
    pad as a polygon; round a pad that was turned over the same circle gets its corners in other places.)"""
    import math
    def contours(ks):
        E=[]; V=set()
        for k in ks:
            if k[0]!='region': continue
            prev=None
            for x,y,d,i,j in k[1]:
                if prev is not None and d=='1': E.append((prev[0],prev[1],x,y))
                prev=(x,y); V.add((x,y))
        return E,V
    (Eo,Vo),(En,Vn)=contours(gone),contours(new); worst=0.0; n=0
    def dist(p,E):
        best=1e9
        for x1,y1,x2,y2 in E:
            if min(x1,x2)-best>p[0] or max(x1,x2)+best<p[0] or min(y1,y2)-best>p[1] or max(y1,y2)+best<p[1]: continue
            dx,dy=x2-x1,y2-y1; L=dx*dx+dy*dy; t=0 if L==0 else max(0,min(1,((p[0]-x1)*dx+(p[1]-y1)*dy)/L)); best=min(best,math.hypot(p[0]-x1-t*dx,p[1]-y1-t*dy))
        return best
    for V,E,W in ((Vn,Eo,Vo),(Vo,En,Vn)):
        for p in V-W:
            n+=1
            if min([abs(p[0]-hx)+abs(-p[1]-hy) for hx,hy in holes] or [1e9])<=3.0: continue
            worst=max(worst,dist(p,E))
    return worst,n

def diff(rev,name,tmp):
    B=assembly.board(name); d=os.path.abspath(B['dir']); rel=os.path.relpath(d,REPO); t=os.path.join(tmp,rel); bad=[]; msg=[]
    if not os.path.exists(os.path.join(tmp,'lib')): os.symlink(os.path.join(REPO,'lib'),os.path.join(tmp,'lib'))      # the schematics name their models as ../../lib
    old(rev,f'{rel}/{name}.kicad_pro',f'{t}/{name}.kicad_pro')      # without its project file kicad-cli does not know where the schematic is, and finds no model
    for f in subprocess.run(['git','-C',REPO,'ls-tree','--name-only',rev,rel+'/'],capture_output=True,text=True).stdout.split():
        if f.endswith('.kicad_sch') and not f.endswith(f'/{name}.kicad_sch'): old(rev,f,os.path.join(tmp,f))      # its sub-sheets (the coupon's bench)
    a=spice(old(rev,f'{rel}/{name}.kicad_sch',f'{t}/{name}.kicad_sch'),f'{t}/old.cir'); b=spice(os.path.join(d,f'{name}.kicad_sch'),f'{t}/new.cir')
    if a!=b: bad.append('netlist')
    po=open(old(rev,f'{rel}/{name}.kicad_pcb',f'{t}/{name}.kicad_pcb')).read(); pn=open(os.path.join(d,f'{name}.kicad_pcb')).read()
    if seg(po)!=seg(pn): bad.append('tracks')
    if via(po)!=via(pn): bad.append('vias')
    st=lambda f:'\n'.join(l for l in open(f).read().splitlines() if not l.startswith(';'))
    if st(old(rev,f'{rel}/fab/{name}.drl',f'{t}/fab/{name}.drl'))!=st(os.path.join(d,'fab',f'{name}.drl')): bad.append('drill')
    hdr=[(float(m.group(1)),float(m.group(2))) for m in re.finditer(r'\(footprint "IDC-Header_2x32[^"]*"\s*\(layer "B.Cu"\)\s*\(uuid "[^"]+"\)\s*\(at ([\d.-]+) ([\d.-]+)',pn)]
    holes={(round(hx,2),round(hy+dy,2)) for hx,hy in hdr for dy in (0,2.54)}
    for suf in ['-F_Cu.gtl','-B_Cu.gbl']+(['-In1_Cu.g1','-In2_Cu.g2'] if B['layers']==4 else [])+['-F_Mask.gts','-B_Mask.gbs','-Edge_Cuts.gm1']:
        gone,new,na,nb=gerber_diff.diff(old(rev,f'{rel}/fab/{name}{suf}',f'{t}/fab/{name}{suf}'),os.path.join(d,'fab',f'{name}{suf}'))
        fl=[k for k in gone+new if k[0]=='flash']; strokes=[k for k in gone+new if k[0]=='stroke']; reg=[k for k in gone+new if k[0]=='region']
        stray=[k for k in fl if (round(k[2],2),round(-k[3],2)) not in holes]
        off,nmoved=pour_shift(gone,new,holes)
        if strokes: bad.append(f'{suf}: {len(strokes)} strokes')
        if stray: bad.append(f'{suf}: {len(stray)} pads elsewhere, e.g. {gerber_diff.show(stray[0])}')
        if off>0.02: bad.append(f'{suf}: the pour\'s outline moved {off*1000:.0f} um away from the header\'s first pins')
        if reg and 'Mask' in suf: bad.append(f'{suf}: filled outlines')
        if gone or new: msg.append(f'{suf[1:].split(".")[0]} {len(fl)//2} pads'+(f', the pour redrawn ({nmoved} corners, none more than {off*1000:.0f} um from the old outline but round the {len(holes)} pads that changed shape)' if reg else ''))
    print(f'{name:10s} netlist {"same" if "netlist" not in bad else "DIFFERS"} ({len(b)} lines), {len(seg(pn))} tracks {"same" if "tracks" not in bad else "DIFFER"}, {len(via(pn))} vias {"same" if "vias" not in bad else "DIFFER"}, '
          f'holes {"same" if "drill" not in bad else "DIFFER"}; {len(hdr)} header{"s" if len(hdr)!=1 else ""} on the back; changed: {"; ".join(msg) or "nothing"}'+(f'   NOT AS EXPECTED: {", ".join(bad)}' if bad else ''))
    return not bad
if __name__=='__main__':
    if len(sys.argv)<3: print(__doc__); sys.exit(2)
    tmp=tempfile.mkdtemp(prefix='board_diff_'); ok=[diff(sys.argv[1],n,tmp) for n in sys.argv[2:]]; shutil.rmtree(tmp,ignore_errors=True)
    print(f'{sum(ok)} of {len(ok)} boards: no copper moved' if all(ok) else f'{len(ok)-sum(ok)} of {len(ok)} boards NOT AS EXPECTED'); sys.exit(0 if all(ok) else 1)
