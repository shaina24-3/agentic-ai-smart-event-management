import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List
from .retriever import retriever

# Llama Model Configuration
# Supports Groq (llama-3.1-8b-instant, llama-3.3-70b-versatile) or Ollama (http://localhost:11434)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def call_llama_api(system_prompt: str, user_prompt: str) -> str:
    """
    Calls a Llama model via Groq API or Ollama.
    Falls back gracefully if no key is configured.
    """
    # 1. Try Groq Llama API if GROQ_API_KEY is available
    if GROQ_API_KEY and not GROQ_API_KEY.startswith("your_"):
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": LLM_MODEL if "llama" in LLM_MODEL else "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[RAG Pipeline] Groq Llama API warning: {e}")

    # 2. Try Local Ollama Llama if running
    try:
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": "llama3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["message"]["content"].strip()
    except Exception:
        pass

    return ""

def answer_policy_question(query: str) -> Dict[str, Any]:
    """
    RAG Pipeline:
    1. Retrieves relevant policy chunks from knowledge base.
    2. Constructs grounded prompt with retrieved context.
    3. Calls Llama model to produce an accurate, policy-grounded answer.
    """
    matched_chunks = retriever.retrieve(query, top_k=2)
    
    if not matched_chunks:
        return {
            "answer": "I could not find a specific policy document covering this inquiry. Please contact an event administrator for further assistance.",
            "source_documents": [],
            "grounded": False
        }

    context_str = "\n\n".join([f"[{c['doc_title']}]:\n{c['text']}" for c in matched_chunks])
    sources = list(set([c["doc_title"] for c in matched_chunks]))

    system_prompt = (
        "You are an AI Smart Event Management Policy Assistant powered by Llama.\n"
        "Answer the user's question accurately using ONLY the provided official policy context.\n"
        "If the context specifies cancellation deadlines, venue rules, or safety caps, cite them clearly.\n"
        "Do not invent facts not supported by the context."
    )

    user_prompt = f"Context:\n{context_str}\n\nUser Question: {query}\n\nAnswer concisely and professionally:"

    # Call Llama
    llama_response = call_llama_api(system_prompt, user_prompt)

    if llama_response:
        final_answer = llama_response
    else:
        # High quality grounded synthesis fallback from the matched policy
        top_chunk = matched_chunks[0]
        final_answer = (
            f"Based on official {top_chunk['doc_title']}:\n"
            f"{top_chunk['text']}"
        )

    return {
        "answer": final_answer,
        "source_documents": sources,
        "grounded": True,
        "context_used": context_str
    }
