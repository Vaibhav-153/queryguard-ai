# Hiring Package

Use only after confirming the linked repository/demo reflects the final code.

## Workday project title

**QueryGuard AI — Governed Data & Document Intelligence Platform**

Role: Individual Developer / GenAI & Python Engineering Portfolio Project

Team size: 1

## 300-character description

Built QueryGuard AI, a FastAPI/Streamlit platform for governed Text-to-SQL over SQLite/Excel/CSV, cited PDF/DOCX/PPTX Q&A, and invoice analytics. Added SQLGlot safety, read-only execution, retrieval evaluation, Ollama/Gemini/Groq support, tests, Docker, and CI.

## 600-character description

Designed and implemented QueryGuard AI, a multi-source GenAI analytics platform. Structured data uses schema retrieval, LLM Text-to-SQL, SQLGlot AST validation, table allowlists, SQLite read-only execution, bounded repair, and result exports. Documents use source-aware extraction, chunk retrieval, and cited answers. Invoice mode normalizes fields into SQLite and preserves text evidence. Added temporary upload workspaces, FastAPI, Streamlit, Ollama/Gemini/Groq provider abstraction, pytest security/integration tests, Docker, GitHub Actions, deployment guides, and measured component evaluations.

## Resume one-liner

Built a governed GenAI analytics platform combining safe Text-to-SQL, cited document retrieval, and hybrid invoice analysis with FastAPI, Streamlit, SQLGlot, SQLite, Ollama/Gemini/Groq, automated tests, Docker, and CI.

## Resume bullets

- Engineered a Text-to-SQL pipeline with schema retrieval, SQLGlot AST validation, active-schema table allowlists, SQLite read-only execution, timeout/row controls, and one bounded repair attempt.
- Extended the platform to temporary SQLite/Excel/CSV workspaces, source-cited PDF/DOCX/PPTX retrieval, and invoice normalization with manual-review flags and downloadable CSV/XLSX/report outputs.
- Built reproducible evaluation/testing/deployment workflows; measured Chinook schema retrieval at Recall@3 **0.967** and documented synthetic document/invoice component results separately from untested LLM/OCR claims.

## LinkedIn description

QueryGuard AI is my end-to-end GenAI/Python portfolio project focused on trustworthy analytics rather than a single chatbot call. It supports governed natural-language analytics over SQLite, Excel and CSV; evidence-grounded questions over PDF, Word and PowerPoint; and hybrid invoice analytics. I implemented schema/document retrieval, LLM provider abstraction, SQL AST safety, read-only execution, temporary upload isolation, tests/evaluation, FastAPI, Streamlit, Docker, GitHub Actions, and local/hosted deployment options. Chinook remains the reproducible demo while users can temporarily analyze their own compatible files.

## Skills

Python, FastAPI, Streamlit, SQL, SQLite, SQLGlot, Text-to-SQL, RAG, information retrieval, pandas, openpyxl, PyMuPDF, python-docx, python-pptx, Ollama, Gemini API, Groq API, pytest, Docker, GitHub Actions, security, evaluation.

## 5-minute demo sequence

1. Open home screen and explain the four modes.
2. Use Chinook demo: “Show the top 5 customers by revenue.”
3. Show retrieved schema, generated SQL, governance checks, result, download.
4. Upload a small Excel/SQLite source and show dynamic schema.
5. Upload a short PDF/DOCX/PPTX and show evidence-cited answer.
6. Show invoice normalized records and `needs_review` concept.
7. End on architecture/evaluation/limitations.

Backup plan: if the hosted LLM/provider is unavailable, use demo mode to show the deterministic governed SQL pipeline and repository evaluation/results screenshots. Do not fake a live model result.
