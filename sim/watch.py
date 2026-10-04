"""The watcher: what the simulation queue is doing, in a few lines.

    python3 watch.py

Reads the logs of the queues in out/ (LOGS below: the log, what it is, how many runs it has), counts the runs that landed
and the ones that failed, and looks at the machine: the ngspice decks that are running and for how long, memory, swap, disk.
Says ATTENTION first when something wants a person: a run failed, work is left and nothing is running, more than two decks
are running, swap is in use by the gigabyte, or the disk is nearly full. Changes nothing."""
import os, re, subprocess, time
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'out')
LOGS=[('starts_hold.log','starts with the hold-off',62),('gate25_cross2_hold.log','crosstalk gate with the hold-off',12),
      ('gate26_smoke.log','gate 26: smoke, 12 ticks',13),('gate26_TYP.log','gate 26: all programs at TYP',13),('gate26_corners.log','gate 26: corners LO, HI, MIX 1, MIX 2',24),
      ('gate26_nop.log','gate 26: nop at LO and HI',2),('gate26_500pF_HI.log','gate 26: 500 pF cables at HI',6),('gate26_vdd45.log','gate 26: 4.5 V supply',12),
      ('gate26_vdd425.log','gate 26: 4.25 V supply',3),('gate26_mix34.log','gate 26: MIX 3 and 4',12),('gate26_cross.log','gate 26: crosstalk',12),
      ('gate26_800pF_HI.log','gate 26: 800 pF cables at HI',6)]
sh=lambda c: subprocess.run(c,shell=True,capture_output=True,text=True).stdout

def main():
    warn=[]; L=[]; left=0
    for f,what,n in LOGS:
        p=os.path.join(OUT,f)
        if not os.path.exists(p): continue
        s=open(p).read(); rows=[l for l in s.splitlines() if re.match(r'^\s+\S.*: (pass|FAIL)',l) and '(from the ledger)' not in l]
        led=sum(1 for l in s.splitlines() if '(from the ledger)' in l); ok=sum(1 for l in rows if ': pass' in l)+led; bad=[l.strip() for l in rows if ': FAIL' in l]
        age=(time.time()-os.path.getmtime(p))/60; done=ok+len(bad); left+=max(0,n-done) if 'did not pass' not in s else 0
        secs=[float(m.group(1)) for l in rows for m in [re.search(r'\((\d+) s',l)] if m]; eta=''
        if secs and done<n: eta=f", about {sum(secs)/len(secs)*(n-done)/2/3600:.1f} h left at two decks"
        L.append(f"{what}: {done} of {n} landed, {ok} pass, {len(bad)} FAIL; last one {age:.0f} min ago{eta}")
        for b in bad[:3]: warn.append('FAILED: '+b[:150])
        if 'Traceback' in s or 'did not pass' in s: warn.append(f'{f}: '+[l for l in s.splitlines() if l.strip()][-1][:150])
    ng=[l.split(None,3) for l in sh("ps -eo pid,etime,rss,command | grep 'ngspice -b' | grep -v grep").splitlines()]
    q=sh("ps -eo command | grep -E 'queue_|gate.py|starts_hold.py|sweep_por.py' | grep -v grep").strip()
    decks=[f"{os.path.basename(x[3].split()[-1])[:60]} ({x[1]}, {int(x[2])/1e6:.1f} GB)" for x in ng]
    L.append(f"running: {len(ng)} ngspice"+(': '+'; '.join(decks) if decks else '')+('' if q else '; no queue script'))
    if len(ng)>2: warn.append(f'{len(ng)} decks are running: two is the most')
    if left and not ng and not q: warn.append(f'{left} runs are left and nothing is running: the queue has stopped')
    sw=re.search(r'used = ([\d.]+)M',sh('sysctl vm.swapusage')); swap=float(sw.group(1))/1024 if sw else 0
    free=re.search(r'System-wide memory free percentage: (\d+)%',sh('memory_pressure 2>/dev/null | tail -1')); disk=sh("df -g ~ | tail -1").split()
    L.append(f"machine: memory free {free.group(1) if free else '?'} %, swap {swap:.1f} GB, disk free {disk[3]} GB")
    if swap>4: warn.append(f'swap in use: {swap:.1f} GB')
    if int(disk[3])<20: warn.append(f'disk free: {disk[3]} GB')
    print('\n'.join(['ATTENTION: '+w for w in warn]+L) if warn else '\n'.join(['all well']+L))

if __name__=='__main__': main()
