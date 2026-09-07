import sys
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def run_tests():
    print("Testing /api/stats ...")
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    print("  Stats:", stats)
    assert stats["documents"] >= 3
    assert stats["facts"] >= 10
    assert stats["corroborations"] >= 1
    assert stats["contradictions"] >= 1
    assert stats["reconciled"] >= 1

    print("\nTesting /api/cases (Superjoin 4 Mandatory Cases) ...")
    res = client.get("/api/cases")
    assert res.status_code == 200
    cases = res.json()
    print("  Found", len(cases), "cases:")
    for c in cases:
        print("   [Case " + str(c.get("case_number")) + "] " + c.get("title") + " (" + c.get("case_type") + ")")
    assert len(cases) == 4

    print("\nTesting /api/facts ...")
    res = client.get("/api/facts")
    assert res.status_code == 200
    facts = res.json()
    print("  Total facts:", len(facts))

    print("\nTesting /api/relationships ...")
    res = client.get("/api/relationships")
    assert res.status_code == 200
    rels = res.json()
    print("  Total relationships:", len(rels))

    print("\nTesting /api/ask (Q&A with grounded citations) ...")
    res = client.post("/api/ask", json={"query": "revenue"})
    assert res.status_code == 200
    ans = res.json()
    print("  Citations:", len(ans.get("grounded_facts", [])))

    print("\n=============================================")
    print("  ALL VERIFICATION TESTS PASSED 100% CLEAN!  ")
    print("=============================================")

if __name__ == "__main__":
    run_tests()