import os
import re
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
import uuid


class FileStorage:
    """Gestione storage file su filesystem con supporto multi-tenancy"""

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _validate_tenant_schema(self, tenant_schema: str) -> None:
        """
        Valida il nome del tenant schema per prevenire directory traversal.

        Args:
            tenant_schema: Nome dello schema tenant

        Raises:
            ValueError: Se il tenant_schema non è valido
        """
        if not tenant_schema:
            raise ValueError("tenant_schema è obbligatorio")

        # Permetti solo caratteri alfanumerici e underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', tenant_schema):
            raise ValueError(
                f"tenant_schema non valido: '{tenant_schema}'. "
                "Sono permessi solo caratteri alfanumerici e underscore."
            )

        # Blocca tentativi di directory traversal
        if '..' in tenant_schema or '/' in tenant_schema or '\\' in tenant_schema:
            raise ValueError(f"tenant_schema contiene caratteri non permessi: '{tenant_schema}'")

    def _get_tenant_path(self, tenant_schema: str) -> Path:
        """
        Ottieni la directory root per un tenant.

        Args:
            tenant_schema: Nome dello schema tenant

        Returns:
            Path della directory tenant
        """
        self._validate_tenant_schema(tenant_schema)
        tenant_path = self.base_path / tenant_schema
        tenant_path.mkdir(parents=True, exist_ok=True)
        return tenant_path

    def _validate_path_security(self, file_path: Path, tenant_path: Path) -> None:
        """
        Verifica che il path risolto sia effettivamente sotto la directory tenant.

        Args:
            file_path: Path del file da validare
            tenant_path: Path root del tenant

        Raises:
            ValueError: Se il path esce dalla directory tenant
        """
        try:
            resolved_file = file_path.resolve()
            resolved_tenant = tenant_path.resolve()

            # Verifica che il file sia sotto la directory tenant
            if not str(resolved_file).startswith(str(resolved_tenant)):
                raise ValueError(
                    f"Tentativo di accesso a path fuori dalla directory tenant: {resolved_file}"
                )
        except Exception as e:
            raise ValueError(f"Errore validazione path: {e}")

    def save_file(
        self,
        file: BinaryIO,
        entity_type: str,
        entity_id: int,
        filename: str,
        tenant_schema: str
    ) -> str:
        """
        Salva un file nella directory del tenant e restituisce il path relativo.

        Args:
            file: File binario da salvare
            entity_type: Tipo entità (SOGGETTO_ANAGRAFICO, IMMOBILE, CONTRATTO, ecc.)
            entity_id: ID dell'entità
            filename: Nome file originale
            tenant_schema: Schema tenant per isolamento dati

        Returns:
            Path relativo del file salvato (include tenant_schema)
        """
        # Ottieni directory tenant
        tenant_path = self._get_tenant_path(tenant_schema)

        # Crea struttura directory: tenant_schema/entity_type/entity_id/
        entity_dir = tenant_path / entity_type.lower() / str(entity_id)
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Genera nome file unico per evitare sovrascritture
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = entity_dir / unique_filename

        # Validazione sicurezza
        self._validate_path_security(file_path, tenant_path)

        # Salva il file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        # Restituisci path relativo (include tenant)
        return str(file_path.relative_to(self.base_path))

    def save_temp_file(
        self,
        file: BinaryIO,
        job_uuid: str,
        filename: str,
        tenant_schema: str
    ) -> str:
        """
        Salva un file temporaneo per upload asincroni.

        Args:
            file: File binario da salvare
            job_uuid: UUID univoco del job
            filename: Nome file originale
            tenant_schema: Schema tenant

        Returns:
            Path relativo del file temporaneo
        """
        tenant_path = self._get_tenant_path(tenant_schema)

        # Directory temporanea: tenant_schema/temp_uploads/job_uuid/
        temp_dir = tenant_path / "temp_uploads" / job_uuid
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Mantieni nome originale per temp (utile per debugging)
        file_extension = Path(filename).suffix
        safe_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = temp_dir / safe_filename

        # Validazione sicurezza
        self._validate_path_security(file_path, tenant_path)

        # Salva il file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        return str(file_path.relative_to(self.base_path))

    def move_from_temp(
        self,
        temp_relative_path: str,
        entity_type: str,
        entity_id: int,
        tenant_schema: str
    ) -> str:
        """
        Sposta un file da temp storage a storage permanente.

        Args:
            temp_relative_path: Path relativo del file temporaneo
            entity_type: Tipo entità destinazione
            entity_id: ID entità destinazione
            tenant_schema: Schema tenant

        Returns:
            Nuovo path relativo in storage permanente
        """
        tenant_path = self._get_tenant_path(tenant_schema)

        # Path sorgente (temp)
        temp_path = self.base_path / temp_relative_path
        if not temp_path.exists():
            raise FileNotFoundError(f"File temporaneo non trovato: {temp_relative_path}")

        # Validazione sicurezza sul path sorgente
        self._validate_path_security(temp_path, tenant_path)

        # Path destinazione
        entity_dir = tenant_path / entity_type.lower() / str(entity_id)
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Mantieni estensione originale
        file_extension = temp_path.suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        dest_path = entity_dir / unique_filename

        # Validazione sicurezza sul path destinazione
        self._validate_path_security(dest_path, tenant_path)

        # Sposta il file
        shutil.move(str(temp_path), str(dest_path))

        # Rimuovi directory temp se vuota
        try:
            temp_path.parent.rmdir()
        except OSError:
            pass  # Directory non vuota, ok

        return str(dest_path.relative_to(self.base_path))

    def get_file_path(self, relative_path: str, tenant_schema: Optional[str] = None) -> Path:
        """
        Ottieni il path assoluto di un file dal path relativo.

        Args:
            relative_path: Path relativo restituito da save_file
            tenant_schema: Schema tenant (opzionale, se già incluso nel relative_path)

        Returns:
            Path assoluto del file
        """
        if tenant_schema:
            self._validate_tenant_schema(tenant_schema)
            tenant_path = self._get_tenant_path(tenant_schema)
            file_path = self.base_path / relative_path
            # Validazione sicurezza
            self._validate_path_security(file_path, tenant_path)
            return file_path
        else:
            # Assume che il tenant sia già nel relative_path
            return self.base_path / relative_path

    def delete_file(self, relative_path: str, tenant_schema: Optional[str] = None) -> bool:
        """
        Elimina un file.

        Args:
            relative_path: Path relativo del file
            tenant_schema: Schema tenant (opzionale, se già incluso nel relative_path)

        Returns:
            True se eliminato con successo
        """
        try:
            file_path = self.get_file_path(relative_path, tenant_schema)

            if file_path.exists():
                file_path.unlink()

                # Prova a rimuovere directory vuote
                try:
                    file_path.parent.rmdir()
                    file_path.parent.parent.rmdir()
                except OSError:
                    pass  # Directory non vuote, ok

                return True
        except Exception as e:
            print(f"Errore eliminazione file: {e}")
        return False

    def get_file_size(self, relative_path: str, tenant_schema: Optional[str] = None) -> int:
        """
        Ottieni dimensione file in bytes.

        Args:
            relative_path: Path relativo del file
            tenant_schema: Schema tenant (opzionale)

        Returns:
            Dimensione in bytes
        """
        file_path = self.get_file_path(relative_path, tenant_schema)
        if file_path.exists():
            return file_path.stat().st_size
        return 0


# Istanza globale
file_storage = FileStorage()
