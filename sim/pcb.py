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
    nc.SetTrackWidth(mm(0.3)); nc.SetClearance(mm(0.25)); nc.SetViaDiameter(mm(0.8)); nc.SetViaDrill(mm(0.4))
    ds.m_MinResolvedSpokes=1; ds.m_TrackMinWidth=mm(0.25); ds.m_ViasMinSize=mm(0.6); ds.m_MinThroughDrill=mm(0.3); ds.m_MinClearance=mm(0.2)
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
    # outline
    for (x1,y1,x2,y2) in [(0,0,W,0),(W,0,W,H),(W,H,0,H),(0,H,0,0)]:
        s=pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(x1,y1)); s.SetEnd(V(x2,y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)
    # silkscreen labels
    for text,x,y,size in plan['silk']+plan['extra'].get('silk',[]):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size),mm(size))); t.SetTextThickness(mm(0.15)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(t)
    for text,x,y,size in plan['extra'].get('silk_big',[]):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size),mm(size))); t.SetTextThickness(mm(0.25)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(t)
    def gnd_pour():
        if 'GND' not in netobj: return
        z=pcbnew.ZONE(board); z.SetLayer(pcbnew.B_Cu); z.SetNet(netobj['GND'])
        o=z.Outline(); o.NewOutline()
        for x,y in [(1,1),(W-1,1),(W-1,H-1),(1,H-1)]: o.Append(mm(x),mm(y))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(0.3))
        z.SetZoneName('GND'); board.Add(z)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcb=os.path.join(projdir,f'{name}.kicad_pcb'); pcbnew.SaveBoard(pcb,board)
    print(f'{name}: {len(comps)} parts, {len(nets)} nets, board {W}x{H} mm')
    if not route: gnd_pour(); pcbnew.SaveBoard(pcb,board)
    if route:
        dsn=os.path.join(projdir,f'{name}.dsn'); ses=os.path.join(projdir,f'{name}.ses')
        pcbnew.ExportSpecctraDSN(board,dsn)
        r=subprocess.run([JAVA,'-Djava.awt.headless=true','-jar',JAR,'-de',dsn,'-do',ses,'-mp',str(passes),'-dct','2'],capture_output=True,text=True,timeout=3600)
        tail=[l for l in r.stdout.splitlines() if 'unrouted' in l.lower() or 'routed' in l.lower() or 'ERROR' in l][-6:]
        print('\n'.join(tail))
        if not os.path.exists(ses): print(r.stdout[-3000:]); raise SystemExit('freerouting produced no SES')
        pcbnew.ImportSpecctraSES(board,ses)
        gnd_pour()
        pcbnew.SaveBoard(pcb,board)
        for f_ in (dsn,ses): os.remove(f_)
    return pcb

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
