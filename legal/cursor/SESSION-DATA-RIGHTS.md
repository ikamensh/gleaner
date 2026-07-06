# Cursor (Anysphere) — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Terms of Service | https://cursor.com/terms-of-service | [terms-of-service.md](terms-of-service.md) |
| Privacy Policy | https://cursor.com/privacy | [privacy-policy.md](privacy-policy.md) |
| Data Use & Privacy Overview | https://cursor.com/data-use | [data-use.md](data-use.md) |
| Security | https://cursor.com/security | [security.md](security.md) |
| Master Services Agreement | https://cursor.com/terms/msa | [msa.md](msa.md) |
| Data Processing Addendum | https://cursor.com/terms/dpa | [dpa.md](dpa.md) |

Which terms apply:
- **Individual users** -> Terms of Service
- **Enterprise / team customers** -> MSA (stronger protections)

## Ownership

**You own both inputs and outputs** (called "Suggestions" in Cursor's terms).

- **ToS Section 5.3:** "You retain all of your right, title, and interest that you have in Inputs, and Anysphere hereby assigns to you all of our right, title, and interest if any in and to any Suggestions."
- **MSA Section 3.2/3.3:** "Customer retains all right, title and interest it has in and to Customer Data." Anysphere "assigns to Customer all of Anysphere's right, title, and interest in and to any Suggestions."

Caveat: outputs are non-exclusive — the same suggestion may be generated for other users, and you have no rights over their copies.

## Training on Your Data

**Headline commitment (ToS Section 1.3, MSA Section 3.3):**
> "ANYSPHERE WILL NOT USE CONTENT TO TRAIN, OR ALLOW ANY THIRD PARTY TO TRAIN, ANY AI MODELS, UNLESS YOU'VE EXPLICITLY AGREED TO THE USE OF CONTENT FOR TRAINING."

**What constitutes "explicit agreement":** turning Privacy Mode OFF in Cursor's settings.

**Three exceptions even with Privacy Mode ON (Privacy Policy Section 2):**
1. Data flagged for security review
2. Data you explicitly report as Feedback
3. Data you've explicitly agreed to provide for training

### Privacy Mode Comparison

| | Privacy Mode ON | Privacy Mode OFF | Privacy Mode (Legacy) |
|---|---|---|---|
| Model provider retention | Zero | May retain | Zero |
| Cursor stores code | Yes, "some code data" | Yes, all types | No |
| Cursor trains on your data | No | Yes | No |
| Shared with model providers | Data transits but isn't retained | Prompts + telemetry shared | Data transits but isn't retained |
| Inference providers store data | No | Yes (temporarily, "deleted after use") | No |

Legacy mode is the strictest. Current Privacy Mode ON still allows Cursor to store some code for features.

## Data Retention

- **Privacy Policy:** No specific durations — "as long as necessary."
- **MSA Section 10.3:** 30 days post-termination to download your data, deleted at day 31.
- **Codebase indexing:** plaintext code "ceases to exist after the life of the request"; embeddings and metadata (hashes, file names) may be stored.
- **File caching:** temporary, encrypted with client-generated keys, keys exist only for request duration.

## What You Can Do

- **Store session data locally:** no prohibition. You own inputs and outputs.
- **ToS Section 10** affirmatively advises: "You should retain copies of any Content as needed so that you have access in the event the Service is modified and you lose access to such Content."

## What You Cannot Do

- **Build competing AI:** cannot "use the Service or any Suggestions to develop or train a model that is competitive with the Service, or engage in model extraction or theft attacks" (ToS Section 1.5(v)).
- **Publish benchmarks** without including all info needed to replicate them (ToS Section 1.5(vii)).
- **Infringe third-party rights** using the Service or Suggestions (ToS Section 1.5(ix)).
- **Feedback is a one-way door:** rating a suggestion or reporting a problem grants Anysphere "unrestricted, perpetual, irrevocable, non-exclusive, fully-paid, royalty-free" rights to that feedback (MSA Section 6.2).

## Notable Points

1. **Your requests always transit Cursor's backend** — even with your own API key. "Your requests will still go through our backend! That's where we do our final prompt building."
2. **Third-party inference providers** (Baseten, Together AI, Fireworks) may temporarily store data when Privacy Mode is OFF.
3. **No specific retention durations** in the Privacy Policy, unlike Anthropic which gives concrete numbers.
4. **Feedback vs Content distinction matters:** Content (your code, prompts) you own. Feedback (ratings, bug reports, improvement suggestions) you give away permanently.

---

*This is a research summary, not legal advice.*
