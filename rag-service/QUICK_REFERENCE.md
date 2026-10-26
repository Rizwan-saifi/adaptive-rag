# Quick Reference Guide

A one-page cheat sheet: how to run things, then the coding standards from
[CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md) in short form.

## 🚀 Run

```bash
# From rag-service/
python -m uvicorn src.main:app --port 8000          # RAG API (docs at /docs)
python -m streamlit run streamlit_app/home.py       # UI on :8501

# From the repository root
docker compose up --build                           # whole stack
.\start-all.ps1                                     # Windows, local processes
```

## 🗺️ Where Things Are

| Need to change... | File |
|---|---|
| Endpoints | `src/api/routes.py` |
| Pipeline (nodes, routing) | `src/rag/graph_builder.py` |
| Prompts | `src/config/prompts.yaml` |
| Vector store (Qdrant) | `src/rag/retriever_setup.py` |
| Parsing / chunking | `src/rag/document_upload.py` |
| Conversations | `src/memory/chat_history_mongo.py` |
| Document records | `src/db/documents.py` |
| Models / providers | `src/llms/provider.py` |
| Settings (env vars) | `src/core/config.py` |
| UI | `streamlit_app/pages/chat.py`, `streamlit_app/utils/api_client.py` |

## 📌 At a Glance

### File Structure Template
```python
"""
Module description explaining the file's purpose.
"""

# Standard library
import logging
from typing import Optional

# Third-party
from pydantic import BaseModel

# Local
from src.core.config import settings

logger = logging.getLogger(__name__)


class MyModel(BaseModel):
    """Class description."""

    name: str
```

## 🎯 Key Standards

### Docstring Format
```python
def function(arg1: str, arg2: int = 10) -> dict:
    """
    One-line summary.

    Longer description when the summary isn't enough.

    Args:
        arg1: Description of arg1.
        arg2: Description of arg2. Defaults to 10.

    Returns:
        Dictionary containing results.

    Raises:
        ValueError: If arg1 is empty.
    """
```

## 📋 Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Functions | snake_case | `load_and_split()` |
| Variables | snake_case | `conversation_id` |
| Classes | PascalCase | `ChatHistory` |
| Constants | UPPER_CASE | `SUPPORTED_EXTENSIONS` |
| Private | _snake_case | `_get_store()` |

## 🔧 Import Order

1. **Standard library** (alphabetical)
2. **Third-party** (alphabetical)
3. **Local** (`src.`, alphabetical)

## ✨ Common Patterns

### Authenticated route
```python
@router.get("/documents")
async def list_documents(user_id: str = Depends(current_user)):
    """The user's uploaded documents, newest first."""
    return await documents.list_for_user(user_id)
```

### Blocking work from an async route
```python
chunks = await run_in_threadpool(load_and_split, filename, content)
```

### Graph node
```python
def retrieve(state: State):
    """Fetch the user's document chunks relevant to the question."""
    return {"documents": search(state["user_id"], state["question"])}
```

### Error Handling
```python
try:
    await run_in_threadpool(add_documents, user_id, doc_id, chunks)
except Exception:
    logger.exception("Storing document chunks failed")
    raise HTTPException(status_code=502, detail="Could not index the document, please try again.")
```

## 🚫 What NOT to Do

### ❌ Bad
```python
# Missing docstring and type hints, unscoped query
def get_data(q):
    x=collection.find(q)
    return x

# Commented code
# old_function()

# Blocking call inside an async route
result = rag_graph.invoke(inputs)
```

### ✅ Good
```python
async def get(user_id: str, doc_id: str) -> Optional[dict]:
    """One of the user's documents, or None if they have no such document."""
    return await collection.find_one({"user_id": user_id, "doc_id": doc_id}, {"_id": 0})

result = await run_in_threadpool(rag_graph.invoke, inputs)
```

## 🔍 Before Submitting

- [ ] Module, classes and functions have docstrings
- [ ] Imports are organized, none unused
- [ ] No commented-out code
- [ ] Type hints present
- [ ] Data is scoped to the authenticated user
- [ ] Prompts are in `prompts.yaml`, settings in `src/core/config.py`

## 🛠️ Optional Formatting Tools

Not installed by `requirements.txt`:

```bash
pip install black isort flake8
black src/ && isort src/ && flake8 src/
```

## 📚 Full Guides

- **[CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md)** - Complete style guide
- **[README.md](README.md)** - Service overview, API and configuration
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - All documentation
