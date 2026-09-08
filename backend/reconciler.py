import json
import re
import uuid
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

STOPWORDS = {
    'the', 'of', 'in', 'and', 'to', 'for', 'a', 'on', 'as', 'at', 'by', 'with', 'is',
    'from', 'under', 'per', 'our', 'its', 'their', 'company', 'limited', 'pvt', 'ltd'
}

def parse_financial_number(val_str: str) -> Optional[float]:
    """Converts strings like '8,142 Cr', '81,415.38 million', '(4,157.43)', '1.4 Mn' to a standardized numeric value."""
    if not val_str:
        return None
    cleaned = re.sub(r"[₹$€£,]", "", val_str).strip()
    is_negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        is_negative = True
        cleaned = cleaned[1:-1].strip()
    elif cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned[1:].strip()

    multiplier = 1.0
    if re.search(r"\bcr(?:ore)?s?\b", cleaned, re.IGNORECASE):
        multiplier = 1e7
        cleaned = re.sub(r"\bcr(?:ore)?s?\b", "", cleaned, flags=re.IGNORECASE).strip()
    elif re.search(r"\blakh?s?\b", cleaned, re.IGNORECASE):
        multiplier = 1e5
        cleaned = re.sub(r"\blakh?s?\b", "", cleaned, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(?:million|mn)\b", cleaned, re.IGNORECASE):
        multiplier = 1e6
        cleaned = re.sub(r"\b(?:million|mn)\b", "", cleaned, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(?:billion|bn)\b", cleaned, re.IGNORECASE):
        multiplier = 1e9
        cleaned = re.sub(r"\b(?:billion|bn)\b", "", cleaned, flags=re.IGNORECASE).strip()
    elif re.search(r"\b(?:thousand|k)\b", cleaned, re.IGNORECASE):
        multiplier = 1e3
        cleaned = re.sub(r"\b(?:thousand|k)\b", "", cleaned, flags=re.IGNORECASE).strip()
    elif re.search(r"\bton(?:ne)?s?\b", cleaned, re.IGNORECASE):
        multiplier = 1e3
        cleaned = re.sub(r"\bton(?:ne)?s?\b", "", cleaned, flags=re.IGNORECASE).strip()

    # Extract first float/int token
    m = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if not m:
        return None
    try:
        val = float(m.group(0))
        if is_negative:
            val = -val
        return val * multiplier
    except Exception:
        return None

def compute_semantic_similarity(fa: Dict[str, Any], fb: Dict[str, Any]) -> float:
    """Computes generic token overlap between the subject and predicate of two facts."""
    words_a = set(re.findall(r"\w+", f"{fa.get('subject', '')} {fa.get('predicate', '')}".lower()))
    words_b = set(re.findall(r"\w+", f"{fb.get('subject', '')} {fb.get('predicate', '')}".lower()))
    words_a -= STOPWORDS
    words_b -= STOPWORDS
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0

def llm_reconcile_pair(fact_a: Dict[str, Any], fact_b: Dict[str, Any], api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Uses Gemini LLM to analyze the relationship between any arbitrary pair of facts.
    Completely generic and dynamic.
    """
    active_key = api_key or GEMINI_API_KEY
    if not active_key:
        return None

    prompt = f"""
You are an objective cross-document reconciliation and verification engine.
Analyze the relationship between the following two extracted claims from documents:

Claim A:
- Document: {fact_a.get('document_name')} (Page {fact_a.get('page_number')})
- Subject: {fact_a.get('subject')}
- Predicate: {fact_a.get('predicate')}
- Stated Value: {fact_a.get('value')} (Unit: {fact_a.get('unit')}, Period: {fact_a.get('temporal_period')}, Scope: {fact_a.get('entity_scope')})
- Source Quote: "{fact_a.get('exact_quote')}"

Claim B:
- Document: {fact_b.get('document_name')} (Page {fact_b.get('page_number')})
- Subject: {fact_b.get('subject')}
- Predicate: {fact_b.get('predicate')}
- Stated Value: {fact_b.get('value')} (Unit: {fact_b.get('unit')}, Period: {fact_b.get('temporal_period')}, Scope: {fact_b.get('entity_scope')})
- Source Quote: "{fact_b.get('exact_quote')}"

Instructions:
1. Determine if they address the same core topic. If they are completely unrelated, return null.
2. If they address the same topic, classify their relationship as one of:
   - "corroboration": Both claims confirm or agree on the same factual reality, even if expressed differently.
   - "contradiction": Direct, mutually exclusive conflict under identical conditions (time, unit, scope).
   - "reconciled": The raw values or assertions appear to conflict, but are fully explained and reconciled by context (such as different measurement units, different timeframes/dates, different reporting scopes like standalone vs consolidated, or differing accounting standards).
3. If "reconciled", identify the context_factor as one of: ["unit", "time", "scope", "accounting"].
4. Provide a clear, evidence-based reasoning explanation citing both documents.

Return ONLY a JSON object:
{{
  "is_related": true,
  "rel_type": "corroboration" | "contradiction" | "reconciled",
  "context_factor": "unit" | "time" | "scope" | "accounting" | "none",
  "reasoning": "..."
}}
"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=active_key)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json"}
        )
        resp = model.generate_content(prompt)
        res_data = json.loads(resp.text.strip())
        if res_data.get("is_related") and res_data.get("rel_type"):
            return {
                "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "rel_type": res_data["rel_type"],
                "context_factor": res_data.get("context_factor", "none"),
                "reasoning": res_data["reasoning"]
            }
    except Exception as e:
        print(f"LLM reconciliation error: {e}")

    return None

def heuristic_reconcile_pair(fact_a: Dict[str, Any], fact_b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Deterministic fallback for comparing numeric metrics across documents.
    Completely generic: relies on normalized numeric values, units, time, and scope.
    """
    sim = compute_semantic_similarity(fact_a, fact_b)
    if sim < 0.25:
        return None

    period_a = str(fact_a.get("temporal_period", "")).strip().lower()
    period_b = str(fact_b.get("temporal_period", "")).strip().lower()
    scope_a = str(fact_a.get("entity_scope", "")).strip().lower()
    scope_b = str(fact_b.get("entity_scope", "")).strip().lower()

    val_a_num = parse_financial_number(fact_a.get("value", ""))
    val_b_num = parse_financial_number(fact_b.get("value", ""))

    # If both are numeric
    if val_a_num is not None and val_b_num is not None:
        max_val = max(abs(val_a_num), abs(val_b_num))
        diff_ratio = abs(val_a_num - val_b_num) / max_val if max_val > 0 else 0.0

        # Scenario 1: Reconciled by time period difference
        if period_a and period_b and period_a != period_b:
            return {
                "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "rel_type": "reconciled",
                "context_factor": "time",
                "reasoning": f"Metrics differ because they represent different time periods ({fact_a.get('temporal_period')} vs {fact_b.get('temporal_period')}). Both figures are grounded in their respective reporting periods."
            }

        # Scenario 2: Same time period, normalized values match (e.g. Unit reconciliation or direct agreement)
        if diff_ratio < 0.02:
            raw_a = re.sub(r"[^\d.]", "", fact_a.get("value", ""))
            raw_b = re.sub(r"[^\d.]", "", fact_b.get("value", ""))
            if raw_a != raw_b and fact_a.get("unit") != fact_b.get("unit"):
                return {
                    "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
                    "fact_a_id": fact_a["id"],
                    "fact_b_id": fact_b["id"],
                    "rel_type": "reconciled",
                    "context_factor": "unit",
                    "reasoning": f"Apparent conflict ('{fact_a['value']}' vs '{fact_b['value']}') is fully reconciled by measurement units ({fact_a.get('unit')} vs {fact_b.get('unit')}). Normalized values are mathematically equivalent (~{val_a_num:,.2f})."
                }
            else:
                return {
                    "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
                    "fact_a_id": fact_a["id"],
                    "fact_b_id": fact_b["id"],
                    "rel_type": "corroboration",
                    "context_factor": "none",
                    "reasoning": f"Both documents corroborate the same metric: {fact_a['document_name']} (p. {fact_a['page_number']}) reports '{fact_a['value']}' and {fact_b['document_name']} (p. {fact_b['page_number']}) reports '{fact_b['value']}'."
                }

        # Scenario 3: Same time period, different scopes (e.g. standalone vs consolidated)
        if scope_a != scope_b and ("standalone" in scope_a or "standalone" in scope_b or "consolidated" in scope_a or "consolidated" in scope_b):
            return {
                "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "rel_type": "reconciled",
                "context_factor": "scope",
                "reasoning": f"Apparent difference ('{fact_a['value']}' vs '{fact_b['value']}') is explained by reporting scope: one represents '{fact_a.get('entity_scope')}' and the other represents '{fact_b.get('entity_scope')}'."
            }

        # Scenario 4: Same time period, same scope, same units, but conflicting numbers -> Contradiction!
        if diff_ratio > 0.05 and fact_a["document_name"] != fact_b["document_name"]:
            return {
                "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "rel_type": "contradiction",
                "context_factor": "accounting",
                "reasoning": f"Direct conflict for '{fact_a['predicate']}' in period {fact_a.get('temporal_period')}: {fact_a['document_name']} states '{fact_a['value']}' while {fact_b['document_name']} states '{fact_b['value']}' under identical scope."
            }

    # Non-numeric text facts: if values match exactly
    if fact_a.get("value", "").strip().lower() == fact_b.get("value", "").strip().lower() and fact_a["document_name"] != fact_b["document_name"]:
        return {
            "id": f"REL-{uuid.uuid4().hex[:8].upper()}",
            "fact_a_id": fact_a["id"],
            "fact_b_id": fact_b["id"],
            "rel_type": "corroboration",
            "context_factor": "none",
            "reasoning": f"Both documents corroborate the assertion '{fact_a['value']}': confirmed in {fact_a['document_name']} (p. {fact_a['page_number']}) and {fact_b['document_name']} (p. {fact_b['page_number']})."
        }

    return None

def analyze_fact_pair(fact_a: Dict[str, Any], fact_b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compares two facts using LLM if available, otherwise generic deterministic heuristic.
    """
    # First try LLM reconciliation if similarity is high
    sim = compute_semantic_similarity(fact_a, fact_b)
    if sim >= 0.25 and GEMINI_API_KEY:
        llm_res = llm_reconcile_pair(fact_a, fact_b, GEMINI_API_KEY)
        if llm_res:
            return llm_res

    # Heuristic fallback
    return heuristic_reconcile_pair(fact_a, fact_b)

def reconcile_all_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs cross-document comparison across all known facts generically."""
    new_rels = []
    seen_pairs = set()
    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):
            fa = facts[i]
            fb = facts[j]
            pair_key = tuple(sorted([fa["id"], fb["id"]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            rel = analyze_fact_pair(fa, fb)
            if rel:
                new_rels.append(rel)
    return new_rels