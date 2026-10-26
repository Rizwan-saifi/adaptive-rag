"""
Document loading and chunking.
"""

import os
import tempfile

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

SUPPORTED_EXTENSIONS = (".pdf", ".txt")


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
    extension = os.path.splitext(filename)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only PDF and TXT files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        if extension == ".pdf":
            docs = PyPDFLoader(tmp_path).load()
        else:
            docs = TextLoader(tmp_path, encoding="utf-8").load()
    except Exception as e:
        raise ValueError(f"Could not read the file: {e}") from e
    finally:
        os.unlink(tmp_path)

    # Record the real file name rather than the temp path, for source attribution
    for doc in docs:
        doc.metadata["source"] = filename

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(docs)
