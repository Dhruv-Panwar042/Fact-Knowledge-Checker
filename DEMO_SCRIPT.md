# 3-Minute Video Demo Script
### Superjoin Hiring Assignment: Fact Knowledge Layer

> **Tip for Recording**: Use [Loom](https://www.loom.com/) or OBS. Keep the video under 3 minutes as requested in the assignment instructions. Follow the timing marks below.

---

### [0:00 - 0:30] Introduction & Problem Overview
- **Action**: Start on the browser at `http://localhost:8000`. Point to the header and top stats bar.
- **Narration**:  
  *"Hi everyone, this is my submission for the Superjoin Fact Knowledge Layer assignment. Corporate facts are often scattered across filings, annual reports, and investor presentations—stated in different units, different timeframes, or sometimes contradicting each other. I built this Fact Knowledge Layer using Python, FastAPI, Google Gemini API, and an interactive knowledge graph to extract, ground, and reconcile facts across documents."*

---

### [0:30 - 1:15] Showcase of the 4 Required Cases
- **Action**: Stay on the default **"The 4 Required Cases"** tab. Scroll through each of the 4 cards.
- **Narration**:  
  - **Case 1 (Corroboration)**:  
    *"Case 1 shows a fact corroborated across documents. In the Q4 FY24 Earnings Presentation on page 6, Delhivery reports 740 million express parcel shipments. The FY24 Annual Report on page 6 corroborates this exact figure. The system verifies this claim with grounded verbatim quotes."*
  - **Case 2 (Genuine Contradiction)**:  
    *"Case 2 highlights a genuine contradiction. In the 2024 Annual Report's Director's Report on page 34, permanent employees are stated as 23,381. But in the BRSR section on page 51, permanent employees and workers sum to 24,425—an unresolved difference of 1,044 personnel without an explanatory note."*
  - **Case 3 (Apparent Contradiction Reconciled by Context)**:  
    *"Case 3 demonstrates an apparent contradiction resolved by context. The Earnings Presentation reports FY24 revenue of 8,142 Crores, while the Annual Report reports 81,415.38 Million. Naive matching would flag this as conflicting, but our engine normalizes the units—1 Crore equals 10 Million—showing they are mathematically identical."*
  - **Case 4 (Extraction & Reasoning Failure Analysis)**:  
    *"Case 4 explains an extraction failure we discovered: in the IPO Prospectus Proforma table, Column D (intragroup eliminations) was placed before Column C (adjustments), causing naive tabular parsers to flip values. Furthermore, accounting parentheses like (4,157.43) are often parsed as positive. We solved this with a two-pass equation-constrained parser and accounting-aware lexer."*

---

### [1:15 - 1:55] Knowledge Graph & Fact Explorer
- **Action**: Click the **"Knowledge Graph"** tab, hover over nodes and edges. Click on a fact node to open the **Evidence Inspector Modal**.
- **Narration**:  
  *"Here in the Knowledge Graph tab, you can visually explore documents connected to their extracted facts. Green edges represent corroborated claims, red dashed lines represent contradictions, and amber edges represent contextually reconciled facts. Clicking any node opens the Evidence Inspector, which displays the exact verbatim quote and page number from the source document."*

---

### [1:55 - 2:35] Live Upload & Incremental Ingestion
- **Action**: Switch to the **"Upload New PDF"** tab. Drop a PDF file or demonstrate the upload. Then switch to **"Ask Knowledge Layer"** and run a query like `What was the FY24 revenue?`.
- **Narration**:  
  *"The system is completely general and accepts any new PDF via drag-and-drop or REST API. When a new document is uploaded, it extracts structured facts using Gemini and incrementally compares them against existing knowledge without wiping previous facts. You can also ask natural language questions in the 'Ask Knowledge Layer' tab, which provides answers strictly grounded in verified facts with citations."*

---

### [2:35 - 3:00] Architecture & Conclusion
- **Action**: Switch briefly to `http://localhost:8000/docs` to show the clean Swagger REST API.
- **Narration**:  
  *"The backend is built with FastAPI with complete REST endpoints for upload, extraction, and graph traversal. The code is modular, well-tested, and ready for evaluation. Thank you, and I look forward to your feedback!"*