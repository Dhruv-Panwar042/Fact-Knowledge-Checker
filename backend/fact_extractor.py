import json
import re
import uuid
import time
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

_EXTRACTOR_COOLDOWN_UNTIL = 0

EXTRACTION_SYSTEM_PROMPT = """
You are an expert document analysis and factual verification engine.
Your task is to extract atomic, meaningful, verifiable facts from the provided document page.

Rules:
1. Extract BOTH numerical metrics (revenue, EBITDA, profits, shareholding %, parcel count, headcount, dates, square feet, etc.) AND semantic/corporate facts (acquisitions, board changes, partnerships, registrations, audits).
2. For EVERY fact, you MUST provide:
   - subject: The entity, segment, or metric subject (e.g. 'Acme Corp', 'Express Parcel Segment', 'Chief Executive Officer').
   - predicate: The property, metric, or event (e.g. 'FY24 revenue from services', 'Resignation date', 'PIN code reach').
   - value: The exact stated value as written in the text (e.g. '8,142 Cr', 'July 01, 2024', '18,793').
   - normalized_value: A normalized comparable string or number (e.g. 81420000000 for 8142 Cr, 2024-07-01 for dates).
   - unit: Unit of measurement (e.g. 'INR (Crores)', 'Shipments (Millions)', 'Headcount', 'Date', 'PIN codes').
   - temporal_period: Relevant fiscal year, quarter, or date (e.g. 'FY24', 'Q4 FY24', 'March 31, 2024', 'May 2022').
   - entity_scope: Scope of reporting (e.g. 'Consolidated Group', 'Standalone Parent', 'Division', 'National').
   - category: One of ['Financial', 'Operational', 'Governance', 'Strategy', 'ESG'].
   - exact_quote: A verbatim exact substring quote from the text that proves this fact. Must be an exact match from the page text.
   - confidence: A score between 0.0 and 1.0.

Return ONLY a JSON array of fact objects. No other markdown or conversational filler.
"""

def extract_facts_from_page(doc_name: str, page_num: int, text: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extracts facts from page text using Gemini API or intelligent heuristic fallback.
    Protected against 429 quota exhaustion.
    """
    global _EXTRACTOR_COOLDOWN_UNTIL
    active_key = api_key or GEMINI_API_KEY
    if active_key and len(text.strip()) > 30 and time.time() >= _EXTRACTOR_COOLDOWN_UNTIL:
        try:
            import google.generativeai as genai
            genai.configure(api_key=active_key)
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json"}
            )
            prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nDocument: {doc_name}\nPage: {page_num}\nText content:\n{text[:4000]}"
            response = model.generate_content(prompt, request_options={"timeout": 6})
            raw_json = response.text.strip()
            data = json.loads(raw_json)
            if isinstance(data, dict) and "facts" in data:
                data = data["facts"]
            if isinstance(data, list):
                extracted = []
                for item in data:
                    pred = str(item.get("predicate", "")).lower()
                    if "page number" in pred or "starts on page" in pred:
                        continue
                    item["id"] = f"FACT-{uuid.uuid4().hex[:8].upper()}"
                    item["document_name"] = doc_name
                    item["page_number"] = page_num
                    extracted.append(item)
                return extracted
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower():
                _EXTRACTOR_COOLDOWN_UNTIL = time.time() + 3600
                print(f"Notice: Gemini quota reached on page {page_num}. Setting 1-hour cooldown and falling back to heuristic extraction.")
            else:
                print(f"Gemini extraction error on page {page_num}: {e}")

    # Fallback heuristic extractor (generic, zero latency)
    return fallback_heuristic_extractor(doc_name, page_num, text)

def infer_document_entity(doc_name: str, text: str) -> str:
    """Infers the primary organization or entity name generically from document name or header."""
    clean_name = re.sub(r"[\-_]", " ", doc_name).replace(".pdf", "").strip()
    words = clean_name.split()
    if words:
        return words[0].title()
    for line in text.split("\n")[:5]:
        line_clean = line.strip()
        if len(line_clean) > 3 and line_clean.isupper():
            return line_clean.title()
    return "Entity"

def fallback_heuristic_extractor(doc_name: str, page_num: int, text: str) -> List[Dict[str, Any]]:
    """
    Generic rule-based extractor for numerical metrics and corporate statements.
    Works for any document without hardcoded entity names.
    """
    facts = []
    entity = infer_document_entity(doc_name, text)
    
    metric_patterns = [
        (r"(Revenue|Total income|Turnover)\D*?([₹$€£]?\s*[\d,]+(?:\.\d+)?\s*(?:Cr|million|billion|crores|mn|bn)?)", "Financial"),
        (r"(EBITDA|Profit|Loss|Net income)\D*?([₹$€£]?\s*[\d,]+(?:\.\d+)?\s*(?:Cr|million|billion|crores|mn|bn)?)", "Financial"),
        (r"([\w\s]+(?:shipments|volume|tonnage|capacity|customers|headcount|employees))\D*?([\d,]+(?:\.\d+)?\s*(?:million|thousand|tonnes|tons|mn|k)?)", "Operational"),
    ]

    for pattern, category in metric_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            label = m.group(1).strip()
            val = m.group(2).strip()
            if len(val) < 2 or not any(c.isdigit() for c in val):
                continue
            
            start = max(0, m.start() - 25)
            end = min(len(text), m.end() + 35)
            quote = text[start:end].replace("\n", " ").strip()

            facts.append({
                "id": f"FACT-{uuid.uuid4().hex[:8].upper()}",
                "document_name": doc_name,
                "page_number": page_num,
                "category": category,
                "subject": entity,
                "predicate": label,
                "value": val,
                "normalized_value": val,
                "unit": "Standard",
                "temporal_period": "Reporting Period",
                "entity_scope": "General",
                "exact_quote": quote,
                "confidence": 0.8
            })
            if len(facts) >= 3:
                break
        if len(facts) >= 4:
            break

    return facts