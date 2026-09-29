"""The print as the fab gets it: a board's pads, mask openings and silkscreen, front and back, without the parts on it.

    python3 silk_proof.py coupon reg0 sequencer ...        (from sim/; kicad-cli, and Chrome for the PNGs)

The 3D render in fab/ puts the parts on the board, and a part's shadow over a name looks like a name that is not there. This
writes out/proof/<board>-front.png and -back.png (the back as it is seen from the back), 20 pixels a millimetre, the silkscreen
in black: what to look at before an order, after any change of a label. The gate's `silk` check counts and measures; this is
for the eyes."""
import sys, os, subprocess
import assembly
HERE=os.path.dirname(os.path.abspath(__file__)); K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'; PX=20
def proof(name):
    B=assembly.board(name); out=os.path.join(HERE,'out','proof'); os.makedirs(out,exist_ok=True); done=[]
    for face,layers,extra in (('front','F.Cu,F.Mask,F.SilkS,Edge.Cuts',[]),('back','B.Cu,B.Mask,B.SilkS,Edge.Cuts',['--mirror'])):
        svg=os.path.join(out,f'{name}-{face}.svg'); png=svg[:-3]+'png'; html=svg[:-3]+'html'
        subprocess.run([K,'pcb','export','svg','--layers',layers,'--mode-single','--page-size-mode','2','--exclude-drawing-sheet']+extra+['-o',svg,os.path.join(B['dir'],f'{name}.kicad_pcb')],capture_output=True)
        s=open(svg).read().replace('#F2EDA1','#000000').replace('#E8B2A7','#000000')      # KiCad's pale silkscreen colours, front and back
        open(svg,'w').write(s); w,h=int(B['size'][0]*PX),int(B['size'][1]*PX)
        open(html,'w').write(f'<html><body style="margin:0;background:#fff"><img src="{os.path.basename(svg)}" style="width:{w}px;height:{h}px"></body></html>')
        if os.path.exists(CHROME):
            subprocess.run([CHROME,'--headless=new','--disable-gpu','--hide-scrollbars',f'--window-size={w},{h}',f'--screenshot={png}','file://'+html],capture_output=True); done.append(png)
        os.remove(html)
    return done
if __name__=='__main__':
    if len(sys.argv)<2: print(__doc__); sys.exit(2)
    for n in sys.argv[1:]: print(n,' '.join(os.path.relpath(p,HERE) for p in proof(n)))
