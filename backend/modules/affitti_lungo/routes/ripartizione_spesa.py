from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import RipartizioneSpesa
from ..models import Spesa
from ..models import MillesimiUnita
from ..models import TabellaMillesimale, TipoRipartizione
from ..schemas.ripartizione_spesa import RipartizioneSpesaCreate, RipartizioneSpesaUpdate, RipartizioneSpesaResponse

router = APIRouter(prefix="/ripartizioni-spese", tags=["Ripartizioni Spese"])


@router.get("/", response_model=List[RipartizioneSpesaResponse])
def get_ripartizioni(
    skip: int = 0,
    limit: int = 100,
    spesa_id: int = None,
    unita_immobiliare_id: int = None,
    db: Session = Depends(get_db)
):
    """Ottieni lista delle ripartizioni spese"""
    query = db.query(RipartizioneSpesa)
    if spesa_id:
        query = query.filter(RipartizioneSpesa.spesa_id == spesa_id)
    if unita_immobiliare_id:
        query = query.filter(RipartizioneSpesa.unita_immobiliare_id == unita_immobiliare_id)
    ripartizioni = query.offset(skip).limit(limit).all()
    return ripartizioni


@router.get("/spesa/{spesa_id}", response_model=List[RipartizioneSpesaResponse])
def get_ripartizioni_by_spesa(spesa_id: int, db: Session = Depends(get_db)):
    """Ottieni tutte le ripartizioni di una spesa"""
    ripartizioni = db.query(RipartizioneSpesa).filter(
        RipartizioneSpesa.spesa_id == spesa_id
    ).all()
    return ripartizioni


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[RipartizioneSpesaResponse])
def get_ripartizioni_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni tutte le ripartizioni per un'unità immobiliare"""
    ripartizioni = db.query(RipartizioneSpesa).filter(
        RipartizioneSpesa.unita_immobiliare_id == unita_immobiliare_id
    ).all()
    return ripartizioni


@router.get("/{ripartizione_id}", response_model=RipartizioneSpesaResponse)
def get_ripartizione(ripartizione_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una ripartizione specifica"""
    ripartizione = db.query(RipartizioneSpesa).filter(RipartizioneSpesa.id == ripartizione_id).first()
    if not ripartizione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ripartizione con ID {ripartizione_id} non trovata"
        )
    return ripartizione


@router.post("/calcola/{spesa_id}", response_model=List[RipartizioneSpesaResponse])
def calcola_ripartizione_spesa(spesa_id: int, db: Session = Depends(get_db)):
    """Calcola automaticamente la ripartizione di una spesa condominiale"""
    # Recupera la spesa
    spesa = db.query(Spesa).filter(Spesa.id == spesa_id).first()
    if not spesa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spesa con ID {spesa_id} non trovata"
        )

    if not spesa.spesa_condominiale:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La spesa non è marcata come spesa condominiale"
        )

    if not spesa.tabella_millesimale_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La spesa non ha una tabella millesimale associata"
        )

    # Recupera la tabella millesimale
    tabella = db.query(TabellaMillesimale).filter(
        TabellaMillesimale.id == spesa.tabella_millesimale_id
    ).first()
    if not tabella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tabella millesimale non trovata"
        )

    # Recupera tutti gli immobili con millesimi per questa tabella
    millesimi_immobili = db.query(MillesimiUnita).filter(
        MillesimiUnita.tabella_millesimale_id == tabella.id
    ).all()

    if not millesimi_immobili:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun immobile associato a questa tabella millesimale"
        )

    # Elimina eventuali ripartizioni precedenti
    db.query(RipartizioneSpesa).filter(RipartizioneSpesa.spesa_id == spesa_id).delete()

    # Calcola la ripartizione in base al tipo
    ripartizioni = []

    if tabella.tipo_ripartizione == TipoRipartizione.MILLESIMI:
        # Ripartizione pura a millesimi
        totale_millesimi = sum(m.millesimi for m in millesimi_immobili)
        for millesimo in millesimi_immobili:
            quota = (millesimo.millesimi / totale_millesimi) * spesa.importo
            ripartizione = RipartizioneSpesa(
                spesa_id=spesa_id,
                unita_immobiliare_id=millesimo.unita_immobiliare_id,
                importo_ripartito=round(quota, 2),
                millesimi_applicati=millesimo.millesimi,
                importo_da_millesimi=round(quota, 2)
            )
            db.add(ripartizione)
            ripartizioni.append(ripartizione)

    elif tabella.tipo_ripartizione == TipoRipartizione.MILLESIMI_CONSUMO:
        # Ripartizione mista millesimi + consumo (es. riscaldamento)
        totale_millesimi = sum(m.millesimi for m in millesimi_immobili)
        totale_consumo = sum(m.consumo for m in millesimi_immobili)

        importo_millesimi = spesa.importo * (tabella.percentuale_millesimi / 100)
        importo_consumo = spesa.importo * (tabella.percentuale_consumo / 100)

        for millesimo in millesimi_immobili:
            quota_millesimi = (millesimo.millesimi / totale_millesimi) * importo_millesimi if totale_millesimi > 0 else 0
            quota_consumo = (millesimo.consumo / totale_consumo) * importo_consumo if totale_consumo > 0 else 0
            quota_totale = quota_millesimi + quota_consumo

            ripartizione = RipartizioneSpesa(
                spesa_id=spesa_id,
                unita_immobiliare_id=millesimo.unita_immobiliare_id,
                importo_ripartito=round(quota_totale, 2),
                millesimi_applicati=millesimo.millesimi,
                consumo_applicato=millesimo.consumo,
                importo_da_millesimi=round(quota_millesimi, 2),
                importo_da_consumo=round(quota_consumo, 2)
            )
            db.add(ripartizione)
            ripartizioni.append(ripartizione)

    elif tabella.tipo_ripartizione == TipoRipartizione.OCCUPANTI:
        # Ripartizione per occupanti
        totale_occupanti = sum(m.numero_occupanti for m in millesimi_immobili)
        if totale_occupanti == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Numero occupanti non specificato per gli immobili"
            )

        for millesimo in millesimi_immobili:
            quota = (millesimo.numero_occupanti / totale_occupanti) * spesa.importo
            ripartizione = RipartizioneSpesa(
                spesa_id=spesa_id,
                unita_immobiliare_id=millesimo.unita_immobiliare_id,
                importo_ripartito=round(quota, 2),
                occupanti_applicati=millesimo.numero_occupanti,
                importo_da_occupanti=round(quota, 2)
            )
            db.add(ripartizione)
            ripartizioni.append(ripartizione)

    elif tabella.tipo_ripartizione == TipoRipartizione.MILLESIMI_PIANO:
        # Ripartizione con coefficiente piano (ascensore)
        # Coefficiente: piano 0 = 1, piano 1 = 1.5, piano 2 = 2, ecc.
        totale_ponderato = 0
        for m in millesimi_immobili:
            piano = m.piano if m.piano is not None else 0
            coefficiente = 1.0 + (piano * 0.5) if piano > 0 else 1.0
            totale_ponderato += m.millesimi * coefficiente

        for millesimo in millesimi_immobili:
            piano = millesimo.piano if millesimo.piano is not None else 0
            coefficiente = 1.0 + (piano * 0.5) if piano > 0 else 1.0
            millesimi_ponderati = millesimo.millesimi * coefficiente
            quota = (millesimi_ponderati / totale_ponderato) * spesa.importo

            ripartizione = RipartizioneSpesa(
                spesa_id=spesa_id,
                unita_immobiliare_id=millesimo.unita_immobiliare_id,
                importo_ripartito=round(quota, 2),
                millesimi_applicati=millesimo.millesimi,
                coefficiente_piano=coefficiente,
                importo_da_millesimi=round(quota, 2)
            )
            db.add(ripartizione)
            ripartizioni.append(ripartizione)

    elif tabella.tipo_ripartizione == TipoRipartizione.PERSONALIZZATA:
        # Ripartizione personalizzata con quote fisse
        totale_quote = sum(m.quota_fissa for m in millesimi_immobili if m.quota_fissa)
        if totale_quote == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quote fisse non specificate per gli immobili"
            )

        for millesimo in millesimi_immobili:
            if millesimo.quota_fissa:
                quota = (millesimo.quota_fissa / totale_quote) * spesa.importo
                ripartizione = RipartizioneSpesa(
                    spesa_id=spesa_id,
                    unita_immobiliare_id=millesimo.unita_immobiliare_id,
                    importo_ripartito=round(quota, 2)
                )
                db.add(ripartizione)
                ripartizioni.append(ripartizione)

    # Marca la spesa come ripartita
    spesa.ripartita = 1

    db.commit()
    for r in ripartizioni:
        db.refresh(r)

    return ripartizioni


@router.post("/", response_model=RipartizioneSpesaResponse, status_code=status.HTTP_201_CREATED)
def create_ripartizione(ripartizione: RipartizioneSpesaCreate, db: Session = Depends(get_db)):
    """Crea una nuova ripartizione manuale"""
    new_ripartizione = RipartizioneSpesa(**ripartizione.model_dump())
    db.add(new_ripartizione)
    db.commit()
    db.refresh(new_ripartizione)
    return new_ripartizione


@router.put("/{ripartizione_id}", response_model=RipartizioneSpesaResponse)
def update_ripartizione(ripartizione_id: int, ripartizione: RipartizioneSpesaUpdate, db: Session = Depends(get_db)):
    """Aggiorna una ripartizione esistente"""
    db_ripartizione = db.query(RipartizioneSpesa).filter(RipartizioneSpesa.id == ripartizione_id).first()
    if not db_ripartizione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ripartizione con ID {ripartizione_id} non trovata"
        )

    update_data = ripartizione.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ripartizione, field, value)

    db.commit()
    db.refresh(db_ripartizione)
    return db_ripartizione


@router.delete("/{ripartizione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ripartizione(ripartizione_id: int, db: Session = Depends(get_db)):
    """Elimina una ripartizione"""
    db_ripartizione = db.query(RipartizioneSpesa).filter(RipartizioneSpesa.id == ripartizione_id).first()
    if not db_ripartizione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ripartizione con ID {ripartizione_id} non trovata"
        )

    db.delete(db_ripartizione)
    db.commit()
    return None
