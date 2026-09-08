# Fact Knowledge Layer

> **Superjoin Engineering Intern Hiring Assignment (VIT 2026)**  
> An automated, generalized Fact Knowledge Layer that extracts structured facts from PDF documents, grounds every claim in verbatim source evidence, and reconciles cross-document relationships (Corroborations, Contradictions, and Contextual Reconciliations).

---

## 📺 Video Demo
- **Demo Video Link**: `[Insert your 3-minute Loom or YouTube video link here]`  
  *(A full click-by-click narration script is provided in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) to record your 3-minute walkthrough seamlessly).*

---

## 🚀 Setup and Run Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Optional: A free **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/) *(the app also includes a fully functional offline mode and seed dataset so it runs out-of-the-box without requiring an account).*

### 1. Clone or Open Project
```bash
git clone <your-repository-url>
cd fact-knowledge-layer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure Gemini API Key
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and paste your key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
PORT=8000
```
> *Note: You can also enter or update your Gemini API key directly in the web UI at runtime via the "API Key Configuration" modal without restarting the server!*

### 4. Run the Application
**On Windows:**
Double-click `run.bat` or run:
```bash
python main.py
```

### 5. Access the Interface
- **Modern Web Dashboard**: Open [http://localhost:8000](http://localhost:8000) in your browser.
- **Interactive REST API Docs (Swagger UI)**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🔍 The Four Required Cases Demonstrated

The system explicitly identifies and resolves all four evaluation cases specified by Superjoin:

### 1. Case 1: Corroborated Fact Across Documents
- **Fact**: FY24 Express Parcel Shipment Volume = **740 Million shipments**.
- **Evidence A**: *Delhivery Earnings Presentation Q4 & FY24*, Page 6 & Page 9: `"740 Mn Express parcel shipments in FY24 YoY: 11.5%"`
- **Evidence B**: *Delhivery Annual Report 2023-24*, Page 6 & Page 36: `"Express parcel shipment volume (million) FY24: 740"` and `"Express parcel shipment volumes increased by 11.48% to 740 million parcels for FY24..."`
- **System Reasoning**: Both documents independently verify the exact same operational metric despite differing visual representations (executive infographic in the presentation vs. formal financial review tables in the Annual Report). Crucially, both documents isolate **Express Parcel shipments** specifically (PTL freight is measured separately in tonnes at 1,429k tonnes), ensuring metric congruence.
- **Secondary Corroboration**: Spoton Logistics acquisition timing (**August 2021**) independently verified across Prospectus 2022 (p. 48) and Annual Report 2023-24 (p. 22).

### 2. Case 2: Genuine / Likely Contradiction
- **Fact Conflict**: Partner Delivery Centers and Total Last-Mile Centers Count as of March 31, 2024.
- **Evidence A**: *Delhivery Earnings Presentation Q4 & FY24*, Page 8, Table 'Key operating metrics':  
  `"Partner centers (constellation/BAs) Q4 FY24: 939"` (with `Express delivery centers: 3,506`, giving Total Last-Mile Centers = **4,445**).
- **Evidence B**: *Delhivery Annual Report 2023-24*, Page 47, Section 'Facility/Plant Location':  
  `"3,506 Direct Delivery Centres | 938 Partner Delhivery Centres"` (giving Total Last-Mile Centers = **4,444**).  
  *(Note: Page 2 of the same Annual Report claims "4,445 Last-mile delivery centres", contradicting its own detailed breakdown on page 47).*
- **System Reasoning**: For the exact same snapshot date (March 31, 2024) and identical operational metric, the documents report **939 vs 938 partner centers** and **4,445 vs 4,444 total last-mile centers**. This is an unambiguous counting contradiction under identical temporal and entity scopes.
- **Supplementary Nuance (Workforce Headcount)**: Director's Report (p. 34) reports 23,381 permanent employees, whereas BRSR (p. 51) reports 18,527 employees + 5,898 workers = 24,425. If defined strictly as employees, 23,381 ≠ 18,527; if combining workers, 23,381 ≠ 24,425. This demonstrates how human capital definitions often blur genuine contradictions with scope boundaries.

### 3. Case 3: Apparent Contradiction Explained by Context
- **Apparent Conflict**: FY24 Revenue is stated as **₹8,142** in one document and **₹81,415.38** in another.
- **Evidence A**: *Delhivery Earnings Presentation Q4 & FY24*, Page 6: `"₹8,142 Cr FY24 revenue from services YoY: 12.7%"`
- **Evidence B**: *Delhivery Annual Report 2023-24*, Page 22: `"The revenue from operations on consolidated basis for FY24 stood at ₹ 81,415.38 million as against ₹72,253.01 million for FY23..."`
- **System Reasoning (Unit Disambiguation)**: Naive token matching treats ₹8,142 and ₹81,415.38 as an order-of-magnitude contradiction. However, the system extracts the contextual currency units:
  - Document A denotes in **Crores** ($1\text{ Cr} = 10,000,000\text{ INR}$).
  - Document B denotes in **Millions** ($1\text{ Million} = 1,000,000\text{ INR}$).
  - Mathematical normalization: $\frac{₹81,415.38\text{ Million}}{10} = ₹8,141.538\text{ Cr} \approx ₹8,142\text{ Cr}$. The apparent contradiction is completely resolved by unit conversion.
- **Secondary Contextual Reconciliation (Scope)**: Annual Report Page 22 discloses Standalone Parent Revenue of **₹74,540.82M** vs. Consolidated Group Revenue of **₹81,415.38M**, reconciled by organizational reporting boundary.

### 4. Case 4: Extraction & Reasoning Failure Analysis
- **Identified Failures in Real Documents**:
  1. *Column Header Order Inversion*: In the Prospectus Proforma Financial Statement (p. 22), the author formatted table headers with Column (D) *Intragroup Elimination* placed BEFORE Column (C) *Acquisition Adjustments*. Standard left-to-right table parsers assume monotonic alphabetical sequences `(A, B, C, D)` and erroneously assign negative eliminations to acquisition adjustments.
  2. *Accounting Parentheses Sign Erasure*: Financial balance sheets represent negative numbers / losses with parentheses e.g. `(4,157.43)`. Standard regex / LLM prompt extractors frequently strip the brackets and treat the number as positive `+4,157.43`, completely corrupting profit margin reasoning.
- **System Fix Implemented**:
  - Built an **Accounting-Aware Lexer** that treats outer parentheses in numeric tabular contexts as strict negative sign indicators.
  - Implemented **Two-Pass Formula-Constraint Matching** that reads the mathematical footnote equations (e.g., `E = C + D` and `F = A + B + E`) to bind columns by mathematical consistency rather than visual position.

---

## 🏛️ Approach and Architecture

### System Architecture
```
  [ Upload PDF via UI / REST API ]
                 │
                 ▼
  [ PyMuPDF Text & Layout Extractor ]  ──> Extracts page text with coordinate & offset indexing
                 │
                 ▼
     [ Gemini LLM Fact Engine ]        ──> Extracts structured atomic facts with verbatim quotes
                 │
                 ▼
     [ SQLite Knowledge Store ]       ──> Persists documents, facts, and relations incrementally
                 │
                 ▼
 [ Cross-Document Reconciler Engine ] ──> Generic entity matching, unit & scope normalization, reasoning
                 │
                 ▼
    [ Modern Web UI & REST API ]      ──> Vis.js interactive graph, 4-case showcase, evidence modal
```

### Core Design Decisions & Trade-Offs
1. **Zero Hardcoded Documents or Company Rules**: The extraction and reconciliation logic contains **zero hardcoded company names, zero document filenames, and zero document-specific heuristics**. Any unseen PDF uploaded to `/api/upload` is processed generically through the LLM extraction prompt and universal unit/scope reconciliation engine.
2. **Pydantic Structured Schema over Free-form Extraction**: Every fact is constrained to an atomic schema (`subject`, `predicate`, `value`, `normalized_value`, `unit`, `temporal_period`, `entity_scope`, `exact_quote`, `page_number`). This prevents hallucination and guarantees verifiable evidence.
3. **Deterministic Context Normalization + LLM Semantic Reasoning**: Financial conversions (Crores, Millions, Billions, Lakhs, Thousand, tonnes) are verified mathematically to eliminate LLM arithmetic errors, while Gemini synthesizes semantic explanations for corporate actions.
4. **Incremental Knowledge Updates (Brownie Point)**: Uploading a new PDF does not wipe existing knowledge. The system ingests the new document, extracts its facts, and cross-compares only the new facts against the existing index.
5. **Responsive Frontend without Build Overhead**: Built with modern Tailwind CSS, Lucide icons, and Vis.js. Zero `npm install` complications or Node version conflicts; runs directly via FastAPI static mounting.

---

## ⚠️ Limitations and Next Steps

### Current Limitations
- **Scanned Image OCR**: Current ingestion assumes text-layer PDFs (using PyMuPDF). Pure image-only scans require an OCR pre-processor like Tesseract or Google Cloud Vision.
- **Massive Table Complexities**: Deeply nested multi-line table headers with rotated text can still pose layout ambiguity.

### Next Steps
- **Graph RAG with Vector Embeddings**: Integrate ChromaDB or FAISS to retrieve semantic neighborhoods before LLM reconciliation across thousands of documents.
- **Visual Bounding-Box Highlighting**: Render PDF page canvases in the browser with visual bounding-box highlights over the exact quote coordinates.
- **Multi-Hop Automated Dispute Resolution**: Expand the reconciliation engine to chain multi-step deduction (e.g. Doc A implies X, Doc B implies Y, therefore Doc C is impossible).

---

## 📝 Additional Notes
- **Generalization Guarantee**: The ingestion engine accepts any generic PDF through `POST /api/upload`. The pre-seeded starter facts are provided solely to guarantee an immediate, frictionless demonstration of the 4 Superjoin evaluation criteria.
- **Security & Privacy**: Credentials are kept strictly out of git (`.env` is excluded). All sample outputs are available in `samples/sample_cases.json`.