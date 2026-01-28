# Documento tecnico – Uso della funzione MRZ/OCR

Questo documento descrive l’uso della funzione di elaborazione documenti `process_document` (core del sistema), i parametri, l’output e i comportamenti attesi. La funzione incapsula l’intera logica di parsing MRZ + OCR.

## Firma funzione
```python
process_document(
    image_path,
    mrz_format="auto",
    rotate_mode="none",
    ocr_backend="tesseract",
    device_mode="auto",
    mrz_crop=None,
    debug_dir=None,
)
```

## Scopo
- Carica un documento (JPG/PNG/PDF).
- Tenta l’estrazione MRZ (se presente) con più strategie.
- Esegue OCR completo e mirato per identificare il Codice Fiscale.
- Restituisce un JSON con i dati rilevati e indicatori di qualità.

## Parametri
- `image_path` (str, **obbligatorio**)  
  Percorso al file sorgente. Supportati: `.jpg`, `.png`, `.pdf`.

- `mrz_format` (str, default `"auto"`)  
  Formato MRZ atteso: `"td1"`, `"td3"`, `"auto"`.

- `rotate_mode` (str, default `"none"`)  
  Modalità rotazione: `"none"` (più veloce), `"auto"` (più robusto).

- `ocr_backend` (str, default `"tesseract"`)  
  Backend OCR: `"tesseract"`, `"easyocr"`, `"paddle"`, `"doctr"`, `"mrzscanner"`.

- `device_mode` (str, default `"auto"`)  
  Selezione device: `"auto"`, `"cpu"`, `"gpu"`.

- `mrz_crop` (float | None, default `None`)  
  Crop verticale (0–1). Es: `0.70` = usa ultimo 30% dell’immagine.

- `debug_dir` (str | None, default `None`)  
  Se impostato, salva immagini intermedie (diagnostica).

## Output
La funzione ritorna un dizionario JSON-serializzabile. Esempio:
```json
{
  "mrz_valid": true,
  "document_number": "YA1234567",
  "surname": "ROSSI",
  "given_names": "MARIO",
  "birth_date_it": "01/01/1980",
  "expiry_date_it": "01/01/2030",
  "codice_fiscale": "RSSMRA80A01H501U",
  "codice_fiscale_source": "ocr_full",
  "confidence_score": 0.8,
  "needs_review": false
}
```

### Campi principali
- `mrz_valid` (bool)  
  `true` se MRZ decodificata correttamente.

- `document_number`, `surname`, `given_names`  
  Dati estratti da MRZ.

- `birth_date_it`, `expiry_date_it`  
  Date in formato italiano (se disponibili).

- `codice_fiscale`  
  Estratto via OCR. Può essere `null`.

- `codice_fiscale_source`  
  Origine del CF: `ocr_full` o `ocr_cf`.

- `confidence_score` (0–1)  
  Stima di qualità basata sui campi trovati.

- `needs_review` (bool)  
  `true` se mancano campi critici.

## Comportamento operativo
1. **Setup OCR**: configura Tesseract e warning.
2. **Caricamento pagine**: PDF → immagini; immagini singole per JPG/PNG.
3. **MRZ**: tenta MRZ nativa, poi OCR MRZ con crop/rotazioni (se `rotate_mode=auto`).
4. **OCR generale**: testo completo + OCR mirato per CF.
5. **Merge**: combina MRZ + OCR; calcola `confidence_score`.

## Errori e gestione
- Se il file non è leggibile: solleva `RuntimeError`.
- Se parametri non validi: solleva `ValueError`.

## Note prestazionali
- `rotate_mode=none` è più veloce, ma meno robusto.
- PDF multipagina aumentano il tempo di elaborazione.
- OCR `tesseract` è il più stabile; alternative possono richiedere GPU.

## Esempio d’uso (Python)
```python
from main import process_document

result = process_document(
    "/percorso/documento.jpg",
    mrz_format="auto",
    rotate_mode="none",
    ocr_backend="tesseract",
    device_mode="auto",
    mrz_crop=None,
    debug_dir=None,
)

print(result)
```
