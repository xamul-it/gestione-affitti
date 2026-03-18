"""
DocumentParsingService - Async document parsing orchestration.

Orchestrates the workflow:
1. Upload document to temp storage
2. Create DocumentJob record
3. Submit to external parsing service (MRZ, OCR, etc.)
4. Handle callback from service
5. Create notification (Scadenza) for user action

Supports multi-tenant isolation and retry logic.
"""
import logging
import uuid
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
import httpx

from app.core.config import settings
from app.core.file_storage import file_storage
from app.core.platform.models import (
    DocumentJob,
    JobStatus,
    Scadenza,
    PrioritaScadenza,
    StatoScadenza,
    DocumentParsingLog,
    ParsingServiceConfig,
)
from app.core.platform_services.document_type_registry import document_type_registry

logger = logging.getLogger(__name__)


class DocumentParsingService:
    """
    Service for asynchronous document parsing orchestration.

    Responsibilities:
        - Upload documents to temp storage
        - Create and track DocumentJob records
        - Submit jobs to external parsing services
        - Handle callbacks and update job status
        - Create notifications for user action
        - Retry failed jobs
    """

    # Parsing service configurations
    PARSING_SERVICES = {
        "mrz": {
            "timeout": 300,
            "supported_formats": ["td1", "td3"]
        },
        "contract_parser": {
            "timeout": 600,
            "supported_formats": ["pdf"]
        }
    }

    def __init__(self, db: Session, tenant_schema: str):
        """
        Initialize service.

        Args:
            db: SQLAlchemy session
            tenant_schema: Tenant schema for data isolation
        """
        self.db = db
        self.tenant_schema = tenant_schema

    def upload_and_parse(
        self,
        file: UploadFile,
        document_type_key: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        parsing_service_override: Optional[str] = None,
        parsing_config_override: Optional[Dict[str, Any]] = None,
        callback_url_override: Optional[str] = None
    ) -> DocumentJob:
        """
        Upload document to temp storage and initiate parsing.

        Workflow:
            1. Validate document type from registry
            2. Save file to temp storage (tenant/temp_uploads/job_uuid/)
            3. Create DocumentJob record (status=PENDING)
            4. Submit to parsing service
            5. Return DocumentJob for status polling

        Args:
            file: Uploaded file
            document_type_key: Full document type key (module.CODE)
            entity_type: Optional target entity type
            entity_id: Optional target entity ID
            user_id: User creating the job

        Returns:
            Created DocumentJob

        Raises:
            HTTPException: If document type invalid or file operations fail
        """
        # 1. Validate document type
        doc_type = document_type_registry.get(document_type_key)
        if not doc_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo documento non valido: {document_type_key}"
            )

        if not doc_type.parsing_service and not parsing_service_override:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo documento '{doc_type.nome}' non supporta parsing automatico"
            )

        # 2. Save file to temp storage
        job_uuid = str(uuid.uuid4())
        logger.info(f"[DocumentParsing] Starting job {job_uuid} for {document_type_key}")

        try:
            # Save to temp storage
            file_content = file.file if hasattr(file, 'file') else file
            temp_path = file_storage.save_temp_file(
                file=file_content,
                job_uuid=job_uuid,
                filename=file.filename,
                tenant_schema=self.tenant_schema
            )

            logger.debug(f"[DocumentParsing] Saved to temp: {temp_path}")

        except Exception as e:
            logger.error(f"[DocumentParsing] Failed to save file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Errore salvataggio file: {str(e)}"
            )

        # 3. Create DocumentJob record
        try:
            parsing_service = parsing_service_override or doc_type.parsing_service
            parsing_config = dict(doc_type.parsing_config or {})
            if parsing_config_override:
                parsing_config.update(parsing_config_override)
            if callback_url_override:
                parsing_config["callback_url"] = callback_url_override

            job = DocumentJob(
                job_uuid=job_uuid,
                tenant_schema=self.tenant_schema,
                file_path=temp_path,
                original_filename=file.filename,
                mime_type=file.content_type if hasattr(file, 'content_type') else None,
                document_type_key=document_type_key,
                parsing_service=parsing_service,
                parsing_config=parsing_config,
                entity_type=entity_type,
                entity_id=entity_id,
                status=JobStatus.PENDING,
                created_by=user_id
            )

            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)

            logger.info(f"[DocumentParsing] Created job #{job.id} (uuid={job_uuid})")

        except Exception as e:
            logger.error(f"[DocumentParsing] Failed to create job record: {e}")
            # Cleanup temp file
            try:
                file_storage.delete_file(temp_path, self.tenant_schema)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Errore creazione job: {str(e)}"
            )

        # 4. Submit to parsing service
        try:
            self._submit_to_parser(job)
        except Exception as e:
            logger.error(f"[DocumentParsing] Failed to submit job {job_uuid}: {e}")
            job.status = JobStatus.FAILED
            job.parsing_error = str(e)
            self.db.commit()

        return job

    def _submit_to_parser(self, job: DocumentJob) -> None:
        """
        Submit job to external parsing service.

        Args:
            job: DocumentJob to submit

        Raises:
            Exception: If submission fails
        """
        # Get service config
        service_config = self.PARSING_SERVICES.get(job.parsing_service)
        if not service_config:
            raise ValueError(f"Parsing service sconosciuto: {job.parsing_service}")

        service_endpoint = self._get_service_endpoint(job.parsing_service)
        transport_type = service_endpoint.get("transport_type")
        service_url = service_endpoint.get("endpoint_url")
        timeout = service_endpoint.get("timeout_seconds") or service_config.get("timeout", 300)
        redis_queue = service_endpoint.get("redis_queue")

        callback_url = self._resolve_callback_url(job)

        logger.info(f"[DocumentParsing] Submitting job {job.job_uuid} to {service_url or transport_type}")

        # Read file from temp storage
        file_path = file_storage.get_file_path(job.file_path, self.tenant_schema)

        try:
            # Prepare multipart request
            with open(file_path, 'rb') as f:
                files = {'file': (job.original_filename, f, job.mime_type or 'application/octet-stream')}

                # Add callback_url and config
                parsing_config = dict(job.parsing_config or {})
                parsing_config.pop("callback_url", None)
                data = {
                    'callback_url': callback_url,
                    **parsing_config
                }

                if transport_type == "REDIS":
                    self._enqueue_redis_job(job, data, redis_queue)
                elif transport_type == "WS":
                    raise Exception("Trasporto WS non supportato")
                else:
                    self._log_parsing_event(
                        job=job,
                        direction="REQUEST",
                        url=service_url,
                        request_payload={
                            "callback_url": callback_url,
                            **parsing_config
                        },
                    )
                    # Submit async request (non-blocking)
                    with httpx.Client(timeout=timeout) as client:
                        response = client.post(
                            service_url,
                            files=files,
                            data=data
                        )
                        response.raise_for_status()

                        # Parse response
                        result = response.json()
                        logger.debug(f"[DocumentParsing] Service response: {result}")
                        self._log_parsing_event(
                            job=job,
                            direction="RESPONSE",
                            url=service_url,
                            status_code=response.status_code,
                            response_payload=result,
                        )

            # Update job status to QUEUED
            job.status = JobStatus.QUEUED
            job.queued_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"[DocumentParsing] Job {job.job_uuid} submitted successfully")

        except httpx.HTTPError as e:
            logger.error(f"[DocumentParsing] HTTP error submitting job {job.job_uuid}: {e}")
            self._log_parsing_event(
                job=job,
                direction="ERROR",
                url=service_url,
                error_text=str(e),
            )
            raise Exception(f"Errore comunicazione con servizio parsing: {str(e)}")
        except Exception as e:
            logger.error(f"[DocumentParsing] Error submitting job {job.job_uuid}: {e}")
            self._log_parsing_event(
                job=job,
                direction="ERROR",
                url=service_url,
                error_text=str(e),
            )
            raise

    def handle_callback(self, job_uuid: str, callback_data: Dict[str, Any]) -> DocumentJob:
        """
        Handle callback from external parsing service.

        Callback payload expected:
        {
            "job_id": "uuid",
            "status": "finished" | "failed",
            "result": {...} | null,
            "error": "..." | null
        }

        Args:
            job_uuid: Job UUID
            callback_data: Callback payload from service

        Returns:
            Updated DocumentJob

        Raises:
            HTTPException: If job not found
        """
        # Load job
        job = self.db.query(DocumentJob).filter(
            DocumentJob.job_uuid == job_uuid
        ).first()

        if not job:
            logger.error(f"[DocumentParsing] Callback for unknown job: {job_uuid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job non trovato: {job_uuid}"
            )

        logger.info(f"[DocumentParsing] Callback for job {job_uuid}, status={callback_data.get('status')}")

        self._log_parsing_event(
            job=job,
            direction="CALLBACK",
            url=None,
            request_payload=callback_data,
        )

        # Handle different callback statuses
        callback_status = callback_data.get("status")

        if callback_status == "finished":
            # Success: save result and create notification
            job.status = JobStatus.COMPLETED
            job.parsing_result = callback_data.get("result", {})
            job.completed_at = datetime.utcnow()

            # Extract confidence score and needs_review
            result = job.parsing_result or {}
            job.confidence_score = int(result.get("confidence_score", 0) * 100) if result.get("confidence_score") else None
            job.needs_review = result.get("needs_review", False)

            self.db.commit()

            # Update DocumentoFile and merge metadata into Documento (if linked)
            self._update_documento_metadata(job, result)

            # Create notification for user action
            self._create_notification(job, result)

            logger.info(f"[DocumentParsing] Job {job_uuid} completed successfully")

        elif callback_status == "failed":
            # Failure: save error and retry if possible
            job.status = JobStatus.FAILED
            job.parsing_error = callback_data.get("error", "Unknown error")
            job.completed_at = datetime.utcnow()
            self.db.commit()

            logger.warning(f"[DocumentParsing] Job {job_uuid} failed: {job.parsing_error}")

            # Retry if possible
            if job.can_retry:
                job.retry_count += 1
                job.status = JobStatus.PENDING
                job.completed_at = None
                self.db.commit()

                logger.info(f"[DocumentParsing] Retrying job {job_uuid} (attempt {job.retry_count})")

                try:
                    self._submit_to_parser(job)
                except Exception as e:
                    logger.error(f"[DocumentParsing] Retry failed for job {job_uuid}: {e}")

        else:
            logger.warning(f"[DocumentParsing] Unknown callback status: {callback_status}")

        return job

    def _create_notification(self, job: DocumentJob, parsed_data: Dict[str, Any]) -> None:
        """
        Create Scadenza notification for user action.

        Args:
            job: Completed DocumentJob
            parsed_data: Parsed data from service
        """
        try:
            # Determine priority based on confidence score
            if job.confidence_score and job.confidence_score >= 80:
                priorita = PrioritaScadenza.BASSA
            elif job.confidence_score and job.confidence_score >= 60:
                priorita = PrioritaScadenza.MEDIA
            else:
                priorita = PrioritaScadenza.ALTA

            # Determine title based on entity attachment
            if job.entity_id is None:
                # "Create from document" workflow
                titolo = f"Completa anagrafica da documento: {job.original_filename}"
                descrizione = "Un documento è stato elaborato. Rivedi i dati estratti e completa la creazione dell'anagrafica."
            else:
                # Document attached to existing entity
                titolo = f"Documento elaborato: {job.original_filename}"
                descrizione = "Un documento è stato elaborato. Rivedi i dati estratti e aggiorna l'entità se necessario."

            # Derive module from document_type_key (module.CODE)
            modulo = None
            if job.document_type_key and "." in job.document_type_key:
                modulo = job.document_type_key.split(".", 1)[0]

            scadenza_entity_type = job.entity_type or "document_job"
            scadenza_entity_id = job.entity_id or job.id

            # Create Scadenza
            scadenza = Scadenza(
                modulo=modulo,
                entity_type=scadenza_entity_type,
                entity_id=scadenza_entity_id,
                titolo=titolo,
                descrizione=descrizione,
                data_scadenza=date.today() + timedelta(days=7),  # Due in 7 days
                priorita=priorita,
                stato=StatoScadenza.ATTIVA,
                creato_da=job.created_by
            )

            self.db.add(scadenza)
            self.db.flush()

            # Link scadenza to job
            job.scadenza_id = scadenza.id
            self.db.commit()

            logger.info(
                f"[DocumentParsing] Created notification #{scadenza.id} for job {job.job_uuid} "
                f"(priority={priorita.value}, confidence={job.confidence_score})"
            )

        except Exception as e:
            logger.error(f"[DocumentParsing] Failed to create notification for job {job.job_uuid}: {e}")
            # Non-critical: job is still completed

    def _log_parsing_event(
        self,
        job: DocumentJob,
        direction: str,
        url: Optional[str],
        request_payload: Optional[Dict[str, Any]] = None,
        response_payload: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_text: Optional[str] = None,
    ) -> None:
        try:
            log_entry = DocumentParsingLog(
                job_uuid=job.job_uuid,
                tenant_schema=job.tenant_schema,
                parsing_service=job.parsing_service,
                direction=direction,
                url=url,
                status_code=status_code,
                request_payload=request_payload,
                response_payload=response_payload,
                error_text=error_text,
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def _get_service_endpoint(self, service_key: str) -> Dict[str, Any]:
        record = self.db.query(ParsingServiceConfig).filter(
            ParsingServiceConfig.service_key == service_key
        ).first()
        if not record or record.enabled != "true":
            raise Exception(
                f"Servizio parsing '{service_key}' non configurato nel core"
            )
        if record.transport_type in {"HTTP", "WS"} and not record.endpoint_url:
            raise Exception(
                f"Servizio parsing '{service_key}' senza endpoint URL configurato"
            )
        if record.transport_type == "REDIS" and not record.redis_queue:
            raise Exception(
                f"Servizio parsing '{service_key}' senza redis_queue configurata"
            )
        return {
            "transport_type": record.transport_type,
            "endpoint_url": record.endpoint_url,
            "redis_queue": record.redis_queue,
            "timeout_seconds": record.timeout_seconds,
        }

    def _enqueue_redis_job(self, job: DocumentJob, data: Dict[str, Any], redis_queue: Optional[str]) -> None:
        try:
            import os
            import json
            import redis  # type: ignore

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            queue_name = redis_queue or "document_parsing_jobs"
            payload = {
                "job_uuid": job.job_uuid,
                "tenant_schema": job.tenant_schema,
                "service": job.parsing_service,
                "file_path": job.file_path,
                "original_filename": job.original_filename,
                "mime_type": job.mime_type,
                "callback_url": data.get("callback_url"),
                "config": data,
            }
            client = redis.Redis.from_url(redis_url)
            client.rpush(queue_name, json.dumps(payload))
            self._log_parsing_event(
                job=job,
                direction="REQUEST",
                url=f"redis://{queue_name}",
                request_payload=payload,
            )
        except Exception as exc:
            raise Exception(f"Errore invio job su Redis: {exc}")

    def _resolve_callback_url(self, job: DocumentJob) -> str:
        default_url = f"{settings.API_BASE_URL}/document-parsing/callback/{job.job_uuid}"
        parsing_config = job.parsing_config or {}
        override = parsing_config.get("callback_url")
        if not override:
            return default_url
        return self._format_callback_url(override, job.job_uuid)

    def _format_callback_url(self, template: str, job_uuid: str) -> str:
        return (
            template
            .replace("{job_uuid}", job_uuid)
            .replace("{api_base_url}", settings.API_BASE_URL)
        )

    def get_job(self, job_uuid: str) -> Optional[DocumentJob]:
        """
        Get job by UUID.

        Args:
            job_uuid: Job UUID

        Returns:
            DocumentJob or None
        """
        return self.db.query(DocumentJob).filter(
            DocumentJob.job_uuid == job_uuid,
            DocumentJob.tenant_schema == self.tenant_schema
        ).first()

    def get_job_or_404(self, job_uuid: str) -> DocumentJob:
        """
        Get job by UUID or raise 404.

        Args:
            job_uuid: Job UUID

        Returns:
            DocumentJob

        Raises:
            HTTPException: If job not found
        """
        job = self.get_job(job_uuid)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job non trovato: {job_uuid}"
            )
        return job

    def get_job_by_id(self, job_id: int) -> Optional[DocumentJob]:
        """
        Get job by numeric ID.
        """
        return self.db.query(DocumentJob).filter(
            DocumentJob.id == job_id,
            DocumentJob.tenant_schema == self.tenant_schema
        ).first()

    def get_user_jobs(
        self,
        user_id: int,
        status_filter: Optional[JobStatus] = None,
        limit: int = 50
    ):
        """
        Get jobs created by a user.

        Args:
            user_id: User ID
            status_filter: Optional status filter
            limit: Max results

        Returns:
            List of DocumentJob
        """
        query = self.db.query(DocumentJob).filter(
            DocumentJob.created_by == user_id,
            DocumentJob.tenant_schema == self.tenant_schema
        )

        if status_filter:
            query = query.filter(DocumentJob.status == status_filter)

        return query.order_by(DocumentJob.created_at.desc()).limit(limit).all()

    def get_pending_documents(self, user_id: int):
        """
        Get completed jobs pending user action (not yet linked to entity).

        Args:
            user_id: User ID

        Returns:
            List of DocumentJob with status=COMPLETED and entity_id=NULL
        """
        return self.db.query(DocumentJob).filter(
            DocumentJob.created_by == user_id,
            DocumentJob.tenant_schema == self.tenant_schema,
            DocumentJob.status == JobStatus.COMPLETED,
            DocumentJob.entity_id.is_(None)
        ).order_by(DocumentJob.completed_at.desc()).all()

    def get_entity_jobs(
        self,
        entity_type: str,
        entity_id: int,
        status_filter: Optional[JobStatus] = None,
        created_by: Optional[int] = None,
        pending_only: bool = True,
    ):
        """
        Get jobs for a specific entity, optionally filtered by status and creator.

        Args:
            entity_type: Target entity type
            entity_id: Target entity ID
            status_filter: Optional status filter
            created_by: Optional creator filter
            pending_only: If True, only jobs with active scadenza are returned

        Returns:
            List of DocumentJob
        """
        query = self.db.query(DocumentJob).filter(
            DocumentJob.tenant_schema == self.tenant_schema,
            DocumentJob.entity_type == entity_type,
            DocumentJob.entity_id == entity_id,
        )

        if created_by is not None:
            query = query.filter(DocumentJob.created_by == created_by)

        if status_filter:
            query = query.filter(DocumentJob.status == status_filter)
        elif pending_only:
            query = query.filter(DocumentJob.status == JobStatus.COMPLETED)

        if pending_only:
            query = query.join(
                Scadenza,
                DocumentJob.scadenza_id == Scadenza.id,
            ).filter(Scadenza.stato == StatoScadenza.ATTIVA)

        return query.order_by(DocumentJob.created_at.desc()).all()

    def _update_documento_metadata(self, job: DocumentJob, parsed_data: Dict[str, Any]) -> None:
        """
        Update DocumentoFile and merge metadata into Documento parent.

        Multi-file documents aggregate parsed data from all files.

        Args:
            job: Completed DocumentJob
            parsed_data: Parsed data from service

        Side Effects:
            - Updates DocumentoFile.parsing_result and confidence_score
            - Merges all files' data into Documento.metadata_parsato
            - Calculates average confidence_score for Documento
        """
        try:
            # Import here to avoid circular dependency
            from modules.anagrafica_italiana.models import DocumentoFile, Documento

            # 1. Find DocumentoFile linked to this job
            doc_file = self.db.query(DocumentoFile).filter(
                DocumentoFile.parsing_job_id == job.id
            ).first()

            if doc_file:
                # 2. Update DocumentoFile with parsing results
                doc_file.parsing_result = parsed_data
                doc_file.confidence_score = job.confidence_score

                logger.info(
                    f"[DocumentParsing] Updated DocumentoFile #{doc_file.id} with parsing results "
                    f"(confidence={doc_file.confidence_score})"
                )

                # 3. Get parent Documento
                documento = self.db.query(Documento).filter(
                    Documento.id == doc_file.documento_id
                ).first()

                if documento:
                    # 4. Merge all files' parsing results into Documento.metadata_parsato
                    all_files = self.db.query(DocumentoFile).filter(
                        DocumentoFile.documento_id == documento.id
                    ).order_by(DocumentoFile.ordine).all()

                    merged_metadata = {}
                    confidence_scores = []

                    for f in all_files:
                        if f.parsing_result:
                            # Merge results - later files override earlier ones for same keys
                            merged_metadata.update(f.parsing_result)

                            if f.confidence_score is not None:
                                confidence_scores.append(f.confidence_score)

                    # Calculate average confidence
                    avg_confidence = None
                    if confidence_scores:
                        avg_confidence = int(sum(confidence_scores) / len(confidence_scores))

                    # Update Documento
                    documento.metadata_parsato = merged_metadata if merged_metadata else None
                    documento.confidence_score = avg_confidence

                    self.db.commit()

                    logger.info(
                        f"[DocumentParsing] Updated Documento #{documento.id} metadata_parsato "
                        f"(avg_confidence={avg_confidence}, num_files={len(all_files)})"
                    )

            else:
                logger.debug(
                    f"[DocumentParsing] Job {job.id} not linked to DocumentoFile "
                    "(might be legacy single-file document)"
                )

        except Exception as e:
            logger.error(
                f"[DocumentParsing] Failed to update documento metadata for job {job.id}: {e}",
                exc_info=True
            )
            # Non-critical: job is still completed even if metadata update fails
            self.db.rollback()
