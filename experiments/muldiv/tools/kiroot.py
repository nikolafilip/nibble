"""Apply the root-sheet edit plan as text edits on Untitled.kicad_sch."""
import sys, re, collections; sys.path.insert(0,'.')
from kisch import *
import kiw, devnet

def apply(root_path, out_path, sub_uuid, tb_uuid):
    plan,s,uf,pins=devnet.root_edit_plan()
    text=s.text
    edits=[]   # (start,end,replacement)
    byref={sym.prop('Reference'):sym for sym in s.symbols}
    def delete_node(n):
        # include preceding whitespace up to previous newline
        st=n.start
        while st>0 and text[st-1] in ' \t': st-=1
        if st>0 and text[st-1]=='\n': st-=1
        edits.append((st,n.end,''))
    def replace_in_node(n,old,new,count=1):
        seg=text[n.start:n.end]; assert old in seg,(old,seg[:200])
        edits.append((n.start,n.end,seg.replace(old,new,count)))
    deleted=set(plan['delete_sources'])
    for e in plan['encoder']: deleted|=set(e['delete'])
    deleted_pts=set()
    for ref in deleted:
        sym=byref[ref]; delete_node(sym)
        for num,(x,y,name) in s.pin_coords(sym).items(): deleted_pts.add(key((x,y)))
    for r in plan['rename_labels']:
        node=[l for l in s.labels if l.find('uuid')[1]==r['uuid']][0]
        replace_in_node(node,f'(global_label "{r["old"]}"',f'(global_label "{r["new"]}"')
    for ref,val in plan['power_values']:
        replace_in_node(byref[ref],'(property "Value" "+5V"' if val in('Y2','X5') else '(property "Value" "SUB"',f'(property "Value" "{val}"')
    for ref in plan['pullup_22k']:
        replace_in_node(byref[ref],'(property "Value" "4.7k"','(property "Value" "2.2k"')
    for old,new in plan['rename_local']:
        for l in s.labels:
            if l.tag=='label' and l[1]==old: replace_in_node(l,f'(label "{old}"',f'(label "{new}"')
    for t in s.root.find_all('text'):
        if t[1].startswith('.tran') or t[1].startswith('.ic'): delete_node(t)
    # ---- new elements ----
    add=''
    new_label_pts=set()
    def gl(name,x,y,rot,shape):
        nonlocal add; add+=kiw.glabel(name,x,y,rot,shape); new_label_pts.add(key((x,y)))
    for e in plan['encoder']:
        n,(x,y)=e['label_in']; gl(n,x,y,0,'output')
        n,(x,y)=e['label_out']; gl(n,x,y,0,'input')
    n,(x,y)=plan['clock_label']; gl(n,x,y,270,'input')
    for l in s.labels:
        if l.tag=='label' and (l[1] in ('S0','S1','S2','S3') or re.fullmatch(r'[XY][1-7]',l[1])) and l[1] not in ('Y2','X5'):
            x,y,rot=l.at(); gl(l[1],x,y,int(rot),'output' if l[1][0]=='S' else 'input'); delete_node(l)   # convert local -> global
    add+=kiw.sheet("MULDIV","muldiv.kicad_sch",2540,63.5,152.4,50.8,"2",sub_uuid)
    add+=kiw.sheet("TESTBENCH","testbench.kicad_sch",2540,190.5,152.4,50.8,"3",tb_uuid)
    add+=kiw.text("MULDIV sheet: multiply/divide extension (re-uses this sheet's adder).  TESTBENCH sheet: keypad/op-code/clock stimulus + .tran directive.\nRoot-sheet changes: keypad-encoder output inverters for A0..A2 / EB0..EB2 moved into MULDIV (operand muxes); memory register D inputs renamed REG_D0..3 / REG_DS;\nclock source moved to TESTBENCH (MEMCLK is gated in MULDIV); converter XOR control SUB -> SIGB (bug fix); S0..S3 and OUT_B0/OUT_B1 pull-ups 4.7k -> 2.2k (fan-out).",2540,40.64,1.6)
    # ---- dangling wire cleanup ----
    wires=s.wires; wsegs=[]
    for w in wires:
        pts=[key((float(xy[1]),float(xy[2]))) for xy in w.find('pts').find_all('xy')]
        wsegs.append((w,pts[0],pts[1]))
    remaining_pins=collections.Counter()
    for ref,num,name,xy,sym in pins:
        if ref not in deleted: remaining_pins[xy]+=1
    label_pts=set(key(l.at()[:2]) for l in s.labels)|new_label_pts
    alive=[True]*len(wsegs)
    def attached(p,skip):
        if remaining_pins[p] or p in label_pts: return True
        for i,(w,a,b) in enumerate(wsegs):
            if i==skip or not alive[i]: continue
            if p==a or p==b or on_segment(p,a,b): return True
        return False
    def has_label_on(i):
        w,a,b=wsegs[i]
        return any(on_segment(lp,a,b) for lp in label_pts)
    frontier=set(deleted_pts); removed=0
    while frontier:
        nxt=set()
        for i,(w,a,b) in enumerate(wsegs):
            if not alive[i]: continue
            if (a in frontier or b in frontier) and not has_label_on(i) and (not attached(a,i) or not attached(b,i)):
                alive[i]=False; removed+=1; delete_node(w); nxt.add(a); nxt.add(b)
        frontier=nxt
    # junctions with nothing left
    for j in s.junctions:
        p=key(j.at()[:2])
        if p in deleted_pts and not attached(p,-1): delete_node(j)
    # apply edits
    edits.sort(key=lambda e:e[0])
    for i in range(1,len(edits)): assert edits[i][0]>=edits[i-1][1], "overlapping edits"
    out=[]; pos=0
    for st,en,rep in edits:
        out.append(text[pos:st]); out.append(rep); pos=en
    out.append(text[pos:])
    new=''.join(out)
    # insert new elements before sheet_instances
    k=new.rfind('\t(sheet_instances')
    new=new[:k]+add+new[k:]
    open(out_path,'w').write(new)
    return plan, removed

if __name__=='__main__':
    sub_uuid,tb_uuid=open('uuids.txt').read().split()
    plan,nw=apply('/Users/nikolafilip/Documents/Calculator/Untitled.kicad_sch','out_root.kicad_sch',sub_uuid,tb_uuid)
    print("wires removed",nw)
