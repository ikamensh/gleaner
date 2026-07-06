# Mistral AI — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Commercial Terms of Service | https://legal.mistral.ai/terms/commercial-terms-of-service | [commercial-terms.md](commercial-terms.md) |
| Privacy Policy | https://legal.mistral.ai/terms/privacy-policy | [privacy-policy.md](privacy-policy.md) |
| Usage Policy | https://legal.mistral.ai/terms/usage-policy | [usage-policy.md](usage-policy.md) |
| Additional Product Terms | https://legal.mistral.ai/terms/additional-terms | [additional-terms.md](additional-terms.md) |
| Data Processing Addendum | https://legal.mistral.ai/terms/data-processing-addendum | [data-processing-addendum.md](data-processing-addendum.md) |

## Ownership

You own both your inputs and outputs.

> "To the extent permitted by applicable law, Customer (i) retains all ownership rights in Customer Data and (ii) owns all Output. Mistral AI hereby assigns to Customer all right, title, and interest, if any, in and to Output that Mistral AI may have."
> -- Commercial Terms, Section 3.1

"Customer Data" is defined broadly: "prompts (including in the form of text, audio, video, or other media), fine-tuning data, or agent instructions." (Commercial Terms, Section 3.1)

Mistral retains ownership of the Mistral AI Products themselves, including model weights and parameters (Commercial Terms, Section 5.1). Third-Party Content (hyperlinks, snippets, thumbnails from web search) is not Output and you are only granted a right to view it (Commercial Terms, Section 3.1; Additional Terms, Section 7).

Caveat -- outputs are not guaranteed unique:

> "Due to the nature of the Mistral AI Products, Customer's Output may be similar or identical to the response generated for another user of the Mistral AI Products. Mistral AI provides no guarantees that Customer's Output will be unique."
> -- Commercial Terms, Section 3.4

## Training on Your Data

**Paid API users: No, by default.** Mistral does not train on your data when you use paid API products, unless you opt in or trigger specific exceptions.

> "Please note that we do not use your Input and Output to train our artificial intelligence models when you use Le Chat Team, Le Chat Enterprise or the paid version of our APIs."
> -- Privacy Policy, Section 3 (training row)

The Commercial Terms enumerate the exceptions where training does happen:

> "Mistral AI will not use Customer Data or Outputs to train its artificial intelligence models except (a) for Customer Data or Outputs used or generated in connection with the use Mistral AI Products under a free subscription or Le Chat Pro where Customer has not opted-out of training, (b) when Customer or an End User provides Feedback to Mistral AI, (c) when Customer Data or Outputs are flagged as part of Mistral AI's automated moderation or reported by a user under the Additional Terms, (d) as otherwise may be provided in an Order Form or (e) when Customer uses Labs Models."
> -- Commercial Terms, Section 4.2

**Feedback warning:** If you use thumbs-up/thumbs-down or other in-app feedback, Mistral uses the associated input and output for training:

> "Customer acknowledges that if Customer provides feedback to Mistral AI by using the in-app 'thumbs up' or 'thumbs down' features (the 'Feedback'), Mistral will use such Feedback as well as the associated Input and Output, as Controller, to train its artificial intelligence models, conduct research or improve the Mistral AI Products."
> -- Data Processing Addendum, Section 2.3

**Labs Models warning:** Training is on by default for Labs Models (prefixed "labs" in AI Studio), opt-out only via zero data retention:

> "By using Labs Models, you acknowledge that (i) Mistral AI may use Customer Data and Outputs generated from Labs Models to train its artificial intelligence models, unless you have activated zero data retention, and (ii) the opt-out preferences you selected for other Mistral AI Products does not apply to Labs Models."
> -- Commercial Terms, Section 4.3

**Usage Data** (product usage events, performance metrics, billing metrics, Feedback) is used by Mistral for business purposes including research and product improvement, but explicitly *not* for model training:

> "Customer Data and Outputs will not be used to generate such data and statistics."
> -- Data Processing Addendum, Section 2.3

## Data Retention

**Standard API (paid):** Input and Output are retained for 30 rolling days for abuse monitoring, then deleted. Zero data retention can be activated to skip the 30-day window.

> "Except for specific APIs, we keep your Input and Output for the period necessary to generate the Output and then for thirty (30) rolling days to monitor abuse (unless zero data retention is activated)."
> -- Privacy Policy, Section 5

**Agents API:** Input and Output retained until you terminate your account. (Privacy Policy, Section 5)

**Fine-Tuning API:** Fine-tuning data retained until you delete it from Mistral AI Studio or terminate your account. (Privacy Policy, Section 5)

**Post-termination:** Personal Data is no longer accessible 30 days after termination of the Customer's access.

> "Customer acknowledges that the Personal Data will no longer be accessible upon the expiry of a thirty (30) days period following the termination of the Customer's access to and use of the Mistral AI Products."
> -- Data Processing Addendum, Section 10.1

**Legal retention (separate from operational):** Civil identity data kept 5 years post-account deletion; invoices kept 10 years; contracts and contact details kept 5 years post-termination. (Privacy Policy, Section 5)

## What You Can Do

- **Store session data yourself.** Nothing prohibits you from storing your own inputs and outputs. You own them.
- **Use outputs commercially.** You own outputs and can use them in your products and services.
- **Export data before termination.** You must do this before account termination, as data may become inaccessible after.
  > "Customer may not be able to export Customer Data or Outputs once its Customer Account is terminated. If Customer desires to export any Customer Data or Outputs from its Customer Account, Customer must complete such export prior to terminating its account." -- Commercial Terms, Section 11.4
- **Opt out of training.** For free-tier and Le Chat Pro, you can opt out of model training via account settings. Paid API is opted out by default.
- **Activate zero data retention.** Eliminates the 30-day abuse-monitoring retention window for standard API calls.
- **Request deletion of your data** under GDPR/applicable privacy law. (Privacy Policy, Section 8)
- **Connect third-party services** (including MCP servers) to Mistral AI Products, provided you have the necessary rights. (Additional Terms, Section 5)

## What You Cannot Do

- **Use image Outputs to train competing image generation products.**
  > "Customer may not use image Outputs to develop or train any image generation product that competes with a Mistral AI Product." -- Commercial Terms, Section 3.3
- **Reverse-engineer models** using outputs or otherwise.
  > "attempt to reverse engineer, decompile, or otherwise attempt to discover the source code or underlying components (e.g., algorithms, weights, or systems) of the Mistral AI Products, including using the Output or any modified version of the Output to do any of the foregoing" -- Commercial Terms, Section 2.2(d)
- **Claim outputs are human-generated.**
  > "Customer may not represent or imply that the Output was generated by a human when it was generated by the Mistral AI Products." -- Commercial Terms, Section 3.2
- **Use Third-Party Content** (web search results, thumbnails, snippets) beyond viewing: no copying, storing, caching, redistributing, reselling, or using for ML training.
  > "Customer is not allowed to use Third-Party Content displayed using Mistral AI's web-search feature to (i) copy, store, archive, cache or create a database of the Third-Party Content, (ii) redistribute, resell, or sublicense the Third-Party Content, (iii) as part of any machine learning or similar algorithmic activity, or (iv) to create, train, evaluate or improve commercial products or services that you make available to third-parties." -- Additional Terms, Section 7
- **Include children's personal data** (under 13 or applicable digital consent age) as input. (Commercial Terms, Section 2.2(c))
- **Generate content violating the Usage Policy:** illegal activities, CSAM, hate speech, violence, self-harm instructions, fraud, misinformation, privacy violations, unauthorized professional advice, security attacks. (Usage Policy)
- **Sell, transfer, or share API keys or accounts.** (Commercial Terms, Section 2.2(h))
- **Integrate Le Chat or Mistral Code into your products** offered to third parties without prior written authorization. (Commercial Terms, Section 2.2(i))

## Notable Points

1. **Mistral is a GDPR processor** when you use API products on their infrastructure. You are the data controller. The Data Processing Addendum applies automatically. (Commercial Terms, Section 12.3; DPA, Section 2.1)
2. **Feedback is a carve-out from confidentiality.** When you provide Feedback, the associated data is not treated as your Confidential Information and can be used for training. (Commercial Terms, Sections 2.4 and 6.1)
3. **Moderation access.** Mistral monitors API usage via automated means for policy compliance and security, and content flagged through moderation may be used for training. (Additional Terms, Section 6; Commercial Terms, Section 4.2(c))
4. **No guarantee of accuracy.** Outputs are probabilistic and "may occasionally be inaccurate." Mistral disclaims suitability for any particular purpose. (Commercial Terms, Section 3.5)
5. **Mistral offers IP indemnification** for third-party IP infringement claims arising from the Mistral AI Products themselves, but not for claims arising from Customer Data, Customer's use in violation of terms, or combinations with other software. (Commercial Terms, Section 8)
6. **French law governs** for customers outside the Americas and APAC. California law for Americas; Singapore law for APAC. (Commercial Terms, Section 14.10)
7. **CCPA:** Mistral will not sell or share Personal Data, and will not process it outside the direct business relationship. (DPA, Section 12.2)

---

*This is a research summary, not legal advice.*
