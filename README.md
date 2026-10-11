# hermes-ark-plan-plugin

Hermes provider plugin for Volcengine ARK Agent Plan and Coding Plan. Version 1.5.0.

## Providers

| Provider | Protocol | Base URL | Key variable | Model list |
|---|---|---|---|---|
| `ark-agentplan` | OpenAI Responses | `https://ark.cn-beijing.volces.com/api/plan/v3` | `ARK_PLAN_API_KEY` | entered manually |
| `ark-coding-plan` | OpenAI Chat Completions | `https://ark.cn-beijing.volces.com/api/coding/v3` | `ARK_CODING_API_KEY` | read live |

Only OpenAI-compatible providers are registered (Agent Plan → Responses, Coding Plan →
Chat Completions). The two subscriptions use separate keys. No Claude/Codex settings or
`ANTHROPIC_*` environment variables are modified.

Aliases: `ark-plan`, `volcengine-ark-plan`, `ark-agent-plan` → Agent Plan;
`ark-coding`, `volcengine-ark-coding-plan` → Coding Plan.

## No model id is hardcoded

This plugin ships **no static model list**. `fallback_models` is empty for both
providers, and a regression test fails the build if a model-id-looking literal is
introduced into `__init__.py`.

**Coding Plan — dynamic catalog.** At selection time the provider reads the plan's own
`/models` endpoint and offers what it returns, so models appear and disappear with the
account's catalog instead of with a plugin release. Rows are filtered to what a chat
agent can actually use:

- rows whose `status` is `Shutdown` or `Retiring` are dropped;
- rows whose `domain` is `Router` are dropped;
- rows that do not declare `text` in `modalities.output_modalities` are dropped —
  together with the two rules above this removes video, image, 3D and embedding models;
- the result is de-duplicated and sorted. Roughly 16 entries on a current account.

The catalog is cached in-process for five minutes, and a user-configured `model.base_url`
is followed (`<your-base-url>/models`) so a proxy deployment lists through the proxy.

**Agent Plan — manual entry.** `/api/plan/v3/models` does not exist (verified 404), so
the provider reports no catalog and the model id is typed instead:

```sh
hermes chat --provider ark-agentplan -m YOUR_AGENT_PLAN_MODEL_ID
```

**When the catalog cannot be read** — no key, network failure, non-JSON body, or an
endpoint change — `fetch_models()` returns nothing and Hermes falls back to manual entry.
The provider is never left without a way to pick a model.

### Listing is not entitlement

**列表里有，不等于你的套餐能用。** The catalog is the platform's model list, and the plan
enforces entitlement per request. Two measured examples:

- `doubao-seed-2-0-lite-260428` is present in the live catalog but returns
  `UnsupportedModel` on Coding Plan, both as that versioned id and as `doubao-seed-2.0-lite`;
- `doubao-seed-2-0-mini-260428` and `doubao-seed-2.1-lite` are present and do work.

Because the filter cannot know your entitlements, manual entry stays available for both
providers — type any id the plan accepts, including a short alias such as
`glm-5.3-flash` that never appears in the catalog listing.

## Install

```sh
hermes plugins install infinmalum/hermes-ark-plan-plugin
```

Manual installation (fish-compatible):

```fish
git clone https://github.com/infinmalum/hermes-ark-plan-plugin.git
mkdir -p ~/.hermes/plugins/model-providers
ln -s "$PWD/hermes-ark-plan-plugin" ~/.hermes/plugins/model-providers/ark-plan
```

Update an existing `ark-plan` / `ark-agentplan` installation; do not load two copies. For
named profiles use that profile's `$HERMES_HOME`. A running client resolves the catalog
when it opens the picker, so restart it after upgrading from a version that hardcoded
models.

## Keys

Store only the subscriptions you use in the active Hermes home's `.env`
(default `~/.hermes/.env`):

```dotenv
# Optional, for Agent Plan only
ARK_PLAN_API_KEY=YOUR_AGENT_PLAN_KEY
# Optional, for Coding Plan only
ARK_CODING_API_KEY=YOUR_CODING_PLAN_KEY
```

The key is only read from the environment when the caller does not pass one. Removing an
exhausted Agent Plan key does not remove plugin support. Never commit keys or put them in
`config.yaml`.

## Usage

```sh
# Coding Plan: pick any live model from the picker, or type one
hermes chat --provider ark-coding-plan -m deepseek-v4-1-flash-260910
# Agent Plan: always typed
hermes chat --provider ark-agentplan -m YOUR_AGENT_PLAN_MODEL_ID
```

To make Coding Plan the default:

```sh
hermes config set model.provider ark-coding-plan
hermes config set model.default YOUR_MODEL_ID
```

The plugin does not migrate the main provider or auxiliary tasks automatically.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

Offline tests (no API quota) cover provider identities, URLs, transports, alias
uniqueness, the ban on hardcoded model literals, catalog filtering, custom-base-URL
handling, the manual-entry fallback when the catalog is unreadable, and README
consistency.

Verified live against Coding Plan: the catalog endpoint returns HTTP 200 and the
provider resolves 16 selectable ids through the real Hermes runtime;
`glm-5-3-flash-260828`, `deepseek-v4-1-flash-260910`, `doubao-seed-2-1-lite-260915`
and `doubao-seed-2.0-mini` answer requests; `doubao-seed-2.1-lite` also accepts image
input. GLM rejects `thinking.type=disabled`, and a too-small output limit can be
consumed entirely by reasoning, leaving the text empty. Agent Plan needs an active
Agent Plan key for live verification; its registration and endpoint are covered
offline.

## License

MIT
