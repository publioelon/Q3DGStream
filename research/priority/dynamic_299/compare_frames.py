#!/usr/bin/env python3
"""Inspect whether saved priorities evolve between two NTC updates."""
import argparse
from pathlib import Path

# Load project-wide paths instead of machine-specific defaults.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import q3dg_paths as paths
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,default=paths.PRIORITIES_DIR)
p.add_argument('frame_a',type=int)
p.add_argument('frame_b',type=int)
a=p.parse_args()

def load(frame):
    # Load the saved priority order for one update.
    with np.load(a.out/'orders'/f'NTC_{frame:06d}.npz',allow_pickle=False) as z:
        return z['ordered_block_ids'],z['tile_tiers'],z['tile_saliency']
x,tx,sx=load(a.frame_a)
y,ty,sy=load(a.frame_b)
hash_x=x[x<30976]
hash_y=y[y<30976]
print(f'[FRAME {a.frame_a}] P0={np.flatnonzero(tx==0).tolist()} P1={np.flatnonzero(tx==1).tolist()} topHash={hash_x[:12].tolist()}')
print(f'[FRAME {a.frame_b}] P0={np.flatnonzero(ty==0).tolist()} P1={np.flatnonzero(ty==1).tolist()} topHash={hash_y[:12].tolist()}')
print('[SALIENCY] max absolute difference:',float(np.max(np.abs(sx-sy))))
print('[TOP64] Shared original HashGrid block IDs:',len(set(map(int,hash_x[:64])) & set(map(int,hash_y[:64]))),'/64')
print('[RETAINED] Same block IDs:',len(set(map(int,hash_x))&set(map(int,hash_y))), 'of',len(hash_x), 'and',len(hash_y))
print('[NOTE] Different retained IDs and different saliency can both change block rank.')
