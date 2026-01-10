## Documenti Anagrafici – Tipologia Documento

Il modulo Anagrafica gestisce i **documenti identificativi e amministrativi** associati a:
- persone fisiche
- persone giuridiche

Ogni documento è associato a **un solo soggetto anagrafico** e può avere **validità temporale**.

---

## Tipologia Documento – Persona Fisica (DOMINIO)

| Codice | Descrizione |
|------|------------|
| CI | Carta di identità |
| CI_E | Carta di identità elettronica |
| PASS | Passaporto |
| PAT | Patente di guida |
| CF | Tessera codice fiscale |
| PERM | Permesso di soggiorno |
| TS | Tessera sanitaria |
| VIS_PF | Visura anagrafica persona fisica |
| ALT_PF | Altro documento persona fisica |

### Metadati obbligatori
- Tipo documento
- Numero documento
- Ente emittente
- Data rilascio
- Stato documento

### Metadati facoltativi
- Data scadenza
- Luogo rilascio
- Note

---

## Tipologia Documento – Persona Giuridica (DOMINIO)

| Codice | Descrizione |
|------|------------|
| VIS_PG | Visura camerale |
| ATC | Atto costitutivo |
| STAT | Statuto |
| PIVA | Certificato attribuzione Partita IVA |
| CCIAA | Certificato CCIAA |
| DURC | Documento unico regolarità contributiva |
| ISO | Certificazione ISO |
| PROC | Procura |
| DOC_ID_LEG | Documento identità legale rappresentante |
| ALT_PG | Altro documento persona giuridica |

### Metadati obbligatori
- Tipo documento
- Denominazione documento
- Ente emittente
- Data rilascio
- Stato documento

### Metadati facoltativi
- Data scadenza
- Numero protocollo
- Note

---

## Stato Documento Anagrafico (DOMINIO)

| Codice | Descrizione |
|------|------------|
| VAL | Valido |
| SCA | In scadenza |
| SCO | Scaduto |
| SOS | Sostituito |
| NAP | Non applicabile |

---

## Regole funzionali comuni

- Un soggetto può avere **più documenti dello stesso tipo**, ma **una sola versione valida**
- I documenti con data di scadenza **generano scadenze nello scadenziario**
- I documenti senza scadenza hanno stato **NAP**
- La sostituzione di un documento:
  - marca il precedente come **SOS**
  - mantiene lo storico
- I file sono archiviati in un **modulo documentale esterno**
- Il modulo anagrafico conserva solo **metadati e riferimenti**

---

## Integrazione con altri moduli

- I documenti anagrafici possono essere:
  - referenziati da moduli immobiliari
  - consultati da moduli contrattuali
- Nessun modulo può modificare documenti anagrafici senza autorizzazione esplicita

## Scadenza
In fase di inserimento documenti è possibile inserire una data di scadenza del documento e una spunta che abilità l'alert. Se viene abilitato l'alert la scadenza viene registrata sul core per la gestione con il link sull'anagrafica e il riferimento del documento