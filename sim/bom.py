"""Sum the fab BOMs of every routed board (boards/*/fab/*-bom.csv, coupon/fab) into one parts list, as a Markdown table.
    python3 bom.py            all boards
    python3 bom.py --per      one column per board
The table is what docs/order-1.md quotes; run it again after any board changes."""
import csv, glob, os, sys, collections
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..')

def load():
    boards={}
    for f in sorted(glob.glob(os.path.join(ROOT,'boards','*','fab','*-bom.csv')))+glob.glob(os.path.join(ROOT,'coupon','fab','*-bom.csv')):
        name=os.path.basename(os.path.dirname(os.path.dirname(f)))
        c=collections.Counter()
        for r in csv.DictReader(open(f)):
            fp=r['Footprint'].split(':')[-1]; v=r['Value']
            if fp.startswith(('SW_','TestPoint','PinHeader')): v={'SW_':'switch','Tes':'test loop','Pin':'pin header'}[fp[:3]]   # their values are labels, not part numbers
            c[(v,fp)]+=int(r['QUANTITY'])
        boards[name]=c
    return boards

def main():
    boards=load(); per='--per' in sys.argv
    total=collections.Counter()
    for c in boards.values(): total.update(c)
    order=lambda k:(k[1],k[0])
    names=list(boards)
    print("| Part | Footprint |"+("".join(f" {n} |" for n in names) if per else "")+" Total |")
    print("|---|---|"+("---|"*len(names) if per else "")+"---|")
    for k in sorted(total,key=order):
        v,fp=k
        print(f"| {v} | {fp} |"+("".join(f" {boards[n][k] or ''} |" for n in names) if per else "")+f" {total[k]} |")
    print(f"\n{sum(total.values())} parts on {len(names)} boards: "+", ".join(names))

if __name__=='__main__': main()
