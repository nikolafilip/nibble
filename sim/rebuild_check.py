"""Do the builders, run today, still write the boards that are in the repository?

    python3 rebuild_check.py [card ...]          (from sim/; plain python3, kicad-cli; all 26 boards without arguments)

A routed board is never rebuilt for a small change (a rebuild gives the schematic new ids and the router a new run): such a
change is made in place, on the board, the schematic and the plan (pcb.py --silk, --patch, --back-header), and in the
builder, so that the next real rebuild gives the same. This runs every builder into a scratch directory (NIBBLE_CARDS,
SEQ_OUT) and compares what it wrote with what is committed: the plan (every placement, rail, via and label, the router's
settings) and the schematic's netlist (every net's pins, every part's value and footprint). Exit status 1 on a difference."""
import sys,os,json,subprocess,shutil,tempfile
import knet
R=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')); K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
T=tempfile.mkdtemp(prefix='rebuild_'); os.makedirs(T+'/cards'); os.makedirs(T+'/seq')
env=dict(os.environ,NIBBLE_CARDS=T+'/cards',SEQ_OUT=T+'/seq')
B=[('reg%d'%i,['build_reg_card.py',str(i)]) for i in range(4)]+[('alu%d'%i,['build_alu_card.py',str(i)]) for i in range(4)]+[('ctr%d'%i,['build_ctr_card.py',str(i)]) for i in range(8)]+\
  [('memctl',['build_mem_card.py','ctl']),('memslot',['build_mem_card.py','slot']),('panela',['build_panel_card.py','a']),('panelb',['build_panel_card.py','b']),('panelc',['build_panel_card.py','c']),
   ('prog',['build_prog_card.py']),('clock',['build_clock_card.py']),('coupon',['build_coupon_card.py']),('hub',['build_hub_card.py']),('sequencer',['build_sequencer.py'])]
only=sys.argv[1:]; bad=0
def norm(v):
    if isinstance(v,float): return round(v,4)
    if isinstance(v,(list,tuple)): return [norm(x) for x in v]
    if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
    return v
def netl(sch,out):
    subprocess.run([K,'sch','export','netlist','--format','kicadsexpr','-o',out,sch],capture_output=True); n,c=knet.parse(out)
    return {k:sorted(v) for k,v in n.items()},c
for name,cmd in B:
    if only and name not in only: continue
    r=subprocess.run([sys.executable]+cmd,cwd=R+'/sim',env=env,capture_output=True,text=True)
    td=T+'/seq' if name=='sequencer' else f'{T}/cards/{name}'; rd=R+'/boards/03-sequencer' if name=='sequencer' else f'{R}/cards/{name}'
    if not os.path.exists(f'{td}/{name}.plan.json'): print(name,'BUILDER FAILED',r.stderr[-400:]); bad+=1; continue
    a=norm(json.load(open(f'{td}/{name}.plan.json'))); b=norm(json.load(open(f'{rd}/{name}.plan.json'))); msg=[]
    for k in sorted(set(a)|set(b)):
        if k=='silk':
            sa=sorted(map(str,a.get(k,[]))); sb=sorted(map(str,b.get(k,[])))
            if sa!=sb: msg.append(f'silk: {len(set(sa)-set(sb))} only built {sorted(set(sa)-set(sb))[:3]}, {len(set(sb)-set(sa))} only committed {sorted(set(sb)-set(sa))[:3]}')
        elif k in ('rails','vias'):
            sa=sorted(map(str,a.get(k,[]))); sb=sorted(map(str,b.get(k,[])))
            if sa!=sb: msg.append(f'{k}: {len(set(sa)-set(sb))} only built {sorted(set(sa)-set(sb))[:2]}, {len(set(sb)-set(sa))} only committed {sorted(set(sb)-set(sa))[:2]}')
        elif k=='place':
            d=[r for r in set(a[k])|set(b[k]) if a[k].get(r)!=b[k].get(r)]
            if d: msg.append(f'place: {len(d)} differ, e.g. {d[0]} built {a[k].get(d[0])} committed {b[k].get(d[0])}')
        elif a.get(k)!=b.get(k):
            if isinstance(a.get(k),dict) and isinstance(b.get(k),dict):
                dk=[x for x in set(a[k])|set(b[k]) if a[k].get(x)!=b[k].get(x)]; msg.append(f'{k}: keys differ {dk}')
            else: msg.append(f'{k} differs')
    na,ca=netl(f'{td}/{name}.kicad_sch',f'{td}/{name}.net'); nb,cb=netl(f'{rd}/{name}.kicad_sch',f'{T}/{name}_repo.net')
    if na!=nb:
        dn=[n for n in set(na)|set(nb) if na.get(n)!=nb.get(n)]; msg.append(f'netlist: {len(dn)} nets differ, e.g. {dn[0]}: built {na.get(dn[0])} committed {nb.get(dn[0])}')
    if ca!=cb: msg.append(f'parts: {len([r for r in set(ca)|set(cb) if ca.get(r)!=cb.get(r)])} differ')
    print(f'{name:10s}','the builder writes what is committed' if not msg else 'DIFFERS: '+' | '.join(msg)); bad+=bool(msg)
shutil.rmtree(T,ignore_errors=True)
print('every builder writes what is committed' if not bad else f'{bad} boards differ'); sys.exit(1 if bad else 0)
