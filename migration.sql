-- Migrazione per aggiungere tipo_cliente alla tabella clienti

-- Aggiungi la colonna tipo_cliente con valore default 'normale'
ALTER TABLE clienti ADD COLUMN tipo_cliente VARCHAR(20) DEFAULT 'normale' NOT NULL;

-- Verifica i risultati
SELECT id, nome, cognome, tipo_cliente FROM clienti LIMIT 5;