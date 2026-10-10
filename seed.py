"""Seed a few forge heats (run after schema update).

Usage:
    python seed.py forge
"""
from __future__ import annotations

import sys

import pixeltable as pxt


def main(catalog: str = 'forge') -> None:
    t = pxt.get_table(f'{catalog}/heats')
    rows = [
        dict(forge_id='F-A1', alloy='4140', status='done', peak_c=870.0, hold_min=40.0, quench='oil', operator='maya', note='normalize batch'),
        dict(forge_id='F-A1', alloy='316L', status='firing', peak_c=1050.0, hold_min=55.0, quench='air', operator='leo', note='austenitize'),
        dict(forge_id='F-B2', alloy='H13', status='quench', peak_c=1225.0, hold_min=95.0, quench='brine', operator='sam', note='near melt'),
        dict(forge_id='F-C3', alloy='A36', status='cool', peak_c=620.0, hold_min=20.0, quench='air', operator='rina', note='stress relief'),
        dict(forge_id='F-B2', alloy='4140', status='hold', peak_c=980.0, hold_min=70.0, quench='water', operator='maya', note='waiting QC'),
    ]
    # idempotent-ish: only insert if empty
    if t.count() > 0:
        print(f'{catalog}/heats already has {t.count()} rows')
        print(t.select(t.forge_id, t.alloy, t.status, t.band, t.risk, t.tag, t.lane).collect())
        return
    status = t.insert(rows)
    print(f'inserted {len(rows)} rows -> count={t.count()} status={status}')
    print(t.select(t.forge_id, t.alloy, t.status, t.band, t.risk, t.tag, t.lane).collect())


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'forge')
