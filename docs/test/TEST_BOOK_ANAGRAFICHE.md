# Test Book - Validazione Anagrafiche

**Data creazione:** 2026-01-09
**Versione:** 1.0
**Dati di riferimento:** `seed_soggetti_report.md`

---

## Indice

1. [Panoramica](#1-panoramica)
2. [Validazione Codice Fiscale](#2-validazione-codice-fiscale)
3. [Validazione Partita IVA](#3-validazione-partita-iva)
4. [Validazione Numeri di Telefono](#4-validazione-numeri-di-telefono)
5. [Validazione Indirizzi](#5-validazione-indirizzi)
6. [Validazione Email e PEC](#6-validazione-email-e-pec)
7. [Validazioni Cross-Field](#7-validazioni-cross-field)
8. [Test Cases Negativi](#8-test-cases-negativi)
9. [Riepilogo Copertura](#9-riepilogo-copertura)

---

## 1. Panoramica

### 1.1 Scopo del Test Book

Questo documento definisce i casi di test per la validazione dei dati anagrafici inseriti nel sistema. L'obiettivo è verificare:

- **Correttezza formale** dei dati in ingresso
- **Coerenza interna** tra campi correlati
- **Validità** rispetto ai registri ufficiali italiani

### 1.2 Dati di Test

| Categoria | Quantità | Note |
|-----------|----------|------|
| Persone Fisiche | 70 | Con CF, alcuni con P.IVA |
| Persone Giuridiche | 30 | Con P.IVA e PEC |
| **Totale** | **100** | |

### 1.3 Priorità Test

| Priorità | Descrizione |
|----------|-------------|
| **P1** | Bloccante - Dati critici per identificazione |
| **P2** | Alta - Validazione formale obbligatoria |
| **P3** | Media - Coerenza e completezza |
| **P4** | Bassa - Validazione esterna (verifica esistenza) |

---

## 2. Validazione Codice Fiscale

### 2.1 Struttura del Codice Fiscale

```
AAABBB12C34D567E
│││││││││││││││└─ Carattere di controllo (CIN)
││││││││││││└┴┴── Codice Comune di nascita (es. H501 = Roma)
│││││││││└┴────── Giorno di nascita (01-31 maschi, 41-71 femmine)
││││││││└──────── Mese di nascita (A-E-H-L-M-P-R-S-T)
│││││└┴┴───────── Anno di nascita (ultime 2 cifre)
││└┴┴──────────── Codice nome (3 consonanti o consonanti+vocali)
└┴┴────────────── Codice cognome (3 consonanti o consonanti+vocali)
```

### 2.2 Test Cases - Formato

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| CF-F-001 | Lunghezza corretta | `FNTLRI86R58H199F` (16 char) | VALIDO | P1 |
| CF-F-002 | Lunghezza insufficiente | `FNTLRI86R58H199` (15 char) | ERRORE: lunghezza invalida | P1 |
| CF-F-003 | Lunghezza eccessiva | `FNTLRI86R58H199FX` (17 char) | ERRORE: lunghezza invalida | P1 |
| CF-F-004 | Caratteri minuscoli | `fntlri86r58h199f` | VALIDO (normalizzare a uppercase) | P2 |
| CF-F-005 | Caratteri speciali | `FNT-LRI-86R58H199F` | ERRORE: caratteri non ammessi | P1 |
| CF-F-006 | Spazi | `FNT LRI 86R58H199F` | ERRORE: caratteri non ammessi | P1 |
| CF-F-007 | Campo vuoto | `` | ERRORE: campo obbligatorio | P1 |
| CF-F-008 | Campo null | `null` | ERRORE: campo obbligatorio | P1 |

### 2.3 Test Cases - Codifica Cognome

**Regola:** Prime 3 consonanti. Se insufficienti, aggiungere vocali. Se ancora insufficienti, aggiungere X.

| ID | Cognome | Codice Atteso | Soggetto di Riferimento | Priorità |
|----|---------|---------------|-------------------------|----------|
| CF-C-001 | FONTANA | FNT | ID 1 - Ilaria Fontana | P1 |
| CF-C-002 | BRUNO | BRN | ID 2 - Luca Bruno | P1 |
| CF-C-003 | FERRARO | FRR | ID 3 - Carlo Ferraro | P1 |
| CF-C-004 | GIORDANO | GRD | ID 4 - Lorenzo Giordano | P1 |
| CF-C-005 | BIANCHI | BNC | ID 5 - Maria Bianchi | P1 |
| CF-C-006 | DE LUCA | DLC | ID 41 - Massimo De Luca | P1 |
| CF-C-007 | DE SANTIS | DSN | ID 65 - Salvatore De Santis | P1 |
| CF-C-008 | VILLA | VLL | ID 9, 40, 59 | P1 |
| CF-C-009 | RIZZO | RZZ | ID 7, 44, 64 | P1 |
| CF-C-010 | COLOMBO | CLM | ID 22, 37, 61 | P1 |

**Test cognomi particolari (casi edge):**

| ID | Cognome | Codice Atteso | Spiegazione | Priorità |
|----|---------|---------------|-------------|----------|
| CF-C-E01 | AI | AIX | 1 consonante + 1 vocale + X | P2 |
| CF-C-E02 | RE | REX | 1 consonante + 1 vocale + X | P2 |
| CF-C-E03 | BO | BOX | 1 consonante + 1 vocale + X | P2 |
| CF-C-E04 | ELIA | LEI | 1 consonante + 2 vocali | P2 |

### 2.4 Test Cases - Codifica Nome

**Regola:** Se ≥4 consonanti: 1a, 3a, 4a consonante. Altrimenti: prime 3 consonanti (come cognome).

| ID | Nome | Codice Atteso | Soggetto di Riferimento | Priorità |
|----|------|---------------|-------------------------|----------|
| CF-N-001 | ILARIA | LRI | ID 1 - Ilaria Fontana (4 cons: L-R→1,3,4) | P1 |
| CF-N-002 | LUCA | LCU | ID 2 - Luca Bruno (3 cons) | P1 |
| CF-N-003 | CARLO | CRL | ID 3 - Carlo Ferraro (3 cons) | P1 |
| CF-N-004 | LORENZO | LNZ | ID 4 - Lorenzo Giordano (4 cons: L-R-N-Z→1,3,4) | P1 |
| CF-N-005 | MARIA | MRA | ID 5 - Maria Bianchi (2 cons + vocale) | P1 |
| CF-N-006 | MICHELE | MHL | ID 6 - Michele Gentile (3 cons) | P1 |
| CF-N-007 | DANIELE | DNL | ID 7 - Daniele Rizzo (3 cons) | P1 |
| CF-N-008 | GIUSEPPE | GPP | ID 11 - Giuseppe Costa (4 cons: G-S-P-P→1,3,4) | P1 |
| CF-N-009 | TERESA | TRS | ID 12 - Teresa Barbieri (3 cons) | P1 |
| CF-N-010 | EMANUELE | MNL | ID 15 - Emanuele Giordano (4 cons: M-N-L→1,3,4) | P1 |
| CF-N-011 | VALENTINA | VNT | ID 24 - Valentina Marchetti (5 cons: V-L-N-T-N→1,3,4) | P1 |
| CF-N-012 | MASSIMO | MSM | ID 41 - Massimo De Luca (3 cons) | P1 |
| CF-N-013 | SALVATORE | SVT | ID 61 - Salvatore Colombo (5 cons: S-L-V-T-R→1,3,4) | P1 |
| CF-N-014 | ALESSANDRA | LSN | ID 69 - Alessandra Parisi (5 cons: L-S-S-N-D-R→1,3,4) | P1 |
| CF-N-015 | FEDERICA | FRC | ID 37 - Federica Colombo (4 cons: F-D-R-C→1,3,4) | P1 |
| CF-N-016 | RICCARDO | RCR | ID 46 - Riccardo Costa (4 cons: R-C-C-R-D→1,3,4) | P1 |

### 2.5 Test Cases - Anno e Mese di Nascita

**Codifica mese:**

| Mese | Codice |
|------|--------|
| Gennaio | A |
| Febbraio | B |
| Marzo | C |
| Aprile | D |
| Maggio | E |
| Giugno | H |
| Luglio | L |
| Agosto | M |
| Settembre | P |
| Ottobre | R |
| Novembre | S |
| Dicembre | T |

| ID | Data Nascita | Anno+Mese Atteso | Soggetto di Riferimento | Priorità |
|----|--------------|------------------|-------------------------|----------|
| CF-D-001 | 1986-10-18 | 86R | ID 1 - Ilaria Fontana | P1 |
| CF-D-002 | 1956-06-26 | 56H | ID 2 - Luca Bruno | P1 |
| CF-D-003 | 1975-12-02 | 75T | ID 3 - Carlo Ferraro | P1 |
| CF-D-004 | 1984-10-08 | 84R | ID 4 - Lorenzo Giordano | P1 |
| CF-D-005 | 1986-06-05 | 86H | ID 5 - Maria Bianchi | P1 |
| CF-D-006 | 1999-10-28 | 99R | ID 22 - Claudia Colombo | P1 |
| CF-D-007 | 2001-01-23 | 01A | ID 40 - Daniela Villa | P1 |
| CF-D-008 | 2000-07-18 | 00L | ID 68 - Sara Barbieri | P1 |
| CF-D-009 | 1997-03-19 | 97C | ID 53 - Giulia Fontana | P1 |
| CF-D-010 | 1954-07-25 | 54L | ID 23 - Michela Lombardi | P1 |

### 2.6 Test Cases - Giorno di Nascita e Sesso

**Regola:** Maschi = giorno (01-31), Femmine = giorno + 40 (41-71)

| ID | Data Nascita | Sesso | Codice Giorno | Soggetto di Riferimento | Priorità |
|----|--------------|-------|---------------|-------------------------|----------|
| CF-G-001 | 1986-10-18 | F | 58 | ID 1 - Ilaria Fontana (18+40) | P1 |
| CF-G-002 | 1956-06-26 | M | 26 | ID 2 - Luca Bruno | P1 |
| CF-G-003 | 1975-12-02 | M | 02 | ID 3 - Carlo Ferraro | P1 |
| CF-G-004 | 1984-10-08 | M | 08 | ID 4 - Lorenzo Giordano | P1 |
| CF-G-005 | 1986-06-05 | F | 45 | ID 5 - Maria Bianchi (05+40) | P1 |
| CF-G-006 | 1993-12-01 | M | 01 | ID 7 - Daniele Rizzo | P1 |
| CF-G-007 | 1983-02-20 | F | 60 | ID 9 - Michela Villa (20+40) | P1 |
| CF-G-008 | 1955-01-31 | F | 71 | ID 27 - Monica Longo (31+40) | P1 |
| CF-G-009 | 1971-01-10 | M | 10 | ID 29 - Simone Marchetti | P1 |
| CF-G-010 | 1994-06-03 | F | 43 | ID 32 - Chiara Fontana (03+40) | P1 |

### 2.7 Test Cases - Codice Comune (Belfiore)

| ID | Luogo Nascita | Codice Atteso | Soggetto di Riferimento | Priorità |
|----|---------------|---------------|-------------------------|----------|
| CF-L-001 | Ravenna | H199 | ID 1 - Ilaria Fontana | P1 |
| CF-L-002 | Cagliari | B354 | ID 2, 13, 18, 29, 46, 47 | P1 |
| CF-L-003 | Bologna | A944 | ID 3, 21, 66 | P1 |
| CF-L-004 | Palermo | G273 | ID 4, 11, 20 | P1 |
| CF-L-005 | Rimini | H294 | ID 5, 44 | P1 |
| CF-L-006 | Trieste | L424 | ID 6, 40, 59 | P1 |
| CF-L-007 | Venezia | L736 | ID 7, 22 | P1 |
| CF-L-008 | Catania | C351 | ID 8 - Maria Parisi | P1 |
| CF-L-009 | Genova | D969 | ID 9 - Michela Villa | P1 |
| CF-L-010 | Reggio Emilia | H223 | ID 10, 16, 43, 52, 69 | P1 |
| CF-L-011 | Roma | H501 | ID 17, 54, 60 | P1 |
| CF-L-012 | Verona | L781 | ID 19, 36, 57, 68 | P1 |
| CF-L-013 | Milano | F205 | ID 23, 27, 32 | P1 |
| CF-L-014 | Torino | L219 | ID 41 - Massimo De Luca | P1 |
| CF-L-015 | Bari | A662 | ID 70 - Ilaria Lombardo | P1 |

### 2.8 Test Cases - Carattere di Controllo (CIN)

**Algoritmo:** Calcolo basato su tabelle di conversione dispari/pari + modulo 26.

| ID | Codice Fiscale | CIN Atteso | Soggetto | Priorità |
|----|----------------|------------|----------|----------|
| CF-CIN-001 | FNTLRI86R58H199 | F | ID 1 - Ilaria Fontana | P1 |
| CF-CIN-002 | BRNLCU56H26B354 | S | ID 2 - Luca Bruno | P1 |
| CF-CIN-003 | FRRCRL75T02A944 | E | ID 3 - Carlo Ferraro | P1 |
| CF-CIN-004 | GRDLNZ84R08G273 | O | ID 4 - Lorenzo Giordano | P1 |
| CF-CIN-005 | BNCMRA86H45H294 | X | ID 5 - Maria Bianchi | P1 |
| CF-CIN-006 | GNTMHL72T30L424 | U | ID 6 - Michele Gentile | P1 |
| CF-CIN-007 | RZZDNL93T01L736 | S | ID 7 - Daniele Rizzo | P1 |
| CF-CIN-008 | PRSMRA75L44C351 | B | ID 8 - Maria Parisi | P1 |
| CF-CIN-009 | VLLMHL83B60D969 | P | ID 9 - Michela Villa | P1 |
| CF-CIN-010 | VTLDNL65C63H223 | W | ID 10 - Daniela Vitale | P1 |

### 2.9 Test Cases - Coerenza CF con Dati Anagrafici

| ID | CF | Nome | Cognome | Data Nascita | Luogo Nascita | Esito | Priorità |
|----|----|----- |---------|--------------|---------------|-------|----------|
| CF-COE-001 | FNTLRI86R58H199F | Ilaria | Fontana | 1986-10-18 | Ravenna | VALIDO | P1 |
| CF-COE-002 | FNTLRI86R58H199F | Maria | Fontana | 1986-10-18 | Ravenna | ERRORE: nome non coerente | P1 |
| CF-COE-003 | FNTLRI86R58H199F | Ilaria | Rossi | 1986-10-18 | Ravenna | ERRORE: cognome non coerente | P1 |
| CF-COE-004 | FNTLRI86R58H199F | Ilaria | Fontana | 1990-10-18 | Ravenna | ERRORE: anno non coerente | P1 |
| CF-COE-005 | FNTLRI86R58H199F | Ilaria | Fontana | 1986-03-18 | Ravenna | ERRORE: mese non coerente | P1 |
| CF-COE-006 | FNTLRI86R58H199F | Ilaria | Fontana | 1986-10-25 | Ravenna | ERRORE: giorno non coerente | P1 |
| CF-COE-007 | FNTLRI86R58H199F | Ilaria | Fontana | 1986-10-18 | Roma | ERRORE: luogo non coerente | P1 |
| CF-COE-008 | FNTLRI86R18H199F | Ilario | Fontana | 1986-10-18 | Ravenna | ERRORE: sesso non coerente (18 vs 58) | P1 |

---

## 3. Validazione Partita IVA

### 3.1 Struttura Partita IVA

```
12345678901
│││││││││└┴── Cifra di controllo (Luhn modificato)
│││││││└───── Cifre progressive
└┴┴────────── Codice provincia/ufficio (001-100 + speciali)
```

### 3.2 Test Cases - Formato

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| PI-F-001 | Lunghezza corretta | `77945570149` (11 cifre) | VALIDO | P1 |
| PI-F-002 | Lunghezza insufficiente | `7794557014` (10 cifre) | ERRORE: lunghezza invalida | P1 |
| PI-F-003 | Lunghezza eccessiva | `779455701491` (12 cifre) | ERRORE: lunghezza invalida | P1 |
| PI-F-004 | Caratteri alfabetici | `7794557014A` | ERRORE: solo numeri ammessi | P1 |
| PI-F-005 | Caratteri speciali | `779-455-7014` | ERRORE: solo numeri ammessi | P1 |
| PI-F-006 | Spazi | `779 455 7014` | ERRORE: solo numeri ammessi | P1 |
| PI-F-007 | Campo vuoto (opzionale) | `` | VALIDO (campo opzionale per PF) | P3 |
| PI-F-008 | Tutti zeri | `00000000000` | ERRORE: P.IVA non valida | P1 |

### 3.3 Test Cases - Cifra di Controllo (Luhn Modificato)

**Algoritmo:**
1. Somma cifre dispari (posizione 1, 3, 5, 7, 9, 11)
2. Somma cifre pari raddoppiate (se >9, sottrarre 9)
3. Controllo: (10 - (somma mod 10)) mod 10

| ID | Partita IVA | Check Digit | Soggetto | Priorità |
|----|-------------|-------------|----------|----------|
| PI-CD-001 | 7794557014**9** | 9 | ID 3 - Carlo Ferraro | P1 |
| PI-CD-002 | 2391203092**3** | 3 | ID 8 - Maria Parisi | P1 |
| PI-CD-003 | 5051517039**2** | 2 | ID 14 - Sergio Lombardo | P1 |
| PI-CD-004 | 7327162010**3** | 3 | ID 15 - Emanuele Giordano | P1 |
| PI-CD-005 | 7040842005**0** | 0 | ID 17 - Andrea Ferrari | P1 |
| PI-CD-006 | 3099322015**8** | 8 | ID 19 - Anna Ferrari | P1 |
| PI-CD-007 | 7536874031**4** | 4 | ID 26 - Pietro Gentile | P1 |
| PI-CD-008 | 9991223031**7** | 7 | ID 30 - Sara Caruso | P1 |
| PI-CD-009 | 7793382009**2** | 2 | ID 71 - Global Logistica | P1 |
| PI-CD-010 | 1235037029**7** | 7 | ID 100 - Trasporti Bianco | P1 |

### 3.4 Test Cases - Codice Provincia

**Codici provincia validi:** 001-100 (province), 120-139 (uffici speciali)

| ID | P.IVA | Codice Prov | Provincia | Soggetto | Priorità |
|----|-------|-------------|-----------|----------|----------|
| PI-PR-001 | 779**455**70149 | 455 (→45) | Milano | ID 3 | P2 |
| PI-PR-002 | 239**120**30923 | 120 | Ufficio speciale | ID 8 | P2 |
| PI-PR-003 | 505**151**70392 | 151 (→15) | Como | ID 14 | P2 |
| PI-PR-004 | 873**184**50719 | 184 (→18) | Foggia | ID 75 | P2 |
| PI-PR-005 | 982**817**00207 | 817 (→81) | Ancona | ID 85 | P2 |

**Note:** Il codice provincia nelle P.IVA moderne non sempre corrisponde alla sede legale attuale.

### 3.5 Test Cases - P.IVA Persone Giuridiche (Obbligatoria)

| ID | Ragione Sociale | P.IVA | Validità | Priorità |
|----|-----------------|-------|----------|----------|
| PI-PG-001 | Global Logistica S.r.l.s. | 77933820092 | VALIDO | P1 |
| PI-PG-002 | Greco Informatica S.r.l.s. | 26146780239 | VALIDO | P1 |
| PI-PG-003 | Bruno & Ferrari S.r.l. | 07823160267 | VALIDO | P1 |
| PI-PG-004 | Omega Project S.a.s. | 23316480336 | VALIDO | P1 |
| PI-PG-005 | Nord Informatica S.p.A. | 16152730095 | VALIDO | P1 |
| PI-PG-006 | Persona Giuridica senza P.IVA | - | ERRORE: P.IVA obbligatoria per PG | P1 |

---

## 4. Validazione Numeri di Telefono

### 4.1 Formati Italiani Accettati

| Tipo | Formato | Pattern Regex | Esempio |
|------|---------|---------------|---------|
| Fisso | `0XX XXXXXXX` | `^0[1-9][0-9]{1,3}\s[0-9]{5,8}$` | `055 8517362` |
| Cellulare | `3XX XXXXXXX` | `^3[0-9]{2}\s[0-9]{6,7}$` | `388 6759839` |
| Fisso (alt) | `0XX-XXXXXXX` | `^0[1-9][0-9]{1,3}-[0-9]{5,8}$` | `055-8517362` |
| Cellulare (alt) | `3XXXXXXXXX` | `^3[0-9]{9}$` | `3886759839` |

### 4.2 Test Cases - Telefono Fisso

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| TF-001 | Formato standard | `055 8517362` | VALIDO | P2 |
| TF-002 | Formato standard | `06 6268613` | VALIDO | P2 |
| TF-003 | Formato standard | `02 7477647` | VALIDO | P2 |
| TF-004 | Formato standard | `091 3639946` | VALIDO | P2 |
| TF-005 | Formato standard | `081 8643050` | VALIDO | P2 |
| TF-006 | Formato con trattino | `055-8517362` | VALIDO (normalizzare) | P2 |
| TF-007 | Senza spazi | `0558517362` | VALIDO (normalizzare) | P2 |
| TF-008 | Prefisso invalido | `000 1234567` | ERRORE: prefisso non valido | P2 |
| TF-009 | Inizia con 1 | `123 4567890` | ERRORE: deve iniziare con 0 | P2 |
| TF-010 | Troppo corto | `06 123` | ERRORE: numero troppo corto | P2 |
| TF-011 | Troppo lungo | `06 12345678901` | ERRORE: numero troppo lungo | P2 |

**Prefissi fissi italiani di riferimento dal dataset:**

| Prefisso | Città | Soggetti |
|----------|-------|----------|
| 055 | Firenze/Toscana | ID 1, 14, 15, 26, 35, 37, 53, 82, 96, 97 |
| 06 | Roma | ID 2, 17, 21, 69, 91 |
| 02 | Milano | ID 7, 18, 38, 77, 86, 100 |
| 091 | Palermo | ID 4, 12, 33, 34, 42, 54, 56, 61, 78, 83, 87 |
| 081 | Napoli | ID 11, 29, 42, 46, 50 |
| 051 | Bologna | ID 6, 28, 30, 74, 93, 95 |
| 041 | Venezia | ID 39, 53, 58, 65, 76, 85 |
| 011 | Torino | ID 16, 20, 25, 62, 80, 83, 84, 90, 99 |
| 010 | Genova | ID 27, 63, 66, 92, 98 |
| 080 | Bari | ID 41, 44, 67, 94 |

### 4.3 Test Cases - Telefono Cellulare

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| TC-001 | Formato standard | `388 6759839` | VALIDO | P2 |
| TC-002 | Formato standard | `392 5928136` | VALIDO | P2 |
| TC-003 | Formato standard | `366 1079030` | VALIDO | P2 |
| TC-004 | Formato standard | `389 9265572` | VALIDO | P2 |
| TC-005 | Formato standard | `377 6879798` | VALIDO | P2 |
| TC-006 | Formato standard | `347 8955146` | VALIDO | P2 |
| TC-007 | Formato standard | `320 2452212` | VALIDO | P2 |
| TC-008 | Formato standard | `333 4749227` | VALIDO | P2 |
| TC-009 | Formato standard | `349 1890925` | VALIDO | P2 |
| TC-010 | Formato standard | `393 3285611` | VALIDO | P2 |
| TC-011 | Senza spazi | `3886759839` | VALIDO (normalizzare) | P2 |
| TC-012 | Con trattino | `388-675-9839` | VALIDO (normalizzare) | P2 |
| TC-013 | Prefisso invalido | `300 1234567` | ERRORE: prefisso cellulare non valido | P2 |
| TC-014 | Troppo corto | `388 12345` | ERRORE: numero troppo corto | P2 |
| TC-015 | Troppo lungo | `388 12345678901` | ERRORE: numero troppo lungo | P2 |
| TC-016 | Inizia con 0 | `088 6759839` | ERRORE: cellulare deve iniziare con 3 | P2 |

**Prefissi cellulari italiani validi:**

| Prefisso | Operatore Storico |
|----------|-------------------|
| 320-329 | TIM |
| 330-339 | TIM |
| 340-349 | TIM/Vodafone |
| 360-369 | TIM |
| 377-379 | Vodafone |
| 380-389 | Wind |
| 390-393 | Wind/3 |

### 4.4 Test Cases - Validazione Prefisso vs Provincia

**Nota:** Questa è una validazione di coerenza, non bloccante ma con warning.

| ID | Soggetto | Telefono | Città | Coerenza | Priorità |
|----|----------|----------|-------|----------|----------|
| TF-COE-001 | ID 1 - Ilaria Fontana | 055 8517362 | Taranto | WARNING: prefisso FI per città TA | P4 |
| TF-COE-002 | ID 2 - Luca Bruno | 06 6268613 | Torino | WARNING: prefisso RM per città TO | P4 |
| TF-COE-003 | ID 11 - Giuseppe Costa | 081 8643050 | Sassari | WARNING: prefisso NA per città SS | P4 |
| TF-COE-004 | ID 16 - Giulia Marino | 011 9353886 | Catania | WARNING: prefisso TO per città CT | P4 |

**Nota:** I numeri di telefono moderni (VoIP, portabilità) rendono questa validazione solo indicativa.

---

## 5. Validazione Indirizzi

### 5.1 Struttura Indirizzo Italiano

```
Via/Viale/Corso/Piazza [Nome], [Numero Civico]
Città (CAP) Provincia
```

### 5.2 Test Cases - Formato Indirizzo

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| IND-F-001 | Via standard | `Via della Repubblica, 197` | VALIDO | P2 |
| IND-F-002 | Via con nome semplice | `Via Roma, 40` | VALIDO | P2 |
| IND-F-003 | Viale | `Viale Europa, 196` | VALIDO | P2 |
| IND-F-004 | Corso | `Corso Italia, 165` | VALIDO | P2 |
| IND-F-005 | Piazza | `Piazza del Duomo, 72` | VALIDO | P2 |
| IND-F-006 | Corso con nome | `Corso Vittorio Emanuele, 80` | VALIDO | P2 |
| IND-F-007 | Via senza numero | `Via Roma` | WARNING: numero civico mancante | P3 |
| IND-F-008 | Solo numero | `197` | ERRORE: indirizzo incompleto | P2 |
| IND-F-009 | Campo vuoto | `` | ERRORE: campo obbligatorio | P2 |

### 5.3 Test Cases - Tipi di Via

**Tipi validi presenti nel dataset:**

| Tipo | Esempi | Quantità |
|------|--------|----------|
| Via | Via Roma, Via Kennedy, Via Mazzini | ~50 |
| Viale | Viale Europa | ~10 |
| Corso | Corso Italia, Corso Vittorio Emanuele | ~10 |
| Piazza | Piazza del Duomo | ~5 |

| ID | Tipo Via | Validità | Priorità |
|----|----------|----------|----------|
| IND-TV-001 | Via | VALIDO | P2 |
| IND-TV-002 | Viale | VALIDO | P2 |
| IND-TV-003 | Corso | VALIDO | P2 |
| IND-TV-004 | Piazza | VALIDO | P2 |
| IND-TV-005 | Largo | VALIDO | P2 |
| IND-TV-006 | Vicolo | VALIDO | P2 |
| IND-TV-007 | Strada | VALIDO | P2 |
| IND-TV-008 | Contrada | VALIDO | P2 |
| IND-TV-009 | xyz | ERRORE: tipo via non riconosciuto | P2 |

### 5.4 Test Cases - CAP

**Formato CAP italiano:** 5 cifre (NNNNN)

| ID | Descrizione | CAP | Città | Risultato Atteso | Priorità |
|----|-------------|-----|-------|------------------|----------|
| CAP-001 | Roma | 00100 | Roma | VALIDO | P2 |
| CAP-002 | Taranto | 74100 | Taranto | VALIDO | P2 |
| CAP-003 | Torino | 10100 | Torino | VALIDO | P2 |
| CAP-004 | Trieste | 34100 | Trieste | VALIDO | P2 |
| CAP-005 | Sassari | 07100 | Sassari | VALIDO | P2 |
| CAP-006 | Messina | 98100 | Messina | VALIDO | P2 |
| CAP-007 | Napoli | 80100 | Napoli | VALIDO | P2 |
| CAP-008 | Modena | 41100 | Modena | VALIDO | P2 |
| CAP-009 | Genova | 16100 | Genova | VALIDO | P2 |
| CAP-010 | Venezia | 30100 | Venezia | VALIDO | P2 |
| CAP-011 | Lunghezza errata | 1234 | - | ERRORE: CAP deve essere 5 cifre | P2 |
| CAP-012 | Lettere | 1234A | - | ERRORE: solo numeri ammessi | P2 |
| CAP-013 | Inesistente | 99999 | - | ERRORE: CAP non esistente | P2 |

### 5.5 Test Cases - Coerenza CAP-Città-Provincia

| ID | Città | CAP | Provincia | Esito | Priorità |
|----|-------|-----|-----------|-------|----------|
| CAP-COE-001 | Roma | 00100 | RM | VALIDO | P1 |
| CAP-COE-002 | Roma | 20100 | RM | ERRORE: CAP 20xxx è di Milano | P1 |
| CAP-COE-003 | Taranto | 74100 | TA | VALIDO | P1 |
| CAP-COE-004 | Taranto | 74100 | BA | ERRORE: 74xxx è di TA, non BA | P1 |
| CAP-COE-005 | Torino | 10100 | TO | VALIDO | P1 |
| CAP-COE-006 | Milano | 20100 | MI | VALIDO | P1 |
| CAP-COE-007 | Napoli | 80100 | NA | VALIDO | P1 |
| CAP-COE-008 | Firenze | 50100 | FI | VALIDO | P1 |
| CAP-COE-009 | Bologna | 40100 | BO | VALIDO | P1 |
| CAP-COE-010 | Padova | 35100 | PD | VALIDO | P1 |

### 5.6 Test Cases - Verifica Esistenza Indirizzo (P4)

**Nota:** Richiede integrazione con servizi esterni (OpenStreetMap, Google Maps API, ISTAT).

| ID | Indirizzo Completo | Verifica | Priorità |
|----|-------------------|----------|----------|
| IND-EX-001 | Via della Repubblica 197, 74100 Taranto TA | Verificare esistenza via API | P4 |
| IND-EX-002 | Via Raffaello 197, 10100 Torino TO | Verificare esistenza via API | P4 |
| IND-EX-003 | Via Roma 40, 34100 Trieste TS | Verificare esistenza via API | P4 |
| IND-EX-004 | Via Kennedy 113, 07100 Sassari SS | Verificare esistenza via API | P4 |
| IND-EX-005 | Via Inventata 999, 00100 Roma RM | ERRORE: via non trovata | P4 |

**Approccio suggerito:**
1. Validazione sintattica (locale) - P2
2. Validazione CAP (database locale ISTAT) - P2
3. Verifica esistenza (API esterna) - P4

---

## 6. Validazione Email e PEC

### 6.1 Test Cases - Formato Email

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| EM-001 | Email standard | `ilariafontana@yahoo.it` | VALIDO | P2 |
| EM-002 | Email con punto | `l.bruno@outlook.it` | VALIDO | P2 |
| EM-003 | Email con punto | `c.ferraro@yahoo.it` | VALIDO | P2 |
| EM-004 | Email con underscore | `nome_cognome@gmail.com` | VALIDO | P2 |
| EM-005 | Senza @ | `ilariafontanayahoo.it` | ERRORE: formato invalido | P2 |
| EM-006 | Senza dominio | `ilariafontana@` | ERRORE: formato invalido | P2 |
| EM-007 | Senza TLD | `ilariafontana@yahoo` | ERRORE: formato invalido | P2 |
| EM-008 | Doppio @ | `ilaria@@yahoo.it` | ERRORE: formato invalido | P2 |
| EM-009 | Spazi | `ilaria fontana@yahoo.it` | ERRORE: spazi non ammessi | P2 |
| EM-010 | Caratteri speciali | `ilaria!@yahoo.it` | ERRORE: caratteri non ammessi | P2 |

### 6.2 Test Cases - Domini Email Comuni

| ID | Dominio | Validità | Note |
|----|---------|----------|------|
| EM-D-001 | @gmail.com | VALIDO | Google |
| EM-D-002 | @yahoo.it | VALIDO | Yahoo Italia |
| EM-D-003 | @outlook.it | VALIDO | Microsoft Italia |
| EM-D-004 | @hotmail.it | VALIDO | Microsoft Italia |
| EM-D-005 | @libero.it | VALIDO | Libero Italia |
| EM-D-006 | @virgilio.it | VALIDO | Virgilio Italia |
| EM-D-007 | @dominio.inesistente | WARNING: dominio sconosciuto | Verificare |

### 6.3 Test Cases - PEC (Posta Elettronica Certificata)

**Domini PEC validi in Italia:**

| Dominio | Gestore |
|---------|---------|
| @pec.it | Aruba |
| @arubapec.it | Aruba |
| @legalmail.it | InfoCert |
| @postecert.it | Poste Italiane |

| ID | Descrizione | Input | Risultato Atteso | Priorità |
|----|-------------|-------|------------------|----------|
| PEC-001 | PEC Aruba | `ferraro@postecert.it` | VALIDO | P2 |
| PEC-002 | PEC Aruba | `parisi@arubapec.it` | VALIDO | P2 |
| PEC-003 | PEC InfoCert | `lombardo@legalmail.it` | VALIDO | P2 |
| PEC-004 | PEC generica | `giordano@arubapec.it` | VALIDO | P2 |
| PEC-005 | PEC con punto | `ferrari@pec.it` | VALIDO | P2 |
| PEC-006 | PEC aziendale | `globallogisticasrls@pec.it` | VALIDO | P2 |
| PEC-007 | PEC aziendale | `bruno&ferrarisrl@arubapec.it` | VALIDO | P2 |
| PEC-008 | Non è PEC | `nome@gmail.com` | WARNING: non è un dominio PEC | P3 |
| PEC-009 | Dominio PEC falso | `nome@fakepec.it` | WARNING: dominio PEC non riconosciuto | P3 |

### 6.4 Test Cases - Unicità Email

| ID | Descrizione | Soggetti | Risultato Atteso | Priorità |
|----|-------------|----------|------------------|----------|
| EM-UN-001 | Email duplicata stesso tipo | `info@immobiliare.it` (ID 76, 83, 86, 87, 96, 99) | WARNING: email condivisa | P3 |
| EM-UN-002 | Email duplicata stesso tipo | `info@delta.it` (ID 81, 90, 92) | WARNING: email condivisa | P3 |
| EM-UN-003 | Email duplicata stesso tipo | `info@omega.it` (ID 74, 85) | WARNING: email condivisa | P3 |
| EM-UN-004 | Email duplicata stesso tipo | `info@euro.it` (ID 80, 84) | WARNING: email condivisa | P3 |
| EM-UN-005 | Email duplicata stesso tipo | `info@nord.it` (ID 77, 97) | WARNING: email condivisa | P3 |

**Nota:** Email duplicate tra persone giuridiche diverse possono indicare gruppi aziendali o errori di inserimento.

---

## 7. Validazioni Cross-Field

### 7.1 Test Cases - Coerenza Tipo Soggetto

| ID | Tipo | Campo | Valore | Esito | Priorità |
|----|------|-------|--------|-------|----------|
| XF-TS-001 | PERSONA_FISICA | Codice Fiscale | FNTLRI86R58H199F | VALIDO | P1 |
| XF-TS-002 | PERSONA_FISICA | Ragione Sociale | - | VALIDO (non richiesto) | P1 |
| XF-TS-003 | PERSONA_FISICA | Nome + Cognome | Ilaria Fontana | VALIDO (richiesti) | P1 |
| XF-TS-004 | PERSONA_GIURIDICA | Ragione Sociale | Global Logistica S.r.l.s. | VALIDO | P1 |
| XF-TS-005 | PERSONA_GIURIDICA | P.IVA | 77933820092 | VALIDO (obbligatoria) | P1 |
| XF-TS-006 | PERSONA_GIURIDICA | Codice Fiscale | - | VALIDO (opzionale) | P1 |
| XF-TS-007 | PERSONA_GIURIDICA | P.IVA | - | ERRORE: P.IVA obbligatoria | P1 |
| XF-TS-008 | PERSONA_FISICA | Nome | - | ERRORE: nome obbligatorio | P1 |
| XF-TS-009 | PERSONA_FISICA | Cognome | - | ERRORE: cognome obbligatorio | P1 |

### 7.2 Test Cases - Coerenza Forma Giuridica

**Forme giuridiche valide presenti:**

| Forma | Descrizione | Esempi ID |
|-------|-------------|-----------|
| S.r.l. | Società a responsabilità limitata | 73, 75, 76, 77, 79, 81, 82, 84, 86, 89, 92, 93, 94, 98, 100 |
| S.r.l.s. | S.r.l. semplificata | 71, 72, 80, 87, 88, 96, 97 |
| S.p.A. | Società per azioni | 77, 85, 90, 99 |
| S.a.s. | Società in accomandita semplice | 74, 91, 95 |
| S.n.c. | Società in nome collettivo | 78, 82, 83 |

| ID | Ragione Sociale | Forma Estratta | Validità | Priorità |
|----|-----------------|----------------|----------|----------|
| XF-FG-001 | Global Logistica S.r.l.s. | S.r.l.s. | VALIDO | P2 |
| XF-FG-002 | Bruno & Ferrari S.r.l. | S.r.l. | VALIDO | P2 |
| XF-FG-003 | Nord Informatica S.p.A. | S.p.A. | VALIDO | P2 |
| XF-FG-004 | Omega Project S.a.s. | S.a.s. | VALIDO | P2 |
| XF-FG-005 | Mancini Immobiliare S.n.c. | S.n.c. | VALIDO | P2 |
| XF-FG-006 | Azienda Test | - | WARNING: forma giuridica mancante | P3 |
| XF-FG-007 | Azienda Test S.r.l.x. | S.r.l.x. | ERRORE: forma giuridica non valida | P2 |

### 7.3 Test Cases - PEC Obbligatoria per PG

| ID | Tipo | Ragione Sociale | PEC | Esito | Priorità |
|----|------|-----------------|-----|-------|----------|
| XF-PEC-001 | PERSONA_GIURIDICA | Global Logistica S.r.l.s. | globallogisticasrls@pec.it | VALIDO | P1 |
| XF-PEC-002 | PERSONA_GIURIDICA | Nord Informatica S.p.A. | nordinformaticaspa@legalmail.it | VALIDO | P1 |
| XF-PEC-003 | PERSONA_GIURIDICA | Azienda senza PEC | - | ERRORE: PEC obbligatoria per PG | P1 |
| XF-PEC-004 | PERSONA_FISICA | Ilaria Fontana | - | VALIDO (PEC opzionale per PF) | P2 |
| XF-PEC-005 | PERSONA_FISICA | Carlo Ferraro | ferraro@postecert.it | VALIDO (PEC presente) | P2 |

### 7.4 Test Cases - Età e Data Nascita

| ID | Data Nascita | Età (al 2026) | Tipo Soggetto | Esito | Priorità |
|----|--------------|---------------|---------------|-------|----------|
| XF-ETA-001 | 1952-08-06 | 73 anni | PERSONA_FISICA | VALIDO | P3 |
| XF-ETA-002 | 2001-12-04 | 24 anni | PERSONA_FISICA | VALIDO | P3 |
| XF-ETA-003 | 1954-07-25 | 71 anni | PERSONA_FISICA | VALIDO | P3 |
| XF-ETA-004 | 2010-01-01 | 16 anni | PERSONA_FISICA | WARNING: minorenne | P3 |
| XF-ETA-005 | 1920-01-01 | 106 anni | PERSONA_FISICA | WARNING: età molto avanzata | P3 |
| XF-ETA-006 | 2030-01-01 | - | PERSONA_FISICA | ERRORE: data nel futuro | P1 |

---

## 8. Test Cases Negativi

### 8.1 Injection e Sicurezza

| ID | Campo | Input Malevolo | Esito Atteso | Priorità |
|----|-------|----------------|--------------|----------|
| SEC-001 | Nome | `<script>alert('XSS')</script>` | ERRORE: caratteri non ammessi | P1 |
| SEC-002 | Cognome | `'; DROP TABLE soggetti; --` | ERRORE: caratteri non ammessi | P1 |
| SEC-003 | Email | `test@test.com<script>` | ERRORE: formato email invalido | P1 |
| SEC-004 | Indirizzo | `../../../etc/passwd` | ERRORE: caratteri non ammessi | P1 |
| SEC-005 | CF | `AAAAAAAAAAAAAAAA' OR '1'='1` | ERRORE: formato CF invalido | P1 |
| SEC-006 | P.IVA | `11111111111; DELETE *` | ERRORE: solo numeri ammessi | P1 |

### 8.2 Boundary Values

| ID | Campo | Input | Esito Atteso | Priorità |
|----|-------|-------|--------------|----------|
| BV-001 | Nome | `A` | WARNING: nome troppo corto | P3 |
| BV-002 | Nome | (200 caratteri) | ERRORE: nome troppo lungo | P2 |
| BV-003 | Cognome | `X` | WARNING: cognome troppo corto | P3 |
| BV-004 | Cognome | (200 caratteri) | ERRORE: cognome troppo lungo | P2 |
| BV-005 | Civico | `0` | WARNING: numero civico 0 | P3 |
| BV-006 | Civico | `99999` | WARNING: numero civico molto alto | P3 |
| BV-007 | CAP | `00000` | ERRORE: CAP non valido | P2 |
| BV-008 | CAP | `99999` | ERRORE: CAP non esistente | P2 |

### 8.3 Caratteri Speciali e Unicode

| ID | Campo | Input | Esito Atteso | Priorità |
|----|-------|-------|--------------|----------|
| UC-001 | Nome | `François` | VALIDO (ç ammesso) | P2 |
| UC-002 | Cognome | `O'Brien` | VALIDO (apostrofo ammesso) | P2 |
| UC-003 | Cognome | `Müller` | VALIDO (umlaut ammesso) | P2 |
| UC-004 | Nome | `José` | VALIDO (accenti ammessi) | P2 |
| UC-005 | Indirizzo | `Via Pietà, 10` | VALIDO (accenti ammessi) | P2 |
| UC-006 | Nome | `Nome🎉` | ERRORE: emoji non ammessi | P2 |
| UC-007 | Ragione Sociale | `Azienda™` | WARNING: simboli speciali | P3 |

### 8.4 Duplicati

| ID | Tipo Duplicato | Campi | Esito Atteso | Priorità |
|----|----------------|-------|--------------|----------|
| DUP-001 | CF duplicato | FNTLRI86R58H199F | ERRORE: CF già esistente | P1 |
| DUP-002 | P.IVA duplicata | 77933820092 | ERRORE: P.IVA già esistente | P1 |
| DUP-003 | Email duplicata (stesso tipo) | ilariafontana@yahoo.it | WARNING: email già in uso | P2 |
| DUP-004 | PEC duplicata | globallogisticasrls@pec.it | WARNING: PEC già in uso | P2 |
| DUP-005 | Nome+Cognome+DataNascita | Stessa combinazione | WARNING: possibile duplicato | P3 |

---

## 9. Riepilogo Copertura

### 9.1 Matrice di Copertura per Campo

| Campo | Formato | Coerenza | Esistenza | Unicità | Sicurezza |
|-------|---------|----------|-----------|---------|-----------|
| Codice Fiscale | ✅ | ✅ | N/A | ✅ | ✅ |
| Partita IVA | ✅ | ✅ | N/A | ✅ | ✅ |
| Nome | ✅ | ✅ | N/A | N/A | ✅ |
| Cognome | ✅ | ✅ | N/A | N/A | ✅ |
| Ragione Sociale | ✅ | ✅ | N/A | N/A | ✅ |
| Data Nascita | ✅ | ✅ | N/A | N/A | ✅ |
| Luogo Nascita | ✅ | ✅ | ✅ | N/A | ✅ |
| Indirizzo | ✅ | ✅ | ✅ (P4) | N/A | ✅ |
| CAP | ✅ | ✅ | ✅ | N/A | ✅ |
| Provincia | ✅ | ✅ | ✅ | N/A | ✅ |
| Telefono | ✅ | ⚠️ | N/A | N/A | ✅ |
| Cellulare | ✅ | N/A | N/A | N/A | ✅ |
| Email | ✅ | N/A | ⚠️ | ✅ | ✅ |
| PEC | ✅ | ✅ | ⚠️ | ✅ | ✅ |

**Legenda:** ✅ = Coperto | ⚠️ = Parziale | N/A = Non Applicabile

### 9.2 Conteggio Test Cases

| Categoria | Quantità |
|-----------|----------|
| Codice Fiscale - Formato | 8 |
| Codice Fiscale - Cognome | 14 |
| Codice Fiscale - Nome | 16 |
| Codice Fiscale - Data | 10 |
| Codice Fiscale - Giorno/Sesso | 10 |
| Codice Fiscale - Comune | 15 |
| Codice Fiscale - CIN | 10 |
| Codice Fiscale - Coerenza | 8 |
| Partita IVA - Formato | 8 |
| Partita IVA - Check Digit | 10 |
| Partita IVA - Provincia | 5 |
| Partita IVA - PG | 6 |
| Telefono Fisso | 11 |
| Telefono Cellulare | 16 |
| Telefono - Coerenza | 4 |
| Indirizzo - Formato | 9 |
| Indirizzo - Tipo Via | 9 |
| CAP - Formato | 13 |
| CAP - Coerenza | 10 |
| Indirizzo - Esistenza | 5 |
| Email - Formato | 10 |
| Email - Domini | 7 |
| PEC | 9 |
| Email - Unicità | 5 |
| Cross-Field - Tipo Soggetto | 9 |
| Cross-Field - Forma Giuridica | 7 |
| Cross-Field - PEC | 5 |
| Cross-Field - Età | 6 |
| Sicurezza | 6 |
| Boundary Values | 8 |
| Unicode | 7 |
| Duplicati | 5 |
| **TOTALE** | **~271** |

### 9.3 Priorità Test

| Priorità | Quantità | % |
|----------|----------|---|
| P1 - Bloccante | ~120 | 44% |
| P2 - Alta | ~100 | 37% |
| P3 - Media | ~35 | 13% |
| P4 - Bassa | ~16 | 6% |

### 9.4 Note Implementative

1. **Validazione CF**: Utilizzare libreria `codicefiscale` per Python o equivalente
2. **Validazione P.IVA**: Implementare algoritmo Luhn modificato
3. **CAP**: Database ISTAT comuni italiani
4. **Indirizzi**: OpenStreetMap Nominatim API per verifica esistenza
5. **PEC**: Verificare domini accreditati AgID

### 9.5 Casi dal Dataset con Anomalie da Verificare

| ID | Nome | Anomalia Potenziale |
|----|------|---------------------|
| 1-70 | Telefono fisso | Prefisso non coerente con città residenza |
| 71-100 | Email condivise | `info@immobiliare.it` usata da 6 aziende |
| Vari | Luogo nascita vs residenza | Verificare codice Belfiore |

---

## Appendice A - Codici di Riferimento

### A.1 Codici Belfiore (Comuni di Nascita nel Dataset)

| Codice | Comune |
|--------|--------|
| A662 | Bari |
| A944 | Bologna |
| B157 | Brescia |
| B354 | Cagliari |
| C351 | Catania |
| D548 | Ferrara |
| D612 | Firenze |
| D643 | Foggia |
| D969 | Genova |
| E625 | Livorno |
| F158 | Messina |
| F205 | Milano |
| F839 | Napoli |
| G224 | Padova |
| G273 | Palermo |
| G478 | Perugia |
| G999 | Prato |
| H199 | Ravenna |
| H223 | Reggio Emilia |
| H224 | Reggio Calabria |
| H294 | Rimini |
| H501 | Roma |
| H703 | Salerno |
| I452 | Sassari |
| L049 | Taranto |
| L219 | Torino |
| L424 | Trieste |
| L736 | Venezia |
| L781 | Verona |

### A.2 Codici Provincia

| Sigla | Provincia | CAP Range |
|-------|-----------|-----------|
| BO | Bologna | 40xxx |
| BS | Brescia | 25xxx |
| CA | Cagliari | 09xxx |
| CT | Catania | 95xxx |
| FE | Ferrara | 44xxx |
| FG | Foggia | 71xxx |
| FI | Firenze | 50xxx |
| GE | Genova | 16xxx |
| LI | Livorno | 57xxx |
| ME | Messina | 98xxx |
| MO | Modena | 41xxx |
| NA | Napoli | 80xxx |
| PA | Palermo | 90xxx |
| PD | Padova | 35xxx |
| PG | Perugia | 06xxx |
| PO | Prato | 59xxx |
| RA | Ravenna | 48xxx |
| RC | Reggio Calabria | 89xxx |
| RE | Reggio Emilia | 42xxx |
| RM | Roma | 00xxx |
| RN | Rimini | 47xxx |
| SA | Salerno | 84xxx |
| SS | Sassari | 07xxx |
| TA | Taranto | 74xxx |
| TO | Torino | 10xxx |
| TS | Trieste | 34xxx |
| VE | Venezia | 30xxx |
| VR | Verona | 37xxx |

---

**Fine documento**
