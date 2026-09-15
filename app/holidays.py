"""Public holidays for Germany (national) and Nordrhein-Westfalen (state-specific).

Movable feasts are derived from the date of Easter Sunday via the
anonymous Gregorian algorithm (Meeus/Jones/Butcher).
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Holiday:
    date: date
    name: str


def easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def holidays_for_year(year: int) -> list[Holiday]:
    """German national holidays plus the additional NRW state holidays."""
    easter = easter_sunday(year)

    national = [
        Holiday(date(year, 1, 1), "Neujahr"),
        Holiday(easter - timedelta(days=2), "Karfreitag"),
        Holiday(easter + timedelta(days=1), "Ostermontag"),
        Holiday(date(year, 5, 1), "Tag der Arbeit"),
        Holiday(easter + timedelta(days=39), "Christi Himmelfahrt"),
        Holiday(easter + timedelta(days=50), "Pfingstmontag"),
        Holiday(date(year, 10, 3), "Tag der Deutschen Einheit"),
        Holiday(date(year, 12, 25), "1. Weihnachtstag"),
        Holiday(date(year, 12, 26), "2. Weihnachtstag"),
    ]

    nrw_additional = [
        Holiday(easter + timedelta(days=60), "Fronleichnam"),
        Holiday(date(year, 11, 1), "Allerheiligen"),
    ]

    return sorted(national + nrw_additional, key=lambda h: h.date)


def holidays_in_range(start: date, end: date) -> list[Holiday]:
    years = range(start.year, end.year + 1)
    result = [
        h for year in years for h in holidays_for_year(year) if start <= h.date <= end
    ]
    return sorted(result, key=lambda h: h.date)


def is_holiday(day: date) -> bool:
    return any(h.date == day for h in holidays_for_year(day.year))
