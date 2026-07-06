# Anthropic (Claude Code) — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Consumer Terms of Service | https://www.anthropic.com/legal/consumer-terms | [consumer-terms.md](consumer-terms.md) |
| Commercial Terms of Service | https://www.anthropic.com/legal/commercial-terms | [commercial-terms.md](commercial-terms.md) |
| Acceptable Use Policy | https://www.anthropic.com/legal/aup | [acceptable-use-policy.md](acceptable-use-policy.md) |
| Privacy Policy | https://www.anthropic.com/legal/privacy | [privacy-policy.md](privacy-policy.md) |
| Claude Code Legal & Compliance | https://code.claude.com/docs/en/legal-and-compliance | [claude-code-legal-and-compliance.md](claude-code-legal-and-compliance.md) |
| Claude Code Data Usage | https://code.claude.com/docs/en/data-usage | [claude-code-data-usage.md](claude-code-data-usage.md) |

Which terms apply depends on how Claude Code is authenticated:
- **Free / Pro / Max plan** (OAuth login) -> Consumer Terms
- **Team / Enterprise / API key** -> Commercial Terms
- **Existing commercial agreement** (AWS Bedrock, Google Vertex) -> that agreement extends to Claude Code

## Ownership

**You own both inputs and outputs** under all plan types.

- **Consumer Terms:** "you retain any right, title, and interest" in Inputs. Anthropic "assigns to you all [its] right, title, and interest (if any) in Outputs."
- **Commercial Terms:** "Customer retains all rights to its Inputs." "Customer owns its Outputs." Anthropic "assigns to Customer its right, title and interest (if any) in and to Outputs."

The "if any" qualifier reflects that AI-generated content IP is legally unsettled — Anthropic is not guaranteeing the outputs are protectable IP.

## Training on Your Data

| Plan | Anthropic trains on your data? |
|---|---|
| Consumer (training opt-in, default) | Yes |
| Consumer (training opt-out) | No (except flagged content & feedback) |
| Commercial (Team/Enterprise/API) | No (firm prohibition) |
| Enterprise with ZDR | No |

Opt out at: https://claude.ai/settings/data-privacy-controls

Even with opt-out, Anthropic still uses data when: (1) you provide explicit feedback, or (2) content is flagged for safety review.

## Data Retention

| Plan | Retention |
|---|---|
| Consumer (training opt-in, default) | 5 years |
| Consumer (training opt-out) | 30 days |
| Commercial (Team/Enterprise/API) | 30 days |
| Enterprise with ZDR | Not stored (violations: up to 2 years) |

Claude Code itself stores sessions locally for up to 30 days (configurable).

## What You Can Do

- Store session data locally or in your own systems — no prohibition exists.
- Under **Commercial Terms**, you can explicitly use outputs "to power products and services Customer makes available to its own customers and end users."
- Under **Consumer Terms**, there is no explicit commercial-use grant, but also no prohibition on using your own data.

## What You Cannot Do

- **Build competing AI products** — cannot use outputs to train competing models (both terms).
- **Violate the Acceptable Use Policy** — no illegal activity, weapons, CSAM, fraud, unauthorized system access.
- **High-risk domains** (legal, healthcare, finance) require human-in-the-loop review and disclosure that AI assisted the output.
- **OAuth tokens** from Free/Pro/Max accounts cannot be used in third-party products.

## Notable Points

1. You own the data — storing it is fine.
2. If on a consumer plan without opt-out, Anthropic also retains a license to use it for training. This doesn't restrict your use, but your data may train future models.
3. If sessions contain third-party code or sensitive data, the "as between you and Anthropic" ownership language means Anthropic makes no claims about third-party rights — handle that yourself.
4. Commercial plans give you the cleanest position: you own everything, Anthropic can't train on it, and you have explicit commercial-use rights.

---

*This is a research summary, not legal advice.*
