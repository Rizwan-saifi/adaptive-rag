# Adaptive RAG - Code Style Guide

## Overview
This document provides guidelines for maintaining consistent code quality and style across the RAG
service (`src/`, `streamlit_app/`). The existing code is the best example; when in doubt,
match the file you are editing.

## General Guidelines

### File Structure
Every Python file should follow this structure:
```python
"""
Module docstring describing the file's purpose.
"""

# Standard library imports
import logging
from datetime import datetime, timezone

# Third-party imports
from fastapi import APIRouter, Depends

# Local imports
from src.core.auth import current_user
from src.core.config import settings
```

### Docstring Format
Functions, classes, and modules have docstrings in Google format. Short helpers can use a one-line
docstring; add `Args`/`Returns`/`Raises` when they say something the signature doesn't.

```python
def load_and_split(filename: str, content: bytes) -> list[Document]:
    """
    Parse an uploaded PDF or TXT file and split it into chunks.

    Args:
        filename: Original file name; its extension selects the parser.
        content: The file's bytes.

    Returns:
        The document's chunks, with the file name as their source.

    Raises:
        ValueError: If the file type is unsupported or the file can't be parsed.
    """
```

### Class Documentation
```python
class ChatHistory:
    """Messages of one of a user's conversations, stored in MongoDB."""

    def __init__(self, user_id: str, conversation_id: str):
        """
        Args:
            user_id: Owner of the conversation.
            conversation_id: Identifies the conversation among the user's ones.
        """
```

## Naming Conventions

### Variables and Functions
- Use `snake_case` for variables and functions
- Use descriptive names (avoid single letters except for loop counters)
- Prefix module-private helpers and state with an underscore (`_get_store()`, `_store`)

```python
# Good
history = ChatHistory(user_id, conversation_id)
def condense_question(state: State):
    ...

# Avoid
h = ChatHistory(u, c)
def process(s):
    ...
```

### Constants
- Use `UPPER_CASE` for constants
- Settings that users may change belong in `src/core/config.py` (read from the environment), not in
  module constants

```python
SUPPORTED_EXTENSIONS = (".pdf", ".txt")
ANSWER_NODES = {"generate", "general_llm"}
MODEL_ERROR = "The model call failed, please try again."
```

### Classes
- Use `PascalCase` for class names
- Use descriptive names that indicate the class purpose

```python
class ChatHistory:
    ...

class RouteIdentifier(BaseModel):
    ...
```

## Code Organization

### Import Order
Follow this order, with a blank line between groups:
1. Future imports
2. Standard library imports (alphabetical)
3. Third-party imports (alphabetical)
4. Local application imports (`src.` / `utils.`, alphabetical)

### Spacing
- Two blank lines between top-level functions and classes
- One blank line between methods in a class
- Blank lines to separate logical groups within functions

## Type Hints
Use type hints for function parameters and return types. Built-in generics (`list[str]`) and
`X | None` are fine; the code targets Python 3.13.

```python
def search(user_id: str, query: str) -> list[Document]:
    """The user's chunks most similar to the query."""

async def get(user_id: str, doc_id: str) -> Optional[dict]:
    """One of the user's documents, or None if they have no such document."""
```

## Error Handling

### Raise plain exceptions in library code, translate them at the API boundary
Lower layers raise standard exceptions with user-readable messages; routes turn them into HTTP errors.

```python
# src/rag/document_upload.py
if extension not in SUPPORTED_EXTENSIONS:
    raise ValueError("Only PDF and TXT files are supported")

# src/api/routes.py
try:
    chunks = await run_in_threadpool(load_and_split, filename, content)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### Exception Handling
Catch specific exceptions where you can. Where any failure of an external call (model, vector store,
web search) must be handled, catch `Exception`, log it with `logger.exception`, and return a clear
error; never swallow it silently.

```python
# Good
try:
    result = await run_in_threadpool(rag_graph.invoke, inputs)
except Exception:
    logger.exception("RAG pipeline failed")
    raise HTTPException(status_code=502, detail=MODEL_ERROR)

# Avoid
try:
    docs = loader.load()
except Exception:
    pass
```

## Logging
Use the standard logging module with a module-level logger and `%`-style arguments (formatted only if
the message is logged):

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Retrieved %d chunks", len(documents))
logger.warning("Web search failed: %s", response["error"])
logger.exception("Storing document chunks failed")   # inside except: includes the traceback
```

Logging is configured once, in `src/main.py`. Don't log secrets or JWTs.

## Async Code
FastAPI routes and MongoDB access (Motor) are async. Model calls, the LangGraph graph, document
parsing and Qdrant calls are blocking, so run them off the event loop:

```python
result = await run_in_threadpool(rag_graph.invoke, inputs)
async for mode, data in iterate_in_threadpool(stream):
    ...
```

## Comment Guidelines

### Good Comments
- Explain WHY, not WHAT
- Provide context and reasoning
- Document non-obvious workarounds

```python
# Embedded Qdrant isn't safe for concurrent use; a Qdrant server is.
_ops_lock = contextlib.nullcontext() if settings.QDRANT_URL else threading.Lock()
```

### Bad Comments
- Redundant comments
- Outdated comments
- Comments that restate code

```python
# Bad: restates the code
count = count + 1  # Increment count

# Good: explains a decision
# Saved only once answered, so failures don't leave an unanswered question in the history.
```

## Code Complexity
- Keep functions focused and concise (< 30 lines when possible)
- Extract complex logic into helper functions
- Use meaningful variable names to reduce need for comments

## Performance Considerations

### Async Operations
Use async for database I/O, and keep blocking work off the event loop (see Async Code).

### Caching
Build expensive clients once:

```python
from functools import cache

@cache
def get_embeddings():
    """The configured embeddings model, built on first use."""
```

The Qdrant store is likewise created lazily on first use (`_get_store()` in `src/rag/retriever_setup.py`).

## Code Review Checklist
Before submitting code:
- ✓ Functions, classes and modules have docstrings
- ✓ Type hints present for parameters and returns
- ✓ Follows naming conventions
- ✓ Configurable values come from `settings`, not hardcoded
- ✓ Proper error handling and logging
- ✓ No unused imports or variables
- ✓ No commented-out code
- ✓ PEP 8 compliant

## Tools and Automation

Formatters and linters are not part of `requirements.txt`; if you use them, install them separately:

```bash
pip install black isort flake8
black src/ streamlit_app/
isort src/ streamlit_app/
flake8 src/
```

## Project-Specific Guidelines

### RAG Pipeline
- Prompts live in `src/config/prompts.yaml`, not in code
- Graph nodes take the `State` and return a dict with only the keys they change
- Nodes whose output is shown to the user must be listed in `ANSWER_NODES` so they are streamed
- Use `structured_llm(...)` for structured output and `message_text(...)` to read message content;
  both handle provider differences
- Every vector store operation filters on the user's `user_id`

### Streamlit Applications
- Keep backend calls in `streamlit_app/utils/api_client.py`; pages call its functions
- Raise `ApiError` with a user-readable message; `SessionExpired` sends the user back to login
- Use session state consistently (`jwt_token`, `conversation_id`, `chat_history`)

### API Routes
- Protect every route with `user_id: str = Depends(current_user)` and scope all data to that user
- Validate input with Pydantic models / `Form(...)` constraints
- Use proper HTTP status codes (400 bad input, 401 auth, 404 not found, 413 too large, 502 upstream failure)

## Version Control
- Use descriptive commit messages
- One logical change per commit
- Format: `<type>: <description>`
  - `feat: add new feature`
  - `fix: resolve bug`
  - `refactor: reorganize code`
  - `docs: update documentation`
  - `style: formatting changes`
