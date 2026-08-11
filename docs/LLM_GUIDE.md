# LLM Provider Guide

QueryGuard uses one provider at a time. The core pipeline does not change when the provider changes.

## Common interface

Real providers implement:

```python
complete(prompt, system_prompt, max_tokens) -> str
```

SQL-specific prompting is handled by `LLMSQLGenerator`; document prompts are handled by `DocumentService`. This prevents provider code from owning business logic.

## 1. Demo provider

Configuration:

```text
QUERYGUARD_LLM_PROVIDER=demo
```

Purpose:

- CI;
- smoke testing;
- deterministic Chinook examples;
- verifying UI/API/database plumbing without network access.

It is **not an AI model** and should not be used to judge Text-to-SQL quality on arbitrary uploaded data.

## 2. Ollama — recommended local/offline path

Ollama runs a model on the user's own machine and exposes a local HTTP server.

Recommended starting model for this project:

```bash
ollama pull qwen2.5-coder:7b
```

Configuration:

```text
QUERYGUARD_LLM_PROVIDER=ollama
QUERYGUARD_OLLAMA_BASE_URL=http://localhost:11434
QUERYGUARD_OLLAMA_MODEL=qwen2.5-coder:7b
```

Then restart FastAPI.

### How the connection works

```text
QueryService / DocumentService
        ↓
llm/factory.py
        ↓
OllamaLLM
        ↓ HTTP POST /api/chat
localhost:11434
```

### Changing the local model

Pull another compatible chat/instruction model:

```bash
ollama pull <model-name>
```

Then change:

```text
QUERYGUARD_OLLAMA_MODEL=<model-name>
```

No source-code edit is necessary.

### Hardware note

Model memory/performance depends on model size and quantization. A smaller model is easier to run; a larger model may improve SQL/document reasoning but needs more RAM/VRAM. Benchmark the exact model before claiming improvement.

## 3. Gemini — recommended hosted demo

Current project default:

```text
QUERYGUARD_LLM_PROVIDER=gemini
QUERYGUARD_GEMINI_MODEL=gemini-3.5-flash
```

Create a Gemini API key in Google AI Studio, then set it only in `.env` locally or deployment secrets:

```text
QUERYGUARD_GEMINI_API_KEY=your-secret-value
```

Never add the real value to GitHub.

The REST client uses the Gemini `generateContent` API and the `x-goog-api-key` header.

Official model/API documentation:

```text
https://ai.google.dev/gemini-api/docs/models
https://ai.google.dev/api
```

Provider quotas/pricing change over time; verify them before deploying.

## 4. Groq — hosted alternative

Configuration:

```text
QUERYGUARD_LLM_PROVIDER=groq
QUERYGUARD_GROQ_MODEL=qwen/qwen3.6-27b
QUERYGUARD_GROQ_API_KEY=your-secret-value
```

The client uses Groq's OpenAI-compatible `/chat/completions` endpoint.

Official model docs:

```text
https://console.groq.com/docs/models
```

## Why not expose API-key text boxes in the public UI?

A public Streamlit input can encourage accidental key sharing, browser persistence, or confusion about where secrets live. QueryGuard deliberately loads provider credentials server-side from environment variables.

The UI displays the active provider/model but does not reveal keys.

## Switching providers locally

1. Stop FastAPI.
2. Edit `.env`.
3. Set `QUERYGUARD_LLM_PROVIDER` and the matching model/key values.
4. Restart FastAPI.
5. Refresh Streamlit.

## Hosted architecture

Recommended:

```text
Streamlit Cloud
   ↓ shared QueryGuard key
Render FastAPI
   ↓ private Gemini key
Gemini API
```

The Gemini key belongs only on Render. Streamlit only needs the QueryGuard UI/API shared key.

## Privacy

- Ollama keeps prompts on the local machine unless other services are involved.
- Hosted providers receive the prompt/context sent to their API.
- Public/free provider terms can change.
- Never use a public portfolio deployment for confidential company/customer documents without reviewing the provider's current data-processing terms.

## Evaluation rule

Never write “QueryGuard has X% accuracy” without recording:

- provider;
- exact model;
- prompt/config version;
- retrieval strategy;
- dataset;
- date;
- hardware/network context where latency is reported.
## Free-tier snapshot (verified 2026-08-11)

Free tiers change, so treat this as deployment context rather than a permanent guarantee. Check the provider's official console before a demo/interview.

### Gemini 3.5 Flash

Google's official Gemini Developer API pricing page currently lists `gemini-3.5-flash` input and output as **free of charge on the Free Tier**. The same page states that Free Tier content can be used to improve Google's products, while the paid tier is listed differently. This is one reason the public portfolio demo should use only public/non-sensitive data.

Official source:

```text
https://ai.google.dev/gemini-api/docs/pricing
```

Billing/card requirement: the project does not require a paid Gemini tier. Account/billing rules can change, so verify the current AI Studio signup flow rather than documenting an unverified card claim.

### Groq + Qwen 3.6 27B

Groq's official Free Plan rate-limit table currently lists `qwen/qwen3.6-27b` at:

```text
30 requests/minute
1,000 requests/day
8,000 tokens/minute
200,000 tokens/day
```

Your account's Limits page is the source of truth because Groq notes that organization-specific limits can differ.

Official sources:

```text
https://console.groq.com/docs/rate-limits
https://console.groq.com/docs/model/qwen/qwen3.6-27b
```

Card requirement: not asserted by this repository because the public documentation reviewed for this build does not state a universal requirement. Check the current Groq console at signup.

### Ollama

Ollama is the local path. There is no hosted API quota in this project because inference runs on the user's machine; the practical limits are hardware memory, model size, and latency.

