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
    get_all_relationships, get_showcase_cases, insert_document, insert_fact,
    insert_relationship
)
from backend.seed_data import populate_seed_data
from backend.pdf_extractor import extract_pdf_pages
from backend.fact_extractor import extract_facts_from_page
from backend.reconciler import reconcile_all_facts

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
        print("Seeding initial data from starter PDFs...")
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
def api_cases():
    return get_showcase_cases()

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

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    saved_path = UPLOAD_DIR / file.filename
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pages = extract_pdf_pages(str(saved_path))
    if not pages:
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")

    doc_id = insert_document(
        filename=file.filename,
        filepath=str(saved_path),
        page_count=len(pages),
        description=f"Uploaded document containing {len(pages)} pages."
    )

    extracted_facts = []
    target_pages = pages[:15] if len(pages) > 15 else pages
    for p in target_pages:
        page_facts = extract_facts_from_page(
            doc_name=file.filename,
            page_num=p["page_number"],
            text=p["text"],
            api_key=config.GEMINI_API_KEY
        )
        for fact in page_facts:
            fact["document_id"] = doc_id
            insert_fact(fact)
            extracted_facts.append(fact)

    all_facts = get_all_facts()
    new_rels = reconcile_all_facts(all_facts)
    for r in new_rels:
        insert_relationship(r)

    return {
        "status": "success",
        "filename": file.filename,
        "pages_processed": len(target_pages),
        "facts_extracted": len(extracted_facts),
        "relationships_found": len(new_rels)
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
    relevant_facts = [
        f for f in facts
        if any(term in f["subject"].lower() or term in f["predicate"].lower() or term in f["value"].lower()
               for term in q_lower.split())
    ][:8]

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
            "answer": "No exact matching facts found in the current knowledge base. Try searching for revenue, express parcel, EBITDA, or workforce.",
            "grounded_facts": []
        }

frontend_dir = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(frontend_dir / "index.html"))
