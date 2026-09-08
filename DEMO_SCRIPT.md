# 3-Minute Video Demo Script
### Superjoin Hiring Assignment: Fact Knowledge Layer

> **Tip for Recording**: Use [Loom](https://www.loom.com/) or OBS. Keep the video under 3 minutes as requested in the assignment instructions. Follow the timing marks and click-by-click actions below.

---

### [0:00 - 0:25] Introduction & Overview
- **Action**: Start in the browser at `http://127.0.0.1:8000`. Point to the masthead title, subtitle, and Gemini runtime status indicator.
- **Narration**:  
  *"Hi everyone, this is my submission for the Superjoin Fact Knowledge Layer assignment. Corporate and macroeconomic facts are scattered across annual reports, investor decks, and prospectuses—stated in different units, timeframes, or sometimes directly conflicting. I built this generalized Fact Knowledge Layer using Python, FastAPI, SQLite, and Google Gemini with an editorial publication UI to extract, ground, and reconcile claims with zero hardcoded company rules."*

---

### [0:25 - 1:05] The 4 Required Cases (Docket View)
- **Action**: Stay on the default **"Cases"** tab. Scroll through each docket card, pointing to the side-by-side exhibits and relation symbols (`≈`, `≠`, `≠*`).
- **Narration**:  
  - **Case 1 (Corroboration `≈`)**:  
    *"Case 1 shows independent cross-document corroboration: both the Q4 FY24 Earnings Presentation (p. 6) and the FY24 Annual Report (p. 6) report 740 million express parcel shipments. Both isolate express parcel volume, verified by grounded quotes."*
  - **Case 2 (Contradiction `≠`)**:  
    *"Case 2 is a genuine contradiction: as of March 31, 2024, the Annual Report reports 939 partner centers, whereas the Earnings Presentation reports 938 partner centers nationwide. A direct counting conflict for the exact same date without explanatory footnotes."*
  - **Case 3 (Reconciled by Context `≠*`)**:  
    *"Case 3 shows an apparent conflict reconciled by context: on page 22 of the Annual Report, Consolidated revenue is ₹81,415.38 million while Standalone revenue is ₹74,540.82 million. Because reporting scope is tracked, our engine resolves this as different valid scopes rather than disagreement."*
  - **Case 4 (Extraction & Failure Analysis `—`)**:  
    *"Case 4 analyzes real-world extraction limits: rotated table images and accounting parentheses notation like (8,987.45) causing negative loss figures to be stripped. We resolved this via mathematical equation matching and accounting-aware parsing."*

---

### [1:05 - 1:40] Knowledge Graph & Interactive Claim Inspector
- **Action**: Click the **"Knowledge graph"** tab. Point out the dark document nodes, fact spokes, and colored relationship links. Click on any fact node to populate the **Inspected Claim** card on the right, then click **"View full evidence →"** to open the modal.
- **Narration**:  
  *"In the Knowledge Graph tab, you can visually explore the entity-fact network. Spoke lines connect filings to their grounded facts, and colored links highlight cross-document relationships: green for corroborations, rust for contradictions, and ochre for reconciled claims. Clicking any node or link displays the verbatim quote and page location in the inspector card with zero visual clutter."*

---

### [1:40 - 2:40] Uploading Any PDF & Where to See Results
- **Action**: Click the **"Add a document"** tab. Drag-and-drop a PDF or select a file, show the processing progress bar. Then navigate through **Facts**, **Knowledge graph**, **Ask**, and **Cases** as you narrate where the results appear.
- **Narration**:  
  *"The system accepts any new PDF. When you upload a document, it extracts structured claims using Gemini—or its deterministic fallback—and incrementally cross-reconciles against existing facts.*

  *Here is exactly where to see the results across the dashboard:*
  - **Tab 3: Facts (The Fact Ledger)**: *Click the Facts tab, select your newly uploaded document in the dropdown filter, and you will see every extracted fact with its stated value, category, and page number. Clicking 'View quote' opens the modal with the verbatim PDF excerpt.*
  - **Tab 2: Knowledge graph**: *Click the Knowledge graph tab and select your new document in the Focus filter at the top. The graph instantly centers on this document with all its extracted claims radiating outward as spokes.*
  - **Tab 4: Ask**: *In the Ask tab, you can ask natural-language questions about the newly uploaded document. Gemini synthesizes answers strictly grounded in the extracted facts, with direct document and page citations.*
  - **Tab 1: Cases**: *If any newly extracted fact corroborates, contradicts, or reconciles with an existing filing, it automatically surfaces in Live graph cases."*

---

### [2:40 - 3:00] Generalized Architecture & Conclusion
- **Action**: Click the **"Gemini Active ⚙"** badge in the header to show runtime API key configuration, and briefly mention the clean FastAPI REST API.
- **Narration**:  
  *"The backend is built with FastAPI and SQLite, runs in worker threadpools for non-blocking performance, and provides complete REST endpoints and automated test suites. The engine is completely generalized, modular, and ready for production. Thank you, and I look forward to your thoughts!"*