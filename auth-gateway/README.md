# Auth Gateway (NestJS)

Backend-For-Frontend for Adaptive RAG, built with NestJS. Handles user signup/login (API token + JWT)
and proxies authenticated chat requests to the Python RAG service.

## Run

```bash
npm install
cp .env.example .env   # then set JWT_SECRET (required)
npm run build
npm run start:prod      # or: npm run start:dev  (watch mode)
```

Listens on `http://127.0.0.1:8080/api` by default (`HOST`/`PORT`). In Docker Compose it runs as the
`auth-gateway` service on `0.0.0.0` inside the container.

## Endpoints

| Method | Path               | Auth                                          | Body                                  | Response                                |
|--------|--------------------|-----------------------------------------------|---------------------------------------|-----------------------------------------|
| POST   | `/api/init`        | none                                          | -                                     | `{ api_token, jwt: null }`              |
| POST   | `/api/create_user` | `X-API-TOKEN`                                 | `{ username, password }`              | `{ status: "created" }` (409 if taken)  |
| POST   | `/api/login`       | `X-API-TOKEN`                                 | `{ username, password }`              | `{ api_token: null, jwt }` (401 if wrong) |
| POST   | `/api/chat`        | `X-API-TOKEN` + `Authorization: Bearer <jwt>` | `{ query, conversation_id? }`         | `{ answer }`                            |

- API tokens from `/api/init` are kept in memory: they expire after `API_TOKEN_EXPIRES_IN` seconds and
  are lost when the gateway restarts.
- JWTs are signed with `JWT_SECRET`, carry the username as `sub`, and last one day by default
  (`JWT_EXPIRES_IN`).
- Signup requires a username of 3–32 characters from `A-Z a-z 0-9 _ . -` and a password of 8–128
  characters. Login only caps the lengths (username ≤ 64, password ≤ 128), so accounts created before
  these rules can still sign in. Invalid bodies get a 400.
- `/api/chat` forwards the query to the RAG service's `POST /rag/query` (`PYTHON_RAG_URL`) with the
  user's JWT, so the RAG service knows whose documents and history to use. `conversation_id` (up to 100
  characters) selects the conversation; without it, messages go to a conversation named `"default"`.
  If the RAG service can't be reached or returns an error the gateway answers 502, and 504 if it takes
  longer than `RAG_TIMEOUT` seconds. This endpoint returns the whole answer at once; the Streamlit UI
  calls the RAG service's streaming endpoint directly instead.

## Configuration

See `.env.example`:

| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET` | none (required) | Signs JWTs; must equal the RAG service's `JWT_SECRET` |
| `PORT` | `8080` | Listening port |
| `HOST` | `127.0.0.1` | Listening interface (`0.0.0.0` in a container) |
| `JWT_EXPIRES_IN` | `86400` | JWT lifetime in seconds |
| `API_TOKEN_EXPIRES_IN` | `86400` | API token lifetime in seconds |
| `DB_PATH` | `users.db` | SQLite file with users (Argon2id password hashes) |
| `PYTHON_RAG_URL` | `http://127.0.0.1:8000/rag/query` | RAG service query endpoint |
| `RAG_TIMEOUT` | `300` | Seconds to wait for the RAG service |
