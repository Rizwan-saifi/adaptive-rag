# Document Upload Flow - How Documents Are Stored and Used

This explains what happens to a document from upload to answer, and how it is deleted.
For diagrams of the same flows see [DOCUMENT_FLOW_VISUAL.md](DOCUMENT_FLOW_VISUAL.md).

---

## 📊 Where Things Live

| What | Where | Code |
|---|---|---|
| Document chunks + embeddings | Qdrant, collection `QDRANT_COLLECTION` (default `user_documents`), shared by all users | `src/rag/retriever_setup.py` |
| Document records (name, description, chunk count) | MongoDB, `documents` collection | `src/db/documents.py` |
| Parsing and chunking | in memory, during the upload request | `src/rag/document_upload.py` |

Qdrant is embedded (data in `QDRANT_PATH`, default `qdrant_data`) unless `QDRANT_URL` points at a
Qdrant server; Docker Compose runs one. Either way documents survive restarts.

---

### **Step 1: Startup**

Nothing is loaded at startup. The Qdrant connection is opened on first use (the first upload, question
or delete). If the collection doesn't exist yet it is created, with the vector size of the configured
embedding model and cosine distance; on a Qdrant server, keyword payload indexes on
`metadata.user_id` and `metadata.doc_id` are created too.

---

### **Step 2: User Uploads a Document**

```
POST /rag/documents/upload
Authorization: Bearer <jwt>
Content-Type: multipart/form-data

file=<PDF or TXT>
description=My document description
```

What happens in `src/api/routes.py` (`upload_file`):

1. **Authenticate**: the JWT's subject becomes the document's `user_id` (401 if the token is missing or invalid).
2. **Check size**: at most `MAX_UPLOAD_MB` (default 10) is read; larger files get a 413.
3. **Load and split** (`load_and_split` in `src/rag/document_upload.py`):
   ```python
   extension = os.path.splitext(filename)[1].lower()
   if extension not in (".pdf", ".txt"):
       raise ValueError("Only PDF and TXT files are supported")    # -> 400
   ...
   docs = PyPDFLoader(tmp_path).load()        # or TextLoader(tmp_path, encoding="utf-8")
   for doc in docs:
       doc.metadata["source"] = filename      # real file name, used to cite sources
   splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
   return splitter.split_documents(docs)
   ```
   Unreadable files, or files with no text, get a 400.
4. **Store the chunks** (`add_documents` in `src/rag/retriever_setup.py`): a new `doc_id` is generated,
   every chunk is tagged with `user_id` and `doc_id`, embedded, and added to the collection.
   If this fails the response is a 502 and no record is saved.
5. **Record the document** in MongoDB and return it:
   ```json
   {"status": true, "document": {"doc_id": "9a1b...", "user_id": "alice", "filename": "guide.pdf",
    "description": "My document description", "chunks": 20, "uploaded_at": "..."}}
   ```

The description is required (1–300 characters) and is only stored and shown in the UI; it doesn't
affect retrieval or routing.

---

### **Step 3: Answering a Question**

```
POST /rag/query            (or /rag/query/stream)
Authorization: Bearer <jwt>
{"query": "Tell me about the uploaded document", "conversation_id": "3f2c..."}
```

The graph in `src/rag/graph_builder.py`:

1. **condense_question**: turns a follow-up into a standalone question, using the conversation history.
2. **retrieve**: `search(user_id, question)` returns the `RETRIEVAL_K` (default 4) most similar chunks,
   filtered on `metadata.user_id`, so a user only ever sees their own documents.
3. **classify**: the model sees the question and the chunks (each labelled `[source: file, page N]`)
   and chooses `index` if they answer it, otherwise `general` or `search`. With no chunks, `index` is
   never chosen.
4. **generate**: for `index`, answers from the chunks and cites the sources. Other routes answer from
   general knowledge or web results instead.

---

### **Step 4: Listing and Deleting**

- `GET /rag/documents` lists the user's records, newest first.
- `DELETE /rag/documents/{doc_id}` checks that the user owns the document (404 otherwise), deletes all
  its chunks from Qdrant (filtered on `user_id` and `doc_id`), then deletes the record.

---

## 🔄 Document Lifecycle

```
Upload (file + description)
  ↓
Parse PDF/TXT → split into chunks (1000 chars, 150 overlap)
  ↓
Tag chunks with user_id + doc_id → embed → store in Qdrant
  ↓
Save record in MongoDB
  ↓
Questions from the same user retrieve matching chunks
  ↓
Delete → chunks removed from Qdrant, record removed from MongoDB
```

---

## ❓ FAQ

**Q: Can I upload multiple documents?**
A: Yes. Each upload adds chunks to the same collection; all of a user's documents are searched together.

**Q: Can other users see my documents?**
A: No. Every search and delete filters on the `user_id` from the JWT.

**Q: Do documents persist after restart?**
A: Yes, in Qdrant (embedded on disk or a server) plus the MongoDB record.

**Q: What's the maximum document size?**
A: `MAX_UPLOAD_MB` (default 10 MB).

**Q: Which file types are supported?**
A: `.pdf` and `.txt` (UTF-8). Scanned PDFs without a text layer produce no text and are rejected.

**Q: What if I change the embedding model?**
A: The existing collection has the old vector size and the service will refuse to use it. Point
`QDRANT_COLLECTION` at a new collection (or delete the old one) and upload the documents again.

---

## 💡 How to Test

Get a JWT from the auth gateway first (see the [RAG service README](README.md#5-example-usage)), then:

```bash
# Upload
curl -X POST http://localhost:8000/rag/documents/upload \
  -H "Authorization: Bearer $JWT" \
  -F "file=@python_guide.pdf" \
  -F "description=Python Programming Guide"

# Ask
curl -X POST http://localhost:8000/rag/query \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "conversation_id": "test-1"}'

# List and delete
curl -H "Authorization: Bearer $JWT" http://localhost:8000/rag/documents
curl -X DELETE -H "Authorization: Bearer $JWT" http://localhost:8000/rag/documents/<doc_id>
```
