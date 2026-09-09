import sys,json; sys.path.insert(0,'.')
import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, tb
outdir=sys.argv[1]
t=np.load(f"{outdir}/e2e_t.npy"); S=np.load(f"{outdir}/e2e_sig.npy"); probes=json.load(open(f"{outdir}/probes.json")); sig={n:S[i] for i,n in enumerate(probes)}
res=json.load(open(f"{outdir}/e2e_result.json")); rows=res['rows']
src,checks,tend,windows=tb.build_stimulus(tb.sequence())
ms=1e3
def strip(ax,names,t0,t1,shade=True,head=0):
    i0,i1=np.searchsorted(t,t0),np.searchsorted(t,t1)
    n=len(names)
    for k,nm in enumerate(names):
        y=sig[nm][i0:i1]; off=(n-1-k)*6
        ax.plot(t[i0:i1]*ms,y+off,lw=0.8,color='C0' if nm.startswith(('OUT','DIV')) else ('C3' if nm in('CLOCK','MEMCLK') else 'C2'))
        ax.axhline(off,color='#ddd',lw=0.5,zorder=0)
        ax.text(t0*ms-0.01*(t1-t0)*ms,off+2.5,nm,ha='right',va='center',fontsize=8)
    ax.set_xlim(t0*ms,t1*ms); ax.set_ylim(-1,n*6+head); ax.set_yticks([]); ax.set_xlabel('time [ms]')
    for sp in ('top','right','left'): ax.spines[sp].set_visible(False)
# ---------- Figure 1: whole sequence ----------
names=['CLOCK','START','OP1','OP0','OUT_SIGN','OUT_B5','OUT_B4','OUT_B3','OUT_B2','OUT_B1','OUT_B0','DIV0']
fig,ax=plt.subplots(figsize=(22,9.5)); strip(ax,names,0,t[-1],head=7)
for (t0,t1,op,a,b),r in zip(windows,rows):
    ax.axvspan(t0*ms,t1*ms,color='C1' if op in('MUL','DIV') else 'C0',alpha=0.06)
    ax.axvline(t0*ms,color='#999',lw=0.5,ls=':')
    sym={'ADD':'+','SUB':'-','MUL':'x','DIV':'/'}[op]
    ax.text((t0+t1)/2*ms,len(names)*6+6.5,f"{a} {sym} {b}\n= {r[4]}\n{'PASS' if r[5]=='True' else 'FAIL'}",ha='center',va='top',fontsize=8,
            color='green' if r[5]=='True' else 'red',fontweight='bold')
ax.set_title("End-to-end transient simulation of the KiCad project (kicad-cli netlist -> ngspice): memory register contents after each operation\n"
             "blue = ADD/SUB windows (3 clocks), orange = MUL/DIV windows (START, 5 sequencer clocks, store).  Memory = OUT_SIGN, OUT_B5..OUT_B0 (DIV: OUT_B2..0 quotient, OUT_B5..3 remainder)",fontsize=10)
fig.tight_layout(); fig.savefig(f"{outdir}/tran_overview.png",dpi=110); plt.close(fig)
# ---------- Figure 2/3: zoom on one MUL and one DIV ----------
def zoom(idx,fname,title):
    t0,t1,op,a,b=windows[idx]
    names=['CLOCK','START','L','T1','T2','T3','DN','MEMCLK','A2','A1','A0','EB2','EB1','EB0','S3','S2','S1','S0','P5','P4','P3','P2','P1','P0','OUT_B5','OUT_B4','OUT_B3','OUT_B2','OUT_B1','OUT_B0']
    fig,ax=plt.subplots(figsize=(16,13)); strip(ax,names,t0-0.02e-3,t1+0.02e-3,head=6)
    edges=np.arange(tb.EDGE,t[-1],tb.T); edges=[e for e in edges if t0<e<t1]
    labels=['L<-1','P<-load A','step 1','step 2','step 3','store','']
    for e,l in zip(edges,labels):
        ax.axvline(e*ms,color='#bbb',lw=0.6,ls='--'); ax.text(e*ms+0.002,len(names)*6+5.5,l,va='top',ha='left',fontsize=8,color='#555')
    # annotate P value after each edge
    for e in edges:
        i=np.searchsorted(t,e+40e-6); p=sum(tb.bit(sig[f'P{k}'][i])<<k for k in range(6))
        ax.text((e+40e-6)*ms,(len(names)-1-names.index('P5'))*6+5.2,f"P={p:06b}",fontsize=7,ha='center',color='C2')
    ax.set_title(title,fontsize=10); fig.tight_layout(); fig.savefig(f"{outdir}/{fname}",dpi=110); plt.close(fig)
mi=[i for i,w in enumerate(windows) if w[2]=='MUL' and w[3]==7 and w[4]==7][0]
zoom(mi,"tran_mul_7x7.png","MUL 7 x 7 = 49: P is loaded with A=7 (P[2:0]), then three shift-add steps using the root adder (A operand = P[5:3], B = 7 when P0=1), result P=110001b=49 stored into OUT_B5..0")
di=[i for i,w in enumerate(windows) if w[2]=='DIV' and w[3]==7 and w[4]==2][0]
zoom(di,"tran_div_7by2.png","DIV 7 / 2: restoring division, three shift-subtract steps (A operand = P[4:2], B = 2 with SUB=1); result P=001011b -> quotient 3 (P[2:0]), remainder 1 (P[5:3])")
# ---------- Figure 4: the two fixed bugs in ADD/SUB ----------
names=['CLOCK','MEMCLK','A2','A1','A0','EB2','EB1','EB0','SUB','S3','S2','S1','S0','SIG','SIGB','REG_D3','REG_D2','REG_D1','REG_D0','OUT_SIGN','OUT_B3','OUT_B2','OUT_B1','OUT_B0']
fig,ax=plt.subplots(figsize=(16,11)); t0=windows[2][0]; t1=windows[3][1]; strip(ax,names,t0-0.02e-3,t1+0.02e-3,head=6)
for i in (2,3):
    w=windows[i]; ax.axvline(w[0]*ms,color='#999',lw=0.6,ls=':'); ax.text((w[0]+w[1])/2*ms,len(names)*6+5.5,f"SUB {w[3]} - {w[4]} = {rows[i][4]}",ha='center',va='top',fontsize=9,fontweight='bold')
ax.set_title("Subtraction after the converter fix: 7-5 stores +2 (original design stored 13: converter XORed with SUB instead of the sign, and carry-out leaked into bit 3), 2-5 stores -3",fontsize=10)
fig.tight_layout(); fig.savefig(f"{outdir}/tran_sub_fix.png",dpi=110); plt.close(fig)
print("plots written")
