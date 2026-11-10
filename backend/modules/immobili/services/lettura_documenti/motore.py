"""
Field engine shared by the backend (native-text PDFs) and the external OCR
service (scans): the same specs, applied the same way.

A spec has `riconosci` (expressions that must ALL match for the text to be of
that type) and `campi` (one expression per field; the value is group `v`,
first match). Flags: case-insensitive, dot matches newline.

The OCR service (~/Progetti/mrz/campi.py) keeps an identical copy: change
both together.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

FLAGS = re.IGNORECASE | re.DOTALL


@dataclass
class SpecTipo:
    codice: str
    riconosci: List[str]
    campi: Dict[str, str] = field(default_factory=dict)
    scarto: Optional[str] = None  # message: the type belongs to another module

    def to_dict(self) -> dict:
        return {"codice": self.codice, "riconosci": list(self.riconosci), "campi": dict(self.campi)}


@dataclass
class RisultatoTipo:
    codice: str
    riconosciuto: bool
    campi: Dict[str, str] = field(default_factory=dict)


def applica(spec: SpecTipo, testo: str) -> RisultatoTipo:
    riconosciuto = all(re.search(p, testo, FLAGS) for p in spec.riconosci)
    campi = {}
    for nome, pattern in spec.campi.items():
        m = re.search(pattern, testo, FLAGS)
        if m and m.group("v") is not None:
            valore = " ".join(m.group("v").split())
            if valore:
                campi[nome] = valore
    return RisultatoTipo(spec.codice, riconosciuto, campi)
