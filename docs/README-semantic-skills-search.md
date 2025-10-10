# Semantic Skills Search — Architecture & Decision README

> **Purpose:** capture requirements, compare solution options, and record the chosen phased path for building **natural‑language semantic search** across a hierarchical skills taxonomy (L1 → L4) stored today as JSON files in S3.

---

## Table of Contents
- [Semantic Skills Search — Architecture \& Decision README](#semantic-skills-search--architecture--decision-readme)
  - [Table of Contents](#table-of-contents)
  - [Capability Context \& Examples](#capability-context--examples)
  - [Requirements Summary](#requirements-summary)
  - [Solution Options (overview)](#solution-options-overview)
    - [Option 1 — Direct Keyword Search ️🔎](#option-1--direct-keyword-search-️)
    - [Option 2 — Localised Vector Database (POC) 🧭](#option-2--localised-vector-database-poc-)
    - [Option 3 — S3 Vector Buckets (AWS Native) ☁️](#option-3--s3-vector-buckets-aws-native-️)
    - [Option 4 — Managed Vector DB (Pinecone, Qdrant, OpenSearch Vector) ⚙️](#option-4--managed-vector-db-pinecone-qdrant-opensearch-vector-️)
    - [Option 5 — LLM‑Orchestrated Hybrid Search 🤖](#option-5--llmorchestrated-hybrid-search-)
  - [Recommended Path Forward — Phased Plan](#recommended-path-forward--phased-plan)
  - [Per‑option Pros \& Cons (Quick Reference Tables)](#peroption-pros--cons-quick-reference-tables)
    - [Option 1 — Direct Keyword Search 🔎](#option-1--direct-keyword-search-)
    - [Option 2 — Localised Vector DB (POC) 🧭](#option-2--localised-vector-db-poc-)
    - [Option 3 — S3 Vector Buckets ☁️](#option-3--s3-vector-buckets-️)
    - [Option 4 — Managed Vector DB ⚙️](#option-4--managed-vector-db-️)
    - [Option 5 — LLM‑Orchestrated Hybrid 🤖](#option-5--llmorchestrated-hybrid-)
  - [Implementation Notes \& Data Modeling Guidance](#implementation-notes--data-modeling-guidance)
    - [Recommended indexing model (pragmatic)](#recommended-indexing-model-pragmatic)
    - [How to store user profiles](#how-to-store-user-profiles)
    - [Explainability](#explainability)
  - [Costs \& Operational Notes (Indicative)](#costs--operational-notes-indicative)
  - [Next Steps / Action Items](#next-steps--action-items)

---

## Capability Context & Examples

You want users to be able to search in **natural language** for skills or capabilities — for example:

- **“Who can design secure serverless architectures on AWS?”**  
- **“Show me people experienced with multi-cloud cost optimization.”**  
- **“Find experts in Kubernetes and Terraform for cloud migration projects.”**

…and have the system return a **ranked list of users** whose selected skills match (semantically) that intent, even when the query wording doesn't exactly match the skill titles or hierarchy. The UI should let the searcher inspect each candidate’s selected skill tree (L1→L4) and ideally ask follow‑up questions to narrow results.

---

## Requirements Summary

<span style="background-color:#E8F5E9; padding:4px 8px; border-radius:6px;">**Key points**</span>

- **Scale:** hundreds to ~1,000 users; hundreds of skill nodes.  
- **Latency:** not critical — seconds are acceptable.  
- **Deployment:** final app will be hosted in AWS; POC may run locally.  
- **Updates:** skill tree rarely changes; user skills update weekly.  
- **Explainability:** beneficial but not mandatory; follow‑up conversational flow is valuable.  
- **Users:** multiple concurrent searchers in production (technical directors initially for POC).  
- **POC constraint:** quick to implement, but architecturally aligned to scale.

---

## Solution Options (overview)

Below are the approaches we considered. Each option includes a short description, a plain‑English approach, pros/cons and an indicative cost note. Detailed pros/cons tables appear later for quick scanning.

---

### Option 1 — Direct Keyword Search ️🔎

**Short description:** simple keyword / tag index (DynamoDB, OpenSearch text index, or local JSON index). No ML required.

**How it fits the problem:** Map skill/technology names → users and do keyword/fuzzy matches. Good first step to deliver immediate functionality.

---

### Option 2 — Localised Vector Database (POC) 🧭

**Short description:** download user JSONs from S3, generate embeddings (local or cloud API), and store them in a lightweight local vector DB (Chroma, LanceDB, FAISS, Milvus Lite). Useful for technical directors to run a POC and iterate quickly.

**How it fits the problem:** Brings semantic matching to the POC stage without the operational overhead of a managed vector service. Good for testing embeddings, ranking logic, and conversational prompts.

---

### Option 3 — S3 Vector Buckets (AWS Native) ☁️

**Short description:** use AWS S3 vector buckets to store embeddings alongside objects for native vector search inside S3 (serverless).

**How it fits the problem:** Seamlessly integrates with existing S3-based storage and reduces operational footprint by keeping vectors where your JSON already lives.

---

### Option 4 — Managed Vector DB (Pinecone, Qdrant, OpenSearch Vector) ⚙️

**Short description:** use a managed vector store to host embeddings and metadata. Sync embeddings into the vector DB and query for semantic results with metadata filters.

**How it fits the problem:** Production-ready, scalable, low-latency, supports metadata filtering, incremental updates, concurrency.

---

### Option 5 — LLM‑Orchestrated Hybrid Search 🤖

**Short description:** combine a vector search with an LLM that parses the query, expands/filters intent, and re-ranks results — enabling conversational follow-ups and explanations.

**How it fits the problem:** Most flexible and user-friendly, ideal when follow-up questions and justifications are prioritized.

---

## Recommended Path Forward — Phased Plan

Below is a concrete, independently explained phased plan. Each phase describes WHAT to implement, WHY it adds value, NEW COMPONENTS introduced, and RATIONALE for moving to the next phase.

| Phase | What to implement | New components / changes | Value add / Rationale |
|---:|---|---|---|
| **Phase 1 — Keyword Search MVP** | Implement a keyword/tag index that maps skills & technologies → user IDs and supports fuzzy matches. | - Lightweight index (DynamoDB / OpenSearch / local JSON) <br> - Simple search API endpoint | Delivers a fast, low-effort prototype to validate UI and flow. Useful for recruiters to test retrieval and for collecting query examples. Low cost and minimal ops. |
| **Phase 2 — Localised Vector DB (POC)** | Build a local POC that pulls user JSONs from S3, generates embeddings, and indexes them in a local vector DB. Provide scripts and a README so technical directors can reproduce. | - Embedding scripts (Python) <br> - Local vector DB (Chroma / LanceDB / FAISS) <br> - Small web UI or CLI for query testing | Adds true semantic matching to validate embedding model choices and ranking heuristics. Enables iteration on prompt/LLM-based explanations and follow-ups. Keeps POC close to production semantics without cloud ops. |
| **Phase 3 — Migrate to S3 Vector Buckets (AWS)** | Move embedding storage & query to S3 Vector Buckets for scalable, managed vector search (or use OpenSearch Vector). | - Vector index hosted in S3 Vectors <br> - Sync/ingest pipeline (Lambda / batch job) <br> - Profile store (DynamoDB or DocumentDB) | Reduces operational burden by using an AWS-native vector service. Easier to integrate with Bedrock and other AWS services for conversational agents. |
| **Phase 4 — Managed Vector DB Integration** | If needed for performance/flexibility, migrate to a managed vector DB (Pinecone / Qdrant / OpenSearch Vector). | - Managed vector service <br> - Incremental update pipeline <br> - Monitoring & autoscaling | Provides lower-latency queries, advanced filtering, and high concurrency. Good for production traffic at scale. |
| **Phase 5 — LLM Hybrid & Conversational Layer** | Add an LLM-driven orchestration layer for parsing queries, reranking candidates, and enabling conversational follow-ups. | - LLM orchestration service (Bedrock / OpenAI) <br> - Knowledge base & agentization <br> - UI conversation flow & provenance display | Elevates UX with natural follow-up, explanations, and richer filtering by intent. Enables advanced recruiter workflows and decision support. |

> **Notes on this path:** Phase 2 is intentionally local and reproducible so technical directors can experiment without AWS costs; Phases 3–5 progressively reduce ops or improve UX and scale.

---

## Per‑option Pros & Cons (Quick Reference Tables)

### Option 1 — Direct Keyword Search 🔎

| ✅ Pros | ❌ Cons |
|---|---|
| Very fast to implement and cheap | No semantic understanding |
| Simple to explain and debug | Poor recall for paraphrases/synonyms |
| Low operational overhead | Hard to rank by semantic closeness |

---

### Option 2 — Localised Vector DB (POC) 🧭

| ✅ Pros | ❌ Cons |
|---|---|
| Quick POC delivery with semantic power | Not ideal for concurrent multi-user production |
| Easy to iterate embedding/ranking choices | Requires manual refresh / reindex scripts |
| Low cost (local compute only) | Limited persistence/scale on same machine |

---

### Option 3 — S3 Vector Buckets ☁️

| ✅ Pros | ❌ Cons |
|---|---|
| Serverless and integrated with S3 | Feature maturity / preview limitations |
| Low ops overhead and cost-efficient | May require reformatting data for indexing |
| Easy Bedrock integration | Regional availability caveats |

---

### Option 4 — Managed Vector DB ⚙️

| ✅ Pros | ❌ Cons |
|---|---|
| Scales easily, low-latency | Monthly service costs |
| Rich metadata filtering & indexing | Adds vendor integration complexity |
| Incremental updates & production readiness | Slightly more setup than S3 Vectors |

---

### Option 5 — LLM‑Orchestrated Hybrid 🤖

| ✅ Pros | ❌ Cons |
|---|---|
| Best UX (follow-ups, explanations) | Highest cost and complexity |
| Easily handles complex intent | Requires prompt engineering & monitoring |
| Powerful for ambiguous/compound queries | More components to secure & scale |

---

## Implementation Notes & Data Modeling Guidance

### Recommended indexing model (pragmatic)
- **Per‑user, per‑skill embedding model:** create embeddings at two granularities:
  - **Generic-skill level (L3)** — captures the user’s proficiency & context for each Generic Skill.
  - **User-level aggregate** — a consolidation of top skills to support broader matching queries.
- **Metadata to attach to each vector:** `userId`, `l3Id`, `rating` (Beginner/Intermediate/Advanced), `topTechnologies` (list), `lastUpdated`.
- **Query flow:** embed query → retrieve candidate vectors → dedupe & aggregate by `userId` → fetch full user profile → final re-rank using a small scoring function: `combined_score = α * vector_score + β * normalized_skill_rating + γ * tech_match_score`.

### How to store user profiles
- Keep canonical **skills-master.json** as the source of truth (S3).
- Use a small DB (DynamoDB or DocumentDB) to serve full profiles to the UI (helps quick reads), while vectors live in S3 Vectors or vector DB.

### Explainability
- For each match, return the matched `l3Id` or `l4Id` and highlight matching keywords in the UI. If using an LLM re-ranker, request a short justification sentence.

---

## Costs & Operational Notes (Indicative)

- **Phase 1 (Keyword):** <$20/month for serverless hosting & index.  
- **Phase 2 (Localised Vector POC):** local compute only; negligible cloud costs.  
- **Phase 3 (S3 Vectors):** modest — storage + request fees (low tens to low hundreds USD monthly depending on queries).  
- **Phase 4 (Managed Vector DB):** $50–$300+/month depending on provider and scale.  
- **Phase 5 (LLM Hybrid):** highest; depends on LLM usage — expect growth with query volume (hundreds to thousands USD/month at scale).

---

## Next Steps / Action Items

1. **POC tasks (Phase 1 → Phase 2):**
   - Implement keyword index and UI for quick feedback.  
   - Run local vector POC using a representative slice of data (100–200 users).  
   - Produce metrics: precision @ K, qualitative assessments of result relevance.

2. **Evaluate embedding model:**
   - Compare embedding providers (OpenAI, local HuggingFace models) using the same POC dataset.

3. **Roadmap to AWS:**
   - If POC is promising, prepare ingest pipeline & IAM roles to move vectors into S3 Vectors or a managed vector DB.

4. **UX decisions:**
   - Decide on conversational follow-up flow vs faceted UI controls.

---
