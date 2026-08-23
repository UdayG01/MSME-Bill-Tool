from datetime import date


def fy_label_for(d: date) -> str:
    """Indian financial year label, e.g. 2026-07-25 -> '2026-27', 2027-02-01 -> '2026-27'."""
    start_year = d.year if d.month >= 4 else d.year - 1
    return f"{start_year}-{str((start_year + 1) % 100).zfill(2)}"
