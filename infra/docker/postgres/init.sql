-- PostgreSQL init. Runs only when the data volume is first created.
-- POSTGRES_DB creates `flashcard`; this adds the separate test database (R11).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE DATABASE flashcard_test OWNER flashcard;

\connect flashcard_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
