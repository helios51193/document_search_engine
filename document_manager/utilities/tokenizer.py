import tiktoken
from django.conf import settings

def count_tokens(text: str) -> int:
    """
    Count tokens for OpenAI-compatible models.
    """
    encoding = tiktoken.encoding_for_model(settings.OPENAI_EMBEDDING_MODEL)
    return len(encoding.encode(text))