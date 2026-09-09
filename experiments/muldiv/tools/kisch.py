"""Minimal KiCad schematic S-expression parser with source offsets + geometry/connectivity."""
import re, math, collections

class Node(list):
    __slots__=('start','end')
    def __init__(self, items=(), start=0, end=0):
        super().__init__(items); self.start=start; self.end=end
    @property
    def tag(self): return self[0] if self and isinstance(self[0],str) else None
    def find_all(self, tag):
        return [c for c in self if isinstance(c,Node) and c.tag==tag]
    def find(self, tag):
        for c in self:
            if isinstance(c,Node) and c.tag==tag: return c
        return None
    def prop(self, name):
        for c in self.find_all('property'):
            if c[1]==name: return c[2]
        return None
    def at(self):
        a=self.find('at'); 
        return (float(a[1]), float(a[2]), float(a[3]) if len(a)>3 else 0.0)

def parse(text):
    i=0; n=len(text); stack=[]; root=None
    while i<n:
        c=text[i]
        if c in ' \t\r\n': i+=1; continue
        if c=='(':
            node=Node(start=i); 
            if stack: stack[-1].append(node)
            else: root=node
            stack.append(node); i+=1; continue
        if c==')':
            node=stack.pop(); node.end=i+1; i+=1; continue
        if c=='"':
            j=i+1
            while True:
                if text[j]=='\\': j+=2; continue
                if text[j]=='"': break
                j+=1
            stack[-1].append(text[i+1:j]); i=j+1; continue
        j=i
        while j<n and text[j] not in ' \t\r\n()': j+=1
        stack[-1].append(text[i:j]); i=j
    return root

def rot(x,y,deg):
    r=math.radians(deg); c=math.cos(r); s=math.sin(r)
    return (x*c - y*s, x*s + y*c)

class Sch:
    def __init__(self, text):
        self.text=text
        self.root=parse(text)
        self.libpins={}
        for ls in self.root.find('lib_symbols').find_all('symbol'):
            pins=[]
            for sub in ls.find_all('symbol'):
                for p in sub.find_all('pin'):
                    a=p.find('at'); name=p.find('name')[1]; num=p.find('number')[1]
                    pins.append((num,name,float(a[1]),float(a[2])))
            self.libpins[ls[1]]=pins
        self.symbols=self.root.find_all('symbol')
        self.wires=self.root.find_all('wire')
        self.labels=self.root.find_all('label')+self.root.find_all('global_label')
        self.junctions=self.root.find_all('junction')
    def pin_coords(self, sym):
        lib=sym[1][1] if sym.find('lib_id') is None else sym.find('lib_id')[1]
        x,y,ang=sym.at()
        mirror=sym.find('mirror'); m=mirror[1] if mirror else None
        out={}
        for num,name,px,py in self.libpins[lib]:
            lx,ly=px,py
            if m=='x': ly=-ly
            if m=='y': lx=-lx
            rx,ry=rot(lx,ly,ang)
            out[num]=(round(x+rx,2), round(y-ry,2), name)
        return out

def key(p): return (round(p[0],2), round(p[1],2))

class UF:
    def __init__(self): self.p={}
    def f(self,a):
        self.p.setdefault(a,a)
        while self.p[a]!=a:
            self.p[a]=self.p[self.p[a]]; a=self.p[a]
        return a
    def u(self,a,b): self.p[self.f(a)]=self.f(b)

def on_segment(p,a,b):
    (px,py),(ax,ay),(bx,by)=p,a,b
    if abs((bx-ax)*(py-ay)-(by-ay)*(px-ax))>1e-3: return False
    return min(ax,bx)-1e-3<=px<=max(ax,bx)+1e-3 and min(ay,by)-1e-3<=py<=max(ay,by)+1e-3

def connectivity(s):
    """Returns (uf, pins) where pins = list of (ref, pinnum, pinname, xy, symbol). Nodes are xy keys."""
    uf=UF(); segs=[]
    for w in s.wires:
        pts=[key((float(xy[1]),float(xy[2]))) for xy in w.find('pts').find_all('xy')]
        for a,b in zip(pts,pts[1:]):
            uf.u(a,b); segs.append((a,b))
    pins=[]
    for sym in s.symbols:
        ref=sym.prop('Reference')
        for num,(x,y,name) in s.pin_coords(sym).items():
            pins.append((ref,num,name,key((x,y)),sym)); uf.f(key((x,y)))
    for l in s.labels:
        x,y,_=l.at(); uf.f(key((x,y)))
    # T-junction: any node lying on the middle of a segment
    nodes=list(uf.p.keys())
    for a,b in segs:
        for nd in nodes:
            if nd!=a and nd!=b and on_segment(nd,a,b): uf.u(nd,a)
    return uf,pins

def netnames(s, uf):
    """map root-node -> set of label names (global/local/power)"""
    names=collections.defaultdict(set)
    for l in s.labels:
        x,y,_=l.at(); names[uf.f(key((x,y)))].add(('G' if l.tag=='global_label' else 'L')+':'+l[1])
    for sym in s.symbols:
        lib=sym.find('lib_id')[1]
        if lib.startswith('power:'):
            for num,(x,y,name) in s.pin_coords(sym).items():
                names[uf.f(key((x,y)))].add('P:'+sym.prop('Value'))
    return names
