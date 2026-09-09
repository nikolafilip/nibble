#!/usr/bin/env python3
"""Route remaining signal nets on the already-placed board."""
import math
import sys
from collections import defaultdict

import pcbnew

# reuse router from build_pcb
sys.path.insert(0, "/Users/nikolafilip/Documents/Calculator")
from build_pcb import Router, mst_pairs, fill_zones, to_mm, mm

PCB = "/Users/nikolafilip/Documents/Calculator/Untitled.kicad_pcb"


def main():
    print("loading", flush=True)
    board = pcbnew.LoadBoard(PCB)
    # board size from edge
    xs, ys = [], []
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            xs.append(to_mm(d.GetStart().x))
            ys.append(to_mm(d.GetStart().y))
            xs.append(to_mm(d.GetEnd().x))
            ys.append(to_mm(d.GetEnd().y))
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    print(f"board {w:.1f}x{h:.1f} tracks={len(list(board.GetTracks()))}", flush=True)

    pads_by_net = defaultdict(list)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            if not name or name in ("GND", "+5V"):
                continue
            p = pad.GetPosition()
            pads_by_net[name].append((to_mm(p.x), to_mm(p.y), pad.GetNetCode()))

    router = Router(board, w, h)
    router.seed_obstacles()
    ok = fail = 0
    nets = sorted(pads_by_net.items(), key=lambda kv: len(kv[1]))
    for i, (name, pads) in enumerate(nets):
        uniq, seen = [], set()
        for x, y, code in pads:
            k = (round(x, 2), round(y, 2))
            if k not in seen:
                seen.add(k)
                uniq.append((x, y, code))
        if len(uniq) < 2:
            continue
        code = uniq[0][2]
        pts = [(x, y) for x, y, _ in uniq]
        for (x1, y1), (x2, y2) in mst_pairs(pts):
            if router.route_pair(x1, y1, x2, y2, code):
                ok += 1
            else:
                fail += 1
        if (i + 1) % 40 == 0:
            print(f"  {i+1}/{len(nets)} ok={ok} fail={fail}", flush=True)
    print(f"done segments ok={ok} fail={fail}", flush=True)
    print("filling zones", flush=True)
    fill_zones(board)
    print("saving", flush=True)
    board.Save(PCB)
    print("saved")


if __name__ == "__main__":
    main()
