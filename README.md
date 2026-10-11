# hermes-ark-plan-plugin

Hermes provider plugin for Volcengine ARK Agent Plan and Coding Plan. Version 1.4.0.

## Providers

| Provider | Protocol | Base URL | Key variable |
|---|---|---|---|
| `ark-agentplan` | OpenAI Responses | `https://ark.cn-beijing.volces.com/api/plan/v3` | `ARK_PLAN_API_KEY` |
| `ark-coding-plan` | OpenAI Chat Completions | `https://ark.cn-beijing.volces.com/api/coding/v3` | `ARK_CODING_API_KEY` |

Only OpenAI-compatible providers are registered: Agent Plan uses Responses;
Coding Plan uses Chat Completions. Anthropic providers and their aliases were removed
in v1.3.0. Existing users must switch any removed provider IDs to the corresponding
`ark-agentplan` or `ark-coding-plan` provider.
The two subscriptions use separate keys. No Claude/Codex settings or `ANTHROPIC_*`
environment variables are modified.

Aliases: `ark-plan`, `volcengine-ark-plan`, `ark-agent-plan` → Agent Plan Responses;
`ark-coding`, `volcengine-ark-coding-plan` → Coding Plan OpenAI.

The key setup and model selection pages now show one entry per subscription:
`Volcengine ARK Agent Plan` and `Volcengine ARK Coding Plan`. Protocol details remain
in the provider descriptions; Hermes desktop itself is not modified.

## Local model catalogs

Each subscription exposes its curated local model catalog in Hermes.

| Exact model ID | Agent Plan | Coding Plan |
|---|---|---|
| `glm-5.3` | Yes | Yes |
| `glm-5.3-flash` | Yes | Yes |
| `doubao-seed-2.1-lite` | Yes | Yes |
| `doubao-seed-2.0-mini` | Yes | Yes |
| `deepseek-v4-pro` | No | Yes |
| `deepseek-v4.1-flash` | No | Yes |

**列出模型不代表账户一定有权限。** Catalog entries are local choices, not live
entitlement checks, and manual model entry remains possible. `doubao-seed-2.0-lite`
was rejected by Coding Plan with `UnsupportedModel`, so it is replaced by
`doubao-seed-2.1-lite`, which was verified live for text and image input.
Remote model-list and `/models` health probes are disabled. An actual inference request
is needed to validate credentials and model support.

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

Update an existing `ark-plan` / `ark-agentplan` installation; do not load two copies.
For named profiles use that profile's `$HERMES_HOME`. Restart a running client if the
old providers or model catalog are still shown.

## Keys

Store only the subscriptions you use in the active Hermes home's `.env`
(default `~/.hermes/.env`):

```dotenv
# Optional, for Agent Plan only
ARK_PLAN_API_KEY=YOUR_AGENT_PLAN_KEY
# Optional, for Coding Plan only
ARK_CODING_API_KEY=YOUR_CODING_PLAN_KEY
```

Removing an exhausted Agent Plan key does not remove plugin support.
Never commit keys or put them in config.yaml.

## Usage

```sh
hermes chat --provider ark-coding-plan -m glm-5.3-flash
hermes chat --provider ark-agentplan -m glm-5.3-flash
```

To make Coding Plan the default:

```sh
hermes config set model.provider ark-coding-plan
hermes config set model.default glm-5.3-flash
```

The plugin does not automatically migrate the main provider or auxiliary tasks.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

Offline tests verify two OpenAI-compatible providers, aliases, URLs, transports, credential isolation,
exact local catalogs and README consistency without spending API quota.
Verified live on Coding Plan: `glm-5.3`, `glm-5.3-flash`, `deepseek-v4.1-flash`,
`doubao-seed-2.0-mini` and `doubao-seed-2.1-lite` (text and image input).
`doubao-seed-2.0-lite` returns `UnsupportedModel`. GLM rejected
`thinking.type=disabled`; too-small token limits may leave only reasoning, no text.
Agent Plan requires an active Agent Plan key for live verification; its registration
and endpoint are covered by offline tests. Historical Anthropic endpoint tests do not
mean this version registers an Anthropic provider.

## License

MIT
