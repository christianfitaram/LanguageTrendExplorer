from datetime import time, datetime, UTC
import re

pattern = r'^(\d+)-(202[5-9]|20[3-9]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$'


def is_valid_sample(sample):
    match = re.match(pattern, sample)
    if not match:
        return False

    # Extract parts from the match
    _, year, month, day = match.groups()
    date_str = f"{year}-{month}-{day}"

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
