-- import_and_encrypt.sql
-- Run while connected to ClientDB.
BEGIN;
-- 3.0 Read encryption_key from ENVIRONMENT
\set encryption_key `echo $ENCRYPTION_KEY`

-- 3.1  Load raw CSV into the staging table
\COPY staging.client_credentials_raw(client_id, clientname, password, email, created_on) FROM '/docker-entrypoint-initdb.d/client_data.csv' WITH (FORMAT csv, HEADER TRUE);
-- Enable pgcrypto for row-level encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- 3.2  One-time encryption pass
INSERT INTO public.client_credentials (
  client_id, encrypted_clientname, 
  encrypted_password, encrypted_email, 
  created_on
) 
SELECT 
  client_id, 
  pgp_sym_encrypt(clientname, :'encryption_key'), 
  pgp_sym_encrypt(password, :'encryption_key'), 
  pgp_sym_encrypt(email, :'encryption_key'), 
  created_on 
FROM 
  staging.client_credentials_raw;
-- 3.3  Clear raw data
TRUNCATE TABLE staging.client_credentials_raw;
COMMIT;
