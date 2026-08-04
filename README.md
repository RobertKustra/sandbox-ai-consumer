# sandbox-ai-consumer

Simple vLLM consumer script with Docker and Make automation.

## Configuration via .env

The script loads values from `.env` in the current directory by default.

Supported variables:

- `VLLM_BASE_URL`
- `VLLM_MODEL`
- `VLLM_PROMPT`
- `VLLM_STRESS` (`true`/`false`, `1`/`0`, `yes`/`no`)
- `VLLM_COUNT`
- `VLLM_PARALLEL`
- `VLLM_REPEAT_MINUTES` (`0` disables repeating)

Example `.env`:

```env
VLLM_BASE_URL=http://127.0.0.1:8000
VLLM_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct
VLLM_PROMPT=Write a short hello message
VLLM_STRESS=false
VLLM_COUNT=50
VLLM_PARALLEL=8
VLLM_REPEAT_MINUTES=0
```

You can also use a custom file path:

`./ai-consumer.py --env-file .env.dev`

CLI arguments still override values loaded from `.env`.

Repeat execution examples:

- Repeat single request every 5 minutes: `./ai-consumer.py --repeat-minutes 5`
- Repeat stress cycle every 10 minutes: `./ai-consumer.py --stress --count 20 --parallel 4 --repeat-minutes 10`
- Stop repeating with `Ctrl+C`

## Build and push image

Default image references:

- Local build tag: `sandbox-ai-consumer:0.1.0`
- GitHub owner: `RobertKustra`
- Push target tag: `ghcr.io/robertkustra/dev/sandbox-ai-consumer:0.1.0` (lowercase required by Docker image naming)

Available targets:

- `make help`
- `make build`
- `make push`

Before `make build`, target `check-git-clean` runs automatically and fails when
there are uncommitted changes in the working tree.

Override image references:

- `LOCAL_IMAGE=my-local-tag:latest make build`
- `OWNER=RobertKustra make push`
- `IMAGE=ghcr.io/my-org/sandbox-ai-consumer:0.1.0 make push`

## CI/CD pipelines

This repository uses GitHub Actions workflows defined in `.github/workflows`:

- `Build and push Docker image` (`build_and_push.yaml`)
  - Runs on pushes to `development` and `main`, and can also be started manually with `workflow_dispatch`.
  - Starts with `actions/checkout` to fetch the repository history needed by the build logic.
  - Determines the target environment (`dev` for `development`, `prod` for `main`) and reads the image tag from the Makefile.
  - Logs in to GHCR using the `GHCR_TOKEN` secret so the workflow can publish the image.
  - Builds the full image reference from the Makefile and checks whether that image already exists in GHCR.
  - If the image is missing, it runs the Make-based `make push` flow to build and publish the container image.
  - For `main` branch builds, it creates a Git tag like `v<version>` after a successful push to mark the release.

- `Validate PR source policy` (`validate_development_pr_source.yaml`)
  - Runs on pull requests targeting `development` and `main`.
  - Enforces the repository promotion policy by rejecting invalid source branches.
  - `feat/*` and `feature/*` branches can target `development`, while only `development` can target `main`.

These workflows are part of the release and branch-protection process described below.

## Docker commands

Build and push without Make:

`docker build -t sandbox-ai-consumer:0.1.0 .`

`docker tag sandbox-ai-consumer:0.1.0 ghcr.io/robertkustra/dev/sandbox-ai-consumer:0.1.0`

`docker push ghcr.io/robertkustra/dev/sandbox-ai-consumer:0.1.0`

Run help:

`docker run --rm sandbox-ai-consumer:0.1.0 --help`

Run single request:

`docker run --rm sandbox-ai-consumer:0.1.0 -u http://host.docker.internal:8000 -p "Test prompt"`

Run stress mode:

`docker run --rm sandbox-ai-consumer:0.1.0 --stress --count 10 --parallel 4`

## Branch flow and merge policy

Code changes must follow this promotion path:

`feat/*` or `feature/*` -> `development` -> `main`

Rules:

- Create all changes on a feature branch.
- Open a Pull Request from `feat/*` or `feature/*` to `development`.
- After validation on `development`, open a Pull Request from `development` to `main`.
- Direct pushes to `development` and `main` are blocked by branch protection.
- PRs targeting `development` and `main` are validated by workflow `Validate PR source policy`.
- `development` accepts only `feat/*` or `feature/*` as source branches.
- `main` accepts only `development` as source branch.

This ensures every change is reviewed and promoted through the expected environments before release.

To fully enforce this rule, set `Validate PR source policy / enforce-source-policy` as a required status check in branch protection for both `development` and `main`.

For full contribution rules, see `CONTRIBUTING.md`.

### Pull Request checklist

Before merging any PR:

- CI checks are green.
- At least one approval is present.
- PR description explains scope, risk, and rollback approach.
- For runtime-impacting changes, include test evidence (logs, screenshots, or command output).
- No direct merge to `main` from `feature/*` branches; promote through `development` first.
