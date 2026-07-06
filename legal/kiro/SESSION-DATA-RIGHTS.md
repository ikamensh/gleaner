# Amazon (Kiro) — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Kiro License | https://kiro.dev/license/ | [kiro-license.md](kiro-license.md) |
| Data Protection | https://kiro.dev/docs/privacy-and-security/data-protection/ | [kiro-data-protection.md](kiro-data-protection.md) |
| Privacy and Security | https://kiro.dev/docs/privacy-and-security/ | [kiro-security.md](kiro-security.md) |
| AWS Customer Agreement | https://aws.amazon.com/agreement/ | [aws-customer-agreement.md](aws-customer-agreement.md) |
| AWS Responsible AI Policy | https://aws.amazon.com/ai/responsible-ai/policy/ | [aws-responsible-ai-policy.md](aws-responsible-ai-policy.md) |

## Ownership

Kiro is classified as "AWS Content" under the AWS Customer Agreement. Your inputs and outputs fall under the agreement's definition of "Your Content":

> "Your Content" means Content that you or any End User transfers to us for processing, storage or hosting by the Services in connection with your AWS account and any computational results that you or any End User derive from the foregoing through their use of the Services.
>
> -- AWS Customer Agreement, Section 12

AWS explicitly disclaims acquiring ownership of Your Content:

> Except as provided in this Section 6, we obtain no rights under this Agreement from you (or your licensors) to Your Content. You consent to our use of Your Content to provide the Services to you and any End Users.
>
> -- AWS Customer Agreement, Section 6.1

**In short: you own your inputs and outputs.** AWS only gets a license to use Your Content to operate the service.

One exception -- "Suggestions" (feature requests or improvement ideas you submit about the service itself) are assigned irrevocably to AWS:

> If you provide any Suggestions to us or our affiliates, we and our affiliates will be entitled to use the Suggestions without restriction. You hereby irrevocably assign to us all right, title, and interest in and to the Suggestions.
>
> -- AWS Customer Agreement, Section 6.5

## Training on Your Data

This is the key area where free/individual and enterprise tiers diverge sharply.

### Free Tier and Individual Subscribers -- training IS permitted by default

> We may use certain content from Kiro Free Tier and Kiro individual subscribers for service improvement. Users that have a paid Kiro subscription and access it through a social login provider (like GitHub or Google) or through AWS Builder ID are considered _individual subscribers_. Content that Kiro may use for service improvement includes, for example, your questions to Kiro, other inputs you provide, and the responses and code that Kiro generates. Kiro may use this content, for example, to provide better responses to common questions, fix Kiro operational issues, for de-bugging, or for model training.
>
> -- Data Protection, "Kiro content used for service improvement"

"Individual subscribers" explicitly includes paid users who log in via GitHub/Google/AWS Builder ID. The term "service improvement" explicitly includes "model training."

### Enterprise Users -- training is NOT permitted

> We do not use content from Kiro enterprise users for service improvement.
>
> -- Data Protection, "Kiro content used for service improvement"

> Kiro enterprise users are automatically opted out of telemetry and content collection by AWS.
>
> -- Data Protection, "Opt out of data sharing"

### Amazon Q Developer Pro Subscribers -- training is NOT permitted

> If you have an Amazon Q Developer Pro subscription and access Kiro through your AWS account with the Amazon Q Developer Pro subscription, then Kiro will not use your content for service improvement.
>
> -- Data Protection, info box

## Data Retention

### Free Tier and Individual Subscribers

Data is stored in US East (N. Virginia):

> If you are a Kiro Free Tier user or a Kiro individual subscriber, your content, such as prompts and responses, will be stored in the US East (N. Virginia) Region.
>
> -- Data Protection, "AWS regions where content is stored and processed"

No specific retention period is stated. The data protection page says Kiro "stores your questions, its responses, and additional context, such as code" but does not specify how long.

### Enterprise Users

> If you are a Kiro enterprise user, your data is not stored.
>
> -- Data Protection, "AWS regions where content is stored and processed"

### Post-termination

After account termination, AWS gives you 30 days to retrieve Your Content (unless terminated for cause):

> During the 30 days following the Termination Date: (i) we will not take action to remove from the AWS systems any of Your Content as a result of the termination; and (ii) we will allow you to retrieve Your Content from the Services only if you have paid all amounts due under this Agreement.
>
> -- AWS Customer Agreement, Section 5.3(b)

## What You Can Do

- **Own your inputs and outputs.** Your code, prompts, and generated content remain Your Content.
- **Opt out of data sharing** (Free/Individual only). Uncheck "Data Sharing and Prompt Logging: Content Collection for Service Improvement" in Settings > User > Application > Telemetry and Content. In the CLI, toggle off "Share Kiro content with AWS."
- **Opt out of telemetry** separately from content sharing, using the same settings panels.
- **Retrieve your data** within 30 days after terminating your account.
- **Use customer-managed encryption keys** (Enterprise only) to control access to data at rest.
- **Choose your processing geography** -- inference stays within your geography (US or Europe) for non-experimental features.

## What You Cannot Do

- **Reverse-engineer, decompile, or derive source code** from Kiro or AWS Content (Section 6.4).
- **Resell** the Services or AWS Content (Section 6.4).
- **Use outputs to circumvent fees** or exceed usage limits (Section 6.4).
- **Use AI outputs for lethal weapon functions without human control**, unlawful surveillance, disinformation, CSAM, or unauthorized impersonation (Responsible AI Policy).
- **Make consequential decisions** (medical, legal, financial, hiring) based on AI outputs without appropriate human oversight and testing (Responsible AI Policy).
- **Assume outputs are correct.** AWS disclaims all warranties and states that "generative AI may produce inaccurate or inappropriate content" (Responsible AI Policy). Services are provided "AS IS" (Section 8).

## Notable Points

1. **Paying does not stop training by itself.** Individual paid subscribers (GitHub/Google/Builder ID login) are treated the same as Free Tier for service improvement. Only Enterprise tier or Amazon Q Developer Pro subscribers are automatically excluded.

2. **"Service improvement" explicitly includes model training.** The data protection page lists "model training" as an example use alongside debugging and operational fixes.

3. **Opt-out exists but is not the default.** Free and Individual users must manually disable content collection. The opt-out covers content collection but may not cover all telemetry (those are separate toggles).

4. **Enterprise data is not stored server-side.** Enterprise users' prompts and responses are not persisted by AWS, which is a stronger guarantee than just "not used for training."

5. **Suggestions are different from Content.** Improvement suggestions about the service are irrevocably assigned to AWS (Section 6.5). This is separate from your code and session content.

6. **Experimental features may route globally.** Non-experimental inference stays within your geography (US or Europe), but experimental features may use "global cross-region inference" across all commercial AWS regions worldwide.

7. **AWS access to Your Content is limited by contract.** Section 1.4: "We will not access or use Your Content except as necessary to maintain or provide the Services, or as necessary to comply with the law or a binding order of a governmental body."

8. **No specific retention period disclosed.** For Free/Individual tiers, content is stored but no duration is stated. Enterprise content is not stored at all.

---

*This is a research summary, not legal advice.*
