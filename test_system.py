import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.app import app, reconcile_new_facts_incrementally
from backend.reconciler import parse_financial_number, heuristic_reconcile_pair
from backend.database import get_dynamic_showcase_cases, get_all_relationships

client = TestClient(app)

def test_api_endpoints():
    print("--- [1/5] Testing REST API Endpoints ---")
    
    # 1. Stats
    res = client.get("/api/stats")
    assert res.status_code == 200, f"Stats failed: {res.text}"
    stats = res.json()
    print(f"  [PASS] /api/stats: {stats}")
    assert stats["documents"] >= 1
    assert stats["facts"] >= 10

    # 2. Facts
    res = client.get("/api/facts")
    assert res.status_code == 200
    facts = res.json()
    print(f"  [PASS] /api/facts returned {len(facts)} facts")

    # 3. Relationships
    res = client.get("/api/relationships")
    assert res.status_code == 200
    rels = res.json()
    print(f"  [PASS] /api/relationships returned {len(rels)} relationships")

    # 4. Showcase cases (dynamic mode)
    res = client.get("/api/cases?mode=dynamic")
    assert res.status_code == 200
    cases_dyn = res.json()
    assert len(cases_dyn) == 4, f"Expected 4 dynamic cases, got {len(cases_dyn)}"
    assert cases_dyn[0]["is_live_derived"] is True
    print(f"  [PASS] /api/cases?mode=dynamic returned 4 live-derived cases")

    # 5. Showcase cases (benchmark mode)
    res = client.get("/api/cases?mode=benchmark")
    assert res.status_code == 200
    cases_bench = res.json()
    assert len(cases_bench) == 4
    print(f"  [PASS] /api/cases?mode=benchmark returned 4 benchmark cases")

    # 6. Grounded Q&A
    res = client.post("/api/ask", json={"query": "revenue"})
    assert res.status_code == 200
    ans = res.json()
    assert "answer" in ans
    assert len(ans.get("grounded_facts", [])) > 0
    print(f"  [PASS] /api/ask returned grounded answer with {len(ans['grounded_facts'])} citations")

def test_numerical_normalization():
    print("\n--- [2/5] Testing Financial Number Normalization ---")
    assert parse_financial_number("₹8,142 Cr") == 81420000000.0
    assert parse_financial_number("₹81,415.38 million") == 81415380000.0
    assert parse_financial_number("740 Mn") == 740000000.0
    assert parse_financial_number("(4,157.43)") == -4157.43
    assert parse_financial_number("1.4 Mn Tons") == 1400000.0
    assert parse_financial_number("24,425") == 24425.0
    print("  [PASS] All financial units (Crores, Millions, Tons, Parentheses losses) normalized accurately.")

def test_reconciler_logic():
    print("\n--- [3/5] Testing Reconciler Engine on Synthetic & Real Pairs ---")
    
    # Pair 1: Unit Reconciliation (Crores vs Millions)
    fa_unit = {
        "id": "T1", "document_name": "DocA.pdf", "page_number": 6,
        "subject": "Acme Corp", "predicate": "FY24 revenue from services",
        "value": "₹8,142 Cr", "unit": "INR (Crores)", "temporal_period": "FY24",
        "entity_scope": "Consolidated", "exact_quote": "₹8,142 Cr FY24 revenue"
    }
    fb_unit = {
        "id": "T2", "document_name": "DocB.pdf", "page_number": 22,
        "subject": "Acme Corp", "predicate": "FY24 revenue from operations",
        "value": "₹81,415.38 million", "unit": "INR (Million)", "temporal_period": "FY24",
        "entity_scope": "Consolidated", "exact_quote": "Revenue stood at ₹81,415.38 million"
    }
    rel_unit = heuristic_reconcile_pair(fa_unit, fb_unit)
    assert rel_unit is not None
    assert rel_unit["rel_type"] == "reconciled"
    assert rel_unit["context_factor"] == "unit"
    print("  [PASS] Unit reconciliation (Crores vs Millions) correctly resolved.")

    # Pair 2: Corroboration (Identical parcel volume)
    fa_corrob = {
        "id": "T3", "document_name": "DocA.pdf", "page_number": 6,
        "subject": "Acme Corp", "predicate": "Express parcel shipments volume",
        "value": "740 Mn", "unit": "Shipments", "temporal_period": "FY24",
        "entity_scope": "Consolidated", "exact_quote": "740 Mn Express parcel shipments"
    }
    fb_corrob = {
        "id": "T4", "document_name": "DocB.pdf", "page_number": 70,
        "subject": "Acme Corp", "predicate": "Express parcel shipment volume",
        "value": "740 Mn", "unit": "Shipments", "temporal_period": "FY24",
        "entity_scope": "Consolidated", "exact_quote": "Express parcel volume: 740 Mn"
    }
    rel_corrob = heuristic_reconcile_pair(fa_corrob, fb_corrob)
    assert rel_corrob is not None
    assert rel_corrob["rel_type"] == "corroboration"
    print("  [PASS] Cross-document corroboration correctly identified.")

    # Pair 3: Genuine Contradiction (939 vs 938 partner centers)
    fa_contra = {
        "id": "T5", "document_name": "DocA.pdf", "page_number": 8,
        "subject": "Acme Corp", "predicate": "Partner centers count",
        "value": "939", "unit": "Centres", "temporal_period": "March 31, 2024",
        "entity_scope": "Last-Mile Network", "exact_quote": "Partner centers: 939"
    }
    fb_contra = {
        "id": "T6", "document_name": "DocB.pdf", "page_number": 47,
        "subject": "Acme Corp", "predicate": "Partner centers count",
        "value": "938", "unit": "Centres", "temporal_period": "March 31, 2024",
        "entity_scope": "Last-Mile Network", "exact_quote": "938 Partner centres"
    }
    rel_contra = heuristic_reconcile_pair(fa_contra, fb_contra)
    assert rel_contra is not None
    assert rel_contra["rel_type"] == "contradiction"
    print("  [PASS] Counting contradiction (939 vs 938) correctly flagged.")

def test_incremental_reconciliation():
    print("\n--- [4/5] Testing Incremental Reconciliation Deduplication ---")
    existing_facts = [
        {"id": "E1", "document_name": "Doc1.pdf", "subject": "A", "predicate": "revenue", "value": "100 Cr", "temporal_period": "FY24", "entity_scope": "Consolidated", "unit": "Cr", "page_number": 1, "exact_quote": "100 Cr"},
        {"id": "E2", "document_name": "Doc2.pdf", "subject": "A", "predicate": "revenue", "value": "100 Cr", "temporal_period": "FY24", "entity_scope": "Consolidated", "unit": "Cr", "page_number": 2, "exact_quote": "100 Cr"},
    ]
    new_facts = [
        {"id": "N1", "document_name": "Doc3.pdf", "subject": "A", "predicate": "revenue", "value": "100 Cr", "temporal_period": "FY24", "entity_scope": "Consolidated", "unit": "Cr", "page_number": 3, "exact_quote": "100 Cr"}
    ]
    
    rels = reconcile_new_facts_incrementally(new_facts, existing_facts)
    print(f"  [PASS] Discovered {len(rels)} incremental relationships without re-evaluating existing pairs.")
    assert len(rels) == 2

def test_dynamic_showcase_synthesizer():
    print("\n--- [5/5] Testing Dynamic Showcase Case Synthesizer ---")
    cases = get_dynamic_showcase_cases(mode="dynamic")
    assert len(cases) == 4
    case_types = [c["case_type"] for c in cases]
    assert "Corroboration" in case_types
    assert "Contradiction" in case_types
    assert "Reconciled Contradiction" in case_types
    assert "Reasoning Failure Analysis" in case_types
    print("  [PASS] Dynamic Showcase generator produced all 4 required evaluation cases directly from active graph.")

if __name__ == "__main__":
    test_api_endpoints()
    test_numerical_normalization()
    test_reconciler_logic()
    test_incremental_reconciliation()
    test_dynamic_showcase_synthesizer()
    print("\n===================================================================")
    print("  ALL 5 TEST SUITES PASSED! REAL PIPELINE & CASES FULLY VERIFIED!  ")
    print("===================================================================")