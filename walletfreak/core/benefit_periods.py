"""
Reusable benefit period calculation extracted from dashboard/views/main.py.

Given a benefit dict, anniversary info and the current date, returns the number
of days until the current period expires and the current-period status.
"""

from datetime import datetime
from calendar import monthrange


def calculate_days_until_expiration(frequency, anniversary_month, anniversary_day, anniversary_year, now=None):
    """Return the number of days until the current benefit period expires.

    Args:
        frequency: The time_category string from the benefit (e.g. 'Monthly', 'Quarterly').
        anniversary_month: Month (1-12) of the card anniversary.
        anniversary_day: Day of the card anniversary.
        anniversary_year: Year of the card anniversary.
        now: Optional datetime override (defaults to datetime.now()).

    Returns:
        int or None — days until the current period ends.
    """
    if now is None:
        now = datetime.now()

    current_year = now.year
    current_month = now.month
    freq = frequency.lower()

    if 'monthly' in freq:
        last_day = monthrange(current_year, current_month)[1]
        period_end = datetime(current_year, current_month, last_day, 23, 59, 59)
        return (period_end - now).days

    if 'quarterly' in freq:
        curr_q = (current_month - 1) // 3 + 1
        quarter_end_month = curr_q * 3
        last_day = monthrange(current_year, quarter_end_month)[1]
        period_end = datetime(current_year, quarter_end_month, last_day, 23, 59, 59)
        return (period_end - now).days

    if 'semi-annually' in freq:
        if current_month <= 6:
            period_end = datetime(current_year, 6, 30, 23, 59, 59)
        else:
            period_end = datetime(current_year, 12, 31, 23, 59, 59)
        return (period_end - now).days

    if 'every 4 years' in freq:
        if anniversary_month:
            this_year_anniv = datetime(current_year, anniversary_month, anniversary_day or 1)
            annual_start_year = current_year - 1 if now < this_year_anniv else current_year
        else:
            annual_start_year = current_year

        base_year = anniversary_year or 2020
        block_idx = (annual_start_year - base_year) // 4
        block_end_year = base_year + (block_idx * 4) + 4

        if anniversary_month:
            period_end = datetime(block_end_year, anniversary_month, anniversary_day or 1, 23, 59, 59)
        else:
            period_end = datetime(block_end_year, 12, 31, 23, 59, 59)
        return (period_end - now).days

    # Annual / anniversary / default
    if 'anniversary' in freq and anniversary_month:
        this_year_anniv = datetime(current_year, anniversary_month, anniversary_day or 1)
        start_year = current_year - 1 if now < this_year_anniv else current_year
        exp_year = start_year + 1
        last_day = monthrange(exp_year, anniversary_month)[1]
        period_end = datetime(exp_year, anniversary_month, min(anniversary_day or last_day, last_day), 23, 59, 59)
    else:
        period_end = datetime(current_year, 12, 31, 23, 59, 59)

    return (period_end - now).days


def get_current_period_key(frequency, anniversary_month, anniversary_day, anniversary_year, now=None):
    """Return the Firestore period key for the current period (e.g. '2026_03', '2026_Q1')."""
    if now is None:
        now = datetime.now()

    current_year = now.year
    current_month = now.month
    freq = frequency.lower()

    if 'monthly' in freq:
        return f"{current_year}_{current_month:02d}"

    if 'quarterly' in freq:
        curr_q = (current_month - 1) // 3 + 1
        return f"{current_year}_Q{curr_q}"

    if 'semi-annually' in freq:
        half = 'H1' if current_month <= 6 else 'H2'
        return f"{current_year}_{half}"

    if 'every 4 years' in freq:
        if anniversary_month:
            this_year_anniv = datetime(current_year, anniversary_month, anniversary_day or 1)
            annual_start_year = current_year - 1 if now < this_year_anniv else current_year
        else:
            annual_start_year = current_year
        base_year = anniversary_year or 2020
        block_idx = (annual_start_year - base_year) // 4
        block_start = base_year + (block_idx * 4)
        return f"{block_start}_{block_start + 4}"

    # Annual / anniversary
    if 'anniversary' in freq and anniversary_month:
        this_year_anniv = datetime(current_year, anniversary_month, anniversary_day or 1)
        start_year = current_year - 1 if now < this_year_anniv else current_year
        return str(start_year)

    return str(current_year)
