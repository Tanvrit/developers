<!-- Tool-neutral mirror of CLAUDE.md. Keep the two in sync; they differ only by the session-plans path. -->

# developers — the developers.tanvrit.com OpenAPI portal

Static site (no framework) that renders the Tanvrit platform API reference with Scalar and serves the hand-authored OpenAPI spec plus auth guides. Consumed by external integrators and internal engineers. Deploys to **Cloudflare Pages** project `tanvrit-developers` → https://developers.tanvrit.com.

This is a **Node/Python static project — there is no Gradle here.** The API it documents lives in `server/`; keep the spec in sync with real server routes (spec `title` is "Tanvrit Server API", POST-RPC style, envelope `{ status, message, payload }`).

## Build / Run / Test

```bash
npm run dev        # wrangler pages dev . --port=4000  → http://localhost:4000
npm run bundle     # python3 scripts/bundle.py → regenerates openapi.yaml from openapi/*.yaml
npm run deploy     # bundle + wrangler pages deploy . --project-name=tanvrit-developers  (SHIPS PROD — see Blast Radius)
```

There is no test suite and no `deploy.sh`. Requires Python 3 with `PyYAML` (`pip3 install pyyaml`) for `bundle.py`, and `wrangler` (via `npx`) for dev/deploy. `wrangler.toml` sets `pages_build_output_dir = "."` — the whole repo root is the served output.

## Spec authoring — the one workflow that matters

`openapi.yaml` (712 KB, at repo root) is a **generated artifact that is committed and served** (Scalar reads it via `data-url="/openapi.yaml"` in `index.html`). Never hand-edit it.

- Edit the per-feature source under `openapi/<feature>.yaml` (paths + `components.schemas`) or shared bits in `openapi/base.yaml` (info, servers, tags, `securitySchemes`, shared schemas).
- Run `npm run bundle`, then commit **both** the changed `openapi/*.yaml` and the regenerated `openapi.yaml`.
- `scripts/bundle.py` merges files in the hardcoded `FEATURE_ORDER` list (20 features, `auth`…`platform-admin`). **A new `openapi/<feature>.yaml` is silently skipped unless you add its name to `FEATURE_ORDER` in `scripts/bundle.py`.**
- The bundler prints `WARNING: duplicate path`/`duplicate schema` on collisions and last-writer-wins. Treat any warning as a defect to resolve — do not ship a spec with duplicates.

Static pages live alongside: `index.html` (Scalar reference), `portal.html` (developer portal), `docs/auth/*.html` (auth/onboarding/OAuth guides + `style.css`). Edit these directly. `_headers` forces `no-cache` + `application/yaml` on `/openapi.yaml` and `/openapi/*` and sets baseline security headers; `_redirects` sends unknown paths to `/index.html` (200 rewrite) — literal files are served first.

## Code patterns / conventions

Monorepo conventions are owned by `docs/` — link, don't restate (ADR-037):

- Repo layout, deploy dispatch, cross-cutting rules → root `/Users/viveksingh/Developer/tanvrit/CLAUDE.md`.
- Security / secrets rules → `docs/SECURITY_GUIDELINES.md` and root `CONTRIBUTING.md`.
- API naming (snake_case wire, `@SerialName` stability, POST-RPC route names) → `docs/NAMING_CONVENTIONS.md`. The spec must mirror the server's actual `@SerialName` field names and route casing.
- Architecture decisions (incl. ADR-037 "link don't duplicate", and the R23/R24 CI-runner migration notes referenced in `.github/workflows/deploy.yml`) → `docs/decisions/`.

Repo-specific deltas only:

- **Two auth schemes documented**, keep both accurate: JWT `Authorization: Bearer <token>` (from `POST /api/auth/AUTHENTICATE` or `/api/auth/LOGIN_EMAIL`) for most endpoints; `X-API-Key` (from `POST /api/ai/v1/keys/create`) for the AI Commerce Gateway. Every `/api/*` request also needs the `X-App-ID` header — the multi-tenant contract (root CLAUDE.md). Reflect these in `openapi/base.yaml` `securitySchemes` and the `index.html` comment block.
- `servers:` in `base.yaml` are `https://api.tanvrit.com` (prod) and `http://localhost:8080` (local). Scalar routes "Try it" calls through `data-proxy-url="https://proxy.scalar.com"`.
- `.editorconfig` governs formatting; there is no ktlint/eslint gate in this repo.

## Deployment & CI/CD

`.github/workflows/deploy.yml` deploys **on every push to `main`** (and `workflow_dispatch`):

- Runs on the self-hosted runner `group: tanvrit, labels: [Linux]` — wrangler is pre-authenticated via runner-local Cloudflare creds. Migrating to `ubuntu-latest` needs a `CLOUDFLARE_API_TOKEN` org secret (R23). Do not change the runner labels without reading the R23/R24 comments in the workflow.
- Uses `environment: production` (**approval-gated**) with `CLOUDFLARE_ACCOUNT_ID=ce3f0ef57641c98d52af95c069bbb6a2` and `CLOUDFLARE_API_TOKEN` from secrets. Command: `npx wrangler pages deploy . --project-name tanvrit-developers --branch main --commit-dirty=true`.
- CI does **not** run `bundle.py` — it deploys the committed tree as-is. So a stale `openapi.yaml` ships if you edited `openapi/*.yaml` but forgot `npm run bundle`. Always bundle before pushing spec changes.

## Blast Radius — needs explicit authorization

Auto-mode never overrides these; confirm each time.

- **Never `npm run deploy`, and never push spec/site changes to `main` casually, unless the user says deploy** — both ship production `developers.tanvrit.com` (push→main triggers `deploy.yml`).
- **Never hand-edit the generated `openapi.yaml`** — edit `openapi/<feature>.yaml`/`base.yaml` and run `npm run bundle`.
- **Never rename/remove an `openapi/<feature>.yaml` without updating `FEATURE_ORDER`** in `scripts/bundle.py`, or it drops silently from the spec.
- **Never change documented `@SerialName`/route names to diverge from the live server** — the spec is a contract; drift breaks integrators (`docs/NAMING_CONVENTIONS.md`).
- **Never commit secrets** — no `.env*`, no `CLOUDFLARE_API_TOKEN`, no `*.pem`/`*.p8`/`service-account*.json` (`.gitignore` already blocks them; keep it that way).
- **Never edit `wrangler.toml`, `_headers`, `_redirects`, or the `deploy.yml` runner/environment config** (project name, account id, self-hosted labels, approval gate) without explicit instruction.
- **Never bypass git hooks** (`--no-verify`) or force-push.
- N/A here (no Gradle/KMP in this repo): `VERSION_*`/`corePluginVersion`, `BaseDataClass`, `settings.gradle.kts` — those guards live in `sdk/`, `core/`, `server/`.

## AI assistant: skills & docs

- Workspace skill catalog: `/Users/viveksingh/Developer/tanvrit/.claude/skills/` (audit-* lenses; e.g. `audit-api-contract` for SDK↔server↔spec drift).
- Monorepo docs index: `/Users/viveksingh/Developer/tanvrit/docs/INDEX.md`; ADRs at `docs/decisions/`.
- Session plans (this repo has no local `docs/`): `~/.codex/plans/`.
