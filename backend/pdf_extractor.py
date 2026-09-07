import os
from typing import List, Dict, Any, Optional

def extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text and page numbers from a PDF file.
    Returns a list of dicts: [{'page_number': 1, 'text': '...', 'char_count': 123}]
    """
    pages = []
    
    # Try PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text()
            pages.append({
                "page_number": page_idx + 1,
                "text": text.strip(),
                "char_count": len(text)
            })
        doc.close()
        return pages
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: PyMuPDF error: {e}")

    # Fallback: pypdf if available
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({
                "page_number": idx + 1,
                "text": text.strip(),
                "char_count": len(text)
            })
        return pages
    except Exception as e:
        print(f"Warning: pypdf error: {e}")

    return pages

def find_evidence_snippet(pages: List[Dict[str, Any]], query_phrase: str, window_chars: int = 250) -> Optional[Dict[str, Any]]:
    """
    Finds the exact occurrence of query_phrase in extracted pages and returns
    the snippet with surrounding context and the page number.
    """
    lower_query = query_phrase.lower().strip()
    for p in pages:
        lower_text = p["text"].lower()
        if lower_query in lower_text:
            pos = lower_text.find(lower_query)
            start = max(0, pos - window_chars)
            end = min(len(p["text"]), pos + len(query_phrase) + window_chars)
            snippet = p["text"][start:end].replace("\n", " ").strip()
            return {
                "page_number": p["page_number"],
                "snippet": f"...{snippet}...",
                "exact_match": True
            }
    return None