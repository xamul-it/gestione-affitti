# MRZ OCR Web Service (async)

Questo servizio espone un endpoint asincrono con coda Redis/RQ.
La chiamata risponde subito con un `job_id`. Il risultato si recupera
con `GET /mrz/{job_id}` oppure via callback.

## Requisiti
- Redis in esecuzione
- Python 3.10+

## Installazione
```bash
pip install -r requirements.txt
```

## Avvio
In terminale separati:
```bash
uvicorn web_service:app --host 0.0.0.0 --port 8000
```
```bash
python worker.py
```

## Endpoint

### POST /mrz
Carica un file e crea un job.

Form fields:
- `file` (required)
- `mrz` (default: auto)
- `rotate` (default: none)
- `ocr` (default: tesseract)
- `device` (default: auto)
- `mrz_crop` (optional, 0.0-1.0)
- `debug` (optional, true/false)
- `callback_url` (optional, URL per webhook)

Risposta:
```json
{
  "job_id": "uuid",
  "status": "queued",
  "status_url": "/mrz/uuid"
}
```

Esempio:
```bash
curl -F "file=@/percorso/documento.jpg" \
  -F "mrz=auto" \
  -F "rotate=none" \
  -F "ocr=tesseract" \
  -F "device=auto" \
  http://localhost:8000/mrz
```

### GET /mrz/{job_id}
Restituisce lo stato del job e, se finito, il risultato.

Esempio risposta:
```json
{
  "job_id": "uuid",
  "status": "finished",
  "result": { "mrz_valid": true, "...": "..." }
}
```

### Callback (opzionale)
Se passi `callback_url`, il worker invia un POST con:
```json
{
  "job_id": "uuid",
  "status": "finished",
  "result": { ... },
  "error": null
}
```
Oppure in caso di errore:
```json
{
  "job_id": "uuid",
  "status": "failed",
  "result": null,
  "error": "messaggio errore"
}
```

## Variabili ambiente
- `REDIS_URL` (default: redis://localhost:6379/0)
- `MRZ_JOBS_DIR` (default: jobs)
- `MRZ_RESULT_TTL` (default: 3600) secondi
- `MRZ_JOB_TIMEOUT` (default: 1800) secondi
