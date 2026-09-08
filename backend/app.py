import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import UPLOAD_DIR, BASE_DIR, GEMINI_API_KEY, GEMINI_MODEL
import backend.config as config
from backend.database import (
    init_db, get_stats, get_all_documents, get_all_facts, get_fact_by_id,
    get_all_relationships, get_dynamic_showcase_cases, insert_document, insert_fact,
    insert_relationship
)
from backend.seed_data import populate_seed_data
from backend.pdf_extractor import extract_pdf_pages
from backend.fact_extractor import extract_facts_from_page
from backend.reconciler import analyze_fact_pair

app = FastAPI(
    title="Fact Knowledge Layer API",
    description="AI-powered Fact Extraction, Grounding, and Cross-Document Reconciliation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    stats = get_stats()
    if stats["documents"] == 0:
        print("Seeding initial starter dataset...")
        populate_seed_data()

# ----------------- REST ENDPOINTS -----------------

@app.get("/api/stats")
def api_stats():
    return get_stats()

@app.get("/api/documents")
def api_documents():
    return get_all_documents()

@app.get("/api/facts")
def api_facts(doc: Optional[str] = None, category: Optional[str] = None, q: Optional[str] = None):
    return get_all_facts(doc_name=doc, category=category, query=q)

@app.get("/api/facts/{fact_id}")
def api_fact_detail(fact_id: str):
    f = get_fact_by_id(fact_id)
    if not f:
        raise HTTPException(status_code=404, detail="Fact not found")
    return f

@app.get("/api/relationships")
def api_relationships(rel_type: Optional[str] = None):
    return get_all_relationships(rel_type=rel_type)

@app.get("/api/cases")
def api_cases(mode: Optional[str] = "dynamic"):
    """
    Returns the 4 showcase evaluation cases.
    - mode='dynamic': Derived live from active relationships in the database knowledge graph.
    - mode='benchmark': Reference ground-truth benchmark cases for starter documents.
    """
    return get_dynamic_showcase_cases(mode=mode or "dynamic")

class APIKeyRequest(BaseModel):
    api_key: str

@app.post("/api/config/key")
def set_api_key(req: APIKeyRequest):
    config.GEMINI_API_KEY = req.api_key.strip()
    return {"status": "success", "message": "Gemini API key updated successfully for runtime."}

@app.get("/api/config/status")
def get_config_status():
    return {
        "has_gemini_key": bool(config.GEMINI_API_KEY),
        "model": config.GEMINI_MODEL
    }

def reconcile_new_facts_incrementally(new_facts: List[Dict[str, Any]], existing_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Truly INCREMENTAL reconciliation:
    1. Compares new facts against each other (intra-batch).
    2. Compares new facts against previously existing facts in the DB (cross-batch).
    3. NEVER re-compares existing facts against existing facts!
    """
    discovered_rels = []
    seen_pairs = set()

    # 1. New facts vs Existing facts
    for nf in new_facts:
        for ef in existing_facts:
            pair_key = tuple(sorted([nf["id"], ef["id"]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            rel = analyze_fact_pair(nf, ef)
            if rel:
                discovered_rels.append(rel)

    # 2. New facts among themselves
    for i in range(len(new_facts)):
        for j in range(i + 1, len(new_facts)):
            nf1 = new_facts[i]
            nf2 = new_facts[j]
            pair_key = tuple(sorted([nf1["id"], nf2["id"]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            rel = analyze_fact_pair(nf1, nf2)
            if rel:
                discovered_rels.append(rel)

    return discovered_rels

@app.post("/api/upload")
def upload_pdf(
    file: UploadFile = File(...),
    max_pages: Optional[int] = Form(None)
):
    """
    Uploads any generic PDF, extracts pages, runs grounded fact extraction with
    page-level error isolation, and reconciles INCREMENTALLY against existing facts.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    saved_path = UPLOAD_DIR / file.filename
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Extract text and page numbers
    try:
        pages = extract_pdf_pages(str(saved_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF structure: {e}")

    if not pages:
        raise HTTPException(status_code=400, detail="PDF has no readable text layer.")

    total_pages = len(pages)
    
    # Page processing limit: transparently handle large files
    limit = max_pages or (20 if total_pages > 25 else total_pages)
    target_pages = pages[:limit]
    is_truncated = total_pages > limit

    # 2. Record Document in DB
    doc_id = insert_document(
        filename=file.filename,
        filepath=str(saved_path),
        page_count=total_pages,
        description=f"Processed {len(target_pages)} of {total_pages} pages."
    )

    # 3. Existing facts in DB before this upload (for incremental comparison)
    existing_facts = get_all_facts()

    # 4. Extract facts page by page with strict error isolation
    new_facts = []
    page_warnings = []

    for p in target_pages:
        try:
            p_text = p.get("text", "")
            if len(p_text.strip()) < 20:
                continue
            
            page_facts = extract_facts_from_page(
                doc_name=file.filename,
                page_num=p["page_number"],
                text=p_text,
                api_key=config.GEMINI_API_KEY
            )

            for f in page_facts:
                try:
                    f["document_id"] = doc_id
                    insert_fact(f)
                    new_facts.append(f)
                except Exception as fact_err:
                    page_warnings.append(f"Page {p['page_number']} fact skipped: {fact_err}")

        except Exception as page_err:
            page_warnings.append(f"Page {p['page_number']} extraction error: {page_err}")
            continue

    # 5. Truly INCREMENTAL reconciliation
    new_rels = reconcile_new_facts_incrementally(new_facts, existing_facts)
    for r in new_rels:
        try:
            insert_relationship(r)
        except Exception as rel_err:
            page_warnings.append(f"Relationship save error: {rel_err}")

    return {
        "status": "success",
        "filename": file.filename,
        "total_pages": total_pages,
        "pages_processed": len(target_pages),
        "is_truncated": is_truncated,
        "truncation_note": f"Processed first {len(target_pages)} of {total_pages} pages to optimize extraction speed." if is_truncated else "Processed all pages.",
        "facts_extracted": len(new_facts),
        "new_relationships_discovered": len(new_rels),
        "warnings": page_warnings[:5]
    }

class QueryRequest(BaseModel):
    query: str

@app.post("/api/ask")
def ask_question(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    facts = get_all_facts()
    q_lower = query.lower()
    
    # Generic token ranking
    q_tokens = [t for t in q_lower.split() if len(t) > 2]
    scored_facts = []
    for f in facts:
        score = 0
        searchable_text = f"{f.get('subject', '')} {f.get('predicate', '')} {f.get('value', '')} {f.get('exact_quote', '')}".lower()
        for tok in q_tokens:
            if tok in searchable_text:
                score += 1
        if score > 0:
            scored_facts.append((score, f))

    scored_facts.sort(key=lambda x: x[0], reverse=True)
    relevant_facts = [f for _, f in scored_facts[:8]]

    if config.GEMINI_API_KEY and relevant_facts:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            context_str = "\n".join([
                f"- Fact: {f['subject']} -> {f['predicate']} = {f['value']} (Doc: {f['document_name']}, Page {f['page_number']}, Quote: '{f['exact_quote']}')"
                for f in relevant_facts
            ])
            prompt = f"""
You are the Superjoin Fact Knowledge Layer answering an analyst query.
Answer the user's question using ONLY the provided verified facts and quotes.
Cite each fact with [Document Name, Page Number].
Highlight any corroborations or contradictions found across documents.

Question: {query}

Verified Facts:
{context_str}
"""
            resp = model.generate_content(prompt)
            return {
                "answer": resp.text,
                "grounded_facts": relevant_facts
            }
        except Exception as e:
            print(f"Gemini query error: {e}")

    if relevant_facts:
        summary = f"Found {len(relevant_facts)} relevant facts in the knowledge layer:\n\n"
        for f in relevant_facts[:5]:
            summary += f"• **{f['subject']} - {f['predicate']}**: {f['value']} *(Source: {f['document_name']}, Page {f['page_number']})*\n"
        return {"answer": summary, "grounded_facts": relevant_facts}
    else:
        return {
            "answer": "No matching facts found. Try searching for specific metrics like revenue, express parcel, EBITDA, or delivery centers.",
            "grounded_facts": []
        }

frontend_dir = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(frontend_dir / "index.html"))
