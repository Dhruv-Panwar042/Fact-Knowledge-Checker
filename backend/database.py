import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        filepath TEXT,
        page_count INTEGER DEFAULT 0,
        uploaded_at TEXT,
        status TEXT DEFAULT 'processed',
        description TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facts (
        id TEXT PRIMARY KEY,
        document_id INTEGER,
        document_name TEXT NOT NULL,
        page_number INTEGER NOT NULL,
        category TEXT NOT NULL,
        subject TEXT NOT NULL,
        predicate TEXT NOT NULL,
        value TEXT NOT NULL,
        normalized_value TEXT,
        unit TEXT,
        temporal_period TEXT,
        entity_scope TEXT,
        exact_quote TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        created_at TEXT,
        FOREIGN KEY (document_id) REFERENCES documents (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        fact_a_id TEXT NOT NULL,
        fact_b_id TEXT NOT NULL,
        rel_type TEXT NOT NULL, -- corroboration, contradiction, reconciled
        context_factor TEXT,     -- unit, time, scope, accounting, none
        reasoning TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY (fact_a_id) REFERENCES facts (id),
        FOREIGN KEY (fact_b_id) REFERENCES facts (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS showcase_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        case_type TEXT NOT NULL,
        fact_a_id TEXT,
        fact_b_id TEXT,
        summary TEXT NOT NULL,
        source_evidence_a TEXT NOT NULL,
        source_evidence_b TEXT,
        system_reasoning TEXT NOT NULL,
        resolution TEXT,
        created_at TEXT
    )
    ''')

    conn.commit()
    conn.close()

def insert_document(filename: str, filepath: str = "", page_count: int = 0, description: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO documents (filename, filepath, page_count, uploaded_at, status, description)
        VALUES (?, ?, ?, ?, 'processed', ?)
    ''', (filename, filepath, page_count, now, description))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def insert_fact(fact_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO facts (
            id, document_id, document_name, page_number, category, subject, predicate,
            value, normalized_value, unit, temporal_period, entity_scope, exact_quote,
            confidence, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fact_data["id"],
        fact_data.get("document_id"),
        fact_data["document_name"],
        fact_data["page_number"],
        fact_data.get("category", "General"),
        fact_data["subject"],
        fact_data["predicate"],
        fact_data["value"],
        fact_data.get("normalized_value", fact_data["value"]),
        fact_data.get("unit", ""),
        fact_data.get("temporal_period", ""),
        fact_data.get("entity_scope", "Consolidated"),
        fact_data["exact_quote"],
        fact_data.get("confidence", 1.0),
        fact_data.get("created_at", now)
    ))
    conn.commit()
    conn.close()

def insert_relationship(rel_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO relationships (
            id, fact_a_id, fact_b_id, rel_type, context_factor, reasoning, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        rel_data["id"],
        rel_data["fact_a_id"],
        rel_data["fact_b_id"],
        rel_data["rel_type"],
        rel_data.get("context_factor", "none"),
        rel_data["reasoning"],
        rel_data.get("created_at", now)
    ))
    conn.commit()
    conn.close()

def insert_showcase_case(case_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO showcase_cases (
            case_number, title, case_type, fact_a_id, fact_b_id,
            summary, source_evidence_a, source_evidence_b, system_reasoning, resolution, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        case_data["case_number"],
        case_data["title"],
        case_data["case_type"],
        case_data.get("fact_a_id"),
        case_data.get("fact_b_id"),
        case_data["summary"],
        json.dumps(case_data.get("source_evidence_a", {})) if isinstance(case_data.get("source_evidence_a"), dict) else case_data.get("source_evidence_a", ""),
        json.dumps(case_data.get("source_evidence_b", {})) if isinstance(case_data.get("source_evidence_b"), dict) else case_data.get("source_evidence_b", ""),
        case_data["system_reasoning"],
        case_data.get("resolution", ""),
        now
    ))
    conn.commit()
    conn.close()

def get_all_documents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_facts(doc_name: Optional[str] = None, category: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM facts WHERE 1=1"
    params = []
    if doc_name:
        sql += " AND document_name = ?"
        params.append(doc_name)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if query:
        sql += " AND (subject LIKE ? OR predicate LIKE ? OR value LIKE ? OR exact_quote LIKE ?)"
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild, q_wild, q_wild])
    sql += " ORDER BY category, id ASC"
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_fact_by_id(fact_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facts WHERE id = ?", (fact_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_relationships(rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    sql = '''
        SELECT r.*,
               fa.subject as subject_a, fa.predicate as predicate_a, fa.value as value_a, fa.document_name as doc_a, fa.page_number as page_a, fa.exact_quote as quote_a, fa.temporal_period as period_a, fa.entity_scope as scope_a,
               fb.subject as subject_b, fb.predicate as predicate_b, fb.value as value_b, fb.document_name as doc_b, fb.page_number as page_b, fb.exact_quote as quote_b, fb.temporal_period as period_b, fb.entity_scope as scope_b
        FROM relationships r
        JOIN facts fa ON r.fact_a_id = fa.id
        JOIN facts fb ON r.fact_b_id = fb.id
    '''
    params = []
    if rel_type:
        sql += " WHERE r.rel_type = ?"
        params.append(rel_type)
    sql += " ORDER BY r.id ASC"
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_showcase_cases() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM showcase_cases ORDER BY case_number ASC")
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["source_evidence_a"] = json.loads(d["source_evidence_a"])
        except Exception:
            pass
        try:
            d["source_evidence_b"] = json.loads(d["source_evidence_b"])
        except Exception:
            pass
        rows.append(d)
    conn.close()
    return rows

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM facts")
    fact_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE rel_type = 'corroboration'")
    corrob_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE rel_type = 'contradiction'")
    contra_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships WHERE rel_type = 'reconciled'")
    reconciled_count = cursor.fetchone()[0]
    conn.close()
    return {
        "documents": doc_count,
        "facts": fact_count,
        "corroborations": corrob_count,
        "contradictions": contra_count,
        "reconciled": reconciled_count
    }
