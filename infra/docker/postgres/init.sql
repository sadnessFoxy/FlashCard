-- Khởi tạo PostgreSQL. Chỉ chạy khi volume dữ liệu được tạo lần đầu.
-- Database chính (flashcard) do POSTGRES_DB tạo; thêm database test riêng (R11).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE DATABASE flashcard_test OWNER flashcard;

\connect flashcard_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
