import sys, collections, re
def load(fn):
    R=[];Q=[]
    for l in open(fn):
        t=l.split()
        if not t: continue
        if t[0][0]=='R' and len(t)==4: R.append(tuple(t))
        if t[0][0]=='Q' and len(t)==5: Q.append(tuple(t))
    return R,Q
def gates(R,Q):
    byC=collections.defaultdict(list)
    for q in Q: byC[q[1]].append(q)
    drv={}
    for n,a,b,v in R:
        if v=='10k':
            for q in Q:
                if q[2]==a: drv[q[0]]=b
                elif q[2]==b: drv[q[0]]=a
    pull={}
    for n,a,b,v in R:
        if v in('4.7k','2.2k'): pull[b if a=='+5V' else a]=v
    def chain(q):
        names=[drv.get(q[0],'?')]; e=q[3]
        while e!='GND':
            nxt=byC.get(e,[]); 
            if len(nxt)!=1: names.append('?'); break
            q=nxt[0]; names.append(drv.get(q[0],'?')); e=q[3]
        return tuple(names)
    g={}
    for out,pu in pull.items():
        g[out]=(pu,tuple(sorted(chain(q) for q in byC.get(out,[]))))
    return g
def canon(n):
    n=n.lstrip('/')
    return n
def wl_hash(g,rounds=6):
    """Weisfeiler-Lehman style hashing of gate graph; returns multiset of hashes and per-net hash"""
    h={o:hash((v[0],len(v[1]),tuple(len(c) for c in v[1]))) for o,v in g.items()}
    prim=set()
    for o,v in g.items():
        for c in v[1]:
            for n in c:
                if n not in g: prim.add(n)
    for p in prim: h[p]=hash(('PRIM',canon(p)))
    for _ in range(rounds):
        h2={}
        for o,v in g.items():
            h2[o]=hash((v[0],tuple(sorted(tuple(h.get(n,0) for n in c) for c in v[1]))))
        for p in prim: h2[p]=h[p]
        h=h2
    return h
a=gates(*load(sys.argv[1])); b=gates(*load(sys.argv[2]))
print("gates",len(a),len(b))
ha=wl_hash(a); hb=wl_hash(b)
ca=collections.Counter(ha.values()); cb=collections.Counter(hb.values())
onlya=ca-cb; onlyb=cb-ca
print("hash multiset diff: only in A:",sum(onlya.values()),"only in B:",sum(onlyb.values()))
inv_a=collections.defaultdict(list); inv_b=collections.defaultdict(list)
for k,v in ha.items(): inv_a[v].append(k)
for k,v in hb.items(): inv_b[v].append(k)
for hsh in list(onlya)[:12]: print("A:",inv_a[hsh][:4], a.get(inv_a[hsh][0]))
for hsh in list(onlyb)[:12]: print("B:",inv_b[hsh][:4], b.get(inv_b[hsh][0]))
# named nets check
named=[n for n in set(map(canon,a))|set(map(canon,b)) if not n.startswith('Net-') and '_bs' not in n and '_st' not in n]
