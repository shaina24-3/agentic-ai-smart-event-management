from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Splits text into chunks preserving sentence/paragraph boundaries when possible.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue
        
        if len(current_chunk) + len(cleaned_para) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + cleaned_para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = cleaned_para

    if current_chunk:
        chunks.append(current_chunk)

    # Fallback if any single chunk is still overly large
    final_chunks = []
    for c in chunks:
        if len(c) > chunk_size * 2:
            words = c.split()
            for i in range(0, len(words), 80):
                final_chunks.append(" ".join(words[i:i + 80]))
        else:
            final_chunks.append(c)

    return final_chunks

def create_chunks_from_documents(documents: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """
    Takes loaded documents and returns chunk objects with metadata.
    """
    all_chunks = []
    chunk_id = 1
    for doc in documents:
        text_chunks = chunk_text(doc["content"])
        for index, text in enumerate(text_chunks):
            all_chunks.append({
                "chunk_id": chunk_id,
                "doc_title": doc["title"],
                "file_name": doc["file_name"],
                "chunk_index": index,
                "text": text
            })
            chunk_id += 1
    return all_chunks
