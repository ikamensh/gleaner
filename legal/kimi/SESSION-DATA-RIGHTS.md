# Moonshot AI (Kimi) — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Terms of Service for Kimi OpenPlatform | https://platform.moonshot.ai/docs/agreement/modeluse | [api-terms-of-service.md](api-terms-of-service.md) |
| Kimi OpenPlatform Privacy Policy | https://platform.moonshot.ai/docs/agreement/userprivacy | [api-privacy-policy.md](api-privacy-policy.md) |

Both documents last updated: **April 30, 2025**

## Ownership

The ToS draws a clear line between the service itself and your content:

> "You represent and warrant that you own or have the necessary license, authorization or clearance to submit your input to the services. You are solely responsible for content and **we do not claim ownership of it**." (ToS, Section 4)

"Content" is defined as both input and output:

> "You and End Users may submit prompts, texts, audios or other content or materials (**'input'**) to the services and the services generate corresponding content as a response (**'output'**). Both input and output are collectively referred to as **'content'**." (ToS, Section 4)

However, Moonshot AI owns all IP in the service itself:

> "Moonshot AI owns all rights (including but not limited to copyright, trademark rights, patent rights, and other intellectual property rights and additional rights) within the scope permitted by applicable laws and regulations with respect to the services" (ToS, Section 6)

**Summary:** You own your inputs and outputs. Moonshot owns the service, models, and platform.

## Training on Your Data

The ToS grants Moonshot a broad usage right over your content:

> "We may use content to provide, maintain, develop, and improve the services, comply with applicable law, enforce our terms and policies, and keep the services safe." (ToS, Section 4)

The Privacy Policy confirms this under "User Content":

> "The prompts, audios, images, videos, files and other content that you input and generate while using our products and services. This information helps us **optimize our models** and understand your needs and preferences, so that we can provide you with more accurate services and support." (Privacy Policy, Section 1)

And under purposes of use:

> "To Improve and Develop Our Services: We analyze how you use the services to identify areas for improvement, develop new features, and enhance the overall user experience. This includes **training and refining our underlying technology, such as machine learning models and algorithms**." (Privacy Policy, Section 2)

**Summary:** Yes, Moonshot may use your inputs and outputs to train and improve their models. There is no opt-out mechanism described in either document.

## Data Retention

> "We store your information as long as necessary to provide the services, fulfill the purposes outlined in this policy and other legitimate business purposes (such as service improvement, resolving disputes, safety or security), comply with legal obligations." (Privacy Policy, Section 6)

> "Retention periods vary based on factors such as information type, sensitivity, and legal requirements. For example, account, input, and payment information are retained while your account is active. Violation-related information is retained until the violation is resolved. Also, in some cases, the length of time we retain data depends on your settings." (Privacy Policy, Section 6)

On termination:

> "After your service is terminated, we will delete your content and data in accordance with the requirements of applicable laws and regulations." (ToS, Section 10)

**Summary:** Data is retained as long as your account is active. No specific retention period is defined. Deletion happens after account termination, subject to legal requirements.

## What You Can Do

- **Own your content.** Inputs and outputs belong to you.
- **Store session data yourself.** The ToS explicitly recommends it: "You agree to maintain a complete and accurate copy of any content in a location that is independent of the service." (ToS, Section 4)
- **Integrate into your applications.** The license allows you to "integrate the services into your own applications, products, or services" and "offer those Customer Applications to End Users." (ToS, Section 1)
- **Delete your account** and request deletion of your data at any time. (ToS, Section 10)
- **Exercise data rights** (access, rectify, delete, port, restrict processing) by contacting opensource@moonshot.cn. (Privacy Policy, Section 4)

## What You Cannot Do

- **Use outputs as sole source of truth.** "Do not regard the output as the sole source of fact or absolutely factual information." (ToS, Section 4)
- **Use outputs as professional advice** in medical, legal, financial, or educational fields. (ToS, Section 4)
- **Make consequential decisions about people** based on outputs: "You must not use any output relating to a person for any purpose that could have a legal or material impact on that person, such as making credit, educational, employment, housing, insurance, legal, medical, or other important decisions about them." (ToS, Section 4)
- **Reverse engineer** the service, models, algorithms, or source code. (ToS, Section 3.2(4))
- **Build competing products** using the service without authorization. (ToS, Section 3.2(5))
- **Resell or sublicense** the service. (ToS, Section 3.2(6))
- **Process HIPAA Protected Health Information.** (ToS, Section 3)
- **Remove or alter AI-generated content labels**, including implicit ones. (ToS, Section 3.3(3))
- **Extract data** from the service outside of the APIs, or transfer API keys to third parties. (ToS, Section 3.4(9))
- **Send personal information of children** under 14. (ToS, Section 3.4(8))

## Notable Points

1. **Jurisdiction and Data Location.** The entity is **Moonshot AI PTE. LTD.**, incorporated in **Singapore**. Data is stored in Singapore: "We store the information we collect in secure servers located in Singapore." (Privacy Policy, Section 6). Governing law is Singapore. Disputes go to SIAC arbitration in Singapore, in English.

2. **Moonshot AI is a Chinese company operating through a Singapore entity.** Moonshot AI (Beijing Moonshot Technology Co., Ltd.) is a Chinese AI company. The API service is offered through their Singapore subsidiary. The Privacy Policy states data is stored in Singapore, but cross-border transfer provisions exist: "When cross-border transfers are necessary, we will implement appropriate safeguards, consistent with applicable data protection laws, to ensure your information is protected for the purposes outlined in this policy." (Privacy Policy, Section 6)

3. **No data backup guarantee.** "While we performs regular backups of Content, it does not guarantee that there will be no loss or corruption of data." (ToS, Section 4)

4. **Liability cap.** "The maximum aggregate liability of us and our affiliates under this agreement...shall not exceed the amount actually paid by you to us in the last one month preceding the date of liability." (ToS, Section 8)

5. **One-year statute of limitations.** "Any legal proceeding or action related to these terms must be initiated within one year from the date of the event." (ToS, Section 11)

6. **No output uniqueness guarantee.** "Due to technical limitations, we cannot guarantee that the content of other customers will be entirely different from yours, and it is possible that there may be similarities in the output." (ToS, Section 4)

---

*This is a research summary, not legal advice.*
