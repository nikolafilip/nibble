import sys,time,json; sys.path.insert(0,'.')
import tb
op=sys.argv[1]; netfile=sys.argv[2]; tag=sys.argv[3]
seq=[(op,a,b) for a in range(8) for b in range(8)]
tb.sequence=lambda: seq
root=[l.rstrip('\n') for l in open(netfile)]
t0=time.time()
t,sig,checks,windows=tb.run(root,tag,'.',step='1u')
ok,rows=tb.evaluate(t,sig,checks)
fails=[r for r in rows if not r[5]]
json.dump(dict(op=op,ok=ok,n=len(rows),fails=[list(map(str,r)) for r in fails],sim_s=time.time()-t0),open(f'{tag}.json','w'))
print(op,"ALL PASS" if ok else f"{len(fails)} FAIL", "%.0fs"%(time.time()-t0))
for r in fails: print(r)
