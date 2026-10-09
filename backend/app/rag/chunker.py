from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> List[str]:
    """
    Splits text into meaningful policy sections, ensuring headings are
    never orphaned from their descriptive policy content.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If current chunk is very short (e.g. just a heading), always append
        if len(current_chunk) < 150:
            current_chunk = (current_chunk + "\n\n" + para) if current_chunk else para
        elif len(current_chunk) + len(para) <= chunk_size:
            current_chunk += "\n\n" + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

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
