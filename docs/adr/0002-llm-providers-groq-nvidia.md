# 0002: Groq + NVIDIA NIM instead of Anthropic + Gemini

## Status
Accepted

## Context
`docs/HANDOFF.md` §1.3 originally specified Claude Haiku (live reply) and Claude Sonnet
(post-call summary) via the Anthropic SDK, with Gemini as a fallback behind the same
`LLMProvider` interface, and `gemini-embedding` for long-term memory retrieval.

## Decision
Replace both roles and the embedding provider:
- **Reply + intent classification** (latency-critical, frequent): Groq
  (`REPLY_LLM_PROVIDER=groq`, default model `openai/gpt-oss-20b` — Groq's catalog moved on
  from the `llama-3.1-*` names this ADR originally picked; verified live against the account).
- **Post-call summary** (not latency-critical, once per call): NVIDIA NIM
  (`SUMMARY_LLM_PROVIDER=nvidia`, default model `nvidia/nemotron-3.5-lightning-30b-a3b` —
  likewise, `meta/llama-3.1-70b-instruct` is gone from NIM's catalog; verified live).
- **Embeddings**: NVIDIA NIM (`EMBEDDING_PROVIDER=nvidia`, `nvidia/nemotron-3-embed-1b`,
  2048-dim — the `memories.embedding` pgvector column was migrated 32 -> 1024 -> 2048 dims to
  match, as the actual model choice firmed up against what the account could reach). NIM's
  embedding models are **asymmetric** (a search query embeds differently from a stored
  passage) and require a NIM-specific `input_type: "query"|"passage"` field with no first-class
  equivalent in the OpenAI SDK — passed via `extra_body`. `EmbeddingProvider.embed()` takes a
  `kind: "query"|"passage" = "query"` parameter for this; `memory/writer.py` (storing) passes
  `"passage"`, everything that searches (`persona/examples.py`, `session_ws.py`) uses the
  default `"query"`.

This is a **two-role split, not an interchangeable backend switch** — `config.py` has
separate `reply_llm_provider` and `summary_llm_provider` settings (each `<provider> | mock`),
and `session_ws.py` constructs two separate `LLMProvider` instances. Both Groq and NVIDIA NIM
expose OpenAI-compatible chat completions APIs, so a single `OpenAICompatibleProvider` base
class (`llm/openai_compatible.py`) backs both `GroqProvider` and `NvidiaNimProvider` — they
differ only in `base_url`/`api_key`/`model`.

## Consequences
- No `anthropic`/`google-genai` SDK dependency; `openai` (pointed at non-OpenAI base URLs) is
  the only LLM SDK dependency.
- `classify`/`summarise` use OpenAI's `response_format={"type": "json_object"}` JSON mode as
  best-effort — `OpenAICompatibleProvider._json_completion` catches any failure (unsupported
  mode, network error, invalid JSON) and returns `{}` rather than raising, since
  `summariser.py`'s retry+fallback and `intent.py`'s rule fallback already handle that.
- Switching `EMBEDDING_PROVIDER` or the embedding model again means updating
  `memory/embeddings.py`'s `EMBEDDING_DIM` and adding a new Alembic migration to resize the
  `memories.embedding` column — `NvidiaEmbeddingProvider` raises `EmbeddingDimensionMismatch`
  immediately if the two drift apart, rather than letting pgvector fail with a confusing
  error deeper in the stack.
- `docs/HANDOFF.md` §1.3/§13's Anthropic/Gemini env vars are superseded by this ADR.
- Both providers' model catalogs turned out to have moved on from what seemed like current
  model names — confirming `docs/HANDOFF.md` §1.3's standing rule to verify model IDs against
  the live API (`GET /v1/models`) rather than trust a remembered name, even within the same
  build session. Hit a live `/v1/models` call against each provider before assuming a model
  ID is real.
