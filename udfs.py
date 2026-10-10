"""Pixeltable UDFs for the forge heat-cycle registry (module path e.g. `udfs.heat_band`)."""
import pixeltable as pxt


@pxt.udf
def heat_band(peak_c: float) -> str:
    """Coarse forge band from peak Celsius: anneal / normalize / austenitize / melt-risk."""
    t = float(peak_c or 0)
    if t < 650:
        return 'anneal'
    if t < 850:
        return 'normalize'
    if t < 1200:
        return 'austenitize'
    return 'melt-risk'


@pxt.udf
def risk_score(peak_c: float, hold_min: float, quench: str) -> int:
    """0-100 risk from peak temp, hold minutes and quench medium."""
    t = float(peak_c or 0)
    hold = float(hold_min or 0)
    q = (quench or 'air').lower()
    base = 10
    if t >= 1200:
        base += 45
    elif t >= 950:
        base += 25
    elif t >= 850:
        base += 12
    if hold > 90:
        base += 20
    elif hold > 45:
        base += 10
    base += {'air': 0, 'oil': 8, 'water': 18, 'brine': 25}.get(q, 5)
    return min(100, int(base))


@pxt.udf
def heat_tag(band: str, risk: int, alloy: str) -> str:
    """Chained label, e.g. 'austenitize-r42-4140'."""
    alloy_slug = (alloy or 'unknown').replace(' ', '-').lower()
    return f'{band}-r{int(risk)}-{alloy_slug}'


@pxt.udf
def priority_lane(risk: int, status: str) -> str:
    """Routing lane from risk + status for shop floor boards."""
    st = (status or '').lower()
    if st in ('scrapped', 'hold'):
        return 'blocked'
    if int(risk) >= 70:
        return 'hot'
    if int(risk) >= 40:
        return 'watch'
    return 'steady'
