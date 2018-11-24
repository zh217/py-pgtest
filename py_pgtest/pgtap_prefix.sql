\unset ECHO
\set QUIET 1
-- Turn off echo and keep things quiet.

-- Format the output for nice TAP.
\pset format unaligned
\pset tuples_only true
\pset pager off

-- Revert all changes on failure.
\set ON_ERROR_ROLLBACK 1
\set ON_ERROR_STOP true

SET client_min_messages TO WARNING;

CREATE SCHEMA IF NOT EXISTS tap;
GRANT USAGE ON SCHEMA tap TO PUBLIC;

ALTER DEFAULT PRIVILEGES IN SCHEMA tap GRANT EXECUTE ON FUNCTIONS TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA tap GRANT USAGE ON TYPES TO PUBLIC;

CREATE EXTENSION IF NOT EXISTS pgtap SCHEMA tap;

SET SEARCH_PATH = "$user", public, tap;
