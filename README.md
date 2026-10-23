# Toolnest

Formerly AppScout.

## Shared Workspace

In the combined site, the header shows the active app name inside an app and Workspace elsewhere. The live interface uses American English. An **All Apps** sidebar replaces the top app tabs, shared account screens use All Apps wording, and sign-in no longer assumes an existing Toolnest account. App headers display their names without workspace breadcrumb prefixes.

Workspace now lives at **workspaceapps.vercel.app**, with an app-independent name for future additions, Musecoach-style blue light/dark themes, a shared header theme toggle, illustrated equal app cards and refreshed account/privacy pages. Both former Workspace addresses stay available for exporting device-only data and shows a migration notice. Browser storage does not move automatically between addresses; sign in again for cloud data or restore an exported review backup and transfer audio explicitly.

Toolnest and Musecoach now have an equal place in [Workspace](https://workspaceapps.vercel.app/), with one Supabase account, an app switcher, shared account settings, account-scoped device data, exports and separate app/account deletion controls. [Toolnest in Workspace](https://workspaceapps.vercel.app/toolnest) uses the existing Toolnest account IDs and catalog. [Musecoach in Workspace](https://workspaceapps.vercel.app/musecoach) offers per-take device or private cloud recording storage.

The combined implementation is maintained in the separate [public Workspace repository](https://github.com/SidAjmera/Workspace), locally alongside both original projects in `../Workspace`. Neither application is the parent product. This repository continues to contain the original standalone Toolnest implementation; the sections below describe that version unless stated otherwise.

Workspace release two adds independent, opt-in profile and review sync, cloud reviews without audio, revision checks and explicit conflict resolution, and Copy/Move controls between device and private cloud recording storage. Review sync does not upload audio. A move saves the destination before removing source audio, and moving to device excludes automatic re-upload. Release two (1.1.0) is live in the shared Workspace: 547 automated tests, TypeScript, the production build, 22 local browser checks and 22 hosted desktop/mobile checks passed. Its RELEASE_STATUS.md records the executed checks and remaining real-account/device verification.

The shared production encryption secret and the neutral Supabase Site URL/confirmation callback have been configured with approval. Existing standalone callbacks remain allowed. Real-account email delivery, confirmation and authenticated cloud recording checks are still pending.

Next.js + TypeScript software discovery, alternatives and comparison app. Designed for Vercel and Supabase, with no developer-funded AI key.

**Live site:** https://toolnest-discover.vercel.app

**Source:** https://github.com/SidAjmera/AppScout

Production is deployed from main through the connected Vercel GitHub integration. Production is connected to the AppScout Supabase project in Singapore. The live catalog endpoint returns source=database with 159 apps. Public URL/publishable-key environment variables and the server-only BYOK session secret are configured on Vercel. Authentication Site URL and exact production/local callback URLs are configured. Public signup still requires custom SMTP; email confirmation remains enabled.

## Run locally

Requires Node 22+ and pnpm 11 (the lockfile pins actual dependency versions).

```sh
pnpm install
cp .env.example .env.local
pnpm dev
```

Open http://127.0.0.1:3000. On PowerShell use `Copy-Item .env.example .env.local`. Without Supabase configuration the app runs in catalog mode: browsing, keyword searches, session preferences, detail pages and comparisons work; account features clearly explain that setup is required. This is not simulated authentication. API keys and sensitive profiles are never stored in browser localStorage. Appearance alone is persisted by next-themes.

## Supabase setup

1. Create a Supabase project. In SQL Editor run [001_appscout.sql](supabase/migrations/001_appscout.sql).
2. Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` from that project. The legacy `NEXT_PUBLIC_SUPABASE_ANON_KEY` remains supported as a fallback. Only the URL and chosen public key belong in public variables.
3. Generate a 32-byte encryption secret with `node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"`. Set `BYOK_SESSION_SECRET` on the server. Do not prefix it with NEXT_PUBLIC.
4. Seed the catalog: generate SQL with `pnpm catalog:sql` and run the generated `supabase/seed.sql` in the Supabase SQL editor after the migration. The SQL is repeatable and contains no credentials. Alternatively, load `.env.local` into the environment and run `node --env-file=.env.local scripts/seed.mjs`. This needs `SUPABASE_SERVICE_ROLE_KEY` locally; the script never prints it.
5. In Supabase Authentication URL Configuration set the production Site URL and allow `https://YOUR-PROJECT.vercel.app/auth/callback`. Add `http://127.0.0.1:3000/auth/callback` for local development. Enable email/password auth and email confirmation.
6. Configure custom SMTP before opening email signup to the public. Supabase’s built-in test mail service only delivers to organization members; keep email confirmation enabled. Free email and database quotas are finite; check the dashboard and provider documentation before inviting users. See https://supabase.com/docs/guides/auth/auth-smtp.

All user tables use RLS. Catalog data is publicly readable; edits require `app_metadata.role = "admin"` set by an operator through the Supabase dashboard or Admin API. Never use editable user_metadata for authorization. Normalized read-only platform, feature, pricing and source views project the curated app JSON; this keeps seed and editorial updates atomic.

The app uses browser-managed Supabase auth refresh and validates the user with getUser at every protected server endpoint. No service role key is used for normal reads, writes, or scoring.

## AI / BYOK

Users must sign in and choose a provider, enter a current model ID and their own key. Connection tests make a small billable provider request. OpenAI, Gemini, Anthropic and Cohere use native AI SDK adapters; Groq, OpenRouter, DeepSeek, Mistral, Together, Fireworks, Perplexity and custom APIs use their compatible chat endpoints. Model names are deliberately not hardcoded because availability changes. Supported providers list models after the first successful connection; others permit manual IDs.

Keys pass only to authenticated server endpoints. AES-256-GCM seals them into an HttpOnly, SameSite=Strict session cookie, bound to the authenticated user and a two-hour expiry. The cookie has no persistent max-age; browsers may restore session cookies, so server expiry is enforced independently. No key is written to the database, filesystem, logs, analytics, URLs or browser storage. Disconnect clears the exact cookie path; signout disconnects too. Rotating BYOK_SESSION_SECRET invalidates existing connections.

A per-user database quota limits connection tests/search pipelines to 30 per hour across serverless instances. Each search uses at most two generation calls (requirements and batched explanations), with no automatic retries. Provider prompts are validated; provider errors are sanitized. Scores and filters are entirely programmatic.

Custom endpoints are disabled until the operator sets CUSTOM_AI_ORIGINS, a comma-separated allowlist of HTTPS origins. Requests disallow credentials, non-443 ports and redirects, reject internal/reserved network ranges, and pin the DNS-validated address during the HTTPS connection. Only allow origins you trust; no browser can arbitrarily proxy internal resources.

## Privacy

Three independent optional choices default off. Preferences persist only with saved-personalization consent; search/comparison history requires history consent in the server and database. Revocation deletes associated records transactionally, including direct consent updates/deletions. Analytics has no active collector.

Data export includes account metadata, profile, preferences, consent, bookmarks, history, suggestions, deletion requests and security usage counters. Deletion removes optional data, bookmarks and suggestions immediately, revokes optional consent and queues an account deletion request. If SUPABASE_SERVICE_ROLE_KEY is present in the server environment, the auth account is deleted immediately, cascading remaining records. If absent or that call fails, an operator must process pending deletion_requests in Supabase. Never represent a queued request as completed deletion.

Before public launch the operator must fill in its identity and privacy contact in the privacy policy, establish retention/deletion response and breach processes, and assess cross-border processing. The included controls are not a legal-compliance certification.

## Catalog and evidence

159 real application entries across six categories. **Only 11 entries currently contain reviewed source-backed facts.** The remaining entries have pending-review labels; pricing, platforms and features remain unknown. This is a broad seed inventory, not 159 fully verified recommendations. No arbitrary match percentages, invented feature support or guessed prices are included. App marks are typographic placeholders, not official logo artwork.

Review details in the administrator dialog or edit src/data/catalog.json and reseed. Each verified claim needs an official evidence URL, claim description and review date. Updating the deployed database through admin takes effect immediately; local fallback data needs a source change.

`pnpm catalog:verify` creates an optional official-homepage reachability report. Reachability does not verify a feature; the script deliberately never marks facts verified.

Pricing is the lowest known entry price, not a promise that every supported feature is included at that price. Plan-specific limitations must be reviewed before choosing an app.

## Scoring

Baseline weights: requested features 40, preferences 25, pricing 15, ease 10, privacy/integrations 10. Explicit priorities increase corresponding weights; normalized weights total 100. Search platform and budget override profile defaults. Known mandatory failures are disqualified. Unknown mandatory information remains eligible but visibly flagged; it never counts as supported.

Known feature support contributes 1; unsupported/unknown contributes 0. Unrequested features, platform preferences, and unrestricted pricing use neutral baselines; the privacy/integration factor still uses its known feature evidence. Ease of use is neutral while no assessment exists. Confidence is independently the proportion of known queried facts. A high score with unknown requirements is provisional, never confirmation. The same rank function powers cards and comparisons, with AI-extracted requirements carried into comparisons.

PostgreSQL FTS retrieves AI candidates via search_catalog. Public catalog requests can use /api/catalog?q=... for database FTS; client filtering of the loaded small catalog keeps ordinary browsing fast and available without AI.

## Tests and deployment

```sh
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

Playwright uses installed Microsoft Edge for desktop and mobile Chromium emulation on this Windows workstation. Set a suitable channel/browser in playwright.config.ts for other environments. No paid browser service is needed. Production and development builds use Webpack for compatibility with this Windows environment.

Unit tests include 40 catalog retrieval scenarios, mandatory filtering, personalized ranking, search overrides, confidence, score consistency, cookie encryption/tampering/user isolation/expiry, private-network rejection, safe error messages and input schemas. An additional 9 tests execute the complete migration in embedded PostgreSQL (PGlite), verifying actual RLS isolation, consent enforcement/withdrawal, administrator permissions, FTS, deletion and quotas. Auth claims are supplied by fixtures; this does not replace a live Supabase Auth/email check or a live AI evaluation.

Import the repository into Vercel, use the Next.js preset, set the environment variables above, and deploy. Keep service role and BYOK encryption secrets server-only. Set the correct Supabase auth URLs after receiving your free vercel.app domain. GitHub and Vercel hosting are now configured: the public repository is SidAjmera/AppScout and the Vercel project is appscout in sidajmera's projects (Hobby). Vercel uses Node 24 and ENABLE_EXPERIMENTAL_COREPACK=1 to honor the pinned pnpm version. The AppScout Supabase project is connected. Local .env.local is ignored by Git; never commit environment values.

Live signup/login, email confirmation, cross-user database RLS, saved preferences/bookmarks, deletion and real provider calls require configured accounts and must be checked before launch. Use two disposable test accounts in a development Supabase project; verify that each cannot read or write the other's rows, consent withdrawal purges stored data, and each provider's invalid/expired/quota errors are understandable. Performance and recommendation quality targets in the brief remain goals until measured with real provider traffic and user testing.

Windows/OneDrive note: if a later build reports EPERM while clearing generated directories, stop the dev server and remove only this project’s .next cache before rebuilding. Source files and .env.local must be preserved. The final build was verified after clearing the generated cache.
