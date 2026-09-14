"""Build, route and check a board from a KiCad project + placement plan.
Run with KiCad's python:  <kicad>/python3 pcb.py <projectdir> <name> [--no-route] [--passes N] [--silk] [--patch] [--dsn-only] [--ses file.ses]   (N: freerouting router and optimizer pass cap, default 300 (a dense card needs about 200 to close its last net); a board that cannot finish stops there with its unrouted nets listed; --silk only replaces the silkscreen text of a routed board from the plan)
Reads <name>.kicad_sch (via kicad-cli netlist), <name>.plan.json; writes <name>.kicad_pcb, fab/ outputs.
"""
import glob, sys, os, json, subprocess, re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pcbnew, knet
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
F='/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
JAVA=os.environ.get('NIBBLE_JAVA') or os.path.expanduser('~/.sdkman/candidates/java/21.0.2-tem/bin/java')      # NIBBLE_JAVA: another JVM (freerouting 2.4.1 needs Java 25; 2.1.0 runs on 21)
JAR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','tools','freerouting-1.9.0.jar')   # 1.9: -mp caps the passes and the SES is written; 2.1 ignores every cap headless
mm=lambda v:int(round(v*1e6))
V=lambda x,y:pcbnew.VECTOR2I(mm(x),mm(y))

def build(projdir,name,route=True,passes=300,dsn_only=False,ses_file=None):
    sch=os.path.join(projdir,f'{name}.kicad_sch'); net=os.path.join(projdir,f'{name}.net')
    subprocess.run([K,'sch','export','netlist','--format','kicadsexpr','-o',net,sch],check=True,capture_output=True)
    nets,comps=knet.parse(net); plan=json.load(open(os.path.join(projdir,f'{name}.plan.json')))
    W,H=plan['outline']; place=plan['place']
    board=pcbnew.NewBoard(os.path.join(projdir,f'{name}.kicad_pcb'))
    layers=plan['extra'].get('layers',2)          # 4 (the sequencer, D051): In1.Cu is a solid GND plane the router leaves alone, In2.Cu a third routing layer
    if layers==4: board.SetCopperLayerCount(4)
    GND_LAYER=pcbnew.In1_Cu if layers==4 else pcbnew.B_Cu
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
    for ref,(val,fp,dnp) in comps.items():
        if not fp or int(re.sub(r'\D','',ref) or 0)>=9000: continue     # testbench parts (refs 9000 and up) are not on the board
        lib,fn=fp.split(':')
        m=pcbnew.FootprintLoad(f'{F}/{lib}.pretty',fn)
        if m is None: missing.append(fp); continue
        m.SetReference(ref); m.SetValue(val)
        hidden=any(ref.startswith(pfx) for pfx in plan['extra'].get('hide_refs',[]))
        if hidden: m.Reference().SetVisible(False)
        if dnp: m.SetDNP(True)
        for t in m.GraphicalItems():    # a hidden part's own silk texts (a diode's "A") clutter a dense tile; a DNP part (an empty matrix crossing, D040) keeps its pads only, so the fitted diodes stand out
            t=t.Cast()
            if t.GetLayer()!=pcbnew.F_SilkS: continue
            if (hidden and isinstance(t,pcbnew.PCB_TEXT)) or dnp: t.SetLayer(pcbnew.F_Fab)     # (a text's visibility is not saved; the fab layer is not made)
        board.Add(m)
        for pad in m.Pads():
            n=padnet.get((ref,pad.GetNumber()))
            if n: pad.SetNet(netobj[n])
        if ref.startswith('H'): holes.append(m); continue
        if ref in place:
            x,y,rot=place[ref]; m.SetPosition(V(x,y)); m.SetOrientationDegrees(rot)
        else: print('WARNING: no placement for',ref,fp); m.SetPosition(V(W+20,10))
    if missing: raise SystemExit('missing footprints: '+str(missing))
    hp=plan['extra'].get('holes')            # explicit hole positions (cards: mid-side), else the four corners
    for k,h in enumerate(holes[:len(hp) if hp else 4]):
        h.SetPosition(V(*hp[k]) if hp else V(4 if k%2==0 else W-4, 4 if k<2 else H-4))
    # outline (inset while routing so the router keeps vias off the edge; restored to full size at the end)
    def outline(inset):
        for d in [d for d in board.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]: board.Remove(d)
        a,b,c,e=inset,inset,W-inset,H-inset
        for (x1,y1,x2,y2) in [(a,b,c,b),(c,b,c,e),(c,e,a,e),(a,e,a,b)]:
            sh=pcbnew.PCB_SHAPE(board); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetStart(V(x1,y1)); sh.SetEnd(V(x2,y2)); sh.SetLayer(pcbnew.Edge_Cuts); sh.SetWidth(mm(0.1)); board.Add(sh)
    outline(1.5 if route else 0)
    add_silk(board,plan)
    def pour(netname,layer):
        if netname not in netobj: return
        z=pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(netobj[netname])
        o=z.Outline(); o.NewOutline()
        for x,y in [(1,1),(W-1,1),(W-1,H-1),(1,H-1)]: o.Append(mm(x),mm(y))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(0.3))
        z.SetZoneName(netname); board.Add(z)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    def gnd_pour():
        for z in list(board.Zones()):
            if not z.GetIsRuleArea(): board.Remove(z)     # the router keepouts stay (a retry exports them again)
        if plan['extra'].get('no_pour'): return      # the hub: the bus lines own the back, ground is wired on the front
        pour('GND',GND_LAYER)
    # pre-routed power rails and stubs (from the tile geometry); the router only sees signals.
    # A rail with an eighth field True is hidden from the router (the inside of the sequencer's diode matrix, D045):
    # it is not on the board while the DSN is written and comes back with the others after the import.
    LAY={'F.Cu':pcbnew.F_Cu,'B.Cu':pcbnew.B_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.Cu':pcbnew.In2_Cu}
    hidden=[]
    def add_rails(all=True):
        for r in plan.get('rails',[]):
            net,layer,x1,y1,x2,y2,wd=r[:7]; hide=len(r)>7 and r[7]
            if hide and not all: continue
            t=pcbnew.PCB_TRACK(board); t.SetStart(V(x1,y1)); t.SetEnd(V(x2,y2)); t.SetWidth(mm(wd)); t.SetLayer(LAY[layer]); t.SetNet(netobj[net]); board.Add(t)
            if hide: hidden.append(t)
        for net,x,y in plan.get('vias',[]):
            v=pcbnew.PCB_VIA(board); v.SetPosition(V(x,y)); v.SetDrill(mm(0.4)); v.SetWidth(mm(0.8)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(netobj[net]); board.Add(v)
    def hide_rails():
        for t in hidden: board.Remove(t)
        hidden.clear()
    router=plan['extra'].get('router',{})
    keepouts=[]
    def add_keepouts():
        """Rule areas the router must stay out of (the matrix): exported to the DSN as keepouts, removed again at the end."""
        for x1,y1,x2,y2 in router.get('keepout',[]):
            z=pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
            ls=pcbnew.LSET(); ls.addLayer(pcbnew.F_Cu); ls.addLayer(pcbnew.B_Cu)
            if layers==4: ls.addLayer(pcbnew.In1_Cu)     # the plane layer too; In2 stays open across the matrix (D051)
            z.SetLayerSet(ls)
            o=z.Outline(); o.NewOutline()
            for x,y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]: o.Append(mm(x),mm(y))
            z.SetZoneName('router keepout'); board.Add(z); keepouts.append(z)
        if layers==4 and not router.get('route_in1'):       # the plane layer: no tracks anywhere (vias still pass); a wire keepout in the DSN, so the router never uses In1 (D051; route_in1: the plan lets the router use In1 too, the GND pour fills what is left)
            z=pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(False)
            ls=pcbnew.LSET(); ls.addLayer(pcbnew.In1_Cu); z.SetLayerSet(ls)
            o=z.Outline(); o.NewOutline()
            for x,y in [(0,0),(W,0),(W,H),(0,H)]: o.Append(mm(x),mm(y))
            z.SetZoneName('plane keepout'); board.Add(z); keepouts.append(z)
    def filter_dsn(path):
        """Take the excluded parts (the matrix diodes, whose pads sit on hidden tracks) out of the DSN: their placements
        and their pins. What stays on those nets is what the router has to reach: the row driver pads and the row
        track tails, the column pull-downs and buffers."""
        ex=set(router.get('exclude_refs',[]))
        if not ex: return
        s=open(path).read()
        # D051: the placements stay (their pads are obstacles on every copper layer, so the inner-layer routes thread between the
        # diodes instead of through their pins); only their pins leave the nets, so the router has nothing to route to them
        s=re.sub(r'\b([A-Za-z]+\d+)-\d+\b',lambda m:'' if m.group(1) in ex else m.group(0),s)
        open(path,'w').write(s)
    add_rails()
    pcb=os.path.join(projdir,f'{name}.kicad_pcb'); pcbnew.SaveBoard(pcb,board)
    sync_project(projdir,name,tw,cl)
    print(f'{name}: {len(comps)} parts, {len(nets)} nets, board {W}x{H} mm')
    gnd_pour(); pcbnew.SaveBoard(pcb,board)     # before routing: the router sees GND as a plane and leaves it alone
    if route:
        dsn=os.path.join(projdir,f'{name}.dsn'); ses=os.path.join(projdir,f'{name}.ses')
        best=None
        add_keepouts()
        for attempt in range(1 if ses_file else router.get('attempts',3)):
            hide_rails(); pcbnew.SaveBoard(pcb,board)
            if attempt:     # a retry starts from the saved board, not the in-memory one after the SES import: the DSN of the latter left the router blind to the open pads
                board=pcbnew.LoadBoard(pcb); netobj={n:board.FindNet(n) for n in nets}
            pcbnew.ExportSpecctraDSN(board,dsn); filter_dsn(dsn)
            # pre-routed power (GND/+5V rails, stubs, stitches) is fixed so the router cannot move it; the SES then omits it,
            # and KiCad's SES import replaces all tracks, so the rails are re-added after every import (add_rails below)
            lines=open(dsn).read().split('\n')
            fixed=set(['GND','+5V'])|set(r[0] for r in plan.get('rails',[]))     # every pre-routed net (power, matrix rows and columns) is fixed
            lines=[l.replace('(type route)','(type fix)') if any(f'(net {n})' in l for n in fixed) else l for l in lines]
            # the router's via: 0.6/0.3 (JLCPCB's minimum) whatever the board's netclass says; with 0.8/0.4 it could not drop the last net past the bus header pins on a dense card
            text='\n'.join(lines)
            # (In1 stays "(type signal)": marked "(type power)", freerouting 2.1 and 2.4 could no longer join the drain pads of a tile, three bare
            # transistors on a test board included; the whole-board wire keepout on In1 from add_keepouts keeps the plane layer free of tracks instead)
            for n in router.get('exclude_nets',[]):    # nets the router must leave alone (the sequencer's GND and +5V, D051): their pins leave the network, the pre-routed
                text=re.sub(r'\(net '+re.escape(n)+r'\s*\(pins[^)]*\)',f'(net {n}\n      (pins)',text,count=1)   # rails stay as obstacles; asked to finish power itself around fixed rails, freerouting left 75 of 509 connections open on a test cut against 9
            order=router.get('layer_order')    # freerouting prefers vertical on even DSN layers and horizontal on odd ones (2.5x against), and its own
            if order:                          # autoroute_settings block stops 2.1.0 dead; listing the layers in another order (KiCad maps the SES by name) picks the directions
                blocks={m.group(1):m.group(0) for m in re.finditer(r'    \(layer (\S+)\n      \(type \w+\)\n      \(property\n        \(index \d+\)\n      \)\n    \)\n',text)}
                assert set(order)==set(blocks), (order,list(blocks))
                first=min(text.index(b) for b in blocks.values())
                for b in blocks.values(): text=text.replace(b,'',1)
                text=text[:first]+''.join(re.sub(r'\(index \d+\)',f'(index {k})',blocks[ln]) for k,ln in enumerate(order))+text[first:]
            open(dsn,'w').write(text)
            import shutil; shutil.copy(dsn,dsn+f'.attempt{attempt+1}')      # what the router was given (kept when a connection stayed open)
            if dsn_only: print('DSN written:',dsn); return pcb
            # freerouting's own log goes to <name>.freerouting.log so a long run can be watched
            if ses_file:      # --ses: a session routed outside this run (freerouting 2.1.0 by hand on the exported DSN); imported like the router's own
                import shutil; shutil.copy(ses_file,ses); open(os.path.join(projdir,f'{name}.freerouting.log'),'w').write(f'session imported from {ses_file}\n')
            with open(os.path.join(projdir,f'{name}.freerouting.log'),'a' if ses_file else 'w') as flog:
                if ses_file: pass
                else: jar=os.path.join(os.path.dirname(JAR),router['jar']) if router.get('jar') else JAR      # the plan may pick another freerouting (2.1.0 for the sequencer: 1.9 needs hours per pass there)
                # 2.1.0 honours the pass cap only with its window up (headless it routes until killed) and saves the SES on its own; 2.4.1 (Java 25) runs headless
                new=os.path.basename(jar)>='freerouting-2.4'; flags=(['-Djava.awt.headless=true'] if new else [])
                if not ses_file: subprocess.run([JAVA]+flags+[f"-Xmx{router.get('xmx','4g')}",'-jar',jar,'-de',dsn,'-do',ses,'-mp',str(passes),'-dct','2']+(['-mt','1'] if new else []),stdout=flog,stderr=subprocess.STDOUT,text=True,timeout=router.get('timeout',3*3600))
            class R: stdout=open(os.path.join(projdir,f'{name}.freerouting.log')).read()
            r=R()
            last=[l for l in r.stdout.splitlines() if 'unrouted' in l.lower()]
            m=re.search(r'\((\d+) unrouted',last[-1]) if last else None      # 1.9 "(N unrouted)", 2.1 "(N unrouted and M violations)"
            unrouted=int(m.group(1)) if m else None      # freerouting 1.9 logs no count when it gives up early; KiCad's DRC below is the gate
            print(f'  route attempt {attempt+1}: router reports {unrouted if unrouted is not None else "no unrouted count"}')
            if not os.path.exists(ses): print(r.stdout[-3000:]); raise SystemExit('freerouting produced no SES')
            pcbnew.ImportSpecctraSES(board,ses); os.remove(ses)
            add_rails(); apply_patches(board,plan); gnd_pour(); pcbnew.SaveBoard(pcb,board)
            for _ in range(2):
                if gnd_stitch(board,pcb,netobj,gnd_pour)==0: break
            n=unconnected(pcb)
            if n:       # which connections the router left open (freerouting 1.9 gives up on a few silently; the next attempt starts from these wires)
                for u in json.load(open(pcb.replace('.kicad_pcb','.drc.json'))).get('unconnected_items',[]): print('     open:',' <-> '.join(i['description'] for i in u['items']))
                done=[l for l in r.stdout.splitlines() if 'completed in' in l]; print('     router:',' | '.join(l.split('INFO')[-1].strip()[:60] for l in done[-3:]))
            if best is None or n<best[0]:
                best=(n,pcb.replace('.kicad_pcb','.best.kicad_pcb')); import shutil; shutil.copy(pcb,best[1])
            if n==0: break
        os.remove(dsn)
        if best and best[0]==0:
            for f in glob.glob(dsn+'.attempt*'): os.remove(f)      # (kept when a connection stayed open, for a look at what the router was given)
        if best and best[0]>0:      # keep the best attempt, not the last
            board=pcbnew.LoadBoard(best[1]); netobj={n:board.FindNet(n) for n in nets}
            def gnd_pour():
                for z in list(board.Zones()):
                    if not z.GetIsRuleArea(): board.Remove(z)     # the router keepouts stay (a retry exports them again)
                if plan['extra'].get('no_pour'): return
                pour('GND',GND_LAYER)
        if best and os.path.exists(best[1]): os.remove(best[1])
        for z in [z for z in board.Zones() if z.GetIsRuleArea()]: board.Remove(z)     # the router keepouts (the board reloaded from best has its own copies)
        outline(0); gnd_pour(); pcbnew.SaveBoard(pcb,board)
    sync_project(projdir,name,tw,cl)     # again: SaveBoard rewrites the project file with KiCad's defaults (0.2 mm clearance)
    return pcb

def apply_patches(board,plan):
    """Hand fixes after the router (plan extra.patches): [{'net','layer','remove':[[x0,y0,x1,y1],...],'add':[[x0,y0,x1,y1],...],'width'}].
    A removed segment must match an existing track of that net and layer by its endpoints (0.01 mm); a patch whose segments are not
    all there is reported and skipped, so a re-route that no longer has the flaw is not damaged. The sequencer's v9 route left ENF
    hooked across CFQ_m1 on In2 in one spot (freerouting's own tracks crossing); the patch straightens ENF there."""
    patches=plan['extra'].get('patches',[])
    if not patches: return
    def key(x,y): return (round(x,2),round(y,2))
    # {'net','move_via':[[x,y],[nx,ny]]}: nudge a via (and the ends of its net's tracks that meet it); panelc's M6 via sat 0.48 mm
    # hole-to-hole from M4's, under JLCPCB's 0.5 mm, with every rule the router knew satisfied. Skipped when no via is there.
    for pt in [p for p in patches if 'move_via' in p]:
        (x,y),(nx,ny)=pt['move_via']; old=pcbnew.VECTOR2I(int(x*1e6),int(y*1e6)); new=pcbnew.VECTOR2I(int(nx*1e6),int(ny*1e6)); n=0
        for t in board.GetTracks():
            if t.GetNetname()!=pt['net']: continue
            if t.GetClass()=='PCB_VIA' and (t.GetPosition()-old).EuclideanNorm()<1000: t.SetPosition(new); n+=1
            elif t.GetClass()!='PCB_VIA':
                if (t.GetStart()-old).EuclideanNorm()<1000: t.SetStart(new); n+=1
                if (t.GetEnd()-old).EuclideanNorm()<1000: t.SetEnd(new); n+=1
        print(f"   patch {pt['net']}: via at {x},{y} moved to {nx},{ny} ({n} items)" if n else f"   patch {pt['net']}: no via at {x},{y}, skipped")
    patches=[p for p in patches if 'move_via' not in p]
    # read every track's geometry first: pcbnew loses the SWIG types after the first board.Remove in a process
    tracks=[(t,t.GetLayerName(),t.GetNetname(),{key(t.GetStart().x*1e-6,t.GetStart().y*1e-6),key(t.GetEnd().x*1e-6,t.GetEnd().y*1e-6)}) for t in board.GetTracks() if t.GetClass()!='PCB_VIA']
    todo=[]
    for pt in patches:
        found=[]
        for x0,y0,x1,y1 in pt.get('remove',[]):
            want={key(x0,y0),key(x1,y1)}
            hit=[t for t,l,n,ends in tracks if l==pt['layer'] and n==pt['net'] and ends==want and t not in found]
            if hit: found.append(hit[0])
        if len(found)==len(pt.get('remove',[])): todo.append((pt,found))
        else: print(f"   patch {pt['net']} on {pt['layer']}: {len(found)} of {len(pt['remove'])} segments found, skipped")
    for pt,found in todo:
        net=board.FindNet(pt['net']); lay=getattr(pcbnew,pt['layer'].replace('.','_'))
        for t in found: board.Remove(t)
        for x0,y0,x1,y1 in pt.get('add',[]):
            t=pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(int(x0*1e6),int(y0*1e6))); t.SetEnd(pcbnew.VECTOR2I(int(x1*1e6),int(y1*1e6)))
            t.SetWidth(int(pt.get('width',0.2)*1e6)); t.SetLayer(lay); t.SetNet(net); board.Add(t)
        print(f"   patch {pt['net']} on {pt['layer']}: {len(found)} segments removed, {len(pt.get('add',[]))} added")

def repatch(projdir,name):
    """Apply the plan's patches to the routed board as it is (a route already done), refill the pour, save."""
    pcb=os.path.join(projdir,f'{name}.kicad_pcb'); plan=json.load(open(os.path.join(projdir,f'{name}.plan.json')))
    board=pcbnew.LoadBoard(pcb); apply_patches(board,plan)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones()); pcbnew.SaveBoard(pcb,board); return pcb

def add_silk(board,plan):
    """Board-level silkscreen text from the plan (labels, then the big board name)."""
    for text,x,y,size in plan['silk']+plan['extra'].get('silk',[]):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size),mm(size))); t.SetTextThickness(mm(0.15)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(t)
    for text,x,y,size in plan['extra'].get('silk_big',[]):
        t=pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size),mm(size))); t.SetTextThickness(mm(0.25)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); board.Add(t)

def resilk(projdir,name):
    """--silk: replace the board-level silkscreen text of an already routed board from the plan, without re-routing."""
    pcb=os.path.join(projdir,f'{name}.kicad_pcb'); board=pcbnew.LoadBoard(pcb)
    plan=json.load(open(os.path.join(projdir,f'{name}.plan.json')))
    hide=plan['extra'].get('hide_refs',[])
    for m in board.GetFootprints():          # the plan's hidden reference prefixes apply here too (a board routed before a prefix was added)
        if not any(m.GetReference().startswith(pfx) for pfx in hide): continue
        m.Reference().SetVisible(False)
        for t in m.GraphicalItems():
            t=t.Cast()
            if t.GetLayer()==pcbnew.F_SilkS and isinstance(t,pcbnew.PCB_TEXT): t.SetLayer(pcbnew.F_Fab)
    # (the footprint pass goes first: after board.Remove of a text, pcbnew hands back untyped footprint objects)
    for d in [d for d in board.GetDrawings() if isinstance(d,pcbnew.PCB_TEXT) and d.GetLayer()==pcbnew.F_SilkS]: board.Remove(d)
    add_silk(board,plan); pcbnew.SaveBoard(pcb,board)
    rules=plan['extra'].get('rules',{}); sync_project(projdir,name,rules.get('track',0.25),rules.get('clearance',0.2))
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

def sync_project(projdir,name,tw,cl):
    """kicad-cli reads design rules from <name>.kicad_pro, which ERC or KiCad may have filled with defaults (0.2 mm clearance):
    write the board's rules into it so DRC judges the board by the rules it was routed with."""
    pro=os.path.join(projdir,f'{name}.kicad_pro'); j=json.load(open(pro)) if os.path.exists(pro) else {}
    ds=j.setdefault('board',{}).setdefault('design_settings',{}); r=ds.setdefault('rules',{})
    r.update({'min_clearance':min(cl,0.2),'min_track_width':min(tw,0.25),'min_via_diameter':0.6,'min_through_hole_diameter':0.3,'min_resolved_spokes':1})
    ns=j.setdefault('net_settings',{}); cls=ns.setdefault('classes',[])
    if not cls: cls.append({'name':'Default'})
    cls[0].update({'clearance':cl,'track_width':tw,'via_diameter':0.6,'via_drill':0.3})     # 0.6/0.3 (JLCPCB's minimum): with 0.8/0.4 the router could not drop the last net past the bus header pins on a dense card
    json.dump(j,open(pro,'w'),indent=2)

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
    subprocess.run([K,'pcb','export','pos','--format','csv','--units','mm','--exclude-dnp','-o',os.path.join(fab,f'{name}-pos.csv'),pcb],capture_output=True)
    subprocess.run([K,'sch','export','bom','--fields','Reference,Value,Footprint,${QUANTITY}','--group-by','Value,Footprint','--exclude-dnp','-o',os.path.join(fab,f'{name}-bom.csv'),os.path.join(d,f'{name}.kicad_sch')],capture_output=True)
    for side,fn in [('top',f'{name}-top.png'),('bottom',f'{name}-bottom.png')]:
        subprocess.run([K,'pcb','render','--side',side,'--width','2000','--height','1400','--quality','high','-o',os.path.join(fab,fn),pcb],capture_output=True)
    print('fab outputs in',fab)

if __name__=='__main__':
    projdir,name=sys.argv[1],sys.argv[2]
    passes=int(sys.argv[sys.argv.index("--passes")+1]) if "--passes" in sys.argv else 300
    if '--dsn-only' in sys.argv: build(projdir,name,passes=passes,dsn_only=True); sys.exit(0)     # write the filtered DSN the router would get, and stop
    ses_file=sys.argv[sys.argv.index('--ses')+1] if '--ses' in sys.argv else None                 # import a session routed by hand from that DSN instead of running the router
    pcb=resilk(projdir,name) if '--silk' in sys.argv else repatch(projdir,name) if '--patch' in sys.argv else build(projdir,name,route='--no-route' not in sys.argv,passes=passes,ses_file=ses_file)
    drc(pcb); outputs(pcb,name)
