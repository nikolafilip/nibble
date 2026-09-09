"""Transient plots for board 01 from a tb_alu run. Usage: python3 plots_alu.py out/kicad_demo_TYP.dat outdir"""
import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, tb_alu, os
dat,outdir=sys.argv[1],sys.argv[2]; os.makedirs(outdir,exist_ok=True)
names=open(dat).readline().split(); a=np.loadtxt(dat,skiprows=1); t=a[:,0]*1e3; col={n[2:-1]:a[:,k] for k,n in enumerate(names) if n.startswith('v(')}
cases=tb_alu.demo_cases(); T=tb_alu.T*1e3
sig=[('a3','A3'),('a2','A2'),('a1','A1'),('a0','A0'),('b3','B3'),('b2','B2'),('b1','B1'),('b0','B0'),('sub','SUB'),('eo','EO'),
     ('s3','S3'),('s2','S2'),('s1','S1'),('s0','S0'),('cf','CF'),('zf','ZF'),('bus3#','BUS3#'),('bus2#','BUS2#'),('bus1#','BUS1#'),('bus0#','BUS0#')]
fig,ax=plt.subplots(figsize=(16,11)); off=0
for k,(n,lab) in enumerate(reversed(sig)):
    y=col[n]/5*0.8+off; c='#1f5f8b' if lab.startswith(('A','B')) and lab not in('BUS3#','BUS2#','BUS1#','BUS0#') else ('#7a4a00' if lab in('SUB','EO') else ('#0a7f3f' if lab[0]=='S' or lab in('CF','ZF') else '#8b1f1f'))
    ax.plot(t,y,color=c,lw=1); ax.text(-0.15,off+0.4,lab,ha='right',va='center',fontsize=9,family='monospace'); off+=1
for k,(A,B,s,eo) in enumerate(cases):
    S,cf,zf=tb_alu.expected(A,B,s)
    ax.axvline(k*T,color='0.85',lw=0.6)
    ax.text((k+0.5)*T,off+0.3,f"{A}{'-' if s else '+'}{B}\n={S}{' C' if cf else ''}{' Z' if zf else ''}{'' if eo else '\nEO=0'}",ha='center',va='bottom',fontsize=8,family='monospace')
ax.set_xlim(0,len(cases)*T); ax.set_ylim(-0.3,off+2.5); ax.set_yticks([]); ax.set_xlabel('time (ms)')
ax.set_title('Board 01 ALU, kicad-cli exported netlist, ngspice transient: inputs (blue/brown), result and flags (green), bus lines active-low (red)')
for s_ in ('top','right','left'): ax.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(f'{outdir}/tran_alu_demo.png',dpi=110)
# zoom: ripple carry on case 5 (15+1) and case 1 (7-5)
fig,axs=plt.subplots(1,2,figsize=(14,5))
for ax,(k,title) in zip(axs,[(5,'15 + 1: carry ripples through all four bits, S=0 CF=1 ZF=1'),(1,'7 - 5 = 2 (the origin design stored 13 here)')]):
    t0=k*T; m=(t>=t0-0.01)&(t<=t0+0.12)
    for n,lab,c in [('s0','S0','#0a7f3f'),('s1','S1','#2aa060'),('s2','S2','#4bbf80'),('s3','S3','#6cd9a0'),('cf','CF','#d08000'),('zf','ZF','#8b1f1f')]:
        ax.plot((t[m]-t0)*1e3,col[n][m],label=lab,color=c,lw=1.2)
    ax.set_xlabel('us after the inputs change'); ax.set_ylabel('V'); ax.set_title(title,fontsize=10); ax.legend(fontsize=8,ncol=3); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(f'{outdir}/tran_alu_zoom.png',dpi=110)
print('ok')
