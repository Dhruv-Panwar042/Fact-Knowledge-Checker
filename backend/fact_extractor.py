import json
import re
import uuid
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

EXTRACTION_SYSTEM_PROMPT = """
You are an expert financial and corporate intelligence analyst. Your task is to extract atomic, meaningful, verifiable facts from the provided document page.

Rules:
1. Extract BOTH numerical metrics (revenue, EBITDA, profits, shareholding %, parcel count, headcount, etc.) AND semantic/corporate facts (acquisitions, board changes, partnerships, registrations, audits).
2. For EVERY fact, you MUST provide:
   - subject: The entity, segment, or metric subject (e.g. 'Delhivery Limited', 'Express Parcel', 'Sandeep Kumar Barasia').
   - predicate: The property or action (e.g. 'FY24 revenue from services', 'Resignation date from Board', 'PIN code reach').
   - value: The exact stated value as written in the text (e.g. '8,142 Cr', 'July 01, 2024', '18,793').
   - normalized_value: A normalized comparable string or number (e.g. 81420000000 for 8142 Cr, 2024-07-01 for dates).
   - unit: Unit of measurement (e.g. 'INR (Crores)', 'Shipments (Millions)', 'Headcount', 'Date', 'PIN codes').
   - temporal_period: Relevant fiscal year, quarter, or date (e.g. 'FY24', 'Q4 FY24', 'March 31, 2024', 'May 2022').
   - entity_scope: Scope of reporting (e.g. 'Consolidated Group', 'Standalone Parent', 'Spoton Logistics', 'Pan-India').
   - category: One of ['Financial', 'Operational', 'Governance', 'Strategy', 'ESG'].
   - exact_quote: A verbatim exact substring quote from the text that proves this fact. Must be an exact match from the page text.
   - confidence: A score between 0.0 and 1.0.

Return ONLY a JSON array of fact objects. No other markdown or conversational filler.
"""

def extract_facts_from_page(doc_name: str, page_num: int, text: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extracts facts from page text using Gemini API or intelligent heuristic fallback.
    """
    active_key = api_key or GEMINI_API_KEY
    if active_key and len(text.strip()) > 30:
        try:
            import google.generativeai as genai
            genai.configure(api_key=active_key)
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={"response_mime_type": "application/json"}
            )
            prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nDocument: {doc_name}\nPage: {page_num}\nText content:\n{text[:4000]}"
            response = model.generate_content(prompt)
            raw_json = response.text.strip()
            data = json.loads(raw_json)
            if isinstance(data, dict) and "facts" in data:
                data = data["facts"]
            if isinstance(data, list):
                extracted = []
                for item in data:
                    item["id"] = f"FACT-{uuid.uuid4().hex[:8].upper()}"
                    item["document_name"] = doc_name
                    item["page_number"] = page_num
                    extracted.append(item)
                return extracted
        except Exception as e:
            print(f"Gemini extraction error on page {page_num}: {e}")

    # Fallback heuristic extractor
    return fallback_heuristic_extractor(doc_name, page_num, text)

def fallback_heuristic_extractor(doc_name: str, page_num: int, text: str) -> List[Dict[str, Any]]:
    """
    Rule-based extractor for common corporate and financial statements when LLM is offline.
    """
    facts = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    # Financial patterns
    revenue_patterns = [
        r"Revenue\s+(?:from\s+operations|from\s+contracts\s+with\s+customers|from\s+services)\D*?(?:Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?\s*(?:Cr|million|crores)?)",
        r"((?:Rs\.?|₹)?\s*[\d,]+(?:\.\d+)?\s*(?:Cr|million))\s+(?:FY\d\d\s+)?revenue",
    ]
    for p in revenue_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            facts.append({
                "id": f"FACT-{uuid.uuid4().hex[:8].upper()}",
                "document_name": doc_name,
                "page_number": page_num,
                "category": "Financial",
                "subject": "Delhivery Limited",
                "predicate": "Revenue",
                "value": val,
                "normalized_value": val,
                "unit": "INR",
                "temporal_period": "FY24",
                "entity_scope": "Consolidated",
                "exact_quote": text[max(0, m.start()-20):min(len(text), m.end()+30)].replace("\n", " "),
                "confidence": 0.85
            })
            break

    return facts