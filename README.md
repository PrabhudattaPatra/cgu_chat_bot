# 🎓 CGU Odisha AI Assistant 🤖

This is an AI-powered assistant built for **C.V. Raman Global University (CGU), Odisha**. The assistant is designed to help students, parents, faculty, and visitors get accurate and up-to-date information about:

- 📌 Admissions
- 🎓 Academic Programs
- 💰 Fee Structures
- 🧠 Scholarships
- 🧑‍💼 Placements
- 🏫 Hostel & Campus Facilities
- 🌐 Contact Details
- 📆 Important Dates (CGET 2025)

It uses PDF-based knowledge retrieval + web search from official sources to ensure **fully verifiable answers**.

---

## 🚀 Features

- 🔍 Answers only from verified sources: CGU PDFs, official website, and Collegedunia
- 📄 Integrates with `PDFKnowledgeBase` using `pgvector` + OpenAI embeddings
- 💬 Built with `AGNO` AI agent framework and `OpenAI GPT-4o-mini`
- 🧠 Memory and context-aware conversation using PostgreSQL
- 📈 Streamlit interface for real-time Q&A

---

## 🧱 Tech Stack

- [flask]([(https://flask.palletsprojects.com/en/stable/)]) – Web UI
- [AGNO](https://github.com/agnonetwork/agno) – LLM Agent Framework
- [OpenAI GPT-4o-mini](https://openai.com/) – AI Model
- [pgvector](https://github.com/pgvector/pgvector) – Vector database
- PostgreSQL – Memory & PDF embedding storage
- PDF Knowledge Base – Admission brochures, fee structure, and important dates

---
