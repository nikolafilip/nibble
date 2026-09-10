# Mounting: the column

Decided 2026-09-10 (D038, D039). The boards are nine different sizes, from
the hub at 142 x 115 mm to the sequencer at 454 x 356 mm, 0.66 m² in all,
and the machine lives in a New York apartment. A wall panel is too big to
own, a flat stack hides the LEDs, a card cage hides them too. So: a
freestanding square column with the boards standing on its four faces,
LEDs out, hub and ribbons inside.

`mounting/column.html` is the model: open it in a browser (it loads three.js
from a CDN), drag to walk around it, slide the program-page count to see how
it grows. The elevations, rail heights, ribbon lengths and parts list on that
page are generated from the same board outlines as the schematics.

## The frame

2020 aluminium extrusion, the 3D-printer profile. Four 900 mm uprights on a
500 mm square, joined top and bottom by 460 mm rails with corner brackets.
Every board gets two 460 mm rails at the height of its top and bottom hole
rows; an M3 T-nut slides into each rail slot, a 12 mm standoff screws into
the T-nut, the board screws onto the standoff. Nothing is drilled, so a board
of any width mounts anywhere on a face and a new board is two rails and four
T-nuts. About 14 m of extrusion, 68 brackets, 50 T-nuts, 50 standoffs, about
100 USD, all stock items. Footprint with boards 57 x 57 cm, height 95 cm.

## The faces

| Face | Boards, bottom to top |
|---|---|
| Front | counter, sequencer |
| Right | registers, data memory |
| Back | program pages 1 and 2 side by side; ALU and clock side by side; panel |
| Left | program pages 3 and up, two per row |

The hub lies flat inside at 450 mm on two cross rails 107 mm apart (its hole
pitch), headers up, USB toward the back, power LED visible from above.

## The ribbons

Every board's 64-way header is a shrouded IDC socket 8 mm from its top edge
(the panel's is on its bottom edge). The ribbon leaves the socket straight
out of the face, folds up over the board's edge, folds again over the rail
and drops inside to the hub: two folds and a slack loop, no tight angles.
Lengths run from 40 to 60 cm per board. Eight half-metre ribbons add about
0.3 nF to each bus line; with the hub's 10k pull-ups that is 3 µs of rise on
a 1 ms tick. The machine deck includes it (300 pF per header line at the hub).

## Program pages

The hub routes nothing: its eight connectors are the same 64 nets, and a
slot is a place to plug in, not a port. A program page decodes PC0..3 into
its sixteen word rows and compares PC4..7 with its four page jumpers
(pins 1-2 = a 1 in that bit, 2-3 = a 0); only a page whose jumpers match the
counter lets a row go high, and the rows drive the M lines through the word
diodes as a wired OR against the hub's 1 Meg pull-downs. So a new page is:
set its jumpers to the next page number, plug it onto the bus, done.
Sixteen pages, 256 words, is the limit of the 8-bit counter.

To make that physical, the program board carries two 64-way headers wired
pin for pin in parallel (D039). One ribbon comes from the hub to the first
page; 10 cm ribbons hop from page to page along the face; the last page has
an empty connector. Electrically identical to a ribbon with several
connectors crimped along it, and any page can be pulled without disturbing
the rest.

## What it does not do

The ribbons show, and that is the look. On the floor the panel's switches
are at 65 to 90 cm, so it wants a low table. It has a back: the program
pages and the ALU face away from wherever you stand, so it wants a spot you
can walk around.
