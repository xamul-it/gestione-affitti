"""
Schema Pydantic per PecCasella.

Regola fondamentale: username_enc e password_enc NON vengono mai esposti nei
response schema. CasellaCreate/CasellaUpdate accettano username e password in
chiaro (cifrati nel route prima del salvataggio). CasellaRead include solo
username_display (parzialmente mascherato).
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CasellaCreate(BaseModel):
    """Payload per creare una nuova casella PEC."""

    nome_display: str = Field(..., max_length=200)
    indirizzo_pec: str = Field(..., max_length=255)

    # Protocollo
    protocollo: str = Field(default="IMAP", max_length=10)

    # IMAP
    imap_host: str = Field(..., max_length=255)
    imap_port: int = Field(default=993)
    imap_ssl: bool = Field(default=True)
    imap_folder: str = Field(default="INBOX", max_length=100)
    segna_letto_su_server: bool = Field(default=False)

    # SMTP (opzionale)
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=465)
    smtp_tls: str | None = Field(default=None, max_length=20)

    # Credenziali in chiaro (cifrate nel route prima del save)
    username: str = Field(..., description="Username IMAP/SMTP in chiaro")
    password: str = Field(..., description="Password IMAP/SMTP in chiaro")

    # Polling
    polling_intervallo_minuti: int = Field(default=15, ge=5)
    is_attiva: bool = Field(default=True)

    note: str | None = None


class CasellaUpdate(BaseModel):
    """Payload per aggiornare una casella PEC — tutti i campi opzionali."""

    nome_display: str | None = Field(default=None, max_length=200)
    indirizzo_pec: str | None = Field(default=None, max_length=255)

    protocollo: str | None = Field(default=None, max_length=10)

    imap_host: str | None = Field(default=None, max_length=255)
    imap_port: int | None = None
    imap_ssl: bool | None = None
    imap_folder: str | None = Field(default=None, max_length=100)
    segna_letto_su_server: bool | None = None

    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = None
    smtp_tls: str | None = Field(default=None, max_length=20)

    # Credenziali opzionali in chiaro
    username: str | None = Field(default=None, description="Nuovo username in chiaro")
    password: str | None = Field(default=None, description="Nuova password in chiaro")

    polling_intervallo_minuti: int | None = Field(default=None, ge=5)
    is_attiva: bool | None = None

    note: str | None = None


class CasellaRead(BaseModel):
    """Response schema completo per una casella PEC.

    Le credenziali cifrate non vengono mai incluse. Al loro posto viene esposto
    username_display con i primi 3 caratteri visibili e il resto mascherato.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_display: str
    indirizzo_pec: str

    protocollo: str

    imap_host: str
    imap_port: int
    imap_ssl: bool
    imap_folder: str
    segna_letto_su_server: bool

    smtp_host: str | None
    smtp_port: int | None
    smtp_tls: str | None

    # username_display: primi 3 caratteri + "***"
    username_display: str

    polling_intervallo_minuti: int
    is_attiva: bool
    ultimo_polling_at: datetime | None
    ultimo_uid_visto: str | None
    errori_consecutivi: int
    ultimo_errore: str | None

    note: str | None
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def from_orm_with_display(cls, obj: object) -> "CasellaRead":
        """
        Costruisce CasellaRead da un ORM object, generando username_display
        dai primi 3 caratteri dello username cifrato (il token Fernet inizia
        sempre con 'gAAAAA...', quindi usiamo il campo indirizzo_pec come
        fallback per il display leggibile).

        Poiché lo username cifrato non è leggibile, username_display viene
        derivato dall'indirizzo_pec della casella (parte prima della @).
        """
        indirizzo = getattr(obj, "indirizzo_pec", "") or ""
        local_part = indirizzo.split("@")[0] if "@" in indirizzo else indirizzo
        if len(local_part) > 3:
            display = local_part[:3] + "***"
        elif local_part:
            display = local_part[0] + "***"
        else:
            display = "***"

        data = {col: getattr(obj, col) for col in [
            "id", "nome_display", "indirizzo_pec", "protocollo",
            "imap_host", "imap_port", "imap_ssl", "imap_folder",
            "segna_letto_su_server", "smtp_host", "smtp_port", "smtp_tls",
            "polling_intervallo_minuti", "is_attiva", "ultimo_polling_at",
            "ultimo_uid_visto", "errori_consecutivi", "ultimo_errore",
            "note", "created_at", "updated_at",
        ]}
        data["username_display"] = display
        return cls(**data)


class CasellaList(BaseModel):
    """Response schema compatto per elenco caselle."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_display: str
    indirizzo_pec: str
    is_attiva: bool
    ultimo_polling_at: datetime | None
    errori_consecutivi: int


class TestConnessioneResult(BaseModel):
    """Risultato del test di connessione IMAP."""

    successo: bool
    messaggio: str
    num_messaggi: int | None = None
