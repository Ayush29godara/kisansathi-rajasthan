# KisanSathi Rajasthan — Knowledge Base Documents Directory (`data/kb_docs/`)

This directory is the storage location for official agricultural reference documents used by the **KisanSathi RAG (Retrieval-Augmented Generation)** knowledge pipeline.

---

## 1. What Documents to Supply

Please place official, verified agricultural package-of-practices and scientific manuals here. Recommended authentic sources include:

1. **ICAR & CAZRI Publications**:
   - Central Arid Zone Research Institute (CAZRI), Jodhpur manuals on arid/semi-arid crops (Bajra, Guar, Moth, Moong, Mustard).
2. **State Agriculture University (SAU) Package of Practices**:
   - Swami Keshwanand Rajasthan Agricultural University (SKRAU), Bikaner
   - Maharana Pratap University of Agriculture and Technology (MPUAT), Udaipur
   - Agriculture University, Kota (AU Kota)
   - Sri Karan Narendra Agriculture University (SKNAU), Jobner
3. **Department of Agriculture, Government of Rajasthan**:
   - Krishi Diary / Package of Practices (कृषि दर्शिका / रबी एवं खरीफ पैकेज ऑफ प्रैक्टिसेज).
   - District Krishi Vigyan Kendra (KVK) advisory bulletins.

---

## 2. Supported File Formats

- **PDF Documents (`.pdf`)**: Scanned text must be machine-readable (text-based PDF, not pure image scans).
- **Plain Text (`.txt`)**: UTF-8 encoded text files.
- **Markdown (`.md`)**: Structured Markdown files with headings (`#`, `##`).

---

## 3. Recommended Naming Convention

Use clear, descriptive filenames indicating crop, region, and source:
```
data/kb_docs/
  ├── ICAR_CAZRI_Bajra_Practices_Rajasthan.pdf
  ├── SKRAU_Mustard_Disease_Management_2025.txt
  ├── Rajasthan_Govt_Wheat_Package_of_Practices.pdf
  ├── KVK_Kota_Soybean_Pest_Control.txt
  └── README.md
```

---

## 4. Ingestion & Embedding Pipeline

Once you place your documents in this directory, run the automated ingestion script:

```bash
# 1. Test document parsing and chunking without calling external APIs (Dry Run):
python scripts/build_kb.py --input-dir data/kb_docs --dry-run

# 2. Ingest into Supabase with Gemini 768-dim embeddings:
# (Requires GEMINI_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY in .env)
python scripts/build_kb.py --input-dir data/kb_docs
```

The script:
- Extracts text page-by-page.
- Splits into ~400-word chunks with 100-word context overlap.
- Detects language (Hindi `hi` / English `en`).
- Calls Gemini's `embedding-001` REST endpoint to obtain 768-dimensional dense vectors.
- Upserts rows with metadata (`source`, `doc_title`, `chunk_text`, `embedding`, `language`) into the Supabase `kb_chunks` table.

---

## 5. RAG Evaluation

To benchmark grounded answers against unassisted Gemini responses on the sample question set:
```bash
python scripts/evaluate_rag.py --eval-file data/rag_eval_questions.csv --output data/rag_evaluation_results.csv
```
