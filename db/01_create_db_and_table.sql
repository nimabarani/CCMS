-- create_db_and_table.sql
-- Run as postgres or another superuser.
\c "ClientDB"

-- A staging schema so we can COPY the raw CSV first
CREATE SCHEMA staging;
-- 2.1  Table that mirrors the incoming CSV
CREATE TABLE IF NOT EXISTS staging.client_credentials_raw (
  client_id BIGINT PRIMARY KEY,
  clientname TEXT, 
  password TEXT NOT NULL,
  email TEXT NOT NULL, 
  created_on timestamptz DEFAULT NOW()
);
-- 2.2  Production table with only encrypted columns
CREATE TABLE IF NOT EXISTS public.client_credentials (
  client_id BIGINT PRIMARY KEY,
  encrypted_clientname bytea NOT NULL, 
  encrypted_password bytea NOT NULL, 
  encrypted_email bytea NOT NULL,
  created_on timestamptz
);
-- 2.3  Table stores users credentials
CREATE TABLE IF NOT EXISTS public.user_credentials (
  user_id SERIAL PRIMARY KEY, 
  password_hash TEXT NOT NULL, 
  email TEXT UNIQUE NOT NULL, 
  salt CHAR(32)
);
CREATE INDEX idx_email ON user_credentials(email);
