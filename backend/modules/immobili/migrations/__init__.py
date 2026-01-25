"""
Migrations for Immobili module.

Le migrazioni Alembic per questo modulo devono essere eseguite dal core della piattaforma.
I moduli non hanno accesso diretto all'engine DB.

Struttura delle migrazioni:
- Le migrazioni creano tabelle con prefisso "immo_"
- Schema target definito nel manifest (public + tenant)
- Il core valida che tutte le tabelle abbiano il prefisso corretto

Tabelle PUBLIC (create durante register):
- immo_categorie_catastali
- immo_tipologie_terreno

Tabelle TENANT (create durante install):
- immo_tipologie_terreno_overrides
- immo_terreni
- immo_unita_immobiliari
- immo_condomini
- immo_proprietari
- immo_diritti_immobile
- immo_certificati_energetici
- immo_tabelle_millesimali
- immo_millesimi_unita
- immo_tipo_immobile_categoria_map
"""
