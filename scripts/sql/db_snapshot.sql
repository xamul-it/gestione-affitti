-- Fotografia del DB per promote.sh: una riga per tabella (public e tenant_*)
-- con il numero di righe, o la versione per le tabelle alembic_version*.
SELECT t.table_schema || '.' || t.table_name || ' ' ||
  CASE WHEN t.table_name ILIKE 'alembic_version%'
    THEN 'version=' || coalesce((xpath('/row/v/text()', query_to_xml(format('SELECT string_agg(version_num, '','' ORDER BY version_num) AS v FROM %I.%I', t.table_schema, t.table_name), false, true, '')))[1]::text, '')
    ELSE 'rows=' || (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I.%I', t.table_schema, t.table_name), false, true, '')))[1]::text
  END
FROM information_schema.tables t
WHERE t.table_type = 'BASE TABLE' AND (t.table_schema = 'public' OR t.table_schema LIKE 'tenant\_%')
ORDER BY 1;
