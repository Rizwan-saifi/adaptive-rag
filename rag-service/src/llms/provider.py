"""
Provider-agnostic chat model and embeddings, selected via environment variables.

    LLM_PROVIDER        groq | openai | gemini | anthropic   (default: groq)
    LLM_MODEL           model name for that provider         (default: per provider)
    EMBEDDING_PROVIDER  local | openai | gemini              (default: local)
    EMBEDDING_MODEL     model name for that provider         (default: per provider)

Each provider reads its own API key from the environment:
GROQ_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY.
"""

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()

DEFAULT_LLM_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-opus-5-5",
}

DEFAULT_EMBEDDING_MODELS = {
    "local": "BAAI/bge-small-en-v1.5",
    "openai": "text-embedding-3-small",
    "gemini": "models/gemini-embedding-001",
}


def _text_only(message: AIMessage) -> AIMessage:
    """Collapse list-style content (e.g. thinking + text blocks) into plain text."""
    # Tool-call turns are sent back to the model, which needs their thinking blocks intact.
    if isinstance(message.content, str) or message.tool_calls:
        return message
    text = "".join(
        block if isinstance(block, str) else block.get("text", "")
        for block in message.content
        if isinstance(block, str) or block.get("type") == "text"
    )
    return message.model_copy(update={"content": text})


def _build_llm():
    model = os.getenv("LLM_MODEL") or DEFAULT_LLM_MODELS.get(LLM_PROVIDER)

    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=0)

    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model)

    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, temperature=0)

    if LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic

        class TextChatAnthropic(ChatAnthropic):
            """Claude responses include thinking blocks; the app expects plain-text content."""

            def _generate(self, *args, **kwargs) -> ChatResult:
                result = super()._generate(*args, **kwargs)
                result.generations = [
                    ChatGeneration(message=_text_only(g.message), generation_info=g.generation_info)
                    for g in result.generations
                ]
                return result

        return TextChatAnthropic(model=model, max_tokens=16000)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use one of: {', '.join(DEFAULT_LLM_MODELS)}"
    )


def _build_embeddings():
    model = os.getenv("EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODELS.get(EMBEDDING_PROVIDER)

    if EMBEDDING_PROVIDER == "local":
        from langchain_community.embeddings import FastEmbedEmbeddings
        return FastEmbedEmbeddings(model_name=model)

    if EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=model)

    if EMBEDDING_PROVIDER == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=model)

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER '{EMBEDDING_PROVIDER}'. "
        f"Use one of: {', '.join(DEFAULT_EMBEDDING_MODELS)}"
    )


llm = _build_llm()
embeddings = _build_embeddings()


def structured_llm(schema):
    """
    Return a runnable that produces an instance of the given Pydantic schema.

    Most providers use native structured output. Current Claude models reject the
    forced tool call that langchain-anthropic uses for this, so for Anthropic we
    ask for JSON in the prompt and parse it instead.
    """
    if LLM_PROVIDER != "anthropic":
        return llm.with_structured_output(schema)

    parser = PydanticOutputParser(pydantic_object=schema)
    instructions = HumanMessage(content=parser.get_format_instructions() + "\nReturn only the JSON.")

    def add_instructions(prompt_value):
        return prompt_value.to_messages() + [instructions]

    return RunnableLambda(add_instructions) | llm | parser
