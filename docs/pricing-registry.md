# Pricing registry

The versioned registry is config/pricing/model_pricing_registry.json. Resolution requires exact provider, exact canonical model, and an effective timestamp. There is no generic rate and no implicit alias.

Bundled entries are a reviewed snapshot, not a live billing service:

| Provider | Model | Status | Official source |
| --- | --- | --- | --- |
| OpenAI | gpt-4.1 | Reviewed | https://openai.com/index/gpt-4-1/ |
| Anthropic | claude-sonnet-4-20250514 | Historical, closed at 2026-06-15 retirement | https://platform.claude.com/docs/en/about-claude/pricing |
| Anthropic | claude-sonnet-5 | Reviewed, effective from 2026-06-30 launch | https://platform.claude.com/docs/en/about-claude/pricing |
| xAI | grok-4.6 | Reviewed, context-tiered schedule effective from 2026-09-19 review | https://docs.x.ai/developers/pricing |
| Google | gemini-3.8-flash | Reviewed, effective from 2026-09-02 launch | https://ai.google.dev/gemini-api/docs/pricing |
| DeepSeek | none | Schema-supported, intentionally unpriced | Official evidence was not reliably retrieved in this pass |
| Moonshot | none | Schema-supported, intentionally unpriced | Official evidence was not reliably retrieved in this pass |

Historical valuations may be pinned with each ledger event so a registry update does not rewrite prior estimates. Use the pricing-update Skill for a reviewed, human-approved update.

Lifecycle evidence is recorded separately from rate evidence:

- Anthropic retirement table: https://platform.claude.com/docs/en/about-claude/model-deprecations
- Anthropic Sonnet 5 launch: https://platform.claude.com/docs/en/release-notes/overview
- Google model release dates: https://ai.google.dev/gemini-api/docs/deprecations
- xAI Grok 4.6 launch notice: https://x.ai/news/grok-4-6

Because the xAI launch notice does not establish the complete current cached/context-tier schedule, that schedule begins at its conservative 2026-09-19 review date.

The resolver evaluates effective dates, context tiers, UTC peak/off-peak windows, service tiers, batch/fast variants, and regional multipliers from data. Missing condition metadata yields a defensible range or Unknown, never an assumed cheaper rate.
