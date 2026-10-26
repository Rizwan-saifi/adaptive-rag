# Auth Gateway (NestJS)

Backend-For-Frontend for Adaptive RAG, built with NestJS. Handles user signup/login (API token + JWT)
and proxies authenticated chat requests to the Python RAG service.

## Run

```bash
npm install
cp .env.example .env   # optional; defaults match the Rust version
npm run build
npm run start:prod      # or: npm run start:dev  (watch mode)
```

Listens on `http://127.0.0.1:8080/api`.

## Endpoints

| Method | Path               | Auth                                        | Body                       | Response                         |
|--------|--------------------|---------------------------------------------|----------------------------|----------------------------------|
| POST   | `/api/init`        | none                                        | -                          | `{ api_token, jwt: null }`       |
| POST   | `/api/create_user` | `X-API-TOKEN`                               | `{ username, password }`   | `{ status: "created" }` (409 if taken) |
| POST   | `/api/login`       | `X-API-TOKEN`                               | `{ username, password }`   | `{ api_token: null, jwt }`       |
| POST   | `/api/chat`        | `X-API-TOKEN` + `Authorization: Bearer <jwt>` | `{ query }`              | `{ answer }`                     |

`/api/chat` forwards to the Python service (`PYTHON_RAG_URL`), using the JWT as `session_id`.

## Configuration

See `.env.example`. `JWT_SECRET` is required and must match the RAG service's `JWT_SECRET`.
Passwords are stored as Argon2id hashes in SQLite (`DB_PATH`).
