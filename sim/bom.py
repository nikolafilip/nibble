"""Sum the fab BOMs of every routed card (cards/*/fab/*-bom.csv, the sequencer from boards/03-sequencer) into one parts
list for the machine, as a Markdown table; the slot and program cards counted as many times as the machine needs.
    python3 bom.py            the machine as cards
    python3 bom.py --per      one column per card
    python3 bom.py --boards   the nine boards instead
The table is what docs/order-1.md quotes; run it again after any board changes."""
import csv, glob, os, sys, collections
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..')

COPIES={'memslot':8,'prog':20}      # cards built more than once: eight slot pairs; program cards for the longest program (sort, 80 words)
def load(cards=True):
    """The BOM of every routed board or card, multiplied by the copies the machine needs (cards: one of each, the slot
    and program cards as COPIES; the sequencer from boards/03-sequencer; the coupon once)."""
    boards={}
    if cards: files=sorted(glob.glob(os.path.join(ROOT,'cards','*','fab','*-bom.csv')))+glob.glob(os.path.join(ROOT,'boards','03-sequencer','fab','*-bom.csv'))
    else: files=sorted(glob.glob(os.path.join(ROOT,'boards','*','fab','*-bom.csv')))+glob.glob(os.path.join(ROOT,'coupon','fab','*-bom.csv'))
    for f in files:
        name=os.path.basename(os.path.dirname(os.path.dirname(f)))
        c=collections.Counter()
        for r in csv.DictReader(open(f)):
            fp=r['Footprint'].split(':')[-1]; v=r['Value']
            if fp.startswith(('SW_','TestPoint','PinHeader','IDC-Header','USB_','Fuse','Potentiometer')): v={'SW_':'switch','Tes':'test loop','Pin':'pin header','IDC':'IDC header','USB':'USB-B socket','Fus':'polyfuse','Pot':'pot'}[fp[:3]]   # their values are labels, not part numbers
            c[(v,fp)]+=int(r['QUANTITY'])*COPIES.get(name,1)
        boards[name]=c
    return boards

def main():
    boards=load(cards='--boards' not in sys.argv); per='--per' in sys.argv
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
