import re
from typing import List, Dict

class DocumentChunker:
    @staticmethod
    def chunk_document(doc: Dict[str, str], max_chunk_size: int = 500) -> List[Dict[str, str]]:
        chunks = []
        content = doc["content"]
        source = doc["source"]
        
        doc_title = ""
        sections = re.split(r'\n(?=#{1,3}\s)', content)
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if section.startswith("# ") and len(section.splitlines()) == 1:
                doc_title = section
                continue
            
            full_text = f"{doc_title}\n{section}".strip() if doc_title else section
            if len(full_text) <= max_chunk_size:
                chunks.append({"source": source, "chunk": full_text})
            else:
                words = full_text.split()
                start = 0
                step = 80
                while start < len(words):
                    end = min(start + step, len(words))
                    chunks.append({"source": source, "chunk": " ".join(words[start:end])})
                    if end == len(words):
                        break
                    start += 65
        return chunks
