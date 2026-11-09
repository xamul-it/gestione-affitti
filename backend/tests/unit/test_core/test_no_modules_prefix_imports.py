"""
Business modules must be imported by their own name (`anagrafica_italiana`),
never as `modules.anagrafica_italiana`.

Both resolve, because backend/ and backend/modules/ are both on sys.path,
but Python treats them as two different modules: every model is defined a
second time on the same declarative Base, and from then on mapper
configuration fails in the whole process ("Multiple classes found for path
'SoggettoAnagrafico'"). That is what broke the document parsing callback
and most of the integration suite when run as a whole.
"""
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
PATTERN = re.compile(r"^\s*(from|import)\s+modules\.\w", re.MULTILINE)


def test_no_imports_through_modules_package():
    offenders = []
    for root in ("app", "modules", "tests"):
        for path in (BACKEND / root).rglob("*.py"):
            if "venv" in path.parts:
                continue
            for match in PATTERN.finditer(path.read_text(encoding="utf-8")):
                line = path.read_text(encoding="utf-8")[: match.start()].count("\n") + 1
                offenders.append(f"{path.relative_to(BACKEND)}:{line}")
    assert offenders == [], "import via 'modules.' (usa il nome del modulo):\n" + "\n".join(offenders)
