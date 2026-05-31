"""
Above-ground structure generator — Trove-style buildings.
All structures use only vanilla block IDs (1-8).
"""
import random
from typing import List, Tuple

_G=1;_D=2;_S=3;_W=4;_SM=5;_P=6;_M=7;_AU=8  # block aliases
_SA=9;_SS=10;_SN=11;_DG=12                  # biome block aliases

# ── Low-level helpers ───────────────────────────────────────────────────
def _box(x0,y0,z0,x1,y1,z1,b):
    return [(x,y,z,b)
            for x in range(x0,x1+1)
            for y in range(y0,y1+1)
            for z in range(z0,z1+1)]

def _ring(x0,y,z0,x1,z1,b):
    """Hollow rectangle of blocks at height y."""
    res=[]
    for x in range(x0,x1+1):
        for z in range(z0,z1+1):
            if x==x0 or x==x1 or z==z0 or z==z1:
                res.append((x,y,z,b))
    return res

def _frame(x0,y0,z0,x1,y1,z1,b):
    """Hollow box: walls only (no floor/roof)."""
    res=[]
    for x in range(x0,x1+1):
        for y in range(y0,y1+1):
            for z in range(z0,z1+1):
                if x==x0 or x==x1 or z==z0 or z==z1:
                    res.append((x,y,z,b))
    return res

def _col(x,z,y0,y1,b):
    return [(x,y,z,b) for y in range(y0,y1+1)]

def _row_x(y,z,x0,x1,b):
    return [(x,y,z,b) for x in range(x0,x1+1)]

def _row_z(y,x,z0,z1,b):
    return [(x,y,z,b) for z in range(z0,z1+1)]

def _dedup(blocks):
    seen=set(); out=[]
    for t in reversed(blocks):  # later writes win
        k=(t[0],t[1],t[2])
        if k not in seen:
            seen.add(k); out.append(t)
    return out


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 1 — Goblin Hut (10 × 6 × 10)
# Planks hut with wood frame, gabled roof, campfire outside
# ══════════════════════════════════════════════════════════════════════
def _build_goblin_hut():
    B=[]
    # Dirt surround, planks floor inside
    B+=_box(0,0,0, 9,0,9,_D)
    B+=_box(1,0,1, 8,0,8,_P)

    # Wood corner pillars (y=1-4)
    for cx,cz in [(1,1),(1,8),(8,1),(8,8)]:
        B+=_col(cx,cz,1,4,_W)

    # Plank walls between pillars y=1..3
    for y in range(1,4):
        # Front z=1 — door gap at x=4,5 on y=1,2
        for x in range(2,8):
            if x in (4,5) and y<=2: pass
            else: B.append((x,y,1,_P))
        # Back z=8
        for x in range(2,8): B.append((x,y,8,_P))
        # Left x=1
        for z in range(2,8):
            if y==2 and z in (3,6): pass   # windows
            else: B.append((1,y,z,_P))
        # Right x=8
        for z in range(2,8):
            if y==2 and z in (3,6): pass
            else: B.append((8,y,z,_P))

    # Overhanging wood roof y=4 (extends 1 block beyond walls)
    B+=_box(0,4,0, 9,4,9,_W)
    # Raised gable ridge y=5 centre-line
    for x in range(1,9):
        B+=[(x,5,4,_W),(x,5,5,_W)]

    # Door stone threshold
    B+=[(4,0,0,_S),(5,0,0,_S)]

    # Interior campfire (gold "fire")
    B+=[(4,1,5,_AU),(5,1,5,_AU)]
    # Stone campfire ring around it
    for dx,dz in [(-1,0),(0,-1),(1,0),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
        B.append((4+dx,1,5+dz,_S))

    # Exterior campfire area (in front of door)
    B+=_box(3,-1,-2, 6,-1,0,_D)
    B+=[(3,0,-1,_S),(6,0,-1,_S),(4,0,-2,_S),(5,0,-2,_S)]
    B+=[(4,1,-1,_AU),(5,1,-1,_AU)]

    # Mud fence posts at entry sides
    B+=_col(2,0,1,2,_M)+_col(7,0,1,2,_M)

    return _dedup(B)


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 2 — Stone Tower (6 × 18 × 6)
# Imposing smooth stone tower with battlements, interior floors, arrow slits
# ══════════════════════════════════════════════════════════════════════
def _build_tower():
    B=[]
    # Wide base slab
    B+=_box(-1,0,-1, 6,0,6,_S)
    B+=_box(0,1,0, 5,1,5,_SM)

    # Tower shaft y=2..13: smooth stone outer, stone accent every 4
    ACCENT={4,8,12}
    for y in range(2,14):
        bid=_S if y in ACCENT else _SM
        for x in range(6):
            for z in range(6):
                if x==0 or x==5 or z==0 or z==5:
                    B.append((x,y,z,bid))

    # Arrow slits: 1-block gaps in front/back walls
    SLITS=[(2,6),(3,6),(2,10),(3,10)]  # (x, y) on z=0 face
    for sx,sy in SLITS:
        B=[(x,y,z,b) for x,y,z,b in B if not (x==sx and y==sy and z==0)]
        B=[(x,y,z,b) for x,y,z,b in B if not (x==sx and y==sy and z==5)]

    # Interior floors at y=5, y=10 (planks)
    B+=_box(1,5,1, 4,5,4,_P)
    B+=_box(1,10,1, 4,10,4,_P)

    # Parapet y=14-15: crenellated (skip every other for merlons)
    for y in range(14,16):
        for x in range(6):
            for z in range(6):
                if x==0 or x==5 or z==0 or z==5:
                    if (x+z) % 2 == 0:   # merlon
                        B.append((x,y,z,_SM if y==14 else _S))

    # Gold capstone at 4 corners y=16
    for cx,cz in [(0,0),(0,5),(5,0),(5,5)]:
        B+=[(cx,16,cz,_AU),(cx,17,cz,_AU)]

    # Door gap: z=0, x=2,3, y=2-4
    B=[(x,y,z,b) for x,y,z,b in B
       if not (z==0 and x in (2,3) and 2<=y<=4)]

    # Entry arch keystone
    B+=[(2,5,0,_S),(3,5,0,_S)]

    return _dedup(B)


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 3 — Ancient Shrine (11 × 7 × 11)
# Stepped pyramid platform, 4 pillars with gold caps, central gold altar
# ══════════════════════════════════════════════════════════════════════
def _build_shrine():
    B=[]
    # Three-tier pyramid base
    B+=_box(0,0,0, 10,0,10,_S)          # tier 1: 11×11 stone
    B+=_box(1,1,1,  9,1, 9,_SM)         # tier 2: 9×9 smooth stone
    B+=_box(2,2,2,  8,2, 8,_S)          # tier 3: 7×7 stone
    # Smooth stone inner surface tier 3
    B+=_box(3,2,3,  7,2, 7,_SM)

    # Stair lip (front entry): clear steps on south side
    B+=[(5,0,-1,_S),(5,1,-1,_S),(4,0,-1,_S),(6,0,-1,_S)]

    # 4 corner pillars (2×2 smooth stone, y=2-5)
    for px,pz in [(2,2),(2,8),(8,2),(8,8)]:
        B+=_box(px,2,pz, px+1,5,pz+1,_SM)
    # Gold pillar caps y=6
    for px,pz in [(2,2),(2,8),(8,2),(8,8)]:
        B+=_box(px,6,pz, px+1,6,pz+1,_AU)

    # Connecting arches (beam) at y=5 between pillars
    B+=_row_x(5,2, 2,9,_SM)+_row_x(5,9, 2,9,_SM)
    B+=_row_z(5,2, 2,9,_SM)+_row_z(5,9, 2,9,_SM)

    # Central altar: 3×3 smooth stone pedestal
    B+=_box(4,3,4, 6,3,6,_SM)
    # Gold top
    B+=_box(4,4,4, 6,4,6,_AU)
    B.append((5,5,5,_AU))   # altar jewel

    # Decorative gold torches at tier-3 corners
    for cx,cz in [(2,2),(2,8),(8,2),(8,8)]:
        B.append((cx,3,cz,_AU))

    return _dedup(B)


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 4 — Dark Stronghold (13 × 9 × 11)
# Three-sided fortress, corner towers, throne inside
# ══════════════════════════════════════════════════════════════════════
def _build_stronghold():
    B=[]
    W,D=13,11
    # Stone floor
    B+=_box(0,0,0, W-1,0,D-1,_SM)

    # Three walls (back z=D-1, left x=0, right x=W-1) — 2 blocks thick, 6 tall
    # Back wall
    B+=_box(0,1,D-2, W-1,6,D-1,_S)
    # Left wall
    B+=_box(0,1,1, 1,6,D-1,_S)
    # Right wall
    B+=_box(W-2,1,1, W-1,6,D-1,_S)

    # Smooth stone facing on inner side of walls
    for y in range(1,7):
        for x in range(1,W-1): B.append((x,y,D-2,_SM))  # inner back
        for z in range(1,D-1): B.append((1,y,z,_SM))     # inner left
        for z in range(1,D-1): B.append((W-2,y,z,_SM))   # inner right

    # 4 corner towers (3×3 smooth stone, y=1-9)
    for tx,tz in [(0,0),(0,D-3),(W-3,0),(W-3,D-3)]:
        B+=_frame(tx,1,tz, tx+2,8,tz+2,_SM)
        B+=_box(tx,8,tz, tx+2,9,tz+2,_S)  # tower top

    # Battlements on main walls (y=7-8): alternating merlons
    for x in range(W):
        if x%2==0:
            B+=[(x,7,D-1,_S),(x,8,D-1,_S)]
    for z in range(D):
        if z%2==0:
            B+=[(0,7,z,_S),(0,8,z,_S)]
            B+=[(W-1,7,z,_S),(W-1,8,z,_S)]

    # Interior details: planks floor
    B+=_box(2,1,1, W-3,1,D-3,_P)

    # Gold throne at back-centre
    B+=_box(5,2,D-3, 7,3,D-3,_AU)
    B.append((6,4,D-3,_S))   # throne back

    # Entrance arch (north face, open): stone pillars at x=2,W-3, y=1-4
    B+=_col(2,0,1,4,_S)+_col(W-3,0,1,4,_S)
    B+=[(3,5,0,_S),(4,5,0,_S),(5,5,0,_SM),(W-4,5,0,_S),(W-5,5,0,_S)]

    return _dedup(B)


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 5 — Desert Pyramid (14 × 14 × 14)
# Stepped sandstone pyramid with inner chamber and gold floor
# ══════════════════════════════════════════════════════════════════════
def _build_desert_pyramid():
    B = {}

    # Sand base layer
    for x in range(14):
        for z in range(14):
            B[(x, 0, z)] = _SA

    # Stepped sandstone tiers (solid)
    for y_start, y_end, off in [(1,2,0),(3,4,1),(5,6,2),(7,8,3),(9,10,4),(11,12,5)]:
        for y in range(y_start, y_end + 1):
            for x in range(off, 14 - off):
                for z in range(off, 14 - off):
                    B[(x, y, z)] = _SS

    # Gold peak
    for x in range(6, 8):
        for z in range(6, 8):
            B[(x, 13, z)] = _AU

    # Carve entrance tunnel: x=5-8, y=1-3, z=0-4
    for x in range(5, 9):
        for y in range(1, 4):
            for z in range(0, 5):
                B.pop((x, y, z), None)

    # Carve inner chamber: x=3-10, y=1-3, z=5-10
    for x in range(3, 11):
        for y in range(1, 4):
            for z in range(5, 11):
                B.pop((x, y, z), None)

    # Gold sarcophagus floor in chamber
    for x in range(3, 11):
        for z in range(5, 11):
            B[(x, 1, z)] = _AU

    # Sandstone columns at chamber corners
    for cx, cz in [(3, 5), (3, 10), (10, 5), (10, 10)]:
        for y in range(1, 4):
            B[(cx, y, cz)] = _SS

    # Decorative sand piles inside
    for sx, sz in [(5, 9), (8, 6)]:
        B[(sx, 2, sz)] = _SA

    return [(x, y, z, b) for (x, y, z), b in B.items()]


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 6 — Snow Tower (8 × 24 × 8)
# Narrow snow tower with stone bands, two internal floors, gold spire tips
# ══════════════════════════════════════════════════════════════════════
def _build_snow_tower():
    B = {}

    # Stone base slab
    for x in range(8):
        for z in range(8):
            B[(x, 0, z)] = _S

    # Snow tower shaft (hollow, 1-block thick walls)
    for y in range(1, 18):
        bid = _S if (y % 4 == 0) else _SN  # stone accent rings
        for x in range(8):
            for z in range(8):
                if x == 0 or x == 7 or z == 0 or z == 7:
                    B[(x, y, z)] = bid

    # Mid-floor at y=9 (stone)
    for x in range(1, 7):
        for z in range(1, 7):
            B[(x, 9, z)] = _S
    B.pop((1, 9, 1), None)  # ladder opening

    # Upper floor at y=17 (snow)
    for x in range(1, 7):
        for z in range(1, 7):
            B[(x, 17, z)] = _SN
    B.pop((1, 17, 1), None)  # ladder opening

    # Door gap: z=0, x=3-4, y=1-3
    for x in range(3, 5):
        for y in range(1, 4):
            B.pop((x, y, 0), None)

    # Battlements at y=18-19: alternating merlons
    for x in range(8):
        for z in range(8):
            if x == 0 or x == 7 or z == 0 or z == 7:
                if (x + z) % 2 == 0:
                    B[(x, 18, z)] = _SN
                    B[(x, 19, z)] = _S

    # Corner spires y=18-22 + gold tips
    for cx, cz in [(0, 0), (0, 7), (7, 0), (7, 7)]:
        for y in range(18, 23):
            B[(cx, y, cz)] = _SN
        B[(cx, 23, cz)] = _AU  # gold tip

    return [(x, y, z, b) for (x, y, z), b in B.items()]


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 7 — Forest Shrine (12 × 9 × 12)
# Overgrown stone temple with wood pillars, dark grass roof, gold altar
# ══════════════════════════════════════════════════════════════════════
def _build_forest_shrine():
    B = {}

    # Stone foundation (2 layers)
    for x in range(12):
        for z in range(12):
            B[(x, 0, z)] = _S
            B[(x, 1, z)] = _SM

    # 4 wood corner pillars (y=2-7) with dark grass vine patches
    for px, pz in [(1, 1), (1, 10), (10, 1), (10, 10)]:
        for y in range(2, 8):
            B[(px, y, pz)] = _W
        B[(px, 3, pz)] = _DG
        B[(px, 5, pz)] = _DG
        # Side vine patches
        for ddx, ddz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, nz = px + ddx, pz + ddz
            if 0 <= nx <= 11 and 0 <= nz <= 11:
                B[(nx, 4, nz)] = _DG

    # Connecting wood beams at y=7
    for x in range(1, 11):
        B[(x, 7, 1)]  = _W
        B[(x, 7, 10)] = _W
    for z in range(1, 11):
        B[(1,  7, z)] = _W
        B[(10, 7, z)] = _W

    # Dark grass canopy roof at y=8
    for x in range(1, 11):
        for z in range(1, 11):
            B[(x, 8, z)] = _DG

    # Overhang (outer ring at y=7)
    for x in range(12):
        B[(x, 7, 0)]  = _DG
        B[(x, 7, 11)] = _DG
    for z in range(12):
        B[(0,  7, z)] = _DG
        B[(11, 7, z)] = _DG

    # Central altar: smooth stone pedestal (y=2-2), gold top (y=3)
    for x in range(4, 8):
        for z in range(4, 8):
            B[(x, 2, z)] = _SM
            B[(x, 3, z)] = _AU

    # Altar centrepiece
    for x in range(5, 7):
        for z in range(5, 7):
            B[(x, 4, z)] = _AU

    # Scattered dark grass on foundation edges
    for gx, gz in [(0,0),(11,0),(0,11),(11,11),(3,0),(8,0),(0,3),(0,8),(3,11),(8,11),(11,3),(11,8)]:
        B[(gx, 0, gz)] = _DG

    # Entry path (south face, x=4-7 cleared + wood planks)
    for x in range(4, 8):
        B.pop((x, 1, 0), None)
        B[(x, 0, 0)] = _P
        B[(x, 1, 0)] = _P

    return [(x, y, z, b) for (x, y, z), b in B.items()]


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 8 — Dungeon Vault (9 × 5 × 9 surface + underground room)
# Stone tower entrance on surface → vertical shaft → underground boss chamber
# Always spawns a boss. Rarer than all other structures.
# ══════════════════════════════════════════════════════════════════════
def _build_dungeon_vault():
    B = {}
    AIR = 0

    # ── Surface marker: 5×5 smooth stone ring, 4 corner towers ──────
    for x in range(5):
        for z in range(5):
            if x == 0 or x == 4 or z == 0 or z == 4:
                B[(x, 0, z)] = _SM   # ground-level ring
    # Open entrance: remove front face segments
    for x in range(1, 4):
        B.pop((x, 0, 0), None)

    # 4 corner towers (dy=1-4) + gold tops
    for px, pz in [(0,0),(0,4),(4,0),(4,4)]:
        for dy in range(1, 5):
            B[(px, dy, pz)] = _SM
        B[(px, 5, pz)] = _AU

    # Cross beams at dy=3 connecting towers
    for x in range(0, 5):
        B[(x, 3, 0)] = _SM;  B[(x, 3, 4)] = _SM
    for z in range(0, 5):
        B[(0, 3, z)] = _SM;  B[(4, 3, z)] = _SM

    # ── Vertical shaft: 3×3 air core, dy=-1 to -8 ────────────────────
    for dy in range(-1, -9, -1):
        for x in range(1, 4):
            for z in range(1, 4):
                B[(x, dy, z)] = AIR   # shaft interior

    # Shaft stone walls (outer ring dy=-1 to -8)
    for dy in range(-1, -9, -1):
        for x in range(0, 5):
            for z in range(0, 5):
                if (x == 0 or x == 4 or z == 0 or z == 4) and (x,dy,z) not in B:
                    B[(x, dy, z)] = _SM

    # ── Underground vault: 9×4×9 chamber at dy=-9 to -12 ────────────
    # Smooth stone walls + air interior
    for x in range(9):
        for z in range(9):
            for dy in range(-12, -8):
                if x == 0 or x == 8 or z == 0 or z == 8:
                    B[(x, dy, z)] = _SM
                else:
                    B[(x, dy, z)] = AIR

    # Stone floor
    for x in range(9):
        for z in range(9):
            B[(x, -13, z)] = _S

    # Gold floor accents (checker)
    for x in range(1, 8, 2):
        for z in range(1, 8, 2):
            B[(x, -13, z)] = _AU

    # Boss altar at vault center (dy=-12 to -10)
    for x in range(3, 6):
        for z in range(3, 6):
            B[(x, -12, z)] = _SM    # altar base
    for x in range(3, 6):
        for z in range(3, 6):
            B[(x, -11, z)] = _AU    # altar top
    B[(4, -10, 4)] = _AU            # altar centerpiece

    # Shaft connects to vault ceiling (clear shaft bottom into vault)
    for x in range(1, 4):
        for z in range(1, 4):
            B[(x, -9, z)] = AIR     # open connection

    # Chest alcove (back-left corner of vault)
    B[(1, -12, 7)] = AIR             # clear alcove space

    return [(x, y, z, b) for (x, y, z), b in B.items()]


# ══════════════════════════════════════════════════════════════════════
# STRUCTURE 9 — Sky Citadel (17 × 14 × 17)
# Stepped stone tower (climbable) with an enclosed boss arena at the TOP.
# Reach the arena by: teleport portal (base), climbing the steps, or digging.
# ══════════════════════════════════════════════════════════════════════
def _build_sky_citadel():
    B = {}
    AIR = 0
    C = 8   # center for 17-wide footprint (x,z = 0..16)

    # ── Climbable stepped pyramid base (ly 0..4) ─────────────────────
    # Each tier steps in 1 block per height → 1-high steps (walkable)
    for ly in range(0, 5):
        half = C - ly                       # 8,7,6,5,4
        bid  = _SM if ly % 2 == 0 else _S
        for x in range(C - half, C + half + 1):
            for z in range(C - half, C + half + 1):
                B[(x, ly, z)] = bid
    # Top platform after climb: 9×9 at y=4 (x4..12)

    # ── Arena floor slab (y=5, 7×7, x5..11) ──────────────────────────
    for x in range(5, 12):
        for z in range(5, 12):
            B[(x, 5, z)] = _S
    for x in range(6, 11, 2):               # gold accents
        for z in range(6, 11, 2):
            B[(x, 5, z)] = _AU

    # ── Arena walls (y=6..9) + ceiling (y=10) ────────────────────────
    for y in range(6, 10):
        for x in range(5, 12):
            for z in range(5, 12):
                if x in (5, 11) or z in (5, 11):
                    B[(x, y, z)] = _SM
    for x in range(5, 12):
        for z in range(5, 12):
            B[(x, 10, z)] = _S

    # Door in front wall (z=5) at x=8, y=6,7 (climbers enter here)
    B[(8, 6, 5)] = AIR
    B[(8, 7, 5)] = AIR
    # Light windows on the other three walls
    for wx_, wz_ in [(8, 11), (5, 8), (11, 8)]:
        B[(wx_, 8, wz_)] = AIR

    # Crenellated crown on the roof edge
    for x in range(5, 12):
        for z in range(5, 12):
            if (x in (5, 11) or z in (5, 11)) and (x + z) % 2 == 0:
                B[(x, 11, z)] = _S
    # Gold spire on top
    for dy in range(11, 14):
        B[(8, dy, 8)] = _AU

    # (Entry portal pad is placed dynamically at terrain level in _place_arena)

    return [(x, y, z, b) for (x, y, z), b in B.items() if b != AIR]


# ══════════════════════════════════════════════════════════════════════
STRUCTURE_DEFS = {
    'goblin_hut': {
        'blocks': _build_goblin_hut(),
        'size':   (10, 6, 10),
        'chest':  (4,  1, 7),
        'floor':  0,
        'boss':   False,
    },
    'tower': {
        'blocks': _build_tower(),
        'size':   (8,  18, 8),
        'chest':  (2,  6,  2),
        'floor':  1,
        'boss':   True,
    },
    'shrine': {
        'blocks': _build_shrine(),
        'size':   (11, 7,  11),
        'chest':  (4,  5,  4),
        'floor':  1,
        'boss':   True,
    },
    'stronghold': {
        'blocks': _build_stronghold(),
        'size':   (13, 9,  11),
        'chest':  (6,  2,  9),
        'floor':  1,
        'boss':   True,
    },
    'desert_pyramid': {
        'blocks': _build_desert_pyramid(),
        'size':   (14, 14, 14),
        'chest':  (6,  2,  7),   # on the gold chamber floor
        'floor':  1,
        'boss':   True,
    },
    'snow_tower': {
        'blocks': _build_snow_tower(),
        'size':   (8,  24, 8),
        'chest':  (3,  17, 3),   # on the upper floor
        'floor':  1,
        'boss':   True,
    },
    'forest_shrine': {
        'blocks': _build_forest_shrine(),
        'size':   (12, 9,  12),
        'chest':  (5,  4,  5),   # on top of the altar
        'floor':  1,
        'boss':   True,
    },
    'dungeon_vault': {
        'blocks':           _build_dungeon_vault(),
        'size':             (9, 5, 9),
        'chest':            (1, -12, 7),   # inside vault room (negative dy)
        'floor':            2,             # highest loot tier
        'boss':             True,
        'boss_guaranteed':  True,          # always spawns boss
        'boss_dy':          -11,           # boss on altar inside vault
    },
    'sky_citadel': {
        'blocks':           _build_sky_citadel(),
        'size':             (17, 14, 17),
        'chest':            (10, 6, 9),    # inside the top arena
        'floor':            2,
        'boss':             True,
        'boss_guaranteed':  True,
        'boss_dy':          6,             # boss on arena floor (top)
    },
}

# Default weights (dungeon_vault removed — handled by separate vault zone system)
_TYPE_WEIGHTS = [
    ('goblin_hut',  0.78),
    ('stronghold',  0.08),
    ('shrine',      0.07),
    ('tower',       0.07),
]

# Biome-specific structure weights: 0=Plains, 1=Desert, 2=Snow, 3=Forest
_BIOME_WEIGHTS = {
    0: _TYPE_WEIGHTS,
    1: [('goblin_hut', 0.76), ('desert_pyramid', 0.14), ('shrine', 0.10)],
    2: [('goblin_hut', 0.76), ('snow_tower',     0.14), ('stronghold', 0.10)],
    3: [('goblin_hut', 0.70), ('forest_shrine',  0.18), ('tower', 0.12)],
}


# ══════════════════════════════════════════════════════════════════════
class StructureGenerator:
    ZONE_SIZE         = 40     # normal structures (goblin huts, towers, etc.)
    SPECIAL_ZONE_SIZE = 2000   # boss arenas (vault / citadel) — one per zone

    def __init__(self, seed: int = 42):
        self._seed       = seed
        self._done       = {}   # (iz, ix) → result dict or None
        self._special_done = {}  # special zone key → result dict or None

    def _try_zone(self, world, terrain_gen, iz: int, ix: int):
        """Deterministically try one zone. Returns result dict or None. Idempotent."""
        key = (iz, ix)
        if key in self._done:
            return self._done[key]

        step      = self.ZONE_SIZE
        zone_seed = (self._seed + iz * 73856093 + ix * 19349663) & 0xFFFFFFFF
        rng       = random.Random(zone_seed)

        wx = ix * step + rng.randint(2, step - 3)
        wz = iz * step + rng.randint(2, step - 3)

        if wx*wx + wz*wz < 196:                   # too close to spawn
            self._done[key] = None; return None
        if rng.random() > 0.35:                    # 65 % zones are empty
            self._done[key] = None; return None

        biome   = terrain_gen.get_biome(wx, wz)
        weights = _BIOME_WEIGHTS.get(biome, _TYPE_WEIGHTS)
        r = rng.random(); acc = 0.0; stype = None
        for t, w in weights:
            acc += w
            if r < acc: stype = t; break
        if stype is None:
            self._done[key] = None; return None

        defn      = STRUCTURE_DEFS[stype]
        surface_y = terrain_gen.get_surface_height(wx, wz)
        wy        = surface_y + 1

        for dx, dy, dz, bid in defn['blocks']:
            world.set_block(wx+dx, wy+dy, wz+dz, bid)

        sx, _, sz = defn['size']
        for fdx in range(sx):
            for fdz in range(sz):
                col_surf = terrain_gen.get_surface_height(wx+fdx, wz+fdz)
                for fy in range(col_surf, wy):
                    if world.get_block(wx+fdx, fy, wz+fdz) == 0:
                        world.set_block(wx+fdx, fy, wz+fdz, _D)

        cdx, cdy, cdz = defn['chest']
        # Dungeon vaults always have a boss; other structures 30% chance
        if defn.get('boss_guaranteed', False):
            boss = defn['boss']
        else:
            boss = defn['boss'] and rng.random() < 0.40
        boss_dy = defn.get('boss_dy', 1)
        result = {
            'type':     stype,
            'wx': wx, 'wy': wy, 'wz': wz,
            'chest_wx': wx+cdx, 'chest_wy': wy+cdy, 'chest_wz': wz+cdz,
            'floor':    defn['floor'],
            'boss':     boss,
            'boss_wx':  wx + sx//2, 'boss_wy': wy + boss_dy, 'boss_wz': wz + sz//2,
        }
        self._done[key] = result
        return result

    # ──────────────────────────────────────────────────────────────────
    # Special zone: boss arena (dungeon_vault or sky_citadel) per big zone
    # ──────────────────────────────────────────────────────────────────
    def _try_special_zone(self, world, terrain_gen, viz: int, vix: int):
        key = (viz, vix)
        if key in self._special_done:
            return self._special_done[key]

        step      = self.SPECIAL_ZONE_SIZE
        zone_seed = ((self._seed ^ 0xDEADBEEF) + viz * 92821 + vix * 49291) & 0xFFFFFFFF
        rng       = random.Random(zone_seed)

        if rng.random() > 0.90:          # 90% chance per zone
            self._special_done[key] = None
            return None

        wx = vix * step + rng.randint(100, step - 100)
        wz = viz * step + rng.randint(100, step - 100)
        if wx * wx + wz * wz < 500 * 500:   # keep away from spawn
            self._special_done[key] = None
            return None

        # Choose arena type: 50% underground vault, 50% sky citadel
        stype  = 'dungeon_vault' if rng.random() < 0.5 else 'sky_citadel'
        result = self._place_arena(world, terrain_gen, wx, wz, stype)
        self._special_done[key] = result
        print(f'[arena] {stype} at ({wx}, {result["wy"]}, {wz})')
        return result

    def _place_arena(self, world, terrain_gen, wx: int, wz: int, stype: str):
        """Place a boss-arena structure (vault/citadel) at (wx, wz). Returns result dict."""
        defn      = STRUCTURE_DEFS[stype]
        surface_y = terrain_gen.get_surface_height(wx, wz)
        wy        = surface_y + 1

        for dx, dy, dz, bid in defn['blocks']:
            world.set_block(wx + dx, wy + dy, wz + dz, bid)

        sx, _, sz = defn['size']
        cdx, cdy, cdz = defn['chest']
        boss_dy = defn.get('boss_dy', 1)

        result = {
            'type':     stype,
            'wx': wx, 'wy': wy, 'wz': wz,
            'chest_wx': wx + cdx, 'chest_wy': wy + cdy, 'chest_wz': wz + cdz,
            'floor':    defn['floor'],
            'boss':     True,
            'boss_wx':  wx + sx // 2,
            'boss_wy':  wy + boss_dy,
            'boss_wz':  wz + sz // 2,
        }

        # ── Portal endpoints (entry pad ↔ arena) ─────────────────────
        if stype == 'sky_citadel':
            # Fill below the 17×17 base down to terrain so it doesn't float
            for fdx in range(17):
                for fdz in range(17):
                    col_surf = terrain_gen.get_surface_height(wx + fdx, wz + fdz)
                    for fy in range(col_surf, wy):
                        if world.get_block(wx + fdx, fy, wz + fdz) == 0:
                            world.set_block(wx + fdx, fy, wz + fdz, _D)
            # Entry pad: 3×3 gold pad on the terrain in front of the tower
            pad_x, pad_z = wx + 8, wz - 3
            pad_surf = terrain_gen.get_surface_height(pad_x, pad_z)
            for ddx in (-1, 0, 1):
                for ddz in (-1, 0, 1):
                    world.set_block(pad_x + ddx, pad_surf, pad_z + ddz, _AU)
                    # clear space above the pad so the portal is reachable
                    for cy in range(1, 4):
                        world.set_block(pad_x + ddx, pad_surf + cy, pad_z + ddz, 0)
            entry = (pad_x, pad_surf + 1.5, pad_z)
            arena = (wx + 8, wy + 6, wz + 7)      # arena floor, just inside door
        else:  # dungeon_vault
            # Entry pad on terrain just in front of the shaft entrance
            pad_x, pad_z = wx + 2, wz - 2
            pad_surf = terrain_gen.get_surface_height(pad_x, pad_z)
            for ddx in (-1, 0, 1):
                for ddz in (-1, 0, 1):
                    world.set_block(pad_x + ddx, pad_surf, pad_z + ddz, _AU)
                    for cy in range(1, 4):
                        world.set_block(pad_x + ddx, pad_surf + cy, pad_z + ddz, 0)
            entry = (pad_x, pad_surf + 1.5, pad_z)
            arena = (wx + 2, wy - 12, wz + 2)     # vault floor (stand height)

        result['portal_a']    = entry
        result['portal_a_to'] = arena
        result['portal_b']    = arena
        result['portal_b_to'] = entry
        return result

    def place_test_arena(self, world, terrain_gen, wx: int, wz: int,
                         stype: str = 'sky_citadel'):
        """Force-place one arena near spawn for easy testing. Returns result dict."""
        result = self._place_arena(world, terrain_gen, wx, wz, stype)
        print(f'[arena] TEST {stype} at ({wx}, {result["wy"]}, {wz})')
        return result

    def place_around(self, world, terrain_gen, cx: int, cz: int,
                     chunk_size: int, rd: int) -> list:
        """Place structures for zones near chunk (cx, cz). Returns NEW results only."""
        step   = self.ZONE_SIZE
        wx0    = cx * chunk_size
        wz0    = cz * chunk_size
        margin = rd * chunk_size - 16

        ix_lo = (wx0 - margin) // step - 1
        ix_hi = (wx0 + margin) // step + 1
        iz_lo = (wz0 - margin) // step - 1
        iz_hi = (wz0 + margin) // step + 1

        results = []
        for iz in range(iz_lo, iz_hi + 1):
            for ix in range(ix_lo, ix_hi + 1):
                if (iz, ix) not in self._done:
                    r = self._try_zone(world, terrain_gen, iz, ix)
                    if r:
                        results.append(r)

        # Special arena zones (much larger grid)
        vstep  = self.SPECIAL_ZONE_SIZE
        vix_lo = (wx0 - margin * 4) // vstep - 1
        vix_hi = (wx0 + margin * 4) // vstep + 1
        viz_lo = (wz0 - margin * 4) // vstep - 1
        viz_hi = (wz0 + margin * 4) // vstep + 1
        for viz in range(viz_lo, viz_hi + 1):
            for vix in range(vix_lo, vix_hi + 1):
                if (viz, vix) not in self._special_done:
                    r = self._try_special_zone(world, terrain_gen, viz, vix)
                    if r:
                        results.append(r)

        return results

    def place_all(self, world, terrain_gen, render_distance: int) -> list:
        results     = self.place_around(world, terrain_gen, 0, 0,
                                        world.chunk_size, render_distance)
        boss_count  = sum(1 for r in results if r['boss'])
        arena_count = sum(1 for r in results
                          if r['type'] in ('dungeon_vault', 'sky_citadel'))
        print(f'[structures] Placed {len(results)} structures'
              f' ({boss_count} boss locations, {arena_count} boss arenas).')
        return results
