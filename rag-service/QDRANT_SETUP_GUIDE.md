# Qdrant Setup Guide

## 📋 Overview

The RAG service stores document chunks in **Qdrant**. You can run it three ways, and none of them
needs code changes, only environment variables in `rag-service/.env`:

| Mode | When | Configuration |
|---|---|---|
| **Embedded** (default) | Local development, single process | Nothing; data goes to `QDRANT_PATH` (default `qdrant_data`, i.e. `rag-service/qdrant_data` when started from `rag-service/`) |
| **Qdrant server via Docker Compose** | `docker compose up --build` | Set automatically (`QDRANT_URL=http://qdrant:6333`), data in the `qdrant_data` volume |
| **Qdrant Cloud** (optional) | Hosted, shared or production use | `QDRANT_URL` + `QDRANT_API_KEY` |

All users share one collection (`QDRANT_COLLECTION`, default `user_documents`); each chunk carries its
owner's `user_id` and its document's `doc_id` in the metadata, and every search and delete filters on
them. The collection is created automatically on first use.

---

## ⚙️ Configuration Reference

```env
# Qdrant server URL; leave unset to use embedded Qdrant
QDRANT_URL=
# API key for the server (needed for Qdrant Cloud)
QDRANT_API_KEY=
# Embedded mode's data folder, relative to the working directory
QDRANT_PATH=qdrant_data
# Collection holding all users' chunks
QDRANT_COLLECTION=user_documents
```

---

## 🖥️ Embedded Mode (default)

With `QDRANT_URL` unset, `qdrant-client` runs Qdrant inside the API process and persists it to
`QDRANT_PATH`. Notes:

- Only one process can open the folder at a time. Run a single Uvicorn worker, and don't open the
  folder from another script while the API is running.
- `qdrant_data/` is git-ignored and excluded from the Docker image.
- To start over, stop the API and delete the folder (document records in MongoDB will then point at
  missing chunks; delete them from the UI or the `documents` collection too).

---

## 🐳 Qdrant Server with Docker

`docker compose up --build` (repository root) starts a `qdrant/qdrant` container and points the API at
it; nothing else to configure.

To use a standalone Qdrant server with a locally run API:

```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant:v1.20.0
```

```env
QDRANT_URL=http://localhost:6333
```

On a server, the service also creates keyword payload indexes on `metadata.user_id` and
`metadata.doc_id` when it creates the collection.

---

## ☁️ Qdrant Cloud (optional)

### **Step 1: Create an Account**
1. Go to https://cloud.qdrant.io/
2. Sign up with GitHub, Google or email, and verify your email

### **Step 2: Create a Free Cluster**
1. Click **"Create cluster"**
2. Choose the **Free** tier
3. Name it (e.g. `adaptive-rag-dev`) and pick the region closest to you
4. Create it and wait a few minutes for provisioning

### **Step 3: Get an API Key**
1. Open the cluster's **API Keys** section and click **"Create API Key"**
2. Copy the key and the cluster URL, e.g. `https://your-cluster-id.us-east-1-0.aws.cloud.qdrant.io:6333`

**⚠️ IMPORTANT**: Store the key securely; it is shown only once.

### **Step 4: Configure the Service**

In `rag-service/.env`:

```env
QDRANT_URL=https://your-cluster-id.us-east-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=...
# optional, defaults to user_documents
QDRANT_COLLECTION=user_documents
```

Under Docker Compose, `QDRANT_URL` is overridden to the local `qdrant` container; to use Qdrant Cloud
there, change the `rag-api` service's `environment` in `docker-compose.yml`.

### **Step 5: Verify the Connection**

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="https://your-cluster-id...:6333", api_key="...")
print(client.get_collections())
```

Then restart the API, upload a document and ask about it. The `user_documents` collection appears in
the Qdrant Cloud dashboard after the first upload or question.

Free-tier limits change over time; check the current ones on the Qdrant Cloud pricing page.

---

## 🔧 Troubleshooting

#### **Storage folder is already accessed by another instance**
Embedded mode: another process (a second API worker, a script, a test) has `QDRANT_PATH` open. Stop it,
or switch to a Qdrant server.

#### **Errors after changing the embedding model**
The collection was created with the previous model's vector size, and the service refuses to use it
with a different one. Set a new `QDRANT_COLLECTION` (or delete the old collection) and upload the
documents again.

#### **401 / 403 from Qdrant Cloud**
Check `QDRANT_API_KEY`, and that the key belongs to this cluster and hasn't expired.

#### **Connection timeout**
Check `QDRANT_URL` (including `https://` and port `6333`) and your network.

#### **Upload returns 502 "Could not index the document"**
Storing the chunks failed; the API log has the underlying Qdrant or embedding error.

---

## 🔐 Security Best Practices

- Keep `QDRANT_API_KEY` in `.env`; never commit it
- Use separate clusters or collections for development and production
- Don't expose a self-hosted Qdrant server publicly without an API key (Docker Compose doesn't publish
  its port)

---

## 📚 Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Cloud](https://qdrant.tech/documentation/cloud/)
- [Local mode of the Python client](https://github.com/qdrant/qdrant-client#local-mode)
- [LangChain Qdrant integration](https://python.langchain.com/docs/integrations/vectorstores/qdrant)

---

## 🎯 Quick Checklist (Qdrant Cloud)

- [ ] Create an account at https://cloud.qdrant.io/
- [ ] Create a free cluster
- [ ] Create an API key, copy the cluster URL
- [ ] Set `QDRANT_URL` and `QDRANT_API_KEY` in `rag-service/.env`
- [ ] Restart the API
- [ ] Upload a document and ask about it
