def split_into_chunks(text: str, max_chars: int = 1200, overlap: int = 150):
    chunks = []
    i = 0
    while i < len(text):
        end = min(len(text), i + max_chars)
        chunks.append(text[i:end].strip())
        i = end - overlap
        if i < 0: i = 0
    return [c for c in chunks if c]
