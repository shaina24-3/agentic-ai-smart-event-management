import os
from typing import List, Dict

DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "documents")

def load_documents(directory: str = DOCUMENTS_DIR) -> List[Dict[str, str]]:
    """
    Scans the documents directory and loads all markdown/text policy documents.
    Returns a list of dicts with 'title', 'content', and 'file_path'.
    """
    documents = []
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return documents

    for filename in os.listdir(directory):
        if filename.endswith(".md") or filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    title = filename.replace("_", " ").replace(".md", "").replace(".txt", "").title()
                    documents.append({
                        "title": title,
                        "file_name": filename,
                        "file_path": file_path,
                        "content": content
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    return documents
