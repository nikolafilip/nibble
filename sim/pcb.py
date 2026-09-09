"""Build, route and check a board from a KiCad project + placement plan.
Run with KiCad's python:  <kicad>/python3 pcb.py <projectdir> <name> [--no-route]
Reads <name>.kicad_sch (via kicad-cli netlist), <name>.plan.json; writes <name>.kicad_pcb, fab/ outputs.
"""
import sys, os, json, subprocess, re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pcbnew, knet
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
F='/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
JAVA=os.path.expanduser('~/.sdkman/candidates/java/21.0.2-tem/bin/java')
JAR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','tools','freerouting-2.1.0.jar')
mm=lambda v:int(round(v*1e6))
V=lambda x,y:pcbnew.VECTOR2I(mm(x),mm(y))

def build(projdir,name,route=True,passes=40):
    sch=os.path.join(projdir,f'{name}.kicad_sch'); net=os.path.join(projdir,f'{name}.net')
    subprocess.run([K,'sch','export','netlist','--format','kicadsexpr','-o',net,sch],check=True,capture_output=True)
    nets,comps=knet.parse(net); plan=json.load(open(os.path.join(projdir,f'{name}.plan.json')))
    W,H=plan['outline']; place=plan['place']
    board=pcbnew.NewBoard(os.path.join(projdir,f'{name}.kicad_pcb'))
    ds=board.GetDesignSettings()
    nc=ds.m_NetSettings.GetDefaultNetclass()
    rules=plan['extra'].get('rules',{}); tw=rules.get('track',0.25); cl=rules.get('clearance',0.2)
    nc.SetTrackWidth(mm(tw)); nc.SetClearance(mm(cl)); nc.SetViaDiameter(mm(0.8)); nc.SetViaDrill(mm(0.4))
    ds.m_MinResolvedSpokes=1; ds.m_TrackMinWidth=mm(min(tw,0.25)); ds.m_ViasMinSize=mm(0.6); ds.m_MinThroughDrill=mm(0.3); ds.m_MinClearance=mm(min(cl,0.2))
    # nets
    netobj={}
    for n in nets:
        ni=pcbnew.NETINFO_ITEM(board,n); board.Add(ni); netobj[n]=ni
    padnet={}
    for n,nodes in nets.items():
        for ref,pin in nodes: padnet[(ref,pin)]=n
    # footprints
    holes=[]; missing=[]
    for ref,(val,fp) in comps.items():
        if not fp: continue
        lib,fn=fp.split(':')
        m=pcbnew.FootprintLoad(f'{F}/{lib}.pretty',fn)
        if m is None: missing.append(fp); continue
        m.SetReference(ref); m.SetValue(val)
        if any(ref.startswith(pfx) for pfx in plan['extra'].get('hide_refs',[])): m.Reference().SetVisible(False)
        board.Add(m)
        for pad in m.Pads():
            n=padnet.get((ref,pad.GetNumber()))
            if n: pad.SetNet(netobj[n])
        if ref.startswith('H'): holes.append(m); continue
        if ref in place:
            x,y,rot=place[ref]; m.SetPosition(V(x,y)); m.SetOrientationDegrees(rot)
        else: print('WARNING: no placement for',ref,fp); m.SetPosition(V(W+20,10))
    if missing: raise SystemExit('missing footprints: '+str(missing))
    for k,h in enumerate(holes[:4]):
        h.SetPosition(V(4 if k%2==0 else W-4, 4 if k<2 else H-4))
    # outline (inset while routing so the router keeps vias off the edge; restored to full size at the end)
    def outline(inset):
        for d in [d for d in board.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]: board.Remove(d)
        a,b,c,e=inset,inset,W-inset,H-inset
        for (x1,y1,x2,y2) in [(a,b,c,b),(c,b,c,e),(c,e,a,e),(a,e,a,b)]:
            sh=pcbnew.PCB_SHAPE(board); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetStart(V(x1,y1)); sh.SetEnd(V(x2,y2)); sh.SetLayer(pcbnew.Edge_Cuts); sh.SetWidth(mm(0.1)); board.Add(sh)
    outline(1.5 if route else 0)
    # silkscreen labels
    for text,x,y,size in plan['silk']+plan['extra'].get('silk',[]):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size),mm(size))); t.SetTextThickness(mm(0.15)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(t)
    for text,x,y,size in plan['extra'].get('silk_big',[]):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size),mm(size))); t.SetTextThickness(mm(0.25)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(t)
    def pour(netname,layer):
        if netname not in netobj: return
        z=pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(netobj[netname])
        o=z.Outline(); o.NewOutline()
        for x,y in [(1,1),(W-1,1),(W-1,H-1),(1,H-1)]: o.Append(mm(x),mm(y))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(0.3))
        z.SetZoneName(netname); board.Add(z)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    def gnd_pour():
        for z in list(board.Zones()): board.Remove(z)
        pour('GND',pcbnew.B_Cu)
    # pre-routed power rails and stubs (from the tile geometry); the router only sees signals
    LAY={'F.Cu':pcbnew.F_Cu,'B.Cu':pcbnew.B_Cu}
    def add_rails():
        for net,layer,x1,y1,x2,y2,wd in plan.get('rails',[]):
            t=pcbnew.PCB_TRACK(board); t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(mm(wd)); t.SetLayer(LAY[layer]); t.SetNet(netobj[net]); board.Add(t)
        for net,x,y in plan.get('vias',[]):
            v=pcbnew.PCB_VIA(board); v.SetPosition(V(x,y)); v.SetDrill(mm(0.4)); v.SetWidth(mm(0.8)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(netobj[net]); board.Add(v)
    add_rails()
    pcb=os.path.join(projdir,f'{name}.kicad_pcb'); pcbnew.SaveBoard(pcb,board)
    print(f'{name}: {len(comps)} parts, {len(nets)} nets, board {W}x{H} mm')
    gnd_pour(); pcbnew.SaveBoard(pcb,board)     # before routing: the router sees GND as a plane and leaves it alone
    if route:
        dsn=os.path.join(projdir,f'{name}.dsn'); ses=os.path.join(projdir,f'{name}.ses')
        for attempt in range(3):
            pcbnew.ExportSpecctraDSN(board,dsn)
            # pre-routed power (GND/+5V rails, stubs, stitches) is fixed so the router cannot move it; the SES then omits it,
            # and KiCad's SES import replaces all tracks, so the rails are re-added after every import (add_rails below)
            lines=open(dsn).read().split('\n')
            lines=[l.replace('(type route)','(type fix)') if ('(net GND)' in l or '(net +5V)' in l) else l for l in lines]
            open(dsn,'w').write('\n'.join(lines))
            r=subprocess.run([JAVA,'-Djava.awt.headless=true','-jar',JAR,'-de',dsn,'-do',ses,'-mp',str(passes),'-dct','2'],capture_output=True,text=True,timeout=3600)
            last=[l for l in r.stdout.splitlines() if 'unrouted' in l.lower()]
            m=re.search(r'\((\d+) unrouted\)',last[-1]) if last else None
            unrouted=int(m.group(1)) if m else 0
            print(f'  route attempt {attempt+1}: {unrouted} unrouted')
            if not os.path.exists(ses): print(r.stdout[-3000:]); raise SystemExit('freerouting produced no SES')
            pcbnew.ImportSpecctraSES(board,ses); os.remove(ses)
            add_rails(); gnd_pour(); pcbnew.SaveBoard(pcb,board)
            for _ in range(2):
                if gnd_stitch(board,pcb,netobj,gnd_pour)==0: break
            if unconnected(pcb)==0: break
        os.remove(dsn)
        outline(0); gnd_pour(); pcbnew.SaveBoard(pcb,board)
    return pcb

def gnd_stitch(board,pcb,netobj,refill,gndname='GND'):
    """For every GND pad DRC reports as not reached by the pour, add a via in a nearby free spot and a short track to it.
    Each candidate is verified with a real DRC run (the spot must actually reduce the unconnected count)."""
    import math
    rep=pcb.replace('.kicad_pcb','.drc.json')
    def drc_count():
        subprocess.run([K,'pcb','drc','--format','json','-o',rep,pcb],capture_output=True)
        return json.load(open(rep)).get('unconnected_items',[])
    items=drc_count(); todo=[]
    for u in items:
        for it in u['items']:
            d=it['description']
            if d.startswith('PTH pad') and f'[{gndname}]' in d and (it['pos']['x'],it['pos']['y']) not in todo: todo.append((it['pos']['x'],it['pos']['y']))
    if not todo: return 0
    gnd=netobj[gndname]
    pads=[(p.GetPosition().x/1e6,p.GetPosition().y/1e6,p.GetNetname()) for fp in board.GetFootprints() for p in fp.Pads()]
    segs=[]; vias=[]
    for t in board.GetTracks():
        if t.GetClass()=='PCB_VIA': vias.append((t.GetPosition().x/1e6,t.GetPosition().y/1e6,t.GetNetname()))
        else: segs.append((t.GetStart().x/1e6,t.GetStart().y/1e6,t.GetEnd().x/1e6,t.GetEnd().y/1e6,t.GetNetname(),t.GetLayer()))
    def dseg(px,py,x1,y1,x2,y2):
        dx,dy=x2-x1,y2-y1; L=dx*dx+dy*dy
        t=0 if L==0 else max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L)); return math.hypot(px-(x1+t*dx),py-(y1+t*dy))
    def free_point(x,y):
        return all(math.hypot(x-px,y-py)>=1.6 for px,py,n in pads) and all(math.hypot(x-vx,y-vy)>=1.3 for vx,vy,n in vias) and all(dseg(x,y,*sg[:4])>=0.9 for sg in segs if sg[4]!=gndname)
    def cross(ax,ay,bx,by,cx,cy,dx,dy):
        def o(px,py,qx,qy,rx,ry): return (qy-py)*(rx-qx)-(qx-px)*(ry-qy)
        o1,o2,o3,o4=o(ax,ay,bx,by,cx,cy),o(ax,ay,bx,by,dx,dy),o(cx,cy,dx,dy,ax,ay),o(cx,cy,dx,dy,bx,by)
        return (o1*o2<0) and (o3*o4<0)
    def free_track(x1,y1,x2,y2,layer):
        for px,py,n in pads:
            if n!=gndname and dseg(px,py,x1,y1,x2,y2)<1.3: return False
        for sg in segs:
            if sg[4]!=gndname and sg[5]==layer:
                if cross(x1,y1,x2,y2,*sg[:4]): return False
                if min(dseg(sg[0],sg[1],x1,y1,x2,y2),dseg(sg[2],sg[3],x1,y1,x2,y2),dseg(x1,y1,*sg[:4]),dseg(x2,y2,*sg[:4]))<0.6: return False
        return True
    bb=board.GetBoardEdgesBoundingBox(); R=bb.GetRight()/1e6; B=bb.GetBottom()/1e6
    added=0; before=len(items)
    for (x,y) in todo:
        done=False; tried=0
        for r in (2.2,2.8,3.4,4.0,5.0,6.0):
            for k in range(16):
                a=2*math.pi*k/16; vx,vy=x+r*math.cos(a),y+r*math.sin(a)
                if not (2<vx<R-2 and 2<vy<B-2) or not free_point(vx,vy): continue
                layer=next((L for L in (pcbnew.F_Cu,pcbnew.B_Cu) if free_track(x,y,vx,vy,L)),None)
                if layer is None: continue
                v=pcbnew.PCB_VIA(board); v.SetPosition(V(vx,vy)); v.SetDrill(mm(0.4)); v.SetWidth(mm(0.8)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(gnd); board.Add(v)
                t=pcbnew.PCB_TRACK(board); t.SetStart(V(x,y)); t.SetEnd(V(vx,vy)); t.SetWidth(mm(0.4)); t.SetLayer(layer); t.SetNet(gnd); board.Add(t)
                refill(); pcbnew.SaveBoard(pcb,board)
                now=len(drc_count()); tried+=1
                if now<before:
                    before=now; vias.append((vx,vy,gndname)); segs.append((x,y,vx,vy,gndname,layer)); added+=1; done=True; break
                board.Remove(v); board.Remove(t)
                if tried>=10: break
            if done or tried>=10: break
        if not done: print('   gnd_stitch: no working spot near',x,y)
    refill(); pcbnew.SaveBoard(pcb,board)
    print(f'   gnd_stitch: {added} vias for {len(todo)} pads, unconnected now {before}')
    return added

def unconnected(pcb):
    rep=pcb.replace('.kicad_pcb','.drc.json')
    subprocess.run([K,'pcb','drc','--format','json','-o',rep,pcb],capture_output=True)
    n=len(json.load(open(rep)).get('unconnected_items',[])); print('   DRC unconnected:',n); return n

def drc(pcb):
    rep=pcb.replace('.kicad_pcb','.drc.json')
    subprocess.run([K,'pcb','drc','--format','json','--severity-all','-o',rep,pcb],capture_output=True)
    j=json.load(open(rep)); import collections
    c=collections.Counter((v['severity'],v['type']) for v in j['violations'])
    unc=len(j.get('unconnected_items',[]))
    print('DRC:',dict(c),'unconnected:',unc)
    for v in j['violations'][:8]: print('  ',v['severity'],v['type'],v['description'][:80])
    return j

def outputs(pcb,name):
    d=os.path.dirname(pcb); fab=os.path.join(d,'fab'); os.makedirs(fab,exist_ok=True)
    subprocess.run([K,'pcb','export','gerbers','-o',fab+'/',pcb],capture_output=True)
    subprocess.run([K,'pcb','export','drill','-o',fab+'/',pcb],capture_output=True)
    subprocess.run([K,'pcb','export','pos','--format','csv','--units','mm','-o',os.path.join(fab,f'{name}-pos.csv'),pcb],capture_output=True)
    subprocess.run([K,'sch','export','bom','--fields','Reference,Value,Footprint,${QUANTITY}','--group-by','Value,Footprint','-o',os.path.join(fab,f'{name}-bom.csv'),os.path.join(d,f'{name}.kicad_sch')],capture_output=True)
    for side,fn in [('top',f'{name}-top.png'),('bottom',f'{name}-bottom.png')]:
        subprocess.run([K,'pcb','render','--side',side,'--width','2000','--height','1400','--quality','high','-o',os.path.join(fab,fn),pcb],capture_output=True)
    print('fab outputs in',fab)

if __name__=='__main__':
    projdir,name=sys.argv[1],sys.argv[2]
    pcb=build(projdir,name,route='--no-route' not in sys.argv)
    drc(pcb); outputs(pcb,name)
