# File: reminder_parser.py
import re
from datetime import datetime
import dateparser
from reminder_repeat import adjust_initial_slots

TIME_WORDS = {
    r"\bутром\b":   "9:00",
    r"\bднем\b":    "13:00",
    r"\bднём\b":    "13:00",
    r"\bвечером\b": "18:00",
    r"\bночью\b":   "23:00",
}

REPEAT_PATTERNS = [
    (r"\bкаждый\s+год\b",                   ("yearly", 1)),
    (r"\bкаждые\s+(\d+)\s+месяц(?:ев|а)?\b", ("monthly", None)),
    (r"\bкаждый\s+месяц\b",                ("monthly", 1)),
    (r"\bежемесячно\b",                     ("monthly", 1)),
    (r"\bкаждые\s+(\d+)\s+недел(?:ей|и|ю)?\b", ("weekly", None)),
    (r"\bкаждую\s+недел(?:ю)\b",           ("weekly", 1)),
    (r"\bеженедельно\b",                    ("weekly", 1)),
    (r"\bкаждый\s+день\b",                 ("daily", 1)),
    (r"\bежедневно\b",                      ("daily", 1)),
    (r"\bкаждые\s+(\d+)\s+дн(?:ей|я|ень)?\b",   ("days", None)),
]


def replace_time_words(text: str) -> str:
    for patt, repl in TIME_WORDS.items():
        text = re.sub(patt, repl, flags=re.IGNORECASE, string=text)
    return text


def normalize_time(text: str) -> str:
    return re.sub(r"(\b[0-2]?\d)[\s\-]+([0-5]\d\b)", r"\1:\2", text)


def split_message(text: str):
    """Делит текст на date_part, time_part (HH:MM) и task_part."""
    txt = replace_time_words(text.lower())
    txt = normalize_time(txt)

    rel = re.match(
        r"^\s*(через\s+\d+\s*(?:минут(?:у|ы)?|час(?:ов|а)?|дн(?:ень|я|ей)?))\b(.*)",
        txt, flags=re.IGNORECASE
    )
    if rel:
        return rel.group(1).strip(), None, rel.group(2).strip()

    m = re.search(r"\b([0-2]?\d:[0-5]\d)\b", txt)
    if m:
        return txt[:m.start()].strip(), m.group(1), txt[m.end():].strip()

    m2 = re.search(r"\b([0-2]?\d)\b", txt)
    if m2:
        h = int(m2.group(1))
        if 0 <= h <= 23:
            return txt[:m2.start()].strip(), f"{h}:00", txt[m2.end():].strip()

    return txt, None, ""


def extract_repeat_info(text: str):
    """Возвращает (rpt_type, interval, cleaned_text)."""
    rpt_type = None
    interval = 1
    cleaned = text
    for patt, (rtype, default) in REPEAT_PATTERNS:
        m = re.search(patt, text)
        if m:
            rpt_type = rtype
            interval = int(m.group(1)) if default is None and m.groups() else default
            cleaned = re.sub(patt, "", cleaned)
            break
    return rpt_type, interval, cleaned.strip()


def parse_input(raw_text: str):
    """Парсит ввод — возвращает reminder_text, slots, rpt_type, interval."""
    # Normalize text and extract repeat info
    txt = replace_time_words(raw_text.lower())
    txt = normalize_time(txt)
    rpt_type, interval, cleaned = extract_repeat_info(txt)

    # Split into parts
    date_part, time_part, task_part = split_message(cleaned)
    date_part = re.sub(r"\b(?:в|к|на|около|примерно)\b\s*$", "", date_part).strip()

    # Parse date
    now = datetime.now()
    parsed = now if rpt_type == "daily" else dateparser.parse(
        date_part,
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now},
        languages=["ru"],
    )
    if not parsed:
        raise ValueError(f"Не удалось распарсить дату: '{date_part}'")
    is_relative = bool(re.match(r"^\s*через\s+", date_part))

    # Build reminder slots
    slots = []
    if time_part:
        h, m = map(int, time_part.split(':'))
        slots.append(parsed.replace(hour=h, minute=m, second=0, microsecond=0))
    elif is_relative:
        slots.append(parsed)
    else:
        slots.extend([
            parsed.replace(hour=9, minute=0, second=0, microsecond=0),
            parsed.replace(hour=21, minute=0, second=0, microsecond=0)
        ])

    # Adjust slots for repeats
    if rpt_type:
        slots = adjust_initial_slots(slots, rpt_type, interval, now)

    # Final reminder text
    reminder_text = (task_part or raw_text).strip()
    return reminder_text, slots, rpt_type, interval
