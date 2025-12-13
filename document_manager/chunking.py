import re

SENTENCE_SPLIT_RE = re.compile(r'(?<=[\.\?\!])\s+')

def _split_into_sentences(text: str) -> list[str]:
    """
    Very small heuristic sentence splitter:
    splits on punctuation followed by whitespace.
    Keeps abbreviations and edge cases imperfect, but works well enough for chunking.
    """
    text = text.strip()
    if not text:
        return []
    sentences = SENTENCE_SPLIT_RE.split(text)
    # Remove empty sentences and strip whitespace
    return [s.strip() for s in sentences if s.strip()]

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> list[dict]:
    """
    Break `text` into chunks approximating `max_chars` characters each.
    Uses sentence boundaries when possible to avoid chopping sentences in half.
    Returns a list of dicts with:
        {
            "index": int,
            "text": str,
            "start": int,   # character start offset in original text
            "end": int      # character end offset (exclusive)
        }

    Parameters:
    - text: full document text
    - max_chars: target maximum characters per chunk (default 1200)
    - overlap: number of characters to overlap between consecutive chunks (default 200).
               If overlap >= max_chars/2 it will be reduced automatically.

    Notes:
    - If a single sentence is longer than max_chars it will be cut forcibly.
    - This is character-based chunking; for token-accurate chunking use a tokenizer (e.g., tiktoken).
    """
    if text is None:
        return []

    text = text.strip()
    if not text:
        return []

    # sanitize overlap
    if overlap < 0:
        overlap = 0
    if overlap >= max_chars // 2:
        # keep some overlap but not too big
        overlap = max(0, max_chars // 4)

    sentences = _split_into_sentences(text)

    chunks = []
    current_chunk = []
    current_len = 0
    current_start = None  # will be set to char offset of first sentence in current_chunk

    # helper to push a chunk to chunks list
    def push_chunk(start_idx: int, chunk_text_str: str):
        idx = len(chunks)
        end_idx = start_idx + len(chunk_text_str)
        chunks.append({"index": idx, "text": chunk_text_str, "start": start_idx, "end": end_idx})

    # Precompute sentence start offsets to map back to character positions
    offsets = []
    pos = 0
    for s in sentences:
        # find the next occurrence of the sentence from pos
        # use find to avoid accidental mismatches
        found = text.find(s, pos)
        if found == -1:
            # fallback: use pos (should rarely happen)
            found = pos
        offsets.append(found)
        pos = found + len(s)

    for i, (sent, sent_start) in enumerate(zip(sentences, offsets)):
        sent_len = len(sent)

        if current_start is None:
            current_start = sent_start

        # if adding this sentence would not exceed max_chars, append it
        if current_len + sent_len <= max_chars:
            current_chunk.append(sent)
            current_len += sent_len + 1  # +1 for a space/newline when joined
        else:
            # if current_chunk is empty, the sentence itself is longer than max_chars
            # force-split the long sentence into smaller pieces
            if not current_chunk:
                s_pos = 0
                while s_pos < sent_len:
                    part = sent[s_pos: s_pos + max_chars]
                    part_start = sent_start + s_pos
                    push_chunk(part_start, part)
                    s_pos += max_chars - overlap  # advance by chunk minus overlap
                current_start = None
                current_chunk = []
                current_len = 0
            else:
                # push the current chunk
                chunk_str = " ".join(current_chunk).strip()
                push_chunk(current_start, chunk_str)

                # compute new start: we want overlap characters from the end of the chunk
                # find overlap start position in original text
                overlap_start_pos = max(current_start, current_start + max(0, len(chunk_str) - overlap))

                # prepare next chunk starting with overlap tail if any
                # find substring of original text that corresponds to overlap_start_pos..end
                tail = text[overlap_start_pos: current_start + len(chunk_str)]
                # reset and if tail non-empty include it as the first piece of the next chunk
                current_chunk = []
                if tail.strip():
                    current_chunk.append(tail.strip())
                    current_len = len(tail)
                    current_start = overlap_start_pos
                else:
                    current_len = 0
                    current_start = None

                # now re-process the current sentence in the next round:
                if current_len + sent_len <= max_chars:
                    if current_start is None:
                        current_start = sent_start
                    current_chunk.append(sent)
                    current_len += sent_len + 1
                else:
                    # sentence still too big, force-split (similar to above)
                    s_pos = 0
                    while s_pos < sent_len:
                        part = sent[s_pos: s_pos + max_chars]
                        part_start = sent_start + s_pos
                        push_chunk(part_start, part)
                        s_pos += max_chars - overlap
                    current_start = None
                    current_chunk = []
                    current_len = 0

    # push any remaining chunk
    if current_chunk:
        chunk_str = " ".join(current_chunk).strip()
        push_chunk(current_start if current_start is not None else 0, chunk_str)

    # final sanity: if no chunks were generated (edge cases), make a single chunk with full text
    if not chunks and text:
        chunks.append({"index": 0, "text": text, "start": 0, "end": len(text)})

    return chunks