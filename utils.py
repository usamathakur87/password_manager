# utils.py
import unicodedata
from datetime import datetime

def parse_datetime(dt_string):
    try:
        return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")  # with microseconds
    except ValueError:
        return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")    # without microseconds

def remove_invisible_chars(s: str) -> str:
    """
    Remove (or normalize away) invisible Unicode characters such as \u202A
    """
    filtered = "".join(ch for ch in s if ch.isprintable())
    filtered = unicodedata.normalize('NFKC', filtered)
    return filtered
