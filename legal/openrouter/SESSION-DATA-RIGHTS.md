# OpenRouter — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Terms of Service (updated 2026-03-16) | https://openrouter.ai/terms | [terms-of-service.md](terms-of-service.md) |
| Privacy Policy (updated 2025-04-15) | https://openrouter.ai/privacy | [privacy-policy.md](privacy-policy.md) |
| AI Model Terms (per-provider) | https://openrouter.ai/docs/features/provider-routing#terms-of-service | (external, varies by model) |

## Ownership

**You retain ownership of your inputs.** From ToS Section 5.1:

> "You retain copyright and any other proprietary rights that you may hold in the Input."

**Output ownership depends on the upstream AI model.** From ToS Section 5.1:

> "Your ownership rights in the Output are set forth in terms for each AI Model you use ('AI Model Terms'), a list of which is provided [here](https://openrouter.ai/docs/features/provider-routing#terms-of-service)."

OpenRouter itself makes no independent claim of ownership over outputs.

## Training on Your Data

### OpenRouter (the aggregator)

OpenRouter does not train its own models. Its data use depends on which features you have opted into:

- **Prompt logging OFF (default for accounts created after 2025-04-03):** OpenRouter does not store your prompts. It uses a hosted categorization model that "does not store or log any Inputs provided to it" (ToS 5.4). Only anonymized category metadata is retained for usage analytics.

- **Prompt logging ON:** You grant OpenRouter a "worldwide, perpetual, irrevocable, non-exclusive, royalty-free, fully paid right and license (with the right to sublicense) to host, store, transfer, display, perform, reproduce, modify [...] and distribute your User Content" (ToS 5.2). This explicitly includes the right to "license or sell your User Content in anonymized form, where your User Content is not associated with you or your account" (ToS 5.2).

- **Private Prompt Storage ON:** A narrower, revocable license -- "solely for purposes of displaying the User Content to you" (ToS 5.3).

**Note for older accounts:** Accounts created between 2023-11-14 and 2025-04-03 had prompt logging enabled by default. Check your dashboard settings.

### Upstream Providers

OpenRouter is an aggregator. Your prompts are forwarded to third-party AI model providers, each with their own terms. From ToS Section 5.1:

> "Some AI Models may store or train on your Inputs for improving their own large language models and may allow you to opt-out of model training, as described in their AI Model Terms."

> "Where possible, OpenRouter has opted out of model training with the AI Models it uses."

From Privacy Policy Section 1:

> "We do not control, and are not responsible for, LLMs' handling of your Inputs or Outputs, including for use in their model training."

OpenRouter disclaims liability for inaccuracies in its representation of provider terms:

> "OpenRouter is not liable for errors or misrepresentations made in any AI Model Terms. You are encouraged to review AI Model Terms yourself as needed." (ToS 5.1)

## Data Retention

OpenRouter does not specify a fixed retention period for session data. From Privacy Policy Section 7:

> "We [...] will retain your information for as long as is reasonably necessary to comply with our business and legal obligations and to meet regulatory and compliance requirements."

Prompt data retention depends on your logging settings:

| Setting | What is stored | Duration |
|---|---|---|
| Prompt logging OFF | Anonymized category metadata only | Unspecified |
| Prompt logging ON | Full inputs, outputs, and tokens | Perpetual (irrevocable license) |
| Private Prompt Storage ON | Full inputs and outputs (visible only to you) | Revocable; details at OpenRouter docs |

Account deletion: All associated personal data is deleted upon confirmed request, "unless we are required to maintain it for regulatory and compliance purposes or for a legal or business necessity" (Privacy Policy Section 4).

Credits expire 365 days after purchase (ToS 4.2).

## What You Can Do

- **Store session data yourself.** Nothing in the terms prohibits you from storing inputs and outputs locally. You retain copyright on your inputs, and output ownership follows the upstream model's terms.
- **Use outputs in your products.** No OpenRouter-specific restriction on commercial use of outputs. Check the specific AI Model Terms for the model you used.
- **Disable all logging.** Turn off prompt logging and private prompt storage in your dashboard. OpenRouter will then not store your prompts after categorization.
- **Request data deletion.** Email privacy@openrouter.ai to delete your account and associated personal data.
- **Request data export.** You have the right to "request a copy of the personal data we process about you" (Privacy Policy Section 4).

## What You Cannot Do

- **Resell API access.** "Access the Site or Service for purposes of reselling API access to AI Models or otherwise developing a competing service" is prohibited (ToS 6.4).
- **Scrape or crawl.** Automated scraping of the site or service is prohibited (ToS 6.5, 6.6).
- **Red Team without written approval.** Prompt injection, jailbreaking, and adversarial attacks on AI models require prior written approval from OpenRouter (ToS 6.10, Section 7).
- **Violate upstream model terms.** You must comply with each AI Model's own terms of service (ToS 6.1, 6.8).
- **Misrepresent your identity or create multiple accounts** to bypass usage limits (ToS 6.3).

## Notable Points

1. **OpenRouter is a passthrough.** It routes your requests to third-party model providers. Even if OpenRouter does not train on your data, the upstream provider might. The terms explicitly disclaim responsibility for this.
2. **Opt-in logging grants a very broad license.** If prompt logging is on, OpenRouter can sublicense and sell your anonymized content. This license is perpetual and irrevocable -- it survives account deletion.
3. **Default logging changed in April 2025.** Accounts created before 2025-04-03 may still have prompt logging enabled from their default settings.
4. **Output accuracy is disclaimed.** "OpenRouter is not responsible for the accuracy or quality of any Output you receive through the Service" (ToS 15).
5. **Binding arbitration.** All disputes are resolved by binding arbitration in New York, not in court. No class actions (ToS 19).
6. **Organizational accounts:** Admin Users can configure prompt logging, chat logging, zero data retention, and model training settings for all Authorized Users in their organization (ToS 3).
7. **Categorization of inputs is always-on.** Even with logging off, OpenRouter categorizes your inputs using a hosted model for usage analytics. The license for this is perpetual and irrevocable, but operates on anonymized data only (ToS 5.4).

---

*This is a research summary, not legal advice.*
