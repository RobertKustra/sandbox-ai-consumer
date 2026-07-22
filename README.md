# sandbox-ai-consumer

Simple vLLM consumer script with Docker and Make automation.

## Build and push image

Default image reference:

ghcr.io/<owner>/dev/sandbox-ai-consumer:0.1.0

Available targets:

- `make help`
- `make build`
- `make push`

Before `make build`, target `check-git-clean` runs automatically and fails when
there are uncommitted changes in the working tree.

Override the image reference:

`IMAGE=ghcr.io/my-org/sandbox-ai-consumer:0.1.0 make build`

## Docker commands

Build without Make:

`docker build -t ghcr.io/<owner>/dev/sandbox-ai-consumer:0.1.0 .`

Run help:

`docker run --rm ghcr.io/<owner>/dev/sandbox-ai-consumer:0.1.0 --help`

Run single request:

`docker run --rm ghcr.io/<owner>/dev/sandbox-ai-consumer:0.1.0 -u http://host.docker.internal:8000 -p "Test prompt"`

Run stress mode:

`docker run --rm ghcr.io/<owner>/dev/sandbox-ai-consumer:0.1.0 --stress --count 10 --parallel 4`
