-- Production database init. Runs only when the data volume is first created.
-- No test database here (R11: tests never run against this server).
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
