# Fase 3: Document Viewer Component - COMPLETATA ✅

**Data Completamento**: 2026-01-31
**Tempo Implementazione**: ~1 ora
**Status**: Ready for Testing

---

## 📦 Deliverables Completati

### 1. Backend Endpoints per Visualizzazione Documenti ✅

**File Modificato**:
- `backend/modules/anagrafica_italiana/routes/documenti.py` (+300 righe)

**Nuovi Endpoints**:

#### a) GET /documenti/{documento_id}/view
Restituisce documento completo con tutti i file associati (multi-file o legacy).

```python
Response:
{
  "id": 123,
  "entity_type": "SOGGETTO_ANAGRAFICO",
  "entity_id": 45,
  "tipo_documento": {
    "id": 1,
    "codice": "CARTA_IDENTITA",
    "nome": "Carta d'Identità",
    "categoria": "identita"
  },
  "is_legacy": false,
  "files": [
    {
      "id": 1,
      "ordine": 1,
      "tipo_pagina": "fronte",
      "nome_file": "carta_identita_fronte.jpg",
      "file_normalizzato_path": "...",
      "is_parsed": true,
      "parsing_result": {...},
      "confidence_score": 95
    },
    {
      "id": 2,
      "ordine": 2,
      "tipo_pagina": "retro",
      "nome_file": "carta_identita_retro.jpg",
      ...
    }
  ],
  "metadata_parsato": {...},     // Aggregated from all files
  "confidence_score": 92,         // Average across files
  "data_scadenza": "2030-01-15",
  "note": "...",
  "created_at": "2026-01-31T10:30:00"
}
```

**Features**:
- ✅ Supporta sia documenti legacy (single-file) che nuovi (multi-file)
- ✅ Include metadata completi di ogni file
- ✅ Include dati parsati aggregati
- ✅ Verifica permessi utente
- ✅ Verifica tenant ownership

#### b) GET /documenti/file/{file_id}/view-normalized
Restituisce file JPEG normalizzato per visualizzazione web.

**Features**:
- ✅ Serve file normalizzato se disponibile
- ✅ Fallback su file originale se normalizzazione non disponibile
- ✅ Ottimizzato per web (JPEG 2048px max, quality 85%)
- ✅ Verifica permessi e tenant ownership

#### c) GET /documenti/file/{file_id}/thumbnail
Genera e cachea thumbnail da file normalizzato.

**Query Parameters**:
- `size`: dimensione massima in pixels (default 320, range 50-1024)

**Features**:
- ✅ Generazione thumbnail con PIL (Pillow)
- ✅ Caching automatico: `{base_name}_thumb_{size}.jpg`
- ✅ Aspect ratio mantenuto
- ✅ Resize con algoritmo LANCZOS (high quality)
- ✅ Conversione RGB per compatibilità JPEG
- ✅ Gestione trasparenza (background bianco)

**Algoritmo**:
```python
1. Check cache: {file}_thumb_{size}.jpg exists?
   ├─ Yes → Return cached thumbnail
   └─ No  → Generate new:
       1. Open source file (normalized or original)
       2. Convert to RGB if needed (RGBA → RGB + white background)
       3. Resize maintaining aspect ratio: thumbnail((size, size))
       4. Save as JPEG (quality 85%, optimized)
       5. Return generated file
```

#### d) GET /documenti/file/{file_id}/download-original
Scarica file originale (pre-normalizzazione).

**Features**:
- ✅ Restituisce file originale nel formato nativo
- ✅ Content-Type originale preservato
- ✅ Filename originale nel response header
- ✅ Verifica permessi e tenant ownership

---

### 2. DocumentViewer React Component ✅

**File Creati**:
- `frontend/src/modules/anagrafica_italiana/components/DocumentViewer/DocumentViewer.jsx` (500 righe)
- `frontend/src/modules/anagrafica_italiana/components/DocumentViewer/DocumentViewer.css` (600 righe)
- `frontend/src/modules/anagrafica_italiana/components/DocumentViewer/index.js`

**Component Props**:
```jsx
<DocumentViewer
  documentoId={123}      // ID documento da visualizzare
  onClose={() => {...}}  // Callback chiusura viewer
/>
```

**Component State**:
- `loading`: boolean (caricamento documento)
- `error`: string | null (errore caricamento)
- `documento`: object | null (dati documento completi)
- `currentPageIndex`: number (pagina corrente, 0-based)
- `zoom`: 'fit' | 50 | 100 | 150 | 200 (livello zoom)
- `rotation`: 0 | 90 | 180 | 270 (rotazione immagine)
- `showMetadata`: boolean (mostra overlay metadata)
- `showThumbnails`: boolean (mostra sidebar miniature)

---

### 3. Features Implementate ✅

#### A) Multi-Page Navigation

**Controls**:
- ✅ **Arrow buttons**: Frecce prev/next sovraimpresse su immagine
- ✅ **Keyboard shortcuts**: `←` prev, `→` next
- ✅ **Thumbnail sidebar**: Click su miniatura per navigare direttamente
- ✅ **Page indicator**: Badge "Pagina X di N" in basso

**Thumbnail Sidebar**:
- ✅ Miniature 160px con lazy loading
- ✅ Evidenziazione pagina corrente (border blu)
- ✅ Label con numero pagina e tipo (fronte/retro/pagina_N)
- ✅ Scroll verticale se molte pagine
- ✅ Toggle visibilità (nascondibile)

**Comportamento**:
- Disabilita prev su prima pagina
- Disabilita next su ultima pagina
- Supporta documenti single-page (nasconde navigation se 1 sola pagina)

#### B) Zoom Controls

**Livelli Zoom**:
1. **Fit** (default): Immagine adattata alla viewport mantenendo aspect ratio
2. **50%**: Immagine ridotta al 50% dimensione originale
3. **100%**: Immagine a dimensione originale
4. **150%**: Ingrandimento 150%
5. **200%**: Ingrandimento massimo 200%

**Controls**:
- ✅ Dropdown select per livello zoom
- ✅ Buttons `🔍-` e `🔍+` per zoom out/in incrementale
- ✅ Keyboard shortcuts: `+` zoom in, `-` zoom out
- ✅ Scroll overflow quando zoom > fit

**CSS Implementation**:
```css
.document-image.zoom-fit {
  max-width: 100%;
  max-height: 100%;
}

.document-image.zoom-100 {
  width: auto;
  height: auto;
}

.document-image.zoom-200 {
  width: 200%;
}
```

#### C) Rotation Controls

**Features**:
- ✅ Rotate left: `↶` button (-90°)
- ✅ Rotate right: `↷` button (+90°)
- ✅ Keyboard shortcut: `R` rotate right
- ✅ Rotazioni: 0°, 90°, 180°, 270° (ciclico)
- ✅ Smooth transition con CSS `transform: rotate()`

**Implementation**:
```jsx
const rotateRight = () => {
  setRotation((rotation + 90) % 360);
};

<img
  style={{ transform: `rotate(${rotation}deg)` }}
  className="document-image"
/>
```

#### D) Download Controls

**Features**:
- ✅ **Download Original**: Button `⬇ Download` scarica file originale
- ✅ Supporta multi-file: scarica file della pagina corrente
- ✅ Supporta legacy: scarica singolo file documento
- ✅ Apre in nuova tab con token authentication

**Implementation**:
```jsx
const downloadOriginal = async () => {
  const currentFile = documento.files[currentPageIndex];

  if (currentFile._legacy) {
    // Legacy single-file
    window.open(`/documenti/${documentoId}/download`, '_blank');
  } else {
    // Multi-file
    window.open(`/documenti/file/${currentFile.id}/download-original`, '_blank');
  }
};
```

#### E) Metadata Overlay

**Toggle**:
- ✅ Button `ℹ Info` in header
- ✅ Keyboard shortcut: `M`
- ✅ Slide-in from right con backdrop blur

**Contenuto Overlay**:

1. **Informazioni Generali**:
   - Tipo documento
   - Descrizione
   - Data scadenza
   - Note

2. **Dati Parsati (Pagina Corrente)**:
   - Confidence score del file corrente
   - Parsing result JSON (syntax highlighted)

3. **Metadata Aggregato**:
   - Confidence score medio di tutti i file
   - Metadata parsato aggregato JSON

**Features**:
- ✅ Scrollable se contenuto lungo
- ✅ JSON syntax highlighting (monospace font, color verde)
- ✅ Responsive: full-screen su mobile
- ✅ Semi-transparent background con blur effect
- ✅ Sezioni collassabili visivamente

#### F) Keyboard Shortcuts

Tutti i controlli principali accessibili da tastiera:

| Shortcut | Azione |
|----------|--------|
| `←` | Pagina precedente |
| `→` | Pagina successiva |
| `+` o `=` | Zoom in |
| `-` | Zoom out |
| `R` | Ruota destra 90° |
| `M` | Toggle metadata overlay |
| `ESC` | Chiudi viewer |

**Help Footer**:
- ✅ Barra footer con reminder shortcuts
- ✅ Sempre visibile
- ✅ Design minimale per non disturbare

---

### 4. UI/UX Design ✅

#### Color Scheme (Dark Mode)

**Background**:
- Overlay: `rgba(0, 0, 0, 0.9)` (semi-trasparente)
- Main background: `#1a1a1a` (nero)
- Panels: `#2a2a2a` (grigio scuro)
- Borders: `#404040` (grigio medio)

**Text**:
- Primary: `#f0f0f0` (bianco sporco)
- Secondary: `#9ca3af` (grigio chiaro)
- Code: `#22c55e` (verde)

**Accents**:
- Primary action: `#3b82f6` (blu)
- Hover: `#2563eb` (blu scuro)
- Active: `#1e3a8a` (blu navy)
- Error: `#ef4444` (rosso)

#### Layout Structure

```
┌─────────────────────────────────────────────────┐
│ HEADER                                          │
│ [Tipo Doc] [Nome File]     [Zoom] [Rot] [Down] │
└─────────────────────────────────────────────────┘
┌──────┬──────────────────────────────┬───────────┐
│ T    │                              │ M         │
│ H    │      MAIN VIEWER             │ E         │
│ U    │                              │ T         │
│ M    │   ┌─────────────────┐        │ A         │
│ B    │   │                 │        │ D         │
│ N    │   │   IMAGE         │◄────►  │ A         │
│ A    │   │                 │        │ T         │
│ I    │   └─────────────────┘        │ A         │
│ L    │        ▼                     │           │
│ S    │   [Pagina X di N]            │ (Toggle)  │
└──────┴──────────────────────────────┴───────────┘
┌─────────────────────────────────────────────────┐
│ FOOTER: Keyboard Shortcuts Help                │
└─────────────────────────────────────────────────┘
```

#### Responsive Breakpoints

**Desktop (> 1024px)**:
- Thumbnail sidebar: 200px
- Metadata overlay: 400px
- Full controls visible

**Tablet (768px - 1024px)**:
- Thumbnail sidebar: 160px
- Metadata overlay: 320px
- Controls wrapped

**Mobile (< 768px)**:
- Thumbnails hidden (auto)
- Metadata overlay: full-screen
- Stacked controls
- Touch-optimized buttons (48px min)

**Small Mobile (< 640px)**:
- Thumbnails completely hidden
- Simplified controls
- Larger touch targets
- Reduced padding

#### Loading States

**Initial Load**:
```jsx
<div className="document-viewer-loading">
  <div className="spinner"></div>  {/* Rotating CSS spinner */}
  <p>Caricamento documento...</p>
</div>
```

**Error State**:
```jsx
<div className="document-viewer-error">
  <h3>Errore</h3>
  <p>{error}</p>
  <button onClick={onClose}>Chiudi</button>
</div>
```

#### Animations

- ✅ **Spinner**: CSS rotation animation (@keyframes spin)
- ✅ **Button hover**: scale 1.1 on nav arrows
- ✅ **Zoom**: smooth transform transition (0.3s ease)
- ✅ **Rotation**: smooth transform transition (0.3s ease)
- ✅ **Metadata overlay**: slide-in with backdrop blur

---

## 🧪 Testing Checklist

### Backend Endpoints

- [ ] Test `GET /documenti/{id}/view` con documento legacy
- [ ] Test `GET /documenti/{id}/view` con documento multi-file
- [ ] Test `GET /documenti/file/{id}/view-normalized` con file normalizzato
- [ ] Test `GET /documenti/file/{id}/view-normalized` fallback su originale
- [ ] Test `GET /documenti/file/{id}/thumbnail?size=320`
- [ ] Test thumbnail caching (2a richiesta deve essere instant)
- [ ] Test thumbnail con size custom (size=160, size=480)
- [ ] Test thumbnail con size invalid (< 50, > 1024) → 400 error
- [ ] Test `GET /documenti/file/{id}/download-original`
- [ ] Test permessi: utente senza accesso → 403
- [ ] Test tenant isolation: documento altro tenant → 403
- [ ] Test file non esistente → 404

### Frontend Component

#### Navigation
- [ ] Test prev/next buttons con multi-page
- [ ] Test prev disabled su prima pagina
- [ ] Test next disabled su ultima pagina
- [ ] Test keyboard arrows (← →)
- [ ] Test click su thumbnail per navigare
- [ ] Test con documento single-page (navigation nascosta)
- [ ] Test page indicator mostra "Pagina X di N"

#### Zoom
- [ ] Test zoom fit (default)
- [ ] Test zoom 50%, 100%, 150%, 200%
- [ ] Test buttons zoom in/out incrementale
- [ ] Test keyboard shortcuts (+ -)
- [ ] Test scroll container quando zoom > fit
- [ ] Test zoom disabled su max/min

#### Rotation
- [ ] Test rotate right button (+90°)
- [ ] Test rotate left button (-90°)
- [ ] Test keyboard shortcut R
- [ ] Test rotazione ciclica (360° → 0°)
- [ ] Test smooth CSS transition

#### Download
- [ ] Test download file corrente (multi-file)
- [ ] Test download con documento legacy
- [ ] Test file aperto in nuova tab
- [ ] Test con diversi formati file (JPEG, PNG, PDF)

#### Metadata Overlay
- [ ] Test toggle con button Info
- [ ] Test keyboard shortcut M
- [ ] Test rendering sezioni metadata
- [ ] Test JSON syntax highlighting
- [ ] Test scroll quando contenuto lungo
- [ ] Test responsive (full-screen su mobile)

#### Thumbnails
- [ ] Test sidebar con 2-5 pagine
- [ ] Test sidebar con 10+ pagine (scrolling)
- [ ] Test evidenziazione pagina corrente
- [ ] Test label tipo_pagina (fronte/retro)
- [ ] Test toggle visibilità sidebar
- [ ] Test auto-hide su mobile

#### Keyboard Shortcuts
- [ ] Test tutti shortcuts da tastiera
- [ ] Test ESC chiude viewer
- [ ] Test shortcuts footer sempre visibile

#### Responsive
- [ ] Test su desktop (> 1024px)
- [ ] Test su tablet (768-1024px)
- [ ] Test su mobile (< 768px)
- [ ] Test su small mobile (< 640px)
- [ ] Test portrait/landscape orientations
- [ ] Test touch gestures (swipe for navigation)

#### Edge Cases
- [ ] Test con documento senza file
- [ ] Test con file normalizzazione fallita
- [ ] Test con parsing non disponibile
- [ ] Test con metadata vuoti
- [ ] Test con file molto grandi (> 10MB)
- [ ] Test con nomi file molto lunghi
- [ ] Test con caratteri speciali in nome file

---

## 📋 Comandi Testing

### 1. Test Backend Endpoints (curl)

```bash
TOKEN="your_jwt_token"

# View documento completo
curl -X GET "http://localhost:8000/api/v1/anagrafica/documenti/123/view" \
  -H "Authorization: Bearer $TOKEN"

# View file normalizzato
curl -X GET "http://localhost:8000/api/v1/anagrafica/documenti/file/1/view-normalized" \
  -H "Authorization: Bearer $TOKEN" \
  -o normalized.jpg

# Get thumbnail 320px
curl -X GET "http://localhost:8000/api/v1/anagrafica/documenti/file/1/thumbnail?size=320" \
  -H "Authorization: Bearer $TOKEN" \
  -o thumbnail_320.jpg

# Download originale
curl -X GET "http://localhost:8000/api/v1/anagrafica/documenti/file/1/download-original" \
  -H "Authorization: Bearer $TOKEN" \
  -o original_file.pdf
```

### 2. Test Frontend Component

```jsx
import { DocumentViewer } from '@/modules/anagrafica_italiana';

// In your component
const [showViewer, setShowViewer] = useState(false);
const [documentoId, setDocumentoId] = useState(null);

const handleOpenViewer = (docId) => {
  setDocumentoId(docId);
  setShowViewer(true);
};

return (
  <>
    <button onClick={() => handleOpenViewer(123)}>
      Visualizza Documento
    </button>

    {showViewer && (
      <DocumentViewer
        documentoId={documentoId}
        onClose={() => setShowViewer(false)}
      />
    )}
  </>
);
```

---

## 📊 Metriche Implementation

| Metrica | Valore |
|---------|--------|
| **Files Created** | 3 frontend + 0 backend |
| **Files Modified** | 1 backend + 1 frontend |
| **Lines of Code** | ~1,400 |
| **Backend Code** | ~300 lines (4 endpoints) |
| **Frontend Code** | ~1,100 lines (component + CSS) |
| **API Endpoints Added** | 4 |
| **Time to Implement** | ~1 hour |

---

## 🎯 Expected Impact

### User Experience
- **Before**: Nessun viewer integrato, necessario download per visualizzare
- **After**: Viewer full-featured integrato con navigation, zoom, metadata
- **Time Saved**: ~30 secondi per documento (no download/upload)

### Developer Experience
- **Reusability**: Component riutilizzabile in tutto il modulo anagrafica
- **Consistency**: UI uniforme per visualizzazione documenti
- **Maintainability**: Codice centralizzato, facile da estendere

### Performance
- **Thumbnail caching**: Richieste successive istantanee (no re-generation)
- **Normalized files**: JPEG ottimizzati per web (< 500KB vs multi-MB PDFs)
- **Lazy loading**: Thumbnails caricate on-demand

---

## 🚀 Next Steps

### Immediate
1. **Integration Testing** con workflow completo:
   - Upload documento → Parsing → View in DocumentViewer
   - Similarity match → Link to existing → View documento completo
2. **Mobile Testing** su dispositivi reali
3. **Performance Testing** con documenti grandi (20+ pagine, file 10MB+)

### Future Enhancements
- [ ] **Gesture support**: Pinch-to-zoom, swipe navigation su mobile
- [ ] **Annotations**: Markup tools (evidenziatore, note, frecce)
- [ ] **OCR overlay**: Selectable text overlay su immagini
- [ ] **Comparison mode**: View 2 documenti side-by-side
- [ ] **Print support**: Print-optimized layout
- [ ] **Share**: Generate shareable link (with expiry)
- [ ] **Full-screen mode**: Presentation mode
- [ ] **Video support**: Extend viewer to support video files

---

**Implementation Completed By**: Claude Code
**Date**: 2026-01-31
**Status**: ✅ READY FOR TESTING
