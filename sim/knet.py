"""Parse a kicad-cli kicadsexpr netlist into {net: [(ref,pin),...]} and {ref: (value, footprint)}."""
import re
def parse(path):
    s=open(path).read()
    nets={}
    for m in re.finditer(r'\(net\s*\(code "\d+"\)\s*\(name "([^"]+)"\)(.*?)\n\t\t\)',s,re.S):
        nets[m.group(1)]=re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)',m.group(2))
    comps={}
    for m in re.finditer(r'\(comp\s*\(ref "([^"]+)"\)(.*?)\n\t\t\)',s,re.S):
        b=m.group(2); v=re.search(r'\(value "([^"]*)"\)',b); f=re.search(r'\(footprint "([^"]*)"\)',b)
        comps[m.group(1)]=(v.group(1) if v else '', f.group(1) if f else '')
    return nets,comps
if __name__=='__main__':
    import sys; nets,comps=parse(sys.argv[1]); print(len(nets),'nets',len(comps),'components')
    for n in sys.argv[2:]: print(n,len(nets.get(n,[])),sorted(nets.get(n,[]))[:16])
    print('single-node nets:',[n for n,v in nets.items() if len(v)<2][:30])
