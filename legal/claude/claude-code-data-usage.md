<!-- Source: https://code.claude.com/docs/en/data-usage -->
<!-- Downloaded: 2026-04-02 -->
<!-- Converted with html2text (deterministic, no AI) -->

# Data usage

Copy page

Learn about Anthropic’s data usage policies for Claude

Copy page

## 

​

Data policies

### 

​

Data training policy

**Consumer users (Free, Pro, and Max plans)** : We give you the choice to allow your data to be used to improve future Claude models. We will train new models using data from Free, Pro, and Max accounts when this setting is on (including when you use Claude Code from these accounts). **Commercial users** : (Team and Enterprise plans, API, 3rd-party platforms, and Claude Gov) maintain existing policies: Anthropic does not train generative models using code or prompts sent to Claude Code under commercial terms, unless the customer has chosen to provide their data to us for model improvement (for example, the [Developer Partner Program](<https://support.claude.com/en/articles/11174108-about-the-development-partner-program>)).

### 

​

Development Partner Program

If you explicitly opt in to methods to provide us with materials to train on, such as via the [Development Partner Program](<https://support.claude.com/en/articles/11174108-about-the-development-partner-program>), we may use those materials provided to train our models. An organization admin can expressly opt-in to the Development Partner Program for their organization. Note that this program is available only for Anthropic first-party API, and not for Bedrock or Vertex users.

### 

​

Feedback using the `/feedback` command

If you choose to send us feedback about Claude Code using the `/feedback` command, we may use your feedback to improve our products and services. Transcripts shared via `/feedback` are retained for 5 years.

### 

​

Session quality surveys

When you see the “How is Claude doing this session?” prompt in Claude Code, responding to this survey (including selecting “Dismiss”), only your numeric rating (1, 2, 3, or dismiss) is recorded. We do not collect or store any conversation transcripts, inputs, outputs, or other session data as part of this survey. Unlike thumbs up/down feedback or `/feedback` reports, this session quality survey is a simple product satisfaction metric. Your responses to this survey do not impact your data training preferences and cannot be used to train our AI models. To disable these surveys, set `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1`. The survey is also disabled when `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set. To control frequency instead of disabling, set [`feedbackSurveyRate`](</docs/en/settings#available-settings>) in your settings file to a probability between `0` and `1`.

### 

​

Data retention

Anthropic retains Claude Code data based on your account type and preferences. **Consumer users (Free, Pro, and Max plans)** :

  * Users who allow data use for model improvement: 5-year retention period to support model development and safety improvements
  * Users who don’t allow data use for model improvement: 30-day retention period
  * Privacy settings can be changed at any time at [claude.ai/settings/data-privacy-controls](<https://claude.ai/settings/data-privacy-controls>).

**Commercial users (Team, Enterprise, and API)** :

  * Standard: 30-day retention period
  * [Zero data retention](</docs/en/zero-data-retention>): available for Claude Code on Claude for Enterprise. ZDR is enabled on a per-organization basis; each new organization must have ZDR enabled separately by your account team
  * Local caching: Claude Code clients may store sessions locally for up to 30 days to enable session resumption (configurable)

You can delete individual Claude Code on the web sessions at any time. Deleting a session permanently removes the session’s event data. For instructions on how to delete sessions, see [Managing sessions](</docs/en/claude-code-on-the-web#managing-sessions>). Learn more about data retention practices in our [Privacy Center](<https://privacy.anthropic.com/>). For full details, please review our [Commercial Terms of Service](<https://www.anthropic.com/legal/commercial-terms>) (for Team, Enterprise, and API users) or [Consumer Terms](<https://www.anthropic.com/legal/consumer-terms>) (for Free, Pro, and Max users) and [Privacy Policy](<https://www.anthropic.com/legal/privacy>).

## 

​

Data access

For all first party users, you can learn more about what data is logged for local Claude Code and remote Claude Code. [Remote Control](</docs/en/remote-control>) sessions follow the local data flow since all execution happens on your machine. Note for remote Claude Code, Claude accesses the repository where you initiate your Claude Code session. Claude does not access repositories that you have connected but have not started a session in.

## 

​

Local Claude Code: Data flow and dependencies

The diagram below shows how Claude Code connects to external services during installation and normal operation. Solid lines indicate required connections, while dashed lines represent optional or user-initiated data flows. Claude Code is installed from [NPM](<https://www.npmjs.com/package/@anthropic-ai/claude-code>). Claude Code runs locally. In order to interact with the LLM, Claude Code sends data over the network. This data includes all user prompts and model outputs. The data is encrypted in transit via TLS and is not encrypted at rest. Claude Code is compatible with most popular VPNs and LLM proxies. Claude Code is built on Anthropic’s APIs. For details regarding our API’s security controls, including our API logging procedures, please refer to compliance artifacts offered in the [Anthropic Trust Center](<https://trust.anthropic.com>).

### 

​

Cloud execution: Data flow and dependencies

When using [Claude Code on the web](</docs/en/claude-code-on-the-web>), sessions run in Anthropic-managed virtual machines instead of locally. In cloud environments:

  * **Code and data storage:** Your repository is cloned to an isolated VM. Code and session data are subject to the retention and usage policies for your account type (see Data retention section above)
  * **Credentials:** GitHub authentication is handled through a secure proxy; your GitHub credentials never enter the sandbox
  * **Network traffic:** All outbound traffic goes through a security proxy for audit logging and abuse prevention
  * **Session data:** Prompts, code changes, and outputs follow the same data policies as local Claude Code usage

For security details about cloud execution, see [Security](</docs/en/security#cloud-execution-security>).

## 

​

Telemetry services

Claude Code connects from users’ machines to the Statsig service to log operational metrics such as latency, reliability, and usage patterns. This logging does not include any code or file paths. Data is encrypted in transit using TLS and at rest using 256-bit AES encryption. Read more in the [Statsig security documentation](<https://www.statsig.com/trust/security>). To opt out of Statsig telemetry, set the `DISABLE_TELEMETRY` environment variable. Claude Code connects from users’ machines to Sentry for operational error logging. The data is encrypted in transit using TLS and at rest using 256-bit AES encryption. Read more in the [Sentry security documentation](<https://sentry.io/security/>). To opt out of error logging, set the `DISABLE_ERROR_REPORTING` environment variable. When users run the `/feedback` command, a copy of their full conversation history including code is sent to Anthropic. The data is encrypted in transit and at rest. Optionally, a Github issue is created in our public repository. To opt out, set the `DISABLE_FEEDBACK_COMMAND` environment variable to `1`.

## 

​

Default behaviors by API provider

By default, error reporting, telemetry, and bug reporting are disabled when using Bedrock, Vertex, or Foundry. Session quality surveys are the exception and appear regardless of provider. You can opt out of all non-essential traffic, including surveys, at once by setting `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`. Here are the full default behaviors:

Service| Claude API| Vertex API| Bedrock API| Foundry API  
---|---|---|---|---  
**Statsig (Metrics)**|  Default on.  
`DISABLE_TELEMETRY=1` to disable.| Default off.  
`CLAUDE_CODE_USE_VERTEX` must be 1.| Default off.  
`CLAUDE_CODE_USE_BEDROCK` must be 1.| Default off.  
`CLAUDE_CODE_USE_FOUNDRY` must be 1.  
**Sentry (Errors)**|  Default on.  
`DISABLE_ERROR_REPORTING=1` to disable.| Default off.  
`CLAUDE_CODE_USE_VERTEX` must be 1.| Default off.  
`CLAUDE_CODE_USE_BEDROCK` must be 1.| Default off.  
`CLAUDE_CODE_USE_FOUNDRY` must be 1.  
**Claude API (`/feedback` reports)**| Default on.  
`DISABLE_FEEDBACK_COMMAND=1` to disable.| Default off.  
`CLAUDE_CODE_USE_VERTEX` must be 1.| Default off.  
`CLAUDE_CODE_USE_BEDROCK` must be 1.| Default off.  
`CLAUDE_CODE_USE_FOUNDRY` must be 1.  
**Session quality surveys**|  Default on.  
`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` to disable.| Default on.  
`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` to disable.| Default on.  
`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` to disable.| Default on.  
`CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1` to disable.  
  
All environment variables can be checked into `settings.json` ([read more](</docs/en/settings>)).

Was this page helpful?

YesNo

[Server-managed settings (beta)](</docs/en/server-managed-settings>)[Zero data retention](</docs/en/zero-data-retention>)

⌘I

[Claude Code Docs home page](</docs/en/overview>)


Company

[Anthropic](<https://www.anthropic.com/company>)[Careers](<https://www.anthropic.com/careers>)[Economic Futures](<https://www.anthropic.com/economic-futures>)[Research](<https://www.anthropic.com/research>)[News](<https://www.anthropic.com/news>)[Trust center](<https://trust.anthropic.com/>)[Transparency](<https://www.anthropic.com/transparency>)

Help and security

[Availability](<https://www.anthropic.com/supported-countries>)[Status](<https://status.anthropic.com/>)[Support center](<https://support.claude.com/>)

Learn

[Courses](<https://www.anthropic.com/learn>)[MCP connectors](<https://claude.com/partners/mcp>)[Customer stories](<https://www.claude.com/customers>)[Engineering blog](<https://www.anthropic.com/engineering>)[Events](<https://www.anthropic.com/events>)[Powered by Claude](<https://claude.com/partners/powered-by-claude>)[Service partners](<https://claude.com/partners/services>)[Startups program](<https://claude.com/programs/startups>)

Terms and policies

Privacy choices[Privacy policy](<https://www.anthropic.com/legal/privacy>)[Disclosure policy](<https://www.anthropic.com/responsible-disclosure-policy>)[Usage policy](<https://www.anthropic.com/legal/aup>)[Commercial terms](<https://www.anthropic.com/legal/commercial-terms>)[Consumer terms](<https://www.anthropic.com/legal/consumer-terms>)

Assistant

Responses are generated using AI and may contain mistakes.
