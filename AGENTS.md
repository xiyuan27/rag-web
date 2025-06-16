# Python Backend Overview

## 1. Framework and Dependencies
- The backend uses **Flask** for the HTTP API. Initialization occurs in `api/apps/__init__.py` where `Flask` and `LoginManager` are set up.
- Database access relies on **Peewee** with `PooledMySQLDatabase` for connection pooling.
- Asynchronous background tasks in `rag/svr/task_executor.py` use **Trio**.
- Object storage is handled by **MinIO** via the `minio` Python client.

Python dependencies are installed via `uv` as documented in `docs/develop/launch_ragflow_from_source.md` using a Python 3.10 virtual environment.

## 2. Project Structure
- `api/` – Flask application and REST endpoints.
- `rag/` – document processing logic and background task executor.
- `plugin/` – plugin framework loaded on startup.
- `conf/service_conf.yaml` – runtime configuration for services like MySQL, MinIO and Redis.
- Entry points:
  - `python api/ragflow_server.py`
  - `python rag/svr/task_executor.py`
  Both require `PYTHONPATH=.`, as shown in development docs.

## 3. Login and Permission Filtering
- `LoginManager` loads users from the `Authorization` header via JWT tokens. See `load_user` in `api/apps/__init__.py`.
- API routes use `@login_required` for session based checks or `token_required` for API key validation.
- `token_required` verifies an API key against the `APIToken` table and injects `tenant_id` into the handler.

## 4. MySQL Handling Modules
- Database connections are defined in `api/db/db_models.py` using `PooledMySQLDatabase`.
- ORM models such as `User`, `Tenant`, `Knowledgebase` reside in this file and are used by service classes under `api/db/services/`.
- The `conf/service_conf.yaml` file specifies MySQL connection parameters like host, port and credentials.

## 5. MinIO Storage Modules
- `rag/utils/minio_conn.py` implements `RAGFlowMinio`, a thin wrapper over the `minio` client to upload, download and manage objects.
- `rag/utils/storage_factory.py` selects the storage implementation (MinIO by default).
- Background tasks (`rag/svr/task_executor.py`) retrieve files from MinIO before processing.

Only the Python backend components are documented here; the front‑end under `web/` is covered separately.
