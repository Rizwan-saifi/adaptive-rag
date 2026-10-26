# 📑 Documentation Index

## 🎯 Start Here

**New to this codebase?** Read these in order:

1. **[../README.md](../README.md)** - Whole platform: architecture, Docker and Windows quick start
2. **[README.md](README.md)** - RAG service: pipeline, API, configuration
3. **[../auth-gateway/README.md](../auth-gateway/README.md)** - Signup, login and JWTs
4. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Where things are, and coding patterns

---

## 📚 All Documentation Files

| File | Purpose |
|------|---------|
| [../README.md](../README.md) | Platform overview and quick start |
| [../auth-gateway/README.md](../auth-gateway/README.md) | Auth gateway endpoints and configuration |
| [README.md](README.md) | RAG service overview, graph, API, configuration, deployment |
| [DOCUMENT_UPLOAD_FLOW.md](DOCUMENT_UPLOAD_FLOW.md) | How documents are uploaded, stored, retrieved and deleted |
| [DOCUMENT_FLOW_VISUAL.md](DOCUMENT_FLOW_VISUAL.md) | The same flows as diagrams |
| [QDRANT_SETUP_GUIDE.md](QDRANT_SETUP_GUIDE.md) | Embedded Qdrant, Qdrant server, optional Qdrant Cloud |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Commands, file map, coding patterns |
| [CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md) | Complete coding standards |
| DOCUMENTATION_INDEX.md | This file |

---

## 🔍 Quick Lookup

### "How do I run everything?"
→ **[../README.md](../README.md)** → "Quick start with Docker" / "Quick start (Windows, without Docker)"

### "How does a question get answered?"
→ **[README.md](README.md)** → "Architecture"
→ **[DOCUMENT_FLOW_VISUAL.md](DOCUMENT_FLOW_VISUAL.md)** → "Scenario 2: User Asks a Question"

### "What endpoints are there and what do they return?"
→ **[README.md](README.md)** → "API Endpoints"
→ **[../auth-gateway/README.md](../auth-gateway/README.md)** → "Endpoints"

### "Which environment variables can I set?"
→ **[README.md](README.md)** → "Environment Configuration"
→ **[../auth-gateway/README.md](../auth-gateway/README.md)** → "Configuration"

### "Where are my documents stored, and do they persist?"
→ **[DOCUMENT_UPLOAD_FLOW.md](DOCUMENT_UPLOAD_FLOW.md)** → "Where Things Live"
→ **[QDRANT_SETUP_GUIDE.md](QDRANT_SETUP_GUIDE.md)** → "Overview"

### "How do I use Qdrant Cloud?"
→ **[QDRANT_SETUP_GUIDE.md](QDRANT_SETUP_GUIDE.md)** → "Qdrant Cloud (optional)"

### "How should I write docstrings, names, imports?"
→ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** → "Key Standards", "Naming Conventions", "Import Order"
→ **[CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md)** → "General Guidelines", "Naming Conventions", "Code Organization"

### "What should I check before committing?"
→ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** → "Before Submitting"
→ **[CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md)** → "Code Review Checklist"

---

## 📂 Project Structure

```
Adaptive RAG/
├── README.md                      # Platform overview
├── docker-compose.yml             # mongo, qdrant, rag-api, auth-gateway, streamlit
├── start-all.ps1                  # Windows: start API, gateway and UI locally
├── auth-gateway/                  # NestJS signup/login + /api/chat proxy
│   ├── README.md
│   └── src/
└── rag-service/
    ├── README.md
    ├── DOCUMENTATION_INDEX.md     # This file
    ├── DOCUMENT_UPLOAD_FLOW.md
    ├── DOCUMENT_FLOW_VISUAL.md
    ├── QDRANT_SETUP_GUIDE.md
    ├── QUICK_REFERENCE.md
    ├── CODE_STYLE_GUIDE.md
    ├── src/                       # FastAPI app and RAG pipeline
    └── streamlit_app/             # UI
```

See [README.md](README.md) → "Project Structure" for the files inside `src/`.

Note: `adaptive_RAG.png` (in `rag-service/` and `src/rag/`) shows an older version of the graph. The
current graph is the Mermaid diagram in [README.md](README.md).

---

## 🎓 Learning Path

### Using the app
1. **[../README.md](../README.md)** - Start the stack
2. **[README.md](README.md)** → "Example Usage"

### Changing the code
1. **[README.md](README.md)** → "Architecture" and "Project Structure"
2. **[DOCUMENT_UPLOAD_FLOW.md](DOCUMENT_UPLOAD_FLOW.md)** - The document path in detail
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Patterns to follow
4. **[CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md)** - When in doubt

### Deploying
1. **[README.md](README.md)** → "Deployment" and "Security Considerations"
2. **[QDRANT_SETUP_GUIDE.md](QDRANT_SETUP_GUIDE.md)** - Choosing a Qdrant mode
