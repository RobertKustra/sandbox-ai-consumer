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
