"""
Invented texts with the layout `pdftotext -layout` gives for the real
samples (APE Emilia-Romagna, RLI12 receipt, visura per immobile). Values are
made up: never put the user's real documents in tests.
"""

APE_ER = """\
                             CERTIFICAZIONE
                Sistema di
                             ENERGETICA
          1. DATI DELL'IMMOBILE
          Comune: TORINO
          Indirizzo: VIA PO n.3
          Piano - Interno: 2°--
          Coordinate Gis: LAT: LON:
          Destinazione d'uso: E1 (1) - Abitazioni civili
            Cod. Comune                            Sezione              Foglio                     Particella            Subalterno                  I
                L219                                  /                    012                        345                     6
          2. DATI GENERALI
          4. PRESTAZIONE ENERGETICA GLOBALE E DEL FABBRICATO
                                                                            80<=Eptot<100                           EP gl,nren
                                                                            100<=Eptot<134
                                                                            134<=Eptot<174
                                                                                                                     111,24
                                                                            174<=Eptot<235
                                                                                                                    kWh/m² anno
                   ATTESTATO DI                                                                              RILASCIATO IL 23/02/2021
              PRESTAZIONE ENERGETICA                                                                       VALIDO FINO AL 23/02/2031
                                                                         Classe
                                                                       Energetica            
             Codice                                                    raggiungibile
              REN 1                                      NO                   10                  90,20                  C
"""

APE_CON_CLASSE = APE_ER + "\n          CLASSE ENERGETICA: D\n"

RLI12 = """\
         SERVIZIO TELEMATICO ENTRATEL DI PRESENTAZIONE DELLE DICHIARAZIONI
COMUNICAZIONE DI AVVENUTO RICEVIMENTO RICHIESTA DI
REGISTRAZIONE CONTRATTI DI LOCAZIONE E AFFITTO DI IMMOBILI (mod.RLI12)
DATI DEGLI IMMOBILI (importi in euro)
Ubicato nel comune di TORINO                                        Prov. TO
"""

VISURA_IMMOBILE = """\
Direzione Provinciale di Torino
                                                                                      Visura per immobile
Dati della richiesta                        Comune di TORINO ( Codice: L219)
Catasto Fabbricati                          Foglio: 12 Particella: 345 Sub.: 6
"""

PLANIMETRIA = """\
Data presentazione: 01/02/2010 - Data: 03/04/2024 - n. T12345 - Richiedente: X
Catasto dei Fabbricati - Situazione al 03/04/2024
Planimetria di u.i.u. in Comune di Torino
Via Po civ. 3
Identificativi Catastali:            Compilata da:
Sezione:                             Rossi Mario
Foglio: 12
Particella: 345
Subalterno: 6
Scheda n. 1    Scala 1:200
"""

TESTO_QUALSIASI = "Fattura n. 12 del 01/02/2024\nTotale euro 100,00\n"
