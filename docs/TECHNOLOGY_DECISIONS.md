# Technology decisions

| Decision | Choice | Requirement served | Alternative | Trade-off / replacement condition |
|---|---|---|---|---|
| Backend | FastAPI | typed API, validation, OpenAPI | Flask | Flask is smaller; FastAPI gives stronger request/response models |
| Demo DB | SQLite | zero-cost reproducibility and read-only demo | PostgreSQL | move when multi-user concurrency or dialect realism matters |
| SQL parser | SQLGlot 30.x | AST governance | regex/sqlparse | regex is not a reliable SQL policy boundary |
| Local LLM | Ollama + Qwen2.5-Coder 7B default | offline/local, no mandatory hosted API | llama.cpp, larger Qwen | change the model when hardware/quality measurements justify it |
| Cloud LLM default | Gemini 3.5 Flash | recruiter-facing hosted inference | Flash-Lite, Groq | provider is configurable; compare measured accuracy/latency before claiming superiority |
| Cloud LLM alternative | Groq + Qwen 3.6 27B | second hosted path using an open-weight model family | other Groq-supported models | useful fallback if Gemini quota/model availability changes |
| Provider integration | small `httpx` clients + protocol/factory | avoids heavy SDK/framework coupling | provider SDKs | switch if provider SDK materially improves reliability or auth support |
| Baseline retrieval | custom BM25-style scorer | explainable baseline | TF-IDF library | custom code is small enough to teach and measure |
| Advanced retrieval | Sentence Transformers | semantic schema matching | API embeddings | local model keeps semantic mode independent from hosted LLM provider |
| Vector search | NumPy exact cosine | small schema | FAISS/Chroma | add ANN only after schema scale makes linear search material |
| Cloud retrieval default | lexical | low RAM/cold-start cost on free preview | Sentence Transformers | use semantic on larger infrastructure after measured gain |
| UI | Streamlit | fast recruiter demo | React | React becomes justified for a more polished production UX |
| Hosted API protection | shared `X-QueryGuard-Key` | blocks direct anonymous backend usage in preview | OAuth/JWT | replace with real identity + rate limiting for production |
| Orchestration | plain service class | deterministic, understandable pipeline | LangChain/agent framework | agents add unnecessary nondeterminism for this task |
| Local deployment | Docker Compose | reproducibility | Kubernetes | K8s is overengineering for a portfolio modular monolith |
| Preview backend | Render Blueprint | GitHub-driven FastAPI deployment | Fly.io/Railway/cloud VM | replace based on resource limits or production requirements |
| Preview frontend | Streamlit Community Cloud | GitHub-connected hosted UI | same Render service/React host | replace when UX, scaling, or auth requirements grow |

## Why no agent

The workflow is mostly deterministic and security-sensitive. A fixed pipeline makes retries bounded, control flow auditable, tests simpler, and accidental tool use less likely. An agent would create complexity without solving a demonstrated requirement.

## Why no vector database

Chinook has only a small number of schema documents. Exact matrix similarity is easy to explain and fast. A vector database would add persistence/configuration/network concepts before the project proves it needs them.

## Why multiple LLM providers

The project requirement is governance around Text-to-SQL, not dependence on one vendor. The provider interface keeps the same retrieval, SQL validation, execution, evaluation, and UI pipeline while allowing:

- Ollama for local/offline demonstrations;
- Gemini for the default lightweight hosted preview;
- Groq/Qwen as an optional hosted alternative.

This is intentionally a small adapter layer rather than a generic multi-provider framework.
