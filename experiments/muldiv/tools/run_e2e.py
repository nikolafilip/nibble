"""E2E: take the netlist exactly as exported by kicad-cli from the project, add only a .control block to dump data, simulate, check, plot."""
import sys,time,subprocess,json,os; sys.path.insert(0,'.')
import numpy as np, tb
netlist=sys.argv[1]; outdir=sys.argv[2]; os.makedirs(outdir,exist_ok=True)
lines=[l.rstrip('\n') for l in open(netlist) if l.strip() and l.strip()!='.end']
probes=tb.PROBE+['SIGB','SUB2','ENL','KSEL','TMB','TDB','IDLE','QD','REG_D0','REG_D1','REG_D2','REG_D3','REG_DS']
lines+=[".control","set filetype=ascii","run",f"wrdata {outdir}/e2e.txt "+" ".join(f"v({n})" for n in probes),"quit",".endc",".end"]
open(f"{outdir}/e2e_run.cir",'w').write("\n".join(lines)+"\n")
t0=time.time(); r=subprocess.run(["ngspice","-b",f"{outdir}/e2e_run.cir"],capture_output=True,text=True); open(f"{outdir}/ngspice.log",'w').write(r.stdout+r.stderr)
d=np.loadtxt(f"{outdir}/e2e.txt"); t=d[:,0]; sig={n:d[:,2*k+1] for k,n in enumerate(probes)}
src,checks,tend,windows=tb.build_stimulus(tb.sequence())
ok,rows=tb.evaluate(t,sig,checks)
print("sim %.0fs, %d samples, tran end %.4g"%(time.time()-t0,len(t),t[-1]))
for op,a,b,want,got,p,tc in rows: print(f"{op} {a},{b}: want {want:14s} got {got:14s} {'PASS' if p else 'FAIL'}")
print("RESULT:","ALL PASS" if ok else "FAILURES")
lv=tb.levels(t,sig,probes,0.4e-3)
new_nets=[n for n in probes if n not in('OUT_SIGN','OUT_B3','OUT_B2','OUT_B1','OUT_B0','CLOCK','START','OP0','OP1','S3','S2','S1','S0','SIG','SUB','A0','A1','A2','EB0','EB1','EB2')]
wh=min((v[0],n) for n,v in lv.items() if n in new_nets and v[0] is not None); wl=max((v[1],n) for n,v in lv.items() if n in new_nets and v[1] is not None)
print("new-logic levels: worst high %.2f V (%s), worst low %.2f V (%s)"%(wh[0],wh[1],wl[0],wl[1]))
mem=[n for n in ('OUT_SIGN','OUT_B3','OUT_B2','OUT_B1','OUT_B0')]
print("root memory bits: worst high %.2f V, worst low %.2f V"%(min(lv[n][0] for n in mem if lv[n][0] is not None), max(lv[n][1] for n in mem if lv[n][1] is not None)))
json.dump(dict(ok=ok,rows=[list(map(str,r)) for r in rows],levels={n:list(map(lambda x: None if x is None else float(x),v)) for n,v in lv.items()}),open(f"{outdir}/e2e_result.json",'w'),indent=1)
np.save(f"{outdir}/e2e_t.npy",t); np.save(f"{outdir}/e2e_sig.npy",np.array([sig[n] for n in probes])); json.dump(probes,open(f"{outdir}/probes.json",'w'))
