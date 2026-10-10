"""Forge Heat Cycle Registry API built with Pixeltable.

Log a forge heat with forge id, alloy, peak temperature, hold time and quench.
Pixeltable derives a heat band, risk score, combined heat tag and priority lane
via a UDF chain, and B-tree indexes on forge, alloy, status and band back the
shop-floor lookup queries. The client demo exercises parallel writers.

Layout: UDFs live in udfs.py; this file holds table models, @pxt.query functions and routes.

Run locally:
    pxt schema update app.py forge
    pxt service run app.py forge
"""
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

from udfs import heat_band, heat_tag, priority_lane, risk_score

# ---- tables ----
TableModel = pxt.model_base()


class Heats(TableModel, name='heats', has_default_idxs=False):
    heat_id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    forge_id: pxt.String
    alloy: pxt.String
    status: pxt.String  # queued / firing / quench / cool / done / hold / scrapped
    peak_c: pxt.Float
    hold_min: pxt.Float
    quench: pxt.String  # air / oil / water / brine
    operator: pxt.String | None
    note: pxt.String | None

    band = heat_band(peak_c)
    risk = risk_score(peak_c, hold_min, quench)
    tag = heat_tag(band, risk, alloy)
    lane = priority_lane(risk, status)

    __indexes__ = [
        pxt.BtreeIndex(forge_id),
        pxt.BtreeIndex(alloy),
        pxt.BtreeIndex(status),
        pxt.BtreeIndex(band),
    ]


# ---- queries ----
@pxt.query
def by_forge(forge_id: str):
    """Heats on one forge (forge_id index), highest risk first."""
    return (
        Heats.where(Heats.forge_id == forge_id)
        .select(Heats.heat_id, Heats.alloy, Heats.status, Heats.peak_c, Heats.band, Heats.risk, Heats.tag, Heats.lane)
        .order_by(Heats.risk, asc=False)
    )


@pxt.query
def by_band_status(band: str, status: str):
    """Heats in a heat band and status (band + status indexes)."""
    return (
        Heats.where((Heats.band == band) & (Heats.status == status))
        .select(Heats.heat_id, Heats.forge_id, Heats.alloy, Heats.peak_c, Heats.risk, Heats.tag, Heats.lane)
        .order_by(Heats.peak_c, asc=False)
    )


@pxt.query
def by_alloy(alloy: str):
    """All heats for an alloy (alloy index)."""
    return (
        Heats.where(Heats.alloy == alloy)
        .select(Heats.heat_id, Heats.forge_id, Heats.status, Heats.band, Heats.risk, Heats.tag)
        .order_by(Heats.forge_id)
    )


@pxt.query
def hot_lane():
    """Shop board: heats currently in the hot priority lane."""
    return (
        Heats.where(Heats.lane == 'hot')
        .select(Heats.heat_id, Heats.forge_id, Heats.alloy, Heats.status, Heats.risk, Heats.tag)
        .order_by(Heats.risk, asc=False)
    )


# ---- routes ----
forge_api = FastAPIRouter(name='forge_api')

forge_api.add_insert_route(
    Heats,
    path='/heats',
    inputs=[Heats.forge_id, Heats.alloy, Heats.status, Heats.peak_c, Heats.hold_min, Heats.quench, Heats.operator, Heats.note],
    outputs=[Heats.heat_id, Heats.band, Heats.risk, Heats.tag, Heats.lane],
)
forge_api.add_update_route(
    Heats,
    path='/heats/status',
    inputs=[Heats.status, Heats.note],
    outputs=[Heats.heat_id, Heats.status, Heats.lane, Heats.tag],
)
forge_api.add_compute_route(
    Heats,
    path='/score',
    inputs=[Heats.peak_c, Heats.hold_min, Heats.quench, Heats.alloy, Heats.status],
    outputs=[Heats.band, Heats.risk, Heats.tag, Heats.lane],
)
forge_api.add_delete_route(Heats, path='/heats/delete')
forge_api.add_query_route(path='/heats/by-forge', query=by_forge, method='get')
forge_api.add_query_route(path='/heats/by-band', query=by_band_status, method='get')
forge_api.add_query_route(path='/heats/by-alloy', query=by_alloy, method='get')
forge_api.add_query_route(path='/heats/hot-lane', query=hot_lane, method='get')
