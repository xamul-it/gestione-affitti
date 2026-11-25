"""
TipoDiritto: kind of right on a property as listed in a visura catastale.
Plain enum (no table): the rights themselves are core relations on beni.
"""
from enum import Enum


class TipoDiritto(str, Enum):
    PROPRIETARIO = "PROPRIETARIO"
    COMPROPRIETARIO = "COMPROPRIETARIO"
    USUFRUTTUARIO = "USUFRUTTUARIO"
    NUDA_PROPRIETA = "NUDA_PROPRIETA"
    USO = "USO"
    ABITAZIONE = "ABITAZIONE"
    SUPERFICIE = "SUPERFICIE"
    ENFITEUSI = "ENFITEUSI"
    ALTRO = "ALTRO"
