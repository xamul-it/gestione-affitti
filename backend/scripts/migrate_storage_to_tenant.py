#!/usr/bin/env python3
"""
Script per migrare file storage esistente alla struttura tenant-aware.

Usage:
    python migrate_storage_to_tenant.py --dry-run  # Simulazione
    python migrate_storage_to_tenant.py --execute  # Esecuzione reale
"""

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime


class StorageMigrator:
    """Migratore per struttura storage tenant-aware"""

    def __init__(self, base_path: str = "./storage", target_tenant: str = "tenant_test"):
        self.base_path = Path(base_path)
        self.target_tenant = target_tenant
        self.stats = {
            "files_moved": 0,
            "directories_created": 0,
            "errors": 0,
            "skipped": 0
        }

    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def is_special_directory(self, dir_name: str) -> bool:
        """Verifica se una directory è speciale (non da migrare)"""
        special_dirs = {
            "temp_uploads",  # Directory temporanea
            self.target_tenant,  # Directory tenant già creata
        }
        return dir_name in special_dirs or dir_name.startswith("tenant_")

    def scan_existing_structure(self):
        """
        Scansiona la struttura esistente e identifica file da migrare.

        Returns:
            Lista di tuple (source_path, relative_path)
        """
        self.log("Scansione struttura esistente...")

        if not self.base_path.exists():
            self.log(f"Directory {self.base_path} non esiste", "WARNING")
            return []

        files_to_migrate = []

        # Scansiona tutte le sottodirectory
        for entity_type_dir in self.base_path.iterdir():
            if not entity_type_dir.is_dir():
                continue

            # Salta directory speciali
            if self.is_special_directory(entity_type_dir.name):
                self.log(f"Skipping directory speciale: {entity_type_dir.name}", "DEBUG")
                continue

            # Scansiona entity IDs
            for entity_id_dir in entity_type_dir.iterdir():
                if not entity_id_dir.is_dir():
                    continue

                # Scansiona file
                for file_path in entity_id_dir.iterdir():
                    if file_path.is_file():
                        # Path relativo rispetto a base_path
                        relative_path = file_path.relative_to(self.base_path)
                        files_to_migrate.append((file_path, relative_path))

        self.log(f"Trovati {len(files_to_migrate)} file da migrare")
        return files_to_migrate

    def migrate_file(self, source_path: Path, relative_path: Path, dry_run: bool = True):
        """
        Migra un singolo file nella nuova struttura tenant.

        Args:
            source_path: Path assoluto del file sorgente
            relative_path: Path relativo del file
            dry_run: Se True, simula senza eseguire
        """
        # Destinazione: base_path/tenant_name/relative_path
        dest_path = self.base_path / self.target_tenant / relative_path

        if dry_run:
            self.log(f"[DRY-RUN] {source_path} → {dest_path}", "INFO")
        else:
            try:
                # Crea directory destinazione
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                self.stats["directories_created"] += 1

                # Copia il file (non spostare, per sicurezza)
                shutil.copy2(source_path, dest_path)
                self.stats["files_moved"] += 1

                self.log(f"✓ Migrato: {relative_path}", "INFO")

            except Exception as e:
                self.stats["errors"] += 1
                self.log(f"✗ Errore migrando {relative_path}: {e}", "ERROR")

    def verify_migration(self, files_to_migrate):
        """
        Verifica che tutti i file siano stati migrati correttamente.

        Args:
            files_to_migrate: Lista di file da verificare

        Returns:
            True se tutti i file sono presenti nella nuova struttura
        """
        self.log("Verifica integrità migrazione...")

        missing_files = []
        for source_path, relative_path in files_to_migrate:
            dest_path = self.base_path / self.target_tenant / relative_path

            if not dest_path.exists():
                missing_files.append(relative_path)
            elif dest_path.stat().st_size != source_path.stat().st_size:
                self.log(f"Dimensione diversa: {relative_path}", "WARNING")
                missing_files.append(relative_path)

        if missing_files:
            self.log(f"✗ {len(missing_files)} file mancanti o corrotti", "ERROR")
            for file in missing_files[:10]:  # Mostra primi 10
                self.log(f"  - {file}", "ERROR")
            return False
        else:
            self.log("✓ Tutti i file migrati correttamente", "INFO")
            return True

    def create_backup(self):
        """Crea backup della directory storage originale"""
        backup_name = f"storage_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.base_path.parent / backup_name

        self.log(f"Creazione backup in {backup_path}...")

        try:
            shutil.copytree(self.base_path, backup_path)
            self.log(f"✓ Backup creato: {backup_path}", "INFO")
            return backup_path
        except Exception as e:
            self.log(f"✗ Errore creazione backup: {e}", "ERROR")
            return None

    def run(self, dry_run: bool = True, create_backup: bool = True):
        """
        Esegue la migrazione completa.

        Args:
            dry_run: Se True, simula senza eseguire
            create_backup: Se True, crea backup prima di eseguire
        """
        self.log("=" * 70)
        self.log(f"Migrazione Storage - {'DRY RUN' if dry_run else 'ESECUZIONE REALE'}")
        self.log("=" * 70)
        self.log(f"Base path: {self.base_path}")
        self.log(f"Target tenant: {self.target_tenant}")
        self.log("")

        # Scansiona file da migrare
        files_to_migrate = self.scan_existing_structure()

        if not files_to_migrate:
            self.log("Nessun file da migrare", "WARNING")
            return True

        # Crea backup se richiesto e non in dry-run
        if not dry_run and create_backup:
            backup_path = self.create_backup()
            if not backup_path:
                self.log("Impossibile creare backup, migrazione annullata", "ERROR")
                return False

        # Migra ogni file
        self.log("")
        self.log("Inizio migrazione...")
        for source_path, relative_path in files_to_migrate:
            self.migrate_file(source_path, relative_path, dry_run)

        # Statistiche
        self.log("")
        self.log("=" * 70)
        self.log("Statistiche migrazione:")
        self.log(f"  File migrati: {self.stats['files_moved']}")
        self.log(f"  Directory create: {self.stats['directories_created']}")
        self.log(f"  Errori: {self.stats['errors']}")
        self.log(f"  Skipped: {self.stats['skipped']}")
        self.log("=" * 70)

        # Verifica solo se esecuzione reale
        if not dry_run:
            success = self.verify_migration(files_to_migrate)
            return success and self.stats["errors"] == 0

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Migra file storage alla struttura tenant-aware"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula migrazione senza eseguire modifiche"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Esegue migrazione reale (ATTENZIONE: modifica filesystem)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Non creare backup prima della migrazione"
    )
    parser.add_argument(
        "--base-path",
        default="./storage",
        help="Path base dello storage (default: ./storage)"
    )
    parser.add_argument(
        "--tenant",
        default="tenant_test",
        help="Nome tenant di destinazione (default: tenant_test)"
    )

    args = parser.parse_args()

    # Validazione argomenti
    if not args.dry_run and not args.execute:
        parser.error("Specificare --dry-run o --execute")

    if args.dry_run and args.execute:
        parser.error("Non puoi specificare sia --dry-run che --execute")

    # Esegui migrazione
    migrator = StorageMigrator(
        base_path=args.base_path,
        target_tenant=args.tenant
    )

    dry_run = args.dry_run
    create_backup = not args.no_backup

    success = migrator.run(dry_run=dry_run, create_backup=create_backup)

    if success:
        if dry_run:
            print("\n✓ Dry-run completato. Esegui con --execute per applicare le modifiche.")
        else:
            print("\n✓ Migrazione completata con successo!")
        sys.exit(0)
    else:
        print("\n✗ Migrazione fallita. Controlla i log per dettagli.")
        sys.exit(1)


if __name__ == "__main__":
    main()
