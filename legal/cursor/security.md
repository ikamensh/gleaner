<!-- Source: https://cursor.com/security -->
<!-- Downloaded: 2026-04-02 -->
<!-- Converted with html2text (deterministic, no AI) -->

# Security

Last updated Jan 27, 2026

### Table of Contents

↑

  * Certifications and third-party assessments
  * Infrastructure security
  * Client security
  * AI requests
  * Codebase indexing
  * Privacy mode guarantee
  * Account deletion
  * Vulnerability disclosures



Keeping your source code and developer environment secure is important to us. This page outlines how we approach security for Cursor.

**Please submit potential vulnerabilities via email to[security-reports@cursor.com](<mailto:security-reports@cursor.com>).**

For any security-related questions, feel free to contact us at [security@cursor.com](<mailto:security@cursor.com>).

_While we have several large organizations already trusting Cursor, please note that we are still in the journey of growing our product and improving our security posture. If you 're working in a highly sensitive environment, you should be careful when using Cursor (or any other AI tool). We hope this page gives insight into our progress and helps you make a proper risk assessment._

## #Certifications and third-party assessments

Cursor is SOC 2 Type II certified. Please visit [trust.cursor.com](<https://trust.cursor.com>) to request a copy of the report.

We commit to doing at-least-annual penetration testing by reputable third parties. Please visit [trust.cursor.com](<https://trust.cursor.com>) to request an executive summary of the latest report.

## #Infrastructure security

We depend on the following subprocessors, roughly organized from most critical to least. Note that code data is sent up to our servers to power all of Cursor's AI features (see [AI Requests section](<https://www.cursor.com/security#ai>)), and that code data for users on privacy mode (legacy) is never persisted (see [Privacy Mode Guarantee](<https://www.cursor.com/security#privacy-mode-guarantee>) section).

Explore how each mode affects how data is sent and stored:

Privacy Mode↓

Explore how each mode affects how data is sent and stored.

  * [AWS](<https://aws.amazon.com/>)Sees and stores code data: Our infrastructure is primarily hosted on AWS. Our primary servers are in the US, with some latency critical services in Europe and Singapore.
  * [Cloudflare](<https://cloudflare.com/>)Sees code data: We use Cloudflare as a reverse proxy in front of parts of our API and website in order to improve performance and security.
  * [Microsoft Azure](<https://azure.microsoft.com/>)Sees code data: Some secondary infrastructure is hosted on Microsoft Azure. All of our Azure servers are in the US.
  * [Google Cloud Platform (GCP)](<https://cloud.google.com/>)Sees code data: Some secondary infrastructure is hosted on Google Cloud Platform (GCP). All of our GCP servers are in the US.
  * [Fireworks](<https://fireworks.ai/>)Sees code data: Our custom models are hosted with Fireworks, on servers in the US, Europe, or Japan. We have a zero data retention agreement with Fireworks for users in Privacy Mode and Privacy Mode (Legacy). For Share Data users, Fireworks may temporarily access and store model inputs and outputs to improve our inference performance, for the minimum duration required to perform such tasks, after which it is securely deleted. Fireworks does not reuse the data for any other purpose.
  * [Baseten](<https://baseten.co/>)Sees code data: Our custom models are hosted with Baseten, on servers in the US and Canada. We have a zero data retention agreement with Baseten for users in Privacy Mode and Privacy Mode (Legacy). For Share Data users, Baseten may temporarily access and store model inputs and outputs to improve our inference performance, for the minimum duration required to perform such tasks, after which it is securely deleted. Baseten does not reuse the data for any other purpose.
  * [Together](<https://together.ai/>)Sees code data: Our custom models are hosted with Together, on servers in the US. We have a zero data retention agreement with Together for users in Privacy Mode and Privacy Mode (Legacy). For Share Data users, Together may temporarily access and store model inputs and outputs to improve our inference performance, for the minimum duration required to perform such tasks, after which it is securely deleted. Together does not reuse the data for any other purpose.
  * [OpenAI](<https://openai.com/>)Sees code data: We rely on OpenAI's models to provide AI responses. In Privacy Mode and Privacy Mode (Legacy), we have a zero data retention agreement with OpenAI. Additionally, requests may be sent to OpenAI for certain background or summarization tasks with zero data retention, regardless of which model provider you have selected*. For users that created their account after October 15, 2025, in Share Data mode, prompts and limited telemetry may also be shared with OpenAI when directly using their models.
  * [Anthropic](<https://anthropic.com/>)Sees code data: We rely on many of Anthropic's models to give AI responses. Additionally, requests may be sent to Anthropic for certain background or summarization tasks with zero data retention, regardless of which model provider you have selected*. We have a zero data retention agreement with Anthropic.
  * [Google Cloud Vertex API](<https://cloud.google.com/vertex-ai>)Sees code data: We rely on some Gemini models offered over Google Cloud's Vertex API to give AI responses. Requests may be sent to Google Cloud Vertex API for certain background or summarization tasks with zero data retention, regardless of which model provider you have selected*. We have a zero data retention agreement with Vertex.
  * [xAI](<https://x.ai/api>)Sees code data: We rely on some Grok models offered over the xAI API to give AI responses. We have a zero data retention agreement with xAI.
  * [Turbopuffer](<https://turbopuffer.com/>)Stores obfuscated code data: Embeddings of indexed codebases, as well as metadata associated with the embeddings (obfuscated file names), are stored with Turbopuffer on Google Cloud's servers in the US. You can read more on the Turbopuffer security page. Users can disable codebase indexing; read more about it in the Codebase Indexing section of this document.
  * [Exa](<https://exa.ai/>)See search requests (potentially derived from code data): Used for web search functionality. Search requests are potentially derived from code data (e.g., when using "@web" in the chat, a separate language model will look at your message, conversation history and current file to determine what to search for, and Exa/SerpApi will see the resulting search query).



*_Cursor respects model blocklists and will not send any requests to models on a blocklist._

None of our infrastructure is in China. We do not directly use any Chinese company as a subprocessor, and to our knowledge none of our subprocessors do either.

We assign infrastructure access to team members on a least-privilege basis. We enforce multi-factor authentication for AWS. We restrict access to resources using both network-level controls and secrets.

## #Client security

Cursor is a fork of the open-source [Visual Studio Code ](<https://github.com/microsoft/vscode>)(VS Code), maintained by Microsoft. They publish security advisories on their [GitHub security page](<https://github.com/microsoft/vscode/security>). Every other mainline VS Code release, we merge the upstream `'microsoft/vscode'` codebase into Cursor. You can check which version of VS Code that your Cursor version is based on by clicking "Cursor > About Cursor" in the app. If there is a high-severity security-related patch in the upstream VS Code, we will cherry-pick the fix before the next merge and release immediately.

Our app will make requests to the following domains to communicate with our backend. If you're behind a corporate proxy, please whitelist these domains to ensure that Cursor works correctly.

  * `'api2.cursor.sh'`: Used for most API requests.

  * `'api5.cursor.sh'`: Used for Cursor's agent requests.

  * `'api3.cursor.sh'`: Used for Cursor Tab requests (HTTP/2 only).

  * `'repo42.cursor.sh'`: Used for codebase indexing (HTTP/2 only).

  * `'api4.cursor.sh'`, `'us-asia.gcpp.cursor.sh'`, `'us-eu.gcpp.cursor.sh'`, `'us-only.gcpp.cursor.sh'`: Used for Cursor Tab requests depending on your location (HTTP/2 only).

  * `'adminportal42.cursor.sh'`: Used to configure SSO and domain verification.

  * `'marketplace.cursorapi.com'`, `'cursor-cdn.com'`, `'downloads.cursor.com'`, `'anysphere-binaries.s3.us-east-1.amazonaws.com'`: Used for client updates and for downloading extensions from the extension marketplace.




Two security-related differences to VS Code to note:

  1. [Workspace Trust](<https://code.visualstudio.com/docs/editor/workspace-trust>) is disabled by default in Cursor. You can enable it by setting `'security.workspace.trust.enabled'` to `'true'` in your Cursor settings. It is disabled by default to prevent confusion between Workspace Trust's "Restricted Mode" and Cursor's "Privacy Mode", and because its trust properties are nuanced and hard to understand (for example, even with Workspace Trust enabled, you are not protected from malicious extensions, only from malicious folders). We are open to community feedback on whether we should enable it by default.

  2. Extension code signatures: Cursor does not verify signatures of extensions that are downloaded from the marketplace. VS Code recently started doing this. In particular, the `'extensions.verifySignature'` setting defaults to `'false'` in Cursor but to `'true'` in VS Code. If you set it to `'true'` in Cursor, you'll see a pop-up saying that signature verification failed, every time you try to download an extension. We hope to start supporting extension signature verification in the medium-term future.




## #AI requests

To provide its features, Cursor makes AI requests to our server. This happens for many different reasons. For example, we send AI requests when you ask questions in chat, we send AI requests on every keystroke so that Cursor Tab can make suggestions for you, and we may also send AI requests in the background for building up context or looking for bugs to show you.

An AI request generally includes context such as your recently viewed files, your conversation history, and relevant pieces of code based on language server information. This code data is sent to our infrastructure on AWS, and then to the appropriate language model inference provider (Fireworks/OpenAI/Anthropic/Google). Note that the requests always hit our infrastructure on AWS even if you have configured your own API key for OpenAI in the settings.

We currently do not have the ability to direct-route from the Cursor app to your enterprise deployment of OpenAI/Azure/Anthropic, as our prompt-building happens on our server, and our custom models on Fireworks are critical in providing a good user experience. We do not yet have a self-hosted server deployment option.

## #Codebase indexing

Cursor allows you to semantically index your codebase, which allows it to answer questions with the context of all of your code as well as write better code by referencing existing implementations. Codebase indexing is enabled by default, but can be turned off in settings.

Our codebase indexing feature works as follows: when enabled, it scans the folder that you open in Cursor and computes a Merkle tree of hashes of all files. Files and subdirectories specified by `'.gitignore'` or `'.cursorignore'` are ignored. The Merkle tree is then synced to the server. Every 10 minutes, we check for hash mismatches, and use the Merkle tree to figure out which files have changed and only upload those.

At our server, we chunk and embed the files, and store the embeddings in [Turbopuffer](<https://turbopuffer.com/>). To allow filtering vector search results by file path, we store with every vector an obfuscated relative file path, as well as the line range the chunk corresponds to. We also store the embedding in a cache in AWS, indexed by the hash of the chunk, to ensure that indexing the same codebase a second time is much faster (which is particularly useful for teams).

At inference time, we compute an embedding, let Turbopuffer do the nearest neighbor search, send back the obfuscated file path and line range to the client, and read those file chunks on the client locally. We then send those chunks back up to the server to answer the user's question. This means that for privacy mode users, no plaintext code is stored on our servers or in Turbopuffer.

Some notes:

  * To block specific files in your codebase from being sent to Cursor's servers and included in AI requests, add a `'.cursorignore'` file to your codebase that lists the files and directories that should be excluded. Cursor will make a best effort to prevent exposure of these files from being included in any request.

  * File path obfuscation details: the path is split by `'/'` and `'.'` and each segment is encrypted with a secret key stored on the client and a deterministic short 6-byte nonce. This leaks information about directory hierarchy, and will have some nonce collisions, but hides most information.

  * Embedding reversal: academic work has shown that reversing embeddings is possible in some cases. Current attacks rely on having access to the model and embedding short strings into big vectors, which makes us believe that the attack would be somewhat difficult to do here. That said, it is definitely possible for an adversary who breaks into our vector database to learn things about the indexed codebases.

  * When codebase indexing is enabled in a Git repo, we also index the Git history. Specifically, we store commit SHAs, parent information and obfuscated file names (same as above). To allow sharing the data structure for users in the same Git repo and on the same team, the secret key for obfuscating the file names is derived from hashes of recent commit contents. Commit messages and file contents or diffs are not indexed.

  * Our indexing feature often experiences heavy load, which can cause many requests to fail. This means that sometimes, files will need to be uploaded several times before they get fully indexed. One way this manifests is that if you check the network traffic to `'repo42.cursor.sh'`, you may see more bandwidth used than expected.




## #Privacy mode guarantee

Privacy mode can be enabled in settings or by a team admin. When it is enabled, we guarantee that code data is never stored by our model providers or used for training. Privacy mode can be enabled by anyone (free or Pro user), and is by default forcibly enabled for any user that is a member of a team.

We take the privacy mode guarantee very seriously. More than 50% of all Cursor users have privacy mode enabled.

Each request to our server includes an `'x-ghost-mode'` header, containing a boolean value denoting if the user is on privacy mode. To prevent accidentally treating a privacy mode user as a non-privacy mode user, we always default to assuming that a user is on privacy mode if the header is missing.

All requests to our server first hit a proxy, that decides which logical service should handle the request (e.g., the "chat service" or the "Cursor Tab service"). Each logical service comes in two near-identical replicas: one replica that handles privacy mode requests, and one replica that handles non-privacy mode requests. The proxy checks the value of the `'x-ghost-mode'` header and sends the request to the appropriate replica. The replicas themselves also check the header for redundancy. By default, all log functions from the privacy mode replicas are no-ops, unless suffixed like `'infoUnrestricted'`, which we carefully review to never attach any potential code data or prompts. For requests that spawn off background tasks, we similarly have parallel queues and worker replicas for privacy mode and non-privacy mode. This parallel infrastructure makes us confident in our privacy mode guarantee and its resilience against accidental mistakes or bugs.

For team-level privacy mode enforcement, each client pings the server every 5 minutes to check if the user is on a team that enforces privacy mode. If so, it overrides the client's privacy mode setting. To prevent cases where the privacy mode ping by the client fails for any reason, our server also, in the hot path, checks whether the user is part of a team that enforces privacy mode, and if so treats the request as if it is on privacy mode even if the header says otherwise. On latency-sensitive services, we cache this value for 5 minutes, and for any cache miss we assume that the user is on privacy mode. All in all, this means that when a user joins a team, they will be guaranteed to be on privacy mode at the very latest 5 minutes after joining the team.

## #Account deletion

You can delete your account at any time in the [Settings dashboard](<https://cursor.com/settings>) (click "Advanced" and then "Delete Account"). This will delete all data associated with your account, including any indexed codebases. We guarantee complete removal of your data within 30 days (we immediately delete the data, but some of our databases and cloud storage have backups of no more than 30 days).

It's worth noting that if any of your data was used in model training (which would only happen if you were not on privacy mode at the time), our existing trained models will not be immediately retrained. However, any future models that are trained will not be trained on your data, since that data will have been deleted.

## #Vulnerability disclosures

If you believe you have found a vulnerability in Cursor, please submit the report to us at [security-reports@cursor.com](<mailto:security-reports@cursor.com>).

We commit to acknowledging vulnerability reports within 5 business days, and addressing them as soon as we are able to. Critical incidents will be communicated via email to all users.

### Product

  * [Agents](</en-US/product>)
  * [Enterprise](</en-US/enterprise>)
  * [Pricing](</en-US/pricing>)
  * [Code Review](</en-US/bugbot>)
  * [Tab](</en-US/product/tab>)
  * [CLI](</en-US/cli>)
  * [Cloud Agents](</agents>)
  * [Marketplace ↗](<https://cursor.com/marketplace>)



### Resources

  * [Download](</en-US/download>)
  * [Changelog](</en-US/changelog>)
  * [Docs](</docs>)
  * [Learn ↗](<https://cursor.com/learn>)
  * [Forum ↗](<https://forum.cursor.com/>)
  * [Help ↗](<https://cursor.com/help>)
  * [Workshops](</en-US/workshops>)
  * [Status ↗](<https://status.cursor.com/>)



### Company

  * [Careers](</en-US/careers>)
  * [Blog](</en-US/blog>)
  * [Community](</en-US/community>)
  * [Students](</en-US/students>)
  * [Brand](</en-US/brand>)
  * [Future](</en-US/future>)
  * [Anysphere ↗](<https://anysphere.inc/>)



### Legal

  * [Terms of Service](</en-US/terms-of-service>)
  * [Privacy Policy](</en-US/privacy>)
  * [Data Use](</en-US/data-use>)
  * [Security](</en-US/security>)



### Connect

  * [X ↗](<https://x.com/cursor_ai>)
  * [LinkedIn ↗](<https://www.linkedin.com/company/cursorai>)
  * [YouTube ↗](<https://www.youtube.com/@cursor_ai>)



© 2026 [Anysphere, Inc.](<https://anysphere.inc>)🛡 [SOC 2 Certified](</en-US/security>)

🌐English↓

  * English✓
  * 简体中文
  * 日本語
  * 繁體中文
  * Español
  * Français
  * Português
  * 한국어
  * Deutsch




[Cursor](</home>)

  * [Product](</product>)↓

    * [Agents](</product>)
    * [Code Review](</bugbot>)
    * [Cloud ↗](<https://cursor.com/agents>)
    * [Tab](</product/tab>)
    * [CLI](</cli>)
    * [Marketplace ↗](<https://cursor.com/marketplace>)

  * [Enterprise](</enterprise>)
  * [Pricing](</pricing>)
  * [Resources](</changelog>)↓

    * [Changelog](</changelog>)
    * [Blog](</blog>)
    * [Docs](</docs>)
    * [Community](</community>)
    * [Help ↗](<https://cursor.com/help>)
    * [Workshops](</workshops>)
    * [Forum ↗](<https://forum.cursor.com/>)
    * [Careers](</careers>)




  * Product →
  * [Enterprise](</enterprise>)

  * [Pricing](</pricing>)

  * Resources →



[Sign in](</dashboard>)[ContactContact sales](</contact-sales?source=navbar>)[Download](</download>)

# Security

Last updated Jan 27, 2026

### Table of Contents

↑

  * Certifications and third-party assessments
  * Infrastructure security
  * Client security
  * AI requests
  * Codebase indexing
  * Privacy mode guarantee
  * Account deletion
  * Vulnerability disclosures



Keeping your source code and developer environment secure is important to us. This page outlines how we approach security for Cursor.

**Please submit potential vulnerabilities via email to[security-reports@cursor.com](<mailto:security-reports@cursor.com>).**

For any security-related questions, feel free to contact us at [security@cursor.com](<mailto:security@cursor.com>).

_While we have several large organizations already trusting Cursor, please note that we are still in the journey of growing our product and improving our security posture. If you 're working in a highly sensitive environment, you should be careful when using Cursor (or any other AI tool). We hope this page gives insight into our progress and helps you make a proper risk assessment._

## #Certifications and third-party assessments

Cursor is SOC 2 Type II certified. Please visit [trust.cursor.com](<https://trust.cursor.com>) to request a copy of the report.

We commit to doing at-least-annual penetration testing by reputable third parties. Please visit [trust.cursor.com](<https://trust.cursor.com>) to request an executive summary of the latest report.

## #Infrastructure security

We depend on the following subprocessors, roughly organized from most critical to least. Note that code data is sent up to our servers to power all of Cursor's AI features (see [AI Requests section](<https://www.cursor.com/security#ai>)), and that code data for users on privacy mode (legacy) is never persisted (see [Privacy Mode Guarantee](<https://www.cursor.com/security#privacy-mode-guarantee>) section).

Explore how each mode affects how data is sent and stored:

Privacy Mode↓

Explore how each mode affects how data is sent and stored.

  * [AWS](<https://aws.amazon.com/>)Sees and stores code data: Our infrastructure is primarily hosted on AWS. Our primary servers are in the US, with some latency critical services in Europe and Singapore.
  * [Cloudflare](<https://cloudflare.com/>)Sees code data: We use Cloudflare as a reverse proxy in front of parts of our API and website in order to improve performance and security.
  * [Microsoft Azure](<https://azure.microsoft.com/>)Sees code data: Some secondary infrastructure is hosted on Microsoft Azure. All of our Azure servers are in the US.
  * [Google Cloud Platform (GCP)](<https://cloud.google.com/>)Sees code data: Some secondary infrastructure is hosted on Google Cloud Platform (GCP). All of our GCP servers are in the US.
  * [Fireworks](<https://fireworks.ai/>)Sees code data: Our custom models are hosted with Fireworks, on servers in the US, Europe, or Japan. We have a zero data retention agreement with Fireworks for users in Privacy Mode and Privacy Mode (Legacy). For Share Data users, Fireworks may temporarily access and store model inputs and outputs to improve our inference performance, for the minimum duration required to perform such tasks, after which it is securely deleted. Fireworks does not reuse the data for any other purpose.
  * [Baseten](<https://baseten.co/>)Sees code data: Our custom models are hosted with Baseten, on servers in the US and Canada. We have a zero data retention agreement with Baseten for users in Privacy Mode and Privacy Mode (Legacy). For Share Data users, Baseten may temporarily access and store model inputs and outputs to improve our inference performance, for the minimum duration required to perform such tasks, after which it is securely deleted. Baseten does not reuse the data for any other purpose.
  * [Together](<https://together.ai/>)Sees code data: Our custom models are hosted with Together, on servers in the US. We have a zero data retention agreement with Together for users in Privacy Mode and Privacy Mode (Legacy). For Share Data users, Together may temporarily access and store model inputs and outputs to improve our inference performance, for the minimum duration required to perform such tasks, after which it is securely deleted. Together does not reuse the data for any other purpose.
  * [OpenAI](<https://openai.com/>)Sees code data: We rely on OpenAI's models to provide AI responses. In Privacy Mode and Privacy Mode (Legacy), we have a zero data retention agreement with OpenAI. Additionally, requests may be sent to OpenAI for certain background or summarization tasks with zero data retention, regardless of which model provider you have selected*. For users that created their account after October 15, 2025, in Share Data mode, prompts and limited telemetry may also be shared with OpenAI when directly using their models.
  * [Anthropic](<https://anthropic.com/>)Sees code data: We rely on many of Anthropic's models to give AI responses. Additionally, requests may be sent to Anthropic for certain background or summarization tasks with zero data retention, regardless of which model provider you have selected*. We have a zero data retention agreement with Anthropic.
  * [Google Cloud Vertex API](<https://cloud.google.com/vertex-ai>)Sees code data: We rely on some Gemini models offered over Google Cloud's Vertex API to give AI responses. Requests may be sent to Google Cloud Vertex API for certain background or summarization tasks with zero data retention, regardless of which model provider you have selected*. We have a zero data retention agreement with Vertex.
  * [xAI](<https://x.ai/api>)Sees code data: We rely on some Grok models offered over the xAI API to give AI responses. We have a zero data retention agreement with xAI.
  * [Turbopuffer](<https://turbopuffer.com/>)Stores obfuscated code data: Embeddings of indexed codebases, as well as metadata associated with the embeddings (obfuscated file names), are stored with Turbopuffer on Google Cloud's servers in the US. You can read more on the Turbopuffer security page. Users can disable codebase indexing; read more about it in the Codebase Indexing section of this document.
  * [Exa](<https://exa.ai/>)See search requests (potentially derived from code data): Used for web search functionality. Search requests are potentially derived from code data (e.g., when using "@web" in the chat, a separate language model will look at your message, conversation history and current file to determine what to search for, and Exa/SerpApi will see the resulting search query).



*_Cursor respects model blocklists and will not send any requests to models on a blocklist._

None of our infrastructure is in China. We do not directly use any Chinese company as a subprocessor, and to our knowledge none of our subprocessors do either.

We assign infrastructure access to team members on a least-privilege basis. We enforce multi-factor authentication for AWS. We restrict access to resources using both network-level controls and secrets.

## #Client security

Cursor is a fork of the open-source [Visual Studio Code ](<https://github.com/microsoft/vscode>)(VS Code), maintained by Microsoft. They publish security advisories on their [GitHub security page](<https://github.com/microsoft/vscode/security>). Every other mainline VS Code release, we merge the upstream `'microsoft/vscode'` codebase into Cursor. You can check which version of VS Code that your Cursor version is based on by clicking "Cursor > About Cursor" in the app. If there is a high-severity security-related patch in the upstream VS Code, we will cherry-pick the fix before the next merge and release immediately.

Our app will make requests to the following domains to communicate with our backend. If you're behind a corporate proxy, please whitelist these domains to ensure that Cursor works correctly.

  * `'api2.cursor.sh'`: Used for most API requests.

  * `'api5.cursor.sh'`: Used for Cursor's agent requests.

  * `'api3.cursor.sh'`: Used for Cursor Tab requests (HTTP/2 only).

  * `'repo42.cursor.sh'`: Used for codebase indexing (HTTP/2 only).

  * `'api4.cursor.sh'`, `'us-asia.gcpp.cursor.sh'`, `'us-eu.gcpp.cursor.sh'`, `'us-only.gcpp.cursor.sh'`: Used for Cursor Tab requests depending on your location (HTTP/2 only).

  * `'adminportal42.cursor.sh'`: Used to configure SSO and domain verification.

  * `'marketplace.cursorapi.com'`, `'cursor-cdn.com'`, `'downloads.cursor.com'`, `'anysphere-binaries.s3.us-east-1.amazonaws.com'`: Used for client updates and for downloading extensions from the extension marketplace.




Two security-related differences to VS Code to note:

  1. [Workspace Trust](<https://code.visualstudio.com/docs/editor/workspace-trust>) is disabled by default in Cursor. You can enable it by setting `'security.workspace.trust.enabled'` to `'true'` in your Cursor settings. It is disabled by default to prevent confusion between Workspace Trust's "Restricted Mode" and Cursor's "Privacy Mode", and because its trust properties are nuanced and hard to understand (for example, even with Workspace Trust enabled, you are not protected from malicious extensions, only from malicious folders). We are open to community feedback on whether we should enable it by default.

  2. Extension code signatures: Cursor does not verify signatures of extensions that are downloaded from the marketplace. VS Code recently started doing this. In particular, the `'extensions.verifySignature'` setting defaults to `'false'` in Cursor but to `'true'` in VS Code. If you set it to `'true'` in Cursor, you'll see a pop-up saying that signature verification failed, every time you try to download an extension. We hope to start supporting extension signature verification in the medium-term future.




## #AI requests

To provide its features, Cursor makes AI requests to our server. This happens for many different reasons. For example, we send AI requests when you ask questions in chat, we send AI requests on every keystroke so that Cursor Tab can make suggestions for you, and we may also send AI requests in the background for building up context or looking for bugs to show you.

An AI request generally includes context such as your recently viewed files, your conversation history, and relevant pieces of code based on language server information. This code data is sent to our infrastructure on AWS, and then to the appropriate language model inference provider (Fireworks/OpenAI/Anthropic/Google). Note that the requests always hit our infrastructure on AWS even if you have configured your own API key for OpenAI in the settings.

We currently do not have the ability to direct-route from the Cursor app to your enterprise deployment of OpenAI/Azure/Anthropic, as our prompt-building happens on our server, and our custom models on Fireworks are critical in providing a good user experience. We do not yet have a self-hosted server deployment option.

## #Codebase indexing

Cursor allows you to semantically index your codebase, which allows it to answer questions with the context of all of your code as well as write better code by referencing existing implementations. Codebase indexing is enabled by default, but can be turned off in settings.

Our codebase indexing feature works as follows: when enabled, it scans the folder that you open in Cursor and computes a Merkle tree of hashes of all files. Files and subdirectories specified by `'.gitignore'` or `'.cursorignore'` are ignored. The Merkle tree is then synced to the server. Every 10 minutes, we check for hash mismatches, and use the Merkle tree to figure out which files have changed and only upload those.

At our server, we chunk and embed the files, and store the embeddings in [Turbopuffer](<https://turbopuffer.com/>). To allow filtering vector search results by file path, we store with every vector an obfuscated relative file path, as well as the line range the chunk corresponds to. We also store the embedding in a cache in AWS, indexed by the hash of the chunk, to ensure that indexing the same codebase a second time is much faster (which is particularly useful for teams).

At inference time, we compute an embedding, let Turbopuffer do the nearest neighbor search, send back the obfuscated file path and line range to the client, and read those file chunks on the client locally. We then send those chunks back up to the server to answer the user's question. This means that for privacy mode users, no plaintext code is stored on our servers or in Turbopuffer.

Some notes:

  * To block specific files in your codebase from being sent to Cursor's servers and included in AI requests, add a `'.cursorignore'` file to your codebase that lists the files and directories that should be excluded. Cursor will make a best effort to prevent exposure of these files from being included in any request.

  * File path obfuscation details: the path is split by `'/'` and `'.'` and each segment is encrypted with a secret key stored on the client and a deterministic short 6-byte nonce. This leaks information about directory hierarchy, and will have some nonce collisions, but hides most information.

  * Embedding reversal: academic work has shown that reversing embeddings is possible in some cases. Current attacks rely on having access to the model and embedding short strings into big vectors, which makes us believe that the attack would be somewhat difficult to do here. That said, it is definitely possible for an adversary who breaks into our vector database to learn things about the indexed codebases.

  * When codebase indexing is enabled in a Git repo, we also index the Git history. Specifically, we store commit SHAs, parent information and obfuscated file names (same as above). To allow sharing the data structure for users in the same Git repo and on the same team, the secret key for obfuscating the file names is derived from hashes of recent commit contents. Commit messages and file contents or diffs are not indexed.

  * Our indexing feature often experiences heavy load, which can cause many requests to fail. This means that sometimes, files will need to be uploaded several times before they get fully indexed. One way this manifests is that if you check the network traffic to `'repo42.cursor.sh'`, you may see more bandwidth used than expected.




## #Privacy mode guarantee

Privacy mode can be enabled in settings or by a team admin. When it is enabled, we guarantee that code data is never stored by our model providers or used for training. Privacy mode can be enabled by anyone (free or Pro user), and is by default forcibly enabled for any user that is a member of a team.

We take the privacy mode guarantee very seriously. More than 50% of all Cursor users have privacy mode enabled.

Each request to our server includes an `'x-ghost-mode'` header, containing a boolean value denoting if the user is on privacy mode. To prevent accidentally treating a privacy mode user as a non-privacy mode user, we always default to assuming that a user is on privacy mode if the header is missing.

All requests to our server first hit a proxy, that decides which logical service should handle the request (e.g., the "chat service" or the "Cursor Tab service"). Each logical service comes in two near-identical replicas: one replica that handles privacy mode requests, and one replica that handles non-privacy mode requests. The proxy checks the value of the `'x-ghost-mode'` header and sends the request to the appropriate replica. The replicas themselves also check the header for redundancy. By default, all log functions from the privacy mode replicas are no-ops, unless suffixed like `'infoUnrestricted'`, which we carefully review to never attach any potential code data or prompts. For requests that spawn off background tasks, we similarly have parallel queues and worker replicas for privacy mode and non-privacy mode. This parallel infrastructure makes us confident in our privacy mode guarantee and its resilience against accidental mistakes or bugs.

For team-level privacy mode enforcement, each client pings the server every 5 minutes to check if the user is on a team that enforces privacy mode. If so, it overrides the client's privacy mode setting. To prevent cases where the privacy mode ping by the client fails for any reason, our server also, in the hot path, checks whether the user is part of a team that enforces privacy mode, and if so treats the request as if it is on privacy mode even if the header says otherwise. On latency-sensitive services, we cache this value for 5 minutes, and for any cache miss we assume that the user is on privacy mode. All in all, this means that when a user joins a team, they will be guaranteed to be on privacy mode at the very latest 5 minutes after joining the team.

## #Account deletion

You can delete your account at any time in the [Settings dashboard](<https://cursor.com/settings>) (click "Advanced" and then "Delete Account"). This will delete all data associated with your account, including any indexed codebases. We guarantee complete removal of your data within 30 days (we immediately delete the data, but some of our databases and cloud storage have backups of no more than 30 days).

It's worth noting that if any of your data was used in model training (which would only happen if you were not on privacy mode at the time), our existing trained models will not be immediately retrained. However, any future models that are trained will not be trained on your data, since that data will have been deleted.

## #Vulnerability disclosures

If you believe you have found a vulnerability in Cursor, please submit the report to us at [security-reports@cursor.com](<mailto:security-reports@cursor.com>).

We commit to acknowledging vulnerability reports within 5 business days, and addressing them as soon as we are able to. Critical incidents will be communicated via email to all users.

### Product

  * [Agents](</en-US/product>)
  * [Enterprise](</en-US/enterprise>)
  * [Pricing](</en-US/pricing>)
  * [Code Review](</en-US/bugbot>)
  * [Tab](</en-US/product/tab>)
  * [CLI](</en-US/cli>)
  * [Cloud Agents](</agents>)
  * [Marketplace ↗](<https://cursor.com/marketplace>)



### Resources

  * [Download](</en-US/download>)
  * [Changelog](</en-US/changelog>)
  * [Docs](</docs>)
  * [Learn ↗](<https://cursor.com/learn>)
  * [Forum ↗](<https://forum.cursor.com/>)
  * [Help ↗](<https://cursor.com/help>)
  * [Workshops](</en-US/workshops>)
  * [Status ↗](<https://status.cursor.com/>)



### Company

  * [Careers](</en-US/careers>)
  * [Blog](</en-US/blog>)
  * [Community](</en-US/community>)
  * [Students](</en-US/students>)
  * [Brand](</en-US/brand>)
  * [Future](</en-US/future>)
  * [Anysphere ↗](<https://anysphere.inc/>)



### Legal

  * [Terms of Service](</en-US/terms-of-service>)
  * [Privacy Policy](</en-US/privacy>)
  * [Data Use](</en-US/data-use>)
  * [Security](</en-US/security>)



### Connect

  * [X ↗](<https://x.com/cursor_ai>)
  * [LinkedIn ↗](<https://www.linkedin.com/company/cursorai>)
  * [YouTube ↗](<https://www.youtube.com/@cursor_ai>)



© 2026 [Anysphere, Inc.](<https://anysphere.inc>)🛡 [SOC 2 Certified](</en-US/security>)

🌐English↓

  * English✓
  * 简体中文
  * 日本語
  * 繁體中文
  * Español
  * Français
  * Português
  * 한국어
  * Deutsch


