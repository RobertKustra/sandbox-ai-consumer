# sandbox-ai-consumer

Simple vLLM consumer script with Docker and Make automation.

## Build and push image

Default image references:

- Local build tag: `sandbox-ai-consumer:0.1.0`
- Push target tag: `ghcr.io/robertkustra/dev/sandbox-ai-consumer:0.1.0`

Available targets:

- `make help`
- `make build`
- `make push`

Before `make build`, target `check-git-clean` runs automatically and fails when
there are uncommitted changes in the working tree.

Override image references:

- `LOCAL_IMAGE=my-local-tag:latest make build`
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
