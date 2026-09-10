# tools

`freerouting-1.9.0.jar` (5 MB) is not in git. Download it from
https://github.com/freerouting/freerouting/releases/tag/v1.9.0 and run it
with Java 21 (it needs a display session even in batch mode; no `-Djava.awt.headless`):

    java -jar tools/freerouting-1.9.0.jar -de board.dsn -do board.ses -mp 40

`sim/pcb.py` calls it. Freerouting 2.1.0 was tried first: headless it ignores
`-mp`, `router.max_passes` and `job_timeout`, so a board it cannot finish runs
for hours and never writes the SES. 1.9 stops after the passes and writes what
it has, so the unrouted nets can be seen and the placement fixed.
