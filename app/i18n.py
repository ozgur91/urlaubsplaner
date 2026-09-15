MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def month_label(year: int, month: int) -> str:
    return f"{MONTHS_DE[month - 1]} {year}"


def weekday_label(weekday_index: int) -> str:
    return WEEKDAYS_DE[weekday_index]
