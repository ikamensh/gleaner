# Google (Gemini) — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Gemini API Additional Terms of Service | https://ai.google.dev/gemini-api/terms | [gemini-api-terms.md](gemini-api-terms.md) |
| Data Logging and Sharing | https://ai.google.dev/gemini-api/docs/logs-policy | [api-data-logging.md](api-data-logging.md) |
| Generative AI Prohibited Use Policy | https://policies.google.com/terms/generative-ai/use-policy | [generative-ai-use-policy.md](generative-ai-use-policy.md) |
| Google APIs Terms of Service | https://developers.google.com/terms | (not downloaded) |
| Data Processing Addendum (Processor) | https://business.safety.google/processorterms/ | (not downloaded) |

Which terms apply depends on whether you use Paid or Unpaid Services:
- **Unpaid Services** -- Google AI Studio (free), Gemini API without billing. Google uses your data for training.
- **Paid Services** -- Gemini API via a Cloud Project with an active billing account, or Google AI Studio accessed through a billing-enabled or Workspace enterprise account. Google does not use your data for training.
- **EEA/Switzerland/UK exception** -- users in those regions get Paid Services data-use terms even on Unpaid Services.

## Ownership

**Google does not claim ownership of your generated content.**

> "Some of our Services allow you to generate original content. Google won't claim ownership over that content."

However, Google reserves the right to produce identical content for others:

> "You acknowledge that Google may generate the same or similar content for others and that we reserve all rights to do so."

There is no explicit "assignment" of rights to you (unlike Anthropic's terms). Google simply disclaims its own ownership claim. Whether AI-generated outputs are protectable IP at all remains legally unsettled.

## Training on Your Data

| Tier | Google trains on your data? | Mechanism |
|---|---|---|
| Unpaid Services | **Yes** | Automatic. Human reviewers may read, annotate, and process your inputs and outputs. Data is disconnected from your account before review. |
| Paid Services | **No** | Prompts and responses are not used for product improvement. Logged only for abuse detection and legal compliance. |
| Paid Services with Grounding (Search/Maps) | **Partially** | Google stores prompts and output for 30 days for debugging/testing of grounding systems, processed under Data Processing Addendum. |
| Opt-in data sharing (Paid, via Logs & Datasets) | **Yes, by explicit choice** | You curate logs into datasets and share them with Google. Shared datasets are then treated under Unpaid Services data-use terms. |

Key quotes:

Unpaid:
> "Google uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies, including Google's enterprise features, products, and services."

> "human reviewers may read, annotate, and process your API input and output."

Paid:
> "Google doesn't use your prompts [...] or responses to improve our products, and will process your prompts and responses in accordance with the Data Processing Addendum for Products Where Google is a Data Processor."

## Data Retention

| Tier | Retention |
|---|---|
| Unpaid Services | Not explicitly stated in these terms (subject to Google Privacy Policy) |
| Paid Services | Logged "for a limited period of time, solely for detecting and preventing violations of the Prohibited Use Policy" |
| Paid + Grounding with Google Search | 30 days for debugging/testing |
| Paid + Grounding with Google Maps | 30 days for debugging/testing |
| API Logs (billing-enabled projects) | 55 days by default, then expire. Logs saved into Datasets persist indefinitely (up to 1,000 per project). |
| Model tuning content | Retained while tuned model exists. Deleted when tuned model is deleted. |

From the Data Logging docs:
> "Logs will expire after 55 days by default. They will become unavailable after this period."

## What You Can Do

- **Store session data yourself** -- no prohibition exists in the terms. You own your inputs; Google disclaims ownership of outputs.
- **Use generated content commercially** -- no restriction on commercial use of outputs (subject to compliance with law and attribution requirements when citations are returned).
- **Opt in to logging** (Paid) to review your own API call history for up to 55 days, or save logs into datasets for longer retention.
- **Share datasets with Google** voluntarily to contribute to model improvement.
- **Use generated content freely**, with the understanding that you are responsible for it:
  > "You're responsible for your use of generated content, and for the use of that content by anyone you share it with."
- **Store Grounded Results text** for up to 2 years for display optimization or end-user chat history.

## What You Cannot Do

- **Build competing services** -- cannot use the Services to "develop models that compete with the Services (e.g., Gemini API or Google AI Studio)."
- **Reverse engineer** -- cannot "reverse engineer, extract or replicate any component of the Services, including the underlying data or models (e.g., parameter weights)."
- **Bypass safety filters** -- cannot "attempt to bypass these protective measures."
- **Clinical/medical use** -- cannot use "in clinical practice, to provide medical advice, or in any manner that is overseen by or requires clearance or approval from a medical device regulatory agency."
- **Train on Grounded Results** -- cannot "train on" Grounded Results or Search Suggestions.
- **Submit sensitive data to Unpaid Services** -- "Do not submit sensitive, confidential, or personal information to the Unpaid Services."
- **Violate the Prohibited Use Policy** -- no CSAM, terrorism, non-consensual imagery, self-harm facilitation, illegal activities, spam/malware, hate speech, harassment, sexually explicit content, fraud, or impersonation.
- **Use in EEA/Switzerland/UK without Paid Services** -- "You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom."
- **Under-18 users** -- cannot use in applications directed at or likely accessed by individuals under 18.

## Notable Points

1. **No explicit IP assignment** -- Unlike Anthropic, which assigns its interest in outputs to you, Google simply says it "won't claim ownership." This is a weaker grant; you get no affirmative IP assignment.
2. **Unpaid = training data** -- On the free tier, everything you send (prompts, system instructions, cached content, files) and all responses become training material. Human reviewers will see it.
3. **Paid tier is clean** -- With billing enabled, Google processes data only under the Data Processing Addendum and retains it only for abuse detection. This is the tier to use for any sensitive or proprietary work.
4. **Opt-in logging, not opt-out** -- For paid users, sharing data with Google for training requires explicit opt-in (curating datasets and sharing them). This is the opposite of many providers where you must opt out.
5. **EEA users get automatic protection** -- Users in EEA/Switzerland/UK get Paid Services data-use terms even on free tier.
6. **Grounding has separate retention** -- Even on Paid Services, Grounding with Google Search/Maps stores data for 30 days for system debugging.
7. **No zero-data-retention option mentioned** -- Unlike Anthropic's Enterprise ZDR, there is no documented option for zero data retention. Paid Services still log data for abuse detection for an unspecified "limited period."
8. **Same-output caveat** -- Google explicitly reserves the right to generate the same content for other users. Non-uniqueness is baked into the terms.

---

*This is a research summary, not legal advice.*
