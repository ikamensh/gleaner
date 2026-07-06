# story: scrub-before-upload [cli]
As a developer I can have PII and secrets stripped from transcripts before they leave my machine so that central storage never holds my credentials or personal data.

## Rules
- With scrubbing enabled, secret-shaped patterns (e.g. `sk-...` API keys) and personal data (e.g. email addresses) are replaced with placeholders client-side, before upload.
- The stored raw transcript on the server does not contain the original secret.
- Metadata counts are unaffected by scrubbing.

## Examples
- Given scrubbing is enabled and a session transcript contains a mock API key
  When the upload hook runs
  Then the transcript retrieved from the server contains a placeholder (e.g. `<REDACTED>`) instead of the key.
