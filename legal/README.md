# Legal Terms for AI Providers

*Downloaded 2026-04-02. Terms change — re-run `download.py` in each folder to refresh.*

Legal documents and analysis for all LLM providers and coding tools used by
[kodo](../../kodo/) and our development workflow.

## How Terms Apply

When you use an AI coding tool, your data passes through up to three entities.
Each entity acts on your data per its own policies — but you can only enforce
terms against entities you have a **direct contract** with.

```
You ──→ Harness ──→ Router (optional) ──→ Model Provider
        (IDE/CLI)   (aggregator)           (LLM API)
```

**Harness** — the tool you interact with (Cursor, Claude Code, Kiro, etc.)
**Router** — optional intermediary (OpenRouter)
**Model provider** — the LLM API (Anthropic, OpenAI, Google, etc.)

### Who you have a contract with

This depends on how the tool accesses the model:

| Scenario | You contract with | Provider's terms protect |
|---|---|---|
| Kodo calls an API directly (your key) | the provider | you |
| Cursor uses its own model access | Cursor only | Cursor, not you |
| Cursor with **your** API key | Cursor AND the provider | you (from provider) |
| Kodo via OpenRouter (your key) | OpenRouter | OpenRouter, not upstream |

When the harness manages model access on your behalf (e.g. Cursor's built-in
Claude access), the provider's customer is the harness, not you. The provider's
data protection promises run to the harness. If the provider violates them,
your recourse is against the harness for breach of *its* terms to you.

### What this means in practice

Each entity that touches your data independently decides whether to store,
train on, or retain it — regardless of your contractual relationship with them.

- **Use restrictions accumulate:** you are bound by all terms you agreed to.
- **Data protection promises don't stack automatically:** a harness promising
  "no training" only covers what the harness does. If it forwards your data
  to a provider that trains by default, the harness's promise doesn't stop
  the provider — only the provider's own terms (or the harness's agreement
  with them) govern that.
- **Your leverage depends on your contract:** you can only demand compliance
  from entities you contracted with directly. For the rest, you depend on
  the intermediary having negotiated adequate protections on your behalf.

## Effective Terms by Kodo Backend

### Direct API access (your key → provider)

You contract directly with the provider. Their terms bind you and protect you.

| Kodo backend | You contract with | Terms |
|---|---|---|
| `anthropic:*` | Anthropic | [claude/](claude/) |
| `openai:*` | OpenAI | [openai/](openai/) |
| `google-gla:*` | Google | [google/](google/) (Gemini API) |
| `google-vertex:*` | Google | [google/](google/) (Vertex AI / GCP) |
| `deepseek:*` | DeepSeek | [deepseek/](deepseek/) |
| `groq:*` | Groq | [groq/](groq/) |
| `mistral:*` | Mistral | [mistral/](mistral/) |
| `xai:*` | xAI | [xai/](xai/) |
| `ollama:*` | (local) | no third-party terms |

### Via router (your key → OpenRouter → upstream provider)

You contract with OpenRouter. The upstream provider's customer is OpenRouter,
not you. What the provider does with your data depends on what OpenRouter
negotiated with them (see [openrouter/](openrouter/) for their logging docs).

| Kodo backend | You contract with | Upstream provider | Terms you can enforce |
|---|---|---|---|
| `openrouter:*` | OpenRouter | varies per model | [openrouter/](openrouter/) only |

### Via coding agent (your subscription → tool → provider)

When the tool manages model access, the tool is the provider's customer.

| Kodo backend | You contract with | Provider's customer is | Terms you can enforce |
|---|---|---|---|
| `claude-code` | Anthropic | you (same entity) | [claude/](claude/) |
| `cursor` | Cursor | Cursor (unless your key) | [cursor/](cursor/) |
| `gemini-cli` | Google | you (same entity) | [google/](google/) |
| `kimi-code` | Moonshot | you (same entity) | [kimi/](kimi/) |
| `codex` | OpenAI | you (same entity) | [openai/](openai/) |
| `kiro-cli` | Amazon | you (same entity) | [kiro/](kiro/) |

**Cursor is the only harness where the provider can differ from the vendor.**
When Cursor uses Claude/GPT/Gemini, Cursor is Anthropic's/OpenAI's/Google's
customer — not you. Your data protection depends on what Cursor negotiated
with them. All requests transit Cursor's backend even with your own API key
(though using your own key gives you a direct contract with the provider too).

## Training and Retention Summary

| Entity | Role | Trains by default? | Opt-out? | Retention |
|---|---|---|---|---|
| **Anthropic** (Consumer) | provider | Yes | Yes ([settings](https://claude.ai/settings/data-privacy-controls)) | 5yr / 30d opt-out |
| **Anthropic** (Commercial) | provider | No | — | 30d (ZDR available) |
| **Cursor** (Privacy Mode ON) | harness | No | — (default) | unspecified |
| **Cursor** (Privacy Mode OFF) | harness | Yes | toggle PM on | unspecified |
| **OpenAI** (API) | provider | No | — | 30d (ZDR available) |
| **Google** (Unpaid API) | provider | Yes | No | 55d logs |
| **Google** (Paid API) | provider | No | — | "limited period" |
| **DeepSeek** | provider | Yes | Yes (toggle) | no fixed period (PRC) |
| **Groq** | provider | No | — | not retained (ZDR available) |
| **OpenRouter** | router | No | — | depends on logging |
| **Mistral** (Paid) | provider | No | — | 30d (ZDR available) |
| **xAI** (API) | provider | No | — | 30d auto-delete |
| **Moonshot/Kimi** | provider | Yes | no documented opt-out | unspecified |
| **Amazon/Kiro** (Free) | harness+provider | Yes | Yes (settings) | unspecified |
| **Amazon/Kiro** (Enterprise) | harness+provider | No | — | not stored |

**Reading this table:** each row describes what that entity does with data it
processes. When Cursor (Privacy Mode ON, no training) routes to DeepSeek
(trains by default), Cursor won't train but DeepSeek will. Whether you can
do anything about it depends on your contracts: if Cursor manages the DeepSeek
access, your recourse is against Cursor. If you provided your own DeepSeek
API key, you can opt out at DeepSeek directly.

## Per-Provider Details

Each folder contains:
- `download.py` — re-fetch documents (deterministic html2text, no AI)
- `SOURCES.txt` — source URLs, purpose, relevance
- `SESSION-DATA-RIGHTS.md` — standardized analysis (same 7 sections in each)
- `*.md` — the actual legal documents

| Folder | Provider | Status |
|---|---|---|
| [claude/](claude/) | Anthropic (Claude Code) | complete |
| [cursor/](cursor/) | Cursor (Anysphere) | complete |
| [openai/](openai/) | OpenAI (GPT, Codex) | docs need manual download (Cloudflare) |
| [google/](google/) | Google (Gemini API, Vertex AI) | complete |
| [deepseek/](deepseek/) | DeepSeek | complete |
| [groq/](groq/) | Groq (GroqCloud) | complete |
| [openrouter/](openrouter/) | OpenRouter | complete |
| [mistral/](mistral/) | Mistral AI | complete |
| [xai/](xai/) | xAI (Grok) | docs need manual download (Cloudflare) |
| [kimi/](kimi/) | Moonshot AI (Kimi) | complete |
| [kiro/](kiro/) | Amazon (Kiro) | complete |
