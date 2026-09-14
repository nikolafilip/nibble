# tools

`freerouting-1.9.0.jar` (5 MB) is not in git. Download it from
https://github.com/freerouting/freerouting/releases/tag/v1.9.0 and run it
with Java 21 (it needs a display session even in batch mode; no `-Djava.awt.headless`):

    java -jar tools/freerouting-1.9.0.jar -de board.dsn -do board.ses -mp 40

`sim/pcb.py` calls it for the cards. `freerouting-2.1.0.jar` (also not in
git, same releases page) is what the sequencer board needs: on that board
1.9 takes hours for a single pass (a thread dump shows it deep in the maze
search), while 2.1.0 does a pass in five to ten minutes. Tested 2026-09-11:
2.1.0 honours `-mp N`, stops after N passes and writes the SES with what it
has, and logs the unrouted count after every pass. A plan picks it with
`extra.router.jar = "freerouting-2.1.0.jar"` (the sequencer's does).
Neither version logs an unrouted count when it gives up early in the way
1.9 does on the cards, so KiCad's DRC is the gate in `pcb.py`.

`freerouting-2.4.1.jar` (same releases page) is what the sequencer uses now
(2026-09-13), and the hub since D052 (1.9 dropped a via inside the bundle of
64 bus lines there and shorted three nets; 2.4.1 routes it clean). It needs Java 25 (`sdk install java 25-tem`); `sim/pcb.py` takes
the JVM from `NIBBLE_JAVA`. Headless it honours `-mp N` and stops on its own
when the score has not improved for ten passes. Its optimizer stage can start
from an older, worse snapshot than the router's last pass and save that, so set
`router.optimizer.max_passes` to 0 in
`~/Library/Application Support/freerouting/freerouting.json`. Findings that
`pcb.py` encodes (plan `extra.router`): a layer marked `(type power)` in the
DSN breaks routing altogether (the ground layer stays a signal layer);
`exclude_nets` takes the power nets out of the router's network and leaves their
pre-routed copper as obstacles; `layer_order` lists the DSN layers so that the
even-indexed ones are the vertical ones (freerouting prefers vertical on even
indexes, horizontal on odd); `route_in1` lets the router use the ground layer,
the pour fills the rest; `attempts` retries from the routed state. The
autoroute settings block freerouting's parser accepts stops 2.1.0 dead (score
NaN), so `pcb.py` writes none.
