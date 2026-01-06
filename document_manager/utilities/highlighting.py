import re
from django.utils.html import escape
from django.utils.safestring import mark_safe

def highlight_text(text: str, query: str, max_length: int = 400,):
    """
        Highlight query terms inside text and return a short snippet.
    """

    if not text or not query:
        snippet = text[:max_length]
        return {
            "html": escape(snippet),
            "truncated": len(text) > max_length,
        }
    
    # Normalize query terms
    terms = [re.escape(t.lower()) for t in query.split() if len(t) > 2 ]

    if not terms:
        snippet = text[:max_length]
        return {
            "html": escape(snippet),
            "truncated": len(text) > max_length,
        }
    
    pattern = re.compile(rf"({'|'.join(terms)})", re.IGNORECASE)

    match = pattern.search(text)
    if match:
        start = max(match.start() - max_length // 2, 0)
    else:
        start = 0

    end = start + max_length
    snippet = text[start:end]
    truncated = end < len(text)

    escaped = escape(snippet)
    highlighted = pattern.sub(r"<mark>\1</mark>", escaped)

    return {
        "html": mark_safe(highlighted),
        "truncated": truncated,
    }


