
IMAGE ?= ghcr.io/RobertKustra/dev/sandbox-ai-consumer:0.1.0

.PHONY: help check-git-clean build push

help:
	@echo "Available targets:"
	@echo "  make build    - Build Docker image after git clean check"
	@echo "  make push     - Build and push Docker image"
	@echo "  make check-git-clean - Fail if working tree has uncommitted changes"
	@echo "  IMAGE=<ref> make build|push - Override image reference"

check-git-clean:
	@if [ -n "$(shell git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Commit or stash all changes before build."; \
		git status --short; \
		exit 1; \
	fi

build: check-git-clean
	docker build -t $(IMAGE) .

push: build
	docker push $(IMAGE)
