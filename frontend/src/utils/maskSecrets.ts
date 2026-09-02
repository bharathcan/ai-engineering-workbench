/** Defense-in-depth display filter for the AI Run screen. Nothing in this
 * codebase constructs prompts from secrets (see the comment on
 * AIRunResponse.prompt in backend/app/schemas/ai_run.py), but the screen
 * renders raw AI provider prompt/response text, so it masks common secret
 * shapes before display in case one is ever pasted into a requirement or
 * instructions field. This is a pattern filter, not a guarantee — it will
 * not catch every possible secret format. */
const SECRET_PATTERNS: RegExp[] = [
  /sk-[A-Za-z0-9]{20,}/g,
  /AKIA[0-9A-Z]{16}/g,
  /Bearer\s+[A-Za-z0-9._-]{10,}/gi,
  /-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----/g,
]

export function maskSecrets(text: string): string {
  let masked = text
  for (const pattern of SECRET_PATTERNS) {
    masked = masked.replace(pattern, '[MASKED]')
  }
  return masked
}
