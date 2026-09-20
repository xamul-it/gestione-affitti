"""
Integration tests for anagrafica_italiana's public_api (trova_o_crea_soggetto).

Uses real PostgreSQL (pg_session), not the SQLite db_session fixture — see
tests/unit/test_core/test_notifica_model.py for why db_session is broken
for any row-creating test in this repo.
"""
import pytest
from datetime import date
from sqlalchemy import text

from app.core.database import SessionLocal
from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
from anagrafica_italiana.services.public_api import trova_o_crea_soggetto


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    session = SessionLocal()
    try:
        session.execute(text("SET search_path TO tenant_qa_test, public"))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


def _cleanup(pg_session, soggetto_ids):
    ids = [i for i in soggetto_ids if i]
    if ids:
        pg_session.query(SoggettoAnagrafico).filter(SoggettoAnagrafico.id.in_(ids)).delete(synchronize_session=False)
    pg_session.commit()


def test_creates_new_soggetto_when_no_match(pg_session):
    """An identifier is required to create anything at all (see
    test_returns_none_and_creates_nothing_without_any_identifier) — this
    test covers the "identifier given, but nothing matches it yet" path."""
    dto = trova_o_crea_soggetto(
        pg_session,
        nome="Anna",
        cognome="Verdi",
        data_nascita=date(1995, 3, 10),
        codice_fiscale="VRDNNA95C50H501X",
    )
    try:
        assert dto is not None
        assert dto.creato_ora is True
        soggetto = pg_session.query(SoggettoAnagrafico).filter_by(id=dto.id).first()
        assert soggetto is not None
        assert soggetto.nome == "Anna"
        assert soggetto.cognome == "Verdi"
    finally:
        _cleanup(pg_session, [dto.id])


def test_reuses_existing_soggetto_on_exact_codice_fiscale(pg_session):
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Mario",
        cognome="Bianchi",
        codice_fiscale="BNCMRA80A01H501Z",
    )
    try:
        assert first.creato_ora is True

        second = trova_o_crea_soggetto(
            pg_session,
            nome="Mario",
            cognome="Bianchi",
            codice_fiscale="bncmra80a01h501z",  # lowercase — must still match
        )
        assert second.creato_ora is False
        assert second.id == first.id

        count = (
            pg_session.query(SoggettoAnagrafico)
            .filter(SoggettoAnagrafico.codice_fiscale == "BNCMRA80A01H501Z")
            .count()
        )
        assert count == 1
    finally:
        _cleanup(pg_session, [first.id])


def test_reuses_existing_soggetto_on_exact_documento_identita(pg_session):
    """The scenario this whole change exists for: a foreign tourist with no
    codice fiscale, identified by passport number instead. Case and
    surrounding whitespace must not matter on ANY of the three document
    fields — not just the number (regression test: tipo_documento_identita
    and stato_rilascio_documento were previously compared case-sensitively,
    silently failing to match "Francia" against a stored "FRANCIA")."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Jean",
        cognome="Dupont",
        data_nascita=date(1988, 7, 4),
        tipo_documento_identita="passaporto",
        numero_documento_identita="fr123456",
        stato_rilascio_documento="Francia",
    )
    try:
        assert first.creato_ora is True

        # Same guest, second stay some time later — different case/whitespace
        # on every one of the three document fields.
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Jean",
            cognome="Dupont",
            data_nascita=date(1988, 7, 4),
            tipo_documento_identita=" PASSAPORTO ",
            numero_documento_identita="FR123456",
            stato_rilascio_documento="FRANCIA",
        )
        assert second.creato_ora is False
        assert second.id == first.id
    finally:
        _cleanup(pg_session, [first.id])


def test_does_not_merge_different_people_sharing_name_and_birthdate(pg_session):
    """A fuzzy name+DOB coincidence must never trigger an automatic merge —
    only a real identifier (CF or document) counts as a certain match. Two
    genuinely different people (different codice fiscale) who happen to
    share a name and birth date — the exact scenario where the fuzzy score
    can coincidentally reach 1.0 (nome+cognome+data_nascita all identical,
    weights sum to 1.0) — must stay two distinct registry entries."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Mario",
        cognome="Rossi",
        data_nascita=date(1980, 1, 1),
        codice_fiscale="RSSMRA80A01H501A",
    )
    second = None
    try:
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1),
            codice_fiscale="RSSMRA80A01H501B",  # different person, different CF
        )
        assert second is not None
        assert second.creato_ora is True
        assert second.id != first.id
    finally:
        _cleanup(pg_session, [first.id, second.id if second else None])


def test_different_document_country_does_not_match(pg_session):
    """A document number alone isn't globally unique — the issuing country
    must match too, or it's treated as a different soggetto."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Anna",
        cognome="Kowalski",
        tipo_documento_identita="CARTA_IDENTITA",
        numero_documento_identita="XYZ1000",
        stato_rilascio_documento="POLONIA",
    )
    second = None
    try:
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Anna",
            cognome="Kowalski",
            tipo_documento_identita="CARTA_IDENTITA",
            numero_documento_identita="XYZ1000",
            stato_rilascio_documento="GERMANIA",
        )
        assert second.creato_ora is True
        assert second.id != first.id
    finally:
        _cleanup(pg_session, [first.id, second.id if second else None])


def test_incomplete_document_on_stored_record_never_matches(pg_session):
    """A registry row with an INCOMPLETE document triple (e.g. created
    through some other path than this one, missing stato_rilascio_documento)
    must never match a later query that supplies the full triple — the
    reverse of the "different country" case, closing the same asymmetry
    (a document match requires all three fields on BOTH sides, not just
    the query side)."""
    existing = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Piotr",
        cognome="Nowak",
        tipo_documento_identita="CARTA_IDENTITA",
        numero_documento_identita="POL5000",
        stato_rilascio_documento=None,  # incomplete on purpose
    )
    pg_session.add(existing)
    pg_session.commit()

    second = None
    try:
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Piotr",
            cognome="Nowak",
            tipo_documento_identita="CARTA_IDENTITA",
            numero_documento_identita="POL5000",
            stato_rilascio_documento="POLONIA",
        )
        assert second is not None
        assert second.creato_ora is True
        assert second.id != existing.id
    finally:
        _cleanup(pg_session, [existing.id, second.id if second else None])


def test_returns_none_and_creates_nothing_without_any_identifier(pg_session):
    """A guest with neither a codice fiscale nor a complete identity
    document (the common case for accompanying guests / minors on
    self-service forms) must not spawn a new, permanently-unlinkable
    registry row on every call — the function returns None instead."""
    before = pg_session.query(SoggettoAnagrafico).count()

    result = trova_o_crea_soggetto(
        pg_session,
        nome="Bimbo",
        cognome="SenzaDocumento",
    )

    assert result is None
    after = pg_session.query(SoggettoAnagrafico).count()
    assert after == before

    # Also: a document missing just the issuing country is still "incomplete".
    result = trova_o_crea_soggetto(
        pg_session,
        nome="Bimbo",
        cognome="SenzaDocumento",
        tipo_documento_identita="CARTA_IDENTITA",
        numero_documento_identita="X1",
    )
    assert result is None
    assert pg_session.query(SoggettoAnagrafico).count() == before


def test_backfills_missing_identifier_on_existing_soggetto(pg_session):
    """A soggetto first seen with only a passport later gets their codice
    fiscale filled in once it's known — without this, they can never
    become findable by CF, permanently defeating cross-module recognition."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Sofia",
        cognome="Costa",
        tipo_documento_identita="PASSAPORTO",
        numero_documento_identita="PT777",
        stato_rilascio_documento="PORTOGALLO",
    )
    try:
        assert first.creato_ora is True

        second = trova_o_crea_soggetto(
            pg_session,
            nome="Sofia",
            cognome="Costa",
            tipo_documento_identita="PASSAPORTO",
            numero_documento_identita="PT777",
            stato_rilascio_documento="PORTOGALLO",
            codice_fiscale="CSTSOF90A01Z000X",
        )
        assert second.id == first.id

        soggetto = pg_session.query(SoggettoAnagrafico).filter_by(id=first.id).first()
        assert soggetto.codice_fiscale == "CSTSOF90A01Z000X"

        # A THIRD encounter, now findable by CF alone.
        third = trova_o_crea_soggetto(
            pg_session,
            nome="Sofia",
            cognome="Costa",
            codice_fiscale="cstsof90a01z000x",
        )
        assert third.id == first.id
    finally:
        _cleanup(pg_session, [first.id])
