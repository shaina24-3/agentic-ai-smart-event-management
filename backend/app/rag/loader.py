import os
from typing import List, Dict

class DocumentLoader:
    @staticmethod
    def load_documents_from_dir(directory_path: str) -> List[Dict[str, str]]:
        documents = []
        if not os.path.exists(directory_path):
            return documents
        
        for filename in os.listdir(directory_path):
            if filename.endswith(".md") or filename.endswith(".txt"):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8-sig") as f:
                        documents.append({
                            "source": filename,
                            "path": file_path,
                            "content": f.read()
                        })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        return documents
