import os
import shutil
from pathlib import Path
from typing import BinaryIO
import uuid


class FileStorage:
    """Gestione storage file su filesystem"""

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file: BinaryIO, entity_type: str, entity_id: int, filename: str) -> str:
        """
        Salva un file e restituisce il path relativo

        Args:
            file: File binario da salvare
            entity_type: Tipo entità (IMMOBILE, CONTRATTO, ecc.)
            entity_id: ID dell'entità
            filename: Nome file originale

        Returns:
            Path relativo del file salvato
        """
        # Crea struttura directory
        entity_dir = self.base_path / entity_type.lower() / str(entity_id)
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Genera nome file unico per evitare sovrascritture
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = entity_dir / unique_filename

        # Salva il file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        # Restituisci path relativo
        return str(file_path.relative_to(self.base_path))

    def get_file_path(self, relative_path: str) -> Path:
        """
        Ottieni il path assoluto di un file dal path relativo

        Args:
            relative_path: Path relativo restituito da save_file

        Returns:
            Path assoluto del file
        """
        return self.base_path / relative_path

    def delete_file(self, relative_path: str) -> bool:
        """
        Elimina un file

        Args:
            relative_path: Path relativo del file

        Returns:
            True se eliminato con successo
        """
        try:
            file_path = self.get_file_path(relative_path)
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

    def get_file_size(self, relative_path: str) -> int:
        """Ottieni dimensione file in bytes"""
        file_path = self.get_file_path(relative_path)
        if file_path.exists():
            return file_path.stat().st_size
        return 0


# Istanza globale
file_storage = FileStorage()
