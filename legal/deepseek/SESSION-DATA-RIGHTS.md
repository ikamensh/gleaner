# DeepSeek — Session Data Rights

*Researched 2026-04-02. Terms may change — check source documents.*

## Governing Documents

| Document | Source | Local Copy |
|---|---|---|
| Terms of Use (Mar 27, 2026) | [deepseek-terms-of-use.html](https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html) | [terms-of-use.md](terms-of-use.md) |
| Privacy Policy (Feb 10, 2026) | [deepseek-privacy-policy.html](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html) | [privacy-policy.md](privacy-policy.md) |
| Open Platform Terms (Mar 27, 2026) | [deepseek-open-platform-terms-of-service.html](https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html) | [open-platform-terms.md](open-platform-terms.md) |
| Model Training Disclosure | [model-algorithm-disclosure.html](https://cdn.deepseek.com/policies/en-US/model-algorithm-disclosure.html) | [model-training-disclosure.md](model-training-disclosure.md) |

## Ownership

**You retain ownership of Inputs. DeepSeek assigns you ownership of Outputs.**

Terms of Use, Section 4.2:

> "Subject to applicable law and our Terms, you have the following rights regarding the Inputs and Outputs of the Services: (1) You retain any rights, title, and interests--if any--in the Inputs you submit; (2) We assign any rights, title, and interests--if any--in the Outputs of the Services to you."

Outputs are not guaranteed unique:

> "Due to the nature of our Services and artificial intelligence generally, Outputs may not be unique and other users may receive similar Outputs from our Services. Our assignment above does not extend to other users' Outputs."

DeepSeek's own IP (model weights, parameters, algorithms, code, framework) remains DeepSeek's. (Open Platform Terms, Section 5.1)

## Training on Your Data

**Yes, by default. You can opt out.**

Terms of Use, Section 4.3:

> "Under the premise of secure encryption technology processing, strict de-identification rendering, and irreversibility to identify specific individuals, we may, to a minimal extent, use Inputs and Outputs to provide, maintain, operate, develop or improve the Services or the underlying technologies supporting the Services."

> "If you refuse to allow us to process the data in the manner described above, you can opt out by turning off 'Improve the model for everyone'."

Model Training Disclosure, Section II.2 (Optimization Training Phase):

> "If user input is used to construct training data, we apply secure encryption, strict de-identification, and anonymization to make it cannot be linked to any specific individual. We also deploy measures to make personal information not appear in the model's outputs to other users and we will not use it for user profiling or personalized recommendations."

Privacy Policy, Your Rights:

> "the right to opt-out of using your Personal Data for training our models or optimizing our technologies."

## Data Retention

**As long as you have an account, plus whatever legal obligations require.**

No specific number of days is stated. The policy uses open-ended language.

Privacy Policy:

> "We retain Personal Data for as long as necessary to provide our Services and for the other purposes set out in this Privacy Policy. We also retain Personal Data when necessary to comply with contractual and legal obligations, when we have a legitimate business interest to do so (such as improving and developing our Services and enhancing their safety, security and stability), and for the exercise or defense of legal claims."

> "when we process your Personal Data to provide you with the Services, we keep this Personal Data for as long as you have an account. This Personal Data includes your account Personal Data, input and payment Personal Data."

> "When the Personal Data collected is no longer required by us, we and our service providers will perform the necessary procedures for destroying, deleting, erasing, or converting it into an anonymous form as permitted or required under applicable laws."

After account deletion, DeepSeek still retains data "as required by laws and regulations." (Terms of Use, Section 2.5)

## What You Can Do

Terms of Use, Section 4.2(3) grants broad usage rights for both Inputs and Outputs:

> "You may apply the Inputs and Outputs of the Services to a wide range of use cases, including personal use, academic research, derivative product development, training other models (such as model distillation), etc., as long as such usage is legal and adhere to these Terms."

Specifically, you may:

- Use Outputs for personal, commercial, or academic purposes
- Build derivative products from Outputs
- Train other models on Outputs (model distillation is explicitly permitted)
- Store your own session data (Inputs and Outputs) -- you own them
- Share Dialogues via the built-in URL sharing feature
- Opt out of model training via the "Improve the model for everyone" toggle
- Request deletion of your data by contacting privacy@deepseek.com
- Request a portable copy of your Personal Data

## What You Cannot Do

- Publish or disseminate Outputs without (1) verifying their accuracy, (2) labeling them as AI-generated, and (3) complying with usage restrictions (Terms of Use, Section 3.1)
- Use DeepSeek branding, trademarks, or logos without permission (Terms of Use, Section 6.2)
- Reverse engineer, decompile, or probe the model/system (Terms of Use, Section 3.5)
- Copy, transfer, lease, lend, sell, or sub-license the Services without authorization (Terms of Use, Section 3.6(4))
- Use the service for hateful, pornographic, violent, discriminatory, or illegal content (Terms of Use, Section 3.4)
- Impersonate real people without labeling the content as "unofficial" or "parody" (Terms of Use, Section 3.4(10))
- Use Outputs as the sole basis for decisions with legal or material impact on people (e.g., credit, employment, insurance, legal, medical) without human review (Terms of Use, Section 5.4)
- Remove or alter AI-generated content labels (Terms of Use, Section 5.3)

## Notable Points

1. **Data jurisdiction: China.** Privacy Policy: "To provide you with our services, we directly collect, process and store your Personal Data in People's Republic of China." This is stated twice (once in the main body, once in the EEA/UK supplement). All data flows to servers in China regardless of where the user is located.

2. **Governing law: PRC.** "The establishment, execution, interpretation, and resolution of disputes under these Terms shall be governed by the laws of the People's Republic of China in the mainland." (Terms of Use, Section 10.1) Disputes go to courts in Hangzhou, China.

3. **EU/UK representation.** DeepSeek has appointed Prighter Group as its privacy representative for the EU and UK. Data subject requests can be sent to rep_deepseek@prighter.com.

4. **No SLA or accuracy guarantees.** Services are provided "AS IS" and "AS AVAILABLE" with no warranty of accuracy, uptime, or fitness for purpose. Liability is capped at the greater of fees paid in the past 12 months or $100.

5. **Sensitive data prohibition.** "We do not ask for, and you should not provide sensitive Personal Data to the Services, whether about yourself or other individuals."

6. **Shared Dialogues can be crawled.** If you use the URL-sharing feature to share conversations publicly, DeepSeek warns that anti-crawling measures "cannot entirely eliminate" the risk of third-party scraping.

7. **Open Platform developers bear end-user liability.** If you build apps on the API, you are the data controller for your end users' personal data. DeepSeek's privacy policy does not cover those end users. (Open Platform Terms, Section 5.3; Privacy Policy, Introduction)

---

*This is a research summary, not legal advice.*
