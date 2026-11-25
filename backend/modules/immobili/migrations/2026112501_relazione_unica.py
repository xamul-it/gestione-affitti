"""Rights and tenancies of beni move into the core relations (phase 3 of
docs/superpowers/specs/2026-11-10-beni-catastali-design.md).

immo_diritti_immobile + immo_proprietari -> core_relazioni (diritti_reali types),
immo_assegnazioni_conduttore + immo_conduttori -> core_relazioni (type conduttore),
documents of a PROPRIETARIO -> the soggetto. The four old tables are then dropped.

The INSERTs bypass RelazioneService and core_relazioni has no uniqueness
constraint: the duplicate pre-check in converti() is the only defence, and
every check runs before the first write. Nothing is zeroed. Downgrade is
the backup.

Order of operations (scripts/sync_modules.py): core alembic -> sync of relation
types -> module migrations. Do not run this migration alone.
"""
import re
from fractions import Fraction

from alembic import op, context
from sqlalchemy import text

revision = "2026112501_relazione_unica"
down_revision = "2026111401_collegamenti_beni"
branch_labels = None
depends_on = None

target_schema = "tenant"

ENTITY_TYPE = "IMMOBILE"
MODULO = "immobili"

# Old TipoDiritto -> relation type code (copy of relazioni_bene.MAPPA_TIPO_DIRITTO:
# migrations do not import application code).
MAPPA_TIPO_DIRITTO = {
    "PROPRIETARIO": "proprieta",
    "COMPROPRIETARIO": "proprieta",
    "NUDA_PROPRIETA": "nuda_proprieta",
    "USUFRUTTUARIO": "usufrutto",
    "USO": "uso",
    "ABITAZIONE": "abitazione",
    "SUPERFICIE": "superficie",
    "ENFITEUSI": "enfiteusi",
    "ALTRO": "diritto_reale_altro",
}

VECCHIE_TABELLE = (
    "immo_assegnazioni_conduttore", "immo_diritti_immobile",
    "immo_conduttori", "immo_proprietari",
)

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_APERTO = "(r.data_fine IS NULL OR r.data_fine >= CURRENT_DATE)"


def quota_in_frazione(percentuale):
    """Old percentage -> (numerator, denominator, da_ricontrollare)."""
    if percentuale is None:
        return None, None, False
    p = round(float(percentuale), 2)
    if p <= 0 or p > 100:
        return None, None, True
    f = Fraction(p / 100).limit_denominator(24)
    if round(float(f) * 100, 2) == p:
        return f.numerator, f.denominator, False
    num = round(p * 100)
    return num, 10000, True


def _esiste(conn, tabella) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": tabella}).scalar())


def _data(valore):
    """Old text date -> ISO string or None; ValueError if malformed."""
    from datetime import date
    if valore is None or str(valore).strip() == "":
        return None
    s = str(valore).strip()
    if not _ISO.match(s):
        raise ValueError(s)
    date.fromisoformat(s)
    return s


def _ruoli(conn, codici):
    rows = conn.execute(text(
        "SELECT codice, id FROM public.core_ruoli_disponibili "
        "WHERE modulo_id = :m AND codice = ANY(:c)"), {"m": MODULO, "c": list(codici)}).all()
    trovati = {r.codice: r.id for r in rows}
    mancanti = sorted(set(codici) - set(trovati))
    if mancanti:
        raise RuntimeError(
            f"Relation types missing in core_ruoli_disponibili: {', '.join(mancanti)}. "
            "Run `alembic -x schema=all upgrade head` and then `python scripts/sync_modules.py` "
            "(do not run the module migration alone).")
    return trovati


def converti(conn) -> dict:
    """Copy rights and tenancies into core_relazioni; returns the counts. Does not drop tables."""
    conteggi = {"diritti": 0, "assegnazioni": 0, "documenti_proprietario": 0,
                "proprietari_senza_diritti": 0, "conduttori_senza_assegnazioni": 0}
    presenti = {t: _esiste(conn, t) for t in VECCHIE_TABELLE}
    if not any(presenti.values()):
        return conteggi
    if not _esiste(conn, "core_relazioni") or not conn.execute(text(
            "SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() "
            "AND table_name = 'core_relazioni' AND column_name = 'quota_numeratore'")).first():
        raise RuntimeError(
            "core_relazioni.quota_numeratore is missing: run `alembic -x schema=all upgrade head` "
            "before the module migrations (scripts/sync_modules.py).")

    diritti = []
    if presenti["immo_diritti_immobile"] and presenti["immo_proprietari"]:
        diritti = conn.execute(text(
            "SELECT d.id, d.bene_id, p.soggetto_id, d.tipo_diritto::text AS tipo_diritto, "
            "d.quota_percentuale, d.data_inizio, d.data_fine, d.note, p.note_proprietario, d.created_at "
            "FROM immo_diritti_immobile d JOIN immo_proprietari p ON p.id = d.proprietario_id "
            "ORDER BY d.id")).all()
    n_assegnazioni = 0
    if presenti["immo_assegnazioni_conduttore"] and presenti["immo_conduttori"]:
        n_assegnazioni = conn.execute(text(
            "SELECT count(*) FROM immo_assegnazioni_conduttore a "
            "JOIN immo_conduttori c ON c.id = a.conduttore_id")).scalar()

    # ---- checks, before any write -------------------------------------------------
    righe = []
    for d in diritti:
        try:
            inizio = _data(d.data_inizio)
        except ValueError:
            raise RuntimeError(f"Diritto {d.id}: data_inizio '{d.data_inizio}' is not YYYY-MM-DD")
        try:
            fine = _data(d.data_fine)
        except ValueError:
            raise RuntimeError(f"Diritto {d.id}: data_fine '{d.data_fine}' is not YYYY-MM-DD")
        tipo = MAPPA_TIPO_DIRITTO.get(d.tipo_diritto)
        if tipo is None:
            raise RuntimeError(f"Diritto {d.id}: unknown tipo_diritto '{d.tipo_diritto}'")
        if inizio and fine and fine < inizio:
            raise RuntimeError(f"Diritto {d.id}: data_fine {fine} precedes data_inizio {inizio}")
        righe.append((d, tipo, inizio, fine))

    from datetime import date
    oggi = date.today().isoformat()
    aperti = {}
    for d, tipo, inizio, fine in righe:
        if fine is None or fine >= oggi:
            aperti.setdefault((d.bene_id, d.soggetto_id, tipo), []).append(d.id)
    doppioni = [f"bene {b}, soggetto {s}, tipo {t}: diritti {ids}"
                for (b, s, t), ids in sorted(aperti.items()) if len(ids) > 1]

    if n_assegnazioni:
        invertite = [r.id for r in conn.execute(text(
            "SELECT a.id FROM immo_assegnazioni_conduttore a JOIN immo_conduttori c ON c.id = a.conduttore_id "
            "WHERE a.data_fine < a.data_inizio ORDER BY a.id"))]
        if invertite:
            raise RuntimeError(f"Assegnazioni {invertite}: data_fine precedes data_inizio, nothing was written")
        for r in conn.execute(text(
                "SELECT a.bene_id, c.soggetto_id, array_agg(a.id ORDER BY a.id) AS ids "
                "FROM immo_assegnazioni_conduttore a JOIN immo_conduttori c ON c.id = a.conduttore_id "
                "WHERE (a.data_fine IS NULL OR a.data_fine >= CURRENT_DATE) "
                "GROUP BY a.bene_id, c.soggetto_id HAVING count(*) > 1 ORDER BY 1, 2")):
            doppioni.append(f"bene {r.bene_id}, soggetto {r.soggetto_id}, tipo conduttore: assegnazioni {list(r.ids)}")

    codici = {tipo for _, tipo, _, _ in righe}
    if n_assegnazioni:
        codici.add("conduttore")
    ruoli = _ruoli(conn, codici) if codici else {}

    # Open relations already in core_relazioni would be duplicated too.
    gia = []
    if ruoli:
        for b, s, t in sorted(aperti):
            esiste = conn.execute(text(
                f"SELECT 1 FROM core_relazioni r WHERE r.ruolo_id = :ruolo AND r.entity_type = :et "
                f"AND r.entity_id = :b AND r.soggetto_id = :s AND {_APERTO}"),
                {"ruolo": ruoli[t], "et": ENTITY_TYPE, "b": b, "s": s}).first()
            if esiste:
                gia.append(f"bene {b}, soggetto {s}, tipo {t}: already in core_relazioni")
        if n_assegnazioni:
            for r in conn.execute(text(
                    f"SELECT a.bene_id, c.soggetto_id FROM immo_assegnazioni_conduttore a "
                    f"JOIN immo_conduttori c ON c.id = a.conduttore_id "
                    f"JOIN core_relazioni r ON r.ruolo_id = :ruolo AND r.entity_type = :et "
                    f"AND r.entity_id = a.bene_id AND r.soggetto_id = c.soggetto_id AND {_APERTO} "
                    f"WHERE (a.data_fine IS NULL OR a.data_fine >= CURRENT_DATE)"),
                    {"ruolo": ruoli["conduttore"], "et": ENTITY_TYPE}):
                gia.append(f"bene {r.bene_id}, soggetto {r.soggetto_id}, tipo conduttore: already in core_relazioni")
    if doppioni or gia:
        raise RuntimeError(
            "Open duplicate rights on the same bene, nothing was written. Close or fix these first: "
            + "; ".join(doppioni + gia))

    # ---- writes -------------------------------------------------------------------
    for d, tipo, inizio, fine in righe:
        num, den, controllo = quota_in_frazione(d.quota_percentuale)
        if controllo:
            print(f"  quota da ricontrollare: diritto {d.id} bene {d.bene_id} "
                  f"soggetto {d.soggetto_id} ({d.quota_percentuale}% -> {num}/{den})", flush=True)
        dati = None
        if d.note_proprietario and d.note_proprietario.strip():
            dati = '{"note_ruolo": ' + _json(d.note_proprietario) + '}'
        conn.execute(text(
            "INSERT INTO core_relazioni (soggetto_id, ruolo_id, entity_type, entity_id, "
            "data_inizio, data_fine, note, dati, quota_numeratore, quota_denominatore, created_at) "
            "VALUES (:s, :ruolo, :et, :b, CAST(:i AS date), CAST(:f AS date), :note, "
            "CAST(:dati AS json), :n, :d, COALESCE(:ca, now()))"),
            {"s": d.soggetto_id, "ruolo": ruoli[tipo], "et": ENTITY_TYPE, "b": d.bene_id,
             "i": inizio, "f": fine, "note": d.note, "dati": dati, "n": num, "d": den,
             "ca": d.created_at})
    conteggi["diritti"] = len(righe)

    if n_assegnazioni:
        res = conn.execute(text(
            "INSERT INTO core_relazioni (soggetto_id, ruolo_id, entity_type, entity_id, "
            "data_inizio, data_fine, note, dati, created_at) "
            "SELECT c.soggetto_id, :ruolo, :et, a.bene_id, a.data_inizio, a.data_fine, a.note, "
            "CASE WHEN btrim(coalesce(c.note, '')) <> '' "
            "THEN json_build_object('note_ruolo', c.note) END, COALESCE(a.created_at, now()) "
            "FROM immo_assegnazioni_conduttore a JOIN immo_conduttori c ON c.id = a.conduttore_id "
            "ORDER BY a.id"), {"ruolo": ruoli["conduttore"], "et": ENTITY_TYPE})
        conteggi["assegnazioni"] = res.rowcount
    if conteggi["assegnazioni"] != n_assegnazioni:
        raise RuntimeError(
            f"Migrated {conteggi['assegnazioni']} tenancies out of {n_assegnazioni}: aborting before the drop")

    if presenti["immo_proprietari"] and _esiste(conn, "core_documenti"):
        conteggi["documenti_proprietario"] = conn.execute(text(
            "UPDATE core_documenti d SET entity_type = 'SOGGETTO_ANAGRAFICO', entity_id = p.soggetto_id "
            "FROM immo_proprietari p WHERE d.entity_type = 'PROPRIETARIO' AND d.entity_id = p.id")).rowcount
    if presenti["immo_proprietari"]:
        conteggi["proprietari_senza_diritti"] = conn.execute(text(
            "SELECT count(*) FROM immo_proprietari p WHERE NOT EXISTS "
            + ("(SELECT 1 FROM immo_diritti_immobile d WHERE d.proprietario_id = p.id)"
               if presenti["immo_diritti_immobile"] else "(SELECT 1 WHERE false)"))).scalar()
    if presenti["immo_conduttori"]:
        conteggi["conduttori_senza_assegnazioni"] = conn.execute(text(
            "SELECT count(*) FROM immo_conduttori c WHERE NOT EXISTS "
            + ("(SELECT 1 FROM immo_assegnazioni_conduttore a WHERE a.conduttore_id = c.id)"
               if presenti["immo_assegnazioni_conduttore"] else "(SELECT 1 WHERE false)"))).scalar()
    return conteggi


def _json(valore: str) -> str:
    import json
    return json.dumps(valore.strip(), ensure_ascii=False)


def _get_target_schema():
    return context.get_x_argument(as_dictionary=True).get("schema")


def upgrade():
    schema = _get_target_schema()
    if not schema or schema == "public":
        return
    conn = op.get_bind()
    conteggi = converti(conn)
    print(f"  [{schema}] relazione_unica: {conteggi}", flush=True)
    for tabella in VECCHIE_TABELLE:
        conn.execute(text(f"DROP TABLE IF EXISTS {tabella}"))


def downgrade():
    raise NotImplementedError("Restore from the backup taken before the migration")
