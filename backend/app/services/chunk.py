import re

def split_into_chunks(text: str, max_chars: int = 1200, overlap: int = 150):
    """
    Split text into overlapping chunks with sentence boundary awareness
    """
    if not text or not text.strip():
        return []
    
    # Clean up text
    text = re.sub(r'\s+', ' ', text).strip()
    
    chunks = []
    i = 0
    
    while i < len(text):
        end = min(len(text), i + max_chars)
        
        # Try to break at sentence boundary if not at end
        if end < len(text):
            # Look for sentence endings within last 200 chars
            search_start = max(i, end - 200)
            last_period = text.rfind('.', search_start, end)
            last_question = text.rfind('?', search_start, end)
            last_exclaim = text.rfind('!', search_start, end)
            
            boundary = max(last_period, last_question, last_exclaim)
            if boundary > i:
                end = boundary + 1
        
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move forward with overlap
        if end >= len(text):
            break
        i = end - overlap
    
    return chunks