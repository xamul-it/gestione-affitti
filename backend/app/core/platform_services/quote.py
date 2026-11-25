"""Shares ("quote") of a relation, written as a fraction like in the cadastral records."""
import re
from typing import Tuple

_QUOTA = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


def parse_quota(testo: str) -> Tuple[int, int]:
    """'1/2' (or '1 / 2') -> (1, 2). The share must be > 0 and <= 1; kept as written (2/4 stays 2/4)."""
    m = _QUOTA.match(testo or "")
    if not m:
        raise ValueError(f"Quota '{testo}' non valida: usare una frazione, es. 1/2")
    num, den = int(m.group(1)), int(m.group(2))
    if den == 0 or num == 0 or num > den:
        raise ValueError(f"Quota '{testo}' non valida: deve essere maggiore di zero e al massimo 1")
    return num, den
